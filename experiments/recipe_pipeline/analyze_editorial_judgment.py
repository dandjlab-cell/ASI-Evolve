#!/usr/bin/env python3
"""
Analyze editorial judgment from approved recipe edits.

Cross-references:
  - /watch-video Pass 1 frame analysis → dense visual descriptions at 2fps
  - Approved edit JSON (parsed from Premiere XML) → structural decisions
  - Pipeline manifest → what the pipeline proposed
  - Pipeline scan.json → VLM descriptions of clip content
  - Pipeline beats.json → editorial beat descriptions
  - Existing annotation JSON (optional) → beat_groups, skipped_pipeline_beats

Uses Claude CLI to infer editorial reasoning per beat, then outputs
an Obsidian markdown annotation file for Dan to review and correct.

Usage:
    python analyze_editorial_judgment.py \
        --recipe basil_pesto \
        --approved approved_edits/basil_pesto.json \
        --manifest ~/DevApps/roughcut-ai/runs/basil_pesto/basil_pesto_manifest.json \
        --scan ~/DevApps/roughcut-ai/runs/basil_pesto/scan.json \
        --beats ~/DevApps/roughcut-ai/runs/basil_pesto/beats.json \
        --frame-analysis ~/DevApps/storyboard-gen/docs/watch-video/pass1_basil_pesto.md \
        --output ~/DevApps/Brain/Projects/ASI-Evolve/Annotations/basil_pesto.md
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from typing import Dict, List, Optional, Tuple


def load_frame_analysis(frame_analysis_path: str, fps: float = 2.0) -> List[dict]:
    """Load Pass 1 frame analysis from /watch-video markdown.

    Parses the shot list table into a list of dicts with:
      frame, time_sec, camera, subject, notes

    Returns list sorted by frame number.
    """
    frames = []
    with open(frame_analysis_path) as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|") or line.startswith("| Frame") or line.startswith("|---"):
                continue
            parts = [p.strip() for p in line.split("|")]
            # parts[0] is empty (before first |), parts[-1] is empty (after last |)
            parts = [p for p in parts if p]
            if len(parts) < 4:
                continue
            try:
                frame_num = int(parts[0])
            except ValueError:
                continue
            time_str = parts[1]  # e.g. "0:01.5"
            # Parse MM:SS.f format
            time_sec = 0.0
            if ":" in time_str:
                mm, ss = time_str.split(":", 1)
                time_sec = float(mm) * 60 + float(ss)
            else:
                time_sec = float(time_str)
            frames.append({
                "frame": frame_num,
                "time_sec": time_sec,
                "camera": parts[2],
                "subject": parts[3],
                "notes": parts[4] if len(parts) > 4 else "",
            })
    return sorted(frames, key=lambda f: f["frame"])


def get_visual_context(
    frame_analysis: List[dict], timeline_in: float, timeline_out: float, margin: float = 0.5
) -> str:
    """Get visual descriptions from frame analysis for a timeline window.

    Returns formatted string of frame descriptions covering the beat's
    timeline range plus a margin before/after for context.
    """
    start = timeline_in - margin
    end = timeline_out + margin
    relevant = [f for f in frame_analysis if start <= f["time_sec"] <= end]
    if not relevant:
        return "(no frame analysis coverage for this timeline range)"

    lines = []
    for f in relevant:
        marker = ""
        if abs(f["time_sec"] - timeline_in) < 0.3:
            marker = " ← CUT IN"
        elif abs(f["time_sec"] - timeline_out) < 0.3:
            marker = " ← CUT OUT"
        notes = f" ({f['notes']})" if f["notes"] else ""
        lines.append(f"  [{f['time_sec']:.1f}s] {f['camera']}: {f['subject']}{notes}{marker}")
    return "\n".join(lines)


def load_beat_groups(annotation_path: str) -> Tuple[List[dict], List[int]]:
    """Load beat_groups and skipped_pipeline_beats from existing annotation JSON.

    Returns (beat_groups, skipped_beats). Empty lists if file doesn't exist.
    """
    if not annotation_path or not os.path.exists(annotation_path):
        return [], []
    with open(annotation_path) as f:
        data = json.load(f)
    return data.get("beat_groups", []), data.get("skipped_pipeline_beats", [])


def find_beat_group(beat_idx: int, beat_groups: List[dict]) -> Optional[dict]:
    """Find which beat group a beat belongs to, if any."""
    for group in beat_groups:
        if beat_idx in group.get("beats", []):
            return group
    return None


def load_scan_descriptions(scan_path: str, clip_name: str, in_point: float) -> str:
    """Get VLM description of a clip near a specific in-point from scan.json."""
    with open(scan_path) as f:
        scan = json.load(f)

    clip_key = clip_name.replace(".mov", "")
    clip_data = scan.get("clips", {}).get(clip_key, {})
    frames = clip_data.get("frames", [])

    if not frames:
        return ""

    # Find the frame closest to the in-point
    best = min(frames, key=lambda fr: abs(fr["t"] - in_point))
    # Also get surrounding frames for context
    nearby = sorted(frames, key=lambda fr: abs(fr["t"] - in_point))[:3]

    descriptions = []
    for fr in nearby:
        descriptions.append(f"[{fr['t']:.1f}s] {fr['description']}")

    return "\n".join(descriptions)


def detect_camera(filename: str, v1_prefix: str) -> str:
    """Detect camera from filename prefix."""
    if filename.startswith(v1_prefix):
        return "front"
    return "overhead"


def detect_v1_prefix(manifest: dict) -> str:
    """Detect V1 camera prefix from pipeline manifest."""
    for entry in manifest.get("timeline", []):
        v1 = entry.get("v1")
        if v1 and isinstance(v1, dict) and v1.get("file"):
            return v1["file"][:4]
    return "B19I"


def match_approved_to_pipeline(
    approved: dict, pipeline: dict, tolerance: float = 3.0
) -> Dict[int, dict]:
    """Match approved beats to pipeline beats by filename + timecode proximity.

    Returns dict mapping approved beat_index → pipeline timeline entry.
    """
    matches = {}
    pipeline_timeline = pipeline.get("timeline", [])
    used = set()

    for a_entry in approved.get("timeline", []):
        a_idx = a_entry["beat_index"]
        a_clip = a_entry.get("v1") or a_entry.get("v2")
        if not a_clip or not a_clip.get("file"):
            continue

        best_match = None
        best_dist = float("inf")

        for i, p_entry in enumerate(pipeline_timeline):
            if i in used:
                continue
            # Check both v1 and v2 from pipeline
            for track in ("v1", "v2"):
                p_clip = p_entry.get(track)
                if not p_clip or not isinstance(p_clip, dict):
                    continue
                if p_clip.get("file") != a_clip["file"]:
                    continue
                dist = abs(p_clip.get("in", 0) - a_clip.get("in", 0))
                if dist < best_dist:
                    best_dist = dist
                    best_match = (i, p_entry, track)

        if best_match is not None:
            used.add(best_match[0])
            matches[a_idx] = {
                "pipeline_entry": best_match[1],
                "matched_track": best_match[2],
                "distance": best_dist,
            }

    return matches


def determine_verdict(
    approved_clip: dict,
    pipeline_match: Optional[dict],
    v1_prefix: str,
    timing_threshold: float = 2.0,
) -> str:
    """Determine what Dan did relative to the pipeline."""
    if pipeline_match is None:
        return "added"

    p_entry = pipeline_match["pipeline_entry"]
    p_track = pipeline_match["matched_track"]
    p_clip = p_entry.get(p_track, {})

    if not p_clip or not p_clip.get("file"):
        return "added"

    a_file = approved_clip["file"]
    p_file = p_clip["file"]

    # Camera swap: different camera prefix
    a_cam = "front" if a_file.startswith(v1_prefix) else "overhead"
    p_cam = "front" if p_file.startswith(v1_prefix) else "overhead"
    if a_cam != p_cam:
        return "camera_swapped"

    # Timing shift
    in_shift = abs(approved_clip.get("in", 0) - p_clip.get("in", 0))
    if in_shift > timing_threshold:
        return "trimmed"

    return "kept"


def describe_effects(clip: dict) -> str:
    """Describe editorial effects applied to a clip for the LLM prompt."""
    effects = clip.get("effects", {})
    if not effects:
        return ""

    parts = []

    # Speed
    speed = effects.get("speed")
    if speed:
        spd_pct = speed.get("speed_percent", 100)
        if speed.get("type") == "speed_ramp":
            kfs = speed.get("keyframes", [])
            ramp_in = next((k for k in kfs if k.get("type") == "ramp_in"), None)
            ramp_out = next((k for k in kfs if k.get("type") == "ramp_out"), None)
            if ramp_in and ramp_out:
                parts.append(f"Speed ramp ({spd_pct}% base, ramp between {ramp_in['time_sec']:.1f}s-{ramp_out['time_sec']:.1f}s)")
            else:
                parts.append(f"Speed ramp ({spd_pct}%)")
        else:
            parts.append(f"Constant slow-motion ({spd_pct}%)")
        if speed.get("reverse"):
            parts.append("Reversed")

    # Scale / zoom
    motion = effects.get("motion", {})
    scale = motion.get("scale")
    if scale:
        if scale.get("type") == "animated":
            start_v = scale.get("start_value", 50)
            end_v = scale.get("end_value", 50)
            direction = "zoom in" if end_v > start_v else "zoom out"
            parts.append(f"Animated {direction} ({start_v}% -> {end_v}%)")
        elif scale.get("type") == "static":
            parts.append(scale.get("editorial_note", f"Scale: {scale.get('value')}%"))

    # Position offset
    pos = motion.get("position")
    if pos and pos.get("type") == "animated":
        parts.append("Animated reframe (position keyframes)")
    elif pos and pos.get("type") == "static":
        parts.append(f"Reframed (offset h:{pos['horiz']:.2f} v:{pos['vert']:.2f})")

    return "; ".join(parts)


def describe_nested(clip: dict) -> str:
    """Describe a nested sequence clip."""
    if not clip.get("nested"):
        return ""
    inner = clip.get("inner_clips", [])
    return f"Nested sequence '{clip.get('nest_name', '?')}' with {len(inner)} inner clips"


def find_overlapping_mogrts(
    timeline_in: float, timeline_out: float, production_layers: dict
) -> List[str]:
    """Find production layer items that overlap a beat's timeline range.

    Filters out always-on layers (watermarks, adjustment layers that span
    the full timeline) since those aren't editorial signals.
    """
    overlaps = []
    for category, items in production_layers.items():
        # Skip always-on layers — not editorial context
        if category in ("watermarks", "adjustment_layers"):
            continue
        for item in items:
            item_in = item.get("timeline_in_sec", 0)
            item_out = item.get("timeline_out_sec", 0)
            # Check overlap
            if item_in < timeline_out and item_out > timeline_in:
                label = category.replace("_", " ").title()
                fname = item.get("file", "?")
                overlaps.append(f"{label}: {fname} ({item_in:.1f}s-{item_out:.1f}s)")
    return overlaps


# Recipe video structure (from Dan's editorial rules):
# 1. Beauty opener (2-3 shots) — scroll-stopper yum moments, mini-story, camera switching
# 2. Ingredient dump — things going into bowl/bag/blender
# 3. Departure — things leaving frame to get baked, refrigerated, etc.
# 4. Transformation — food changes: stirring, blending, sizzling
# 5. Money shots — chocolate pouring, sizzle, steam, etc.
# 6. Beauty close — plating, final hero shots
#
# These sections are cut to music: cuts on beats, hold through phrases,
# build energy through acceleration, breathing room after dense sequences.

# Keywords for each recipe section (matched against beat descriptions)
_SECTION_KEYWORDS = {
    "ingredient dump": [
        "pour", "add", "sprinkle", "scatter", "dump", "measure",
        "drop", "spoon", "squeeze", "drizzle", "crack",
    ],
    "prep / knife work": [
        "chop", "slice", "dice", "mince", "grate", "peel", "crush",
        "zest", "julienne", "cut", "trim", "debone",
    ],
    "technique / active cooking": [
        "stir", "whisk", "mix", "fold", "toss", "sear", "sauté",
        "flip", "fry", "bake", "roast", "grill", "broil",
    ],
    "transformation": [
        "transformation", "transform", "golden", "brown", "bubbl",
        "melt", "thicken", "reduce", "carameliz", "crisp",
    ],
    "money shot": [
        "sizzl", "steam", "chocolat", "glaz", "drip", "ooze",
        "stretch", "pull apart",
    ],
}


def infer_recipe_section(timeline_in: float, total_duration: float, beat_desc: str) -> str:
    """Infer which recipe section a beat falls in.

    Uses position in timeline + beat description keywords.
    Recipe structure: beauty opener → ingredient dump → prep → technique →
    transformation → money shots → beauty close.
    """
    pct = timeline_in / total_duration if total_duration > 0 else 0
    desc_lower = (beat_desc or "").lower()

    # Strong positional signals
    if pct < 0.08:
        return "beauty opener (scroll-stopper, 2-3 hero shots)"
    if pct > 0.92:
        return "beauty close (plating, final hero)"

    # Check for transformation keyword (strong signal anywhere)
    if "transformation" in desc_lower or "TRANSFORMATION" in (beat_desc or ""):
        return "transformation (food changes state)"

    # Keyword matching against description
    for section, keywords in _SECTION_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return section

    # Positional fallback for mid-edit
    if pct > 0.80:
        return "plating / finishing"
    if pct > 0.60:
        return "late-edit (likely transformation or money shots)"

    return "mid-edit"


def build_beat_analysis_prompt(
    beat_idx: int,
    approved_clip: dict,
    camera: str,
    duration: float,
    verdict: str,
    beat_description: str,
    beat_type: str,
    pipeline_clip_info: str,
    scan_description: str,
    visual_context: str,
    prev_beat_info: str,
    next_beat_info: str,
    beat_group_info: str,
    effects_info: str = "",
    nested_info: str = "",
    mogrt_overlaps: List[str] = None,
    recipe_section: str = "",
    is_stop_motion: bool = False,
    stop_motion_info: str = "",
) -> str:
    """Build the LLM prompt for analyzing one beat's editorial reasoning."""
    effects_block = ""
    if effects_info:
        effects_block = f"\n- **Effects applied:** {effects_info}"
    if nested_info:
        effects_block += f"\n- **Nesting:** {nested_info}"
    if is_stop_motion:
        effects_block += f"\n- **Stop-motion sequence:** {stop_motion_info}"

    mogrt_block = ""
    if mogrt_overlaps:
        mogrt_block = "\n- **Overlapping production layers:** " + "; ".join(mogrt_overlaps)

    section_block = ""
    if recipe_section:
        section_block = f"\n- **Recipe section:** {recipe_section}"

    return f"""Analyze this editorial beat from a recipe video. These videos are cut to music — cuts land on beats, durations follow phrases, pacing builds/releases energy.

## Beat {beat_idx}: {beat_description}
- Camera: {camera} (front=eye-level technique, overhead=top-down ingredient)
- Duration: {duration:.1f}s
- Source in-point: {approved_clip.get('in', 0):.1f}s
- Verdict vs pipeline: {verdict}
- Pipeline proposed: {pipeline_clip_info}{effects_block}{mogrt_block}{section_block}
{f"- Beat group: {beat_group_info}" if beat_group_info else ""}

## Frame-by-frame at this timecode (/watch-video):
{visual_context}

## Source clip content (VLM scan):
{scan_description if scan_description else "(no scan data)"}

## Context:
- Previous: {prev_beat_info}
- Next: {next_beat_info}

## Task:
One sentence each. Be specific about what's visible. No hedging.

CAMERA: Why {camera}? What does this angle show that the other wouldn't?
DURATION: Why {duration:.1f}s?{' Account for the speed ramp.' if effects_info and 'speed' in effects_info.lower() else ''}
INPOINT: Why this in-point? What's happening at this frame?
{"EFFECTS: Why " + effects_info + "?" if effects_info else ""}{"STOPMOTION: Why stop-motion here? What does the rapid-fire rhythm do?" if is_stop_motion else ""}
CONFIDENCE: high/medium/low"""


def call_claude(prompt: str, model: str = "sonnet") -> str:
    """Call Claude CLI with a text prompt.

    Uses sonnet for speed — this is bulk inference, not creative work.
    Visual context comes from /watch-video frame descriptions in the prompt.
    """
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--no-session-persistence",
        "--strict-mcp-config",
        "--model", model,
    ]

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            cwd="/tmp",
            env=env,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        print(f"  Claude CLI timed out (180s)", file=sys.stderr)
        return ""

    if result.returncode != 0:
        print(f"  Claude CLI error: {result.stderr[:200]}", file=sys.stderr)
        return ""

    try:
        data = json.loads(result.stdout)
        return data.get("result", "")
    except json.JSONDecodeError:
        return result.stdout


def parse_reasoning_response(response: str) -> dict:
    """Parse the LLM's reasoning response into structured fields."""
    result = {
        "camera_reasoning": "",
        "duration_reasoning": "",
        "inpoint_reasoning": "",
        "effects_reasoning": "",
        "stopmotion_reasoning": "",
        "confidence": "medium",
    }

    def _clean(s: str) -> str:
        """Strip markdown bold/italic markers from a reasoning string."""
        return re.sub(r'[*_]+', '', s).strip()

    for line in response.split("\n"):
        # Strip markdown bold/italic and leading whitespace
        cleaned = _clean(line)
        if cleaned.upper().startswith("CAMERA:"):
            result["camera_reasoning"] = _clean(cleaned[7:])
        elif cleaned.upper().startswith("DURATION:"):
            result["duration_reasoning"] = _clean(cleaned[9:])
        elif cleaned.upper().startswith("INPOINT:") or cleaned.upper().startswith("IN-POINT:") or cleaned.upper().startswith("IN_POINT:"):
            val = re.sub(r'^IN[-_]?POINT:\s*', '', cleaned, flags=re.IGNORECASE)
            result["inpoint_reasoning"] = _clean(val)
        elif cleaned.upper().startswith("EFFECTS:"):
            result["effects_reasoning"] = _clean(cleaned[8:])
        elif cleaned.upper().startswith("STOPMOTION:") or cleaned.upper().startswith("STOP-MOTION:") or cleaned.upper().startswith("STOP_MOTION:"):
            val = re.sub(r'^STOP[-_]?MOTION:\s*', '', cleaned, flags=re.IGNORECASE)
            result["stopmotion_reasoning"] = _clean(val)
        elif cleaned.upper().startswith("CONFIDENCE:"):
            conf = _clean(cleaned[11:]).lower()
            if conf in ("high", "medium", "low"):
                result["confidence"] = conf

    return result


def _group_clips_by_zone(
    timeline: List[dict], production_layers: dict, editorial_techniques: dict
) -> List[dict]:
    """Group timeline clips into editorial beats using production layer zones.

    Grouping rules:
    1. Title card zone (0s to title card end) → beauty opener (one beat)
    2. Each MOGRT zone → one ingredient beat (clips under that MOGRT)
    3. Stop-motion clips (consecutive ≤6 frames) → collapsed into one beat
    4. Remaining clips → standalone beats

    Returns list of grouped entries, each with type and constituent clips.
    """
    title_cards = production_layers.get("title_cards", [])
    mogrts = production_layers.get("mogrts", [])

    # Find title card end time
    title_end = 0
    for tc in title_cards:
        title_end = max(title_end, tc.get("timeline_out_sec", 0))

    # Build stop-motion ranges
    stop_motion_ranges = []
    for seq in editorial_techniques.get("stop_motion_sequences", []):
        stop_motion_ranges.append((seq["timeline_in_sec"], seq["timeline_out_sec"], seq))

    def is_stop_motion_clip(entry: dict) -> bool:
        clip = entry.get("v1") or entry.get("v2") or {}
        dur = clip.get("duration_frames", 999)
        if dur > 6:
            return False
        tl_in = entry.get("timeline_in_sec", 0)
        tl_out = entry.get("timeline_out_sec", 0)
        for sm_in, sm_out, _ in stop_motion_ranges:
            if tl_in >= sm_in - 0.05 and tl_out <= sm_out + 0.05:
                return True
        return False

    def get_stop_motion_info(entries: list) -> dict:
        for sm_in, sm_out, seq in stop_motion_ranges:
            if entries[0].get("timeline_in_sec", 0) >= sm_in - 0.05:
                return seq
        return {"avg_duration_frames": 3}

    # Assign each clip to a zone
    groups = []
    used = set()

    # 1. Beauty opener: all clips under title card
    beauty_clips = []
    for i, entry in enumerate(timeline):
        tl_out = entry.get("timeline_out_sec", 0)
        tl_in = entry.get("timeline_in_sec", 0)
        if tl_in < title_end and title_end > 0:
            beauty_clips.append(entry)
            used.add(i)

    if beauty_clips:
        groups.append({
            "type": "beauty_opener",
            "beat_index": 0,
            "beat_indices": [e["beat_index"] for e in beauty_clips],
            "entries": beauty_clips,
            "timeline_in_sec": beauty_clips[0].get("timeline_in_sec", 0),
            "timeline_out_sec": beauty_clips[-1].get("timeline_out_sec", 0),
            "clip_count": len(beauty_clips),
        })

    # 2. MOGRT zones: clips that overlap each MOGRT
    for mogrt in mogrts:
        m_in = mogrt.get("timeline_in_sec", 0)
        m_out = mogrt.get("timeline_out_sec", 0)
        mogrt_clips = []
        for i, entry in enumerate(timeline):
            if i in used:
                continue
            tl_in = entry.get("timeline_in_sec", 0)
            tl_out = entry.get("timeline_out_sec", 0)
            # Clip overlaps MOGRT zone
            if tl_in < m_out and tl_out > m_in:
                mogrt_clips.append(entry)
                used.add(i)

        if mogrt_clips:
            groups.append({
                "type": "mogrt_zone",
                "beat_index": mogrt_clips[0]["beat_index"],
                "beat_indices": [e["beat_index"] for e in mogrt_clips],
                "entries": mogrt_clips,
                "timeline_in_sec": mogrt_clips[0].get("timeline_in_sec", 0),
                "timeline_out_sec": mogrt_clips[-1].get("timeline_out_sec", 0),
                "clip_count": len(mogrt_clips),
                "mogrt_file": mogrt.get("file", ""),
            })

    # 3. Remaining clips: standalone or stop-motion groups
    remaining = [(i, entry) for i, entry in enumerate(timeline) if i not in used]
    j = 0
    while j < len(remaining):
        i, entry = remaining[j]
        if is_stop_motion_clip(entry):
            # Collect consecutive stop-motion clips
            sm_entries = [entry]
            k = j + 1
            while k < len(remaining):
                _, next_entry = remaining[k]
                if is_stop_motion_clip(next_entry):
                    sm_entries.append(next_entry)
                    k += 1
                else:
                    break
            sm_info = get_stop_motion_info(sm_entries)
            groups.append({
                "type": "stop_motion_group",
                "beat_index": sm_entries[0]["beat_index"],
                "beat_indices": [e["beat_index"] for e in sm_entries],
                "entries": sm_entries,
                "timeline_in_sec": sm_entries[0].get("timeline_in_sec", 0),
                "timeline_out_sec": sm_entries[-1].get("timeline_out_sec", 0),
                "clip_count": len(sm_entries),
                "avg_duration_frames": sm_info.get("avg_duration_frames", 3),
            })
            j = k
        else:
            groups.append({"type": "normal", "entry": entry})
            j += 1

    # Sort by timeline position
    groups.sort(key=lambda g: g.get("timeline_in_sec", 0) if "timeline_in_sec" in g
                else g.get("entry", {}).get("timeline_in_sec", 0))

    return groups


def _describe_group_brief(g: dict, v1_prefix: str) -> str:
    """One-line description of a grouped or normal beat for neighbor context."""
    g_type = g["type"]
    if g_type == "normal":
        entry = g["entry"]
        clip = entry.get("v1") or entry.get("v2") or {}
        cam = detect_camera(clip.get("file", ""), v1_prefix)
        dur = entry.get("timeline_out_sec", 0) - entry.get("timeline_in_sec", 0)
        fx = describe_effects(clip)
        info = f"{clip.get('file', '?')} ({cam}, {dur:.1f}s)"
        if fx:
            info += f" [{fx[:40]}]"
        return info
    elif g_type == "beauty_opener":
        return f"beauty opener ({g['clip_count']} shots, {g['timeline_out_sec'] - g['timeline_in_sec']:.1f}s)"
    elif g_type == "mogrt_zone":
        dur = g["timeline_out_sec"] - g["timeline_in_sec"]
        return f"ingredient beat ({g['clip_count']} clips, {dur:.1f}s, text overlay)"
    elif g_type == "stop_motion_group":
        dur = g["timeline_out_sec"] - g["timeline_in_sec"]
        return f"stop-motion ({g['clip_count']} clips, {dur:.1f}s)"
    return "?"


def _get_neighbor_info(gi: int, grouped_timeline: list, v1_prefix: str) -> Tuple[str, str]:
    """Get previous/next beat info from the grouped timeline."""
    prev_info = "start of video"
    next_info = "end of video"

    if gi > 0:
        prev_info = _describe_group_brief(grouped_timeline[gi - 1], v1_prefix)
    if gi < len(grouped_timeline) - 1:
        next_info = _describe_group_brief(grouped_timeline[gi + 1], v1_prefix)

    return prev_info, next_info


def generate_global_analysis_prompt(
    recipe_name: str,
    beat_count: int,
    total_duration: float,
    camera_stats: dict,
    verdict_stats: dict,
    beat_groups: List[dict],
    skipped_beats: List[int],
) -> str:
    """Prompt for overall edit style analysis."""
    groups_text = ""
    if beat_groups:
        groups_text = "\n- Beat groups:\n"
        for g in beat_groups:
            groups_text += f"  - {g['group']}: {g['description']} (beats {g['beats']})\n"
    skipped_text = ""
    if skipped_beats:
        skipped_text = f"\n- Skipped pipeline beats: {skipped_beats} (pipeline proposed these but editor omitted them)"

    return f"""Analyze the overall editing style of this recipe video edit.

## Recipe: {recipe_name}
- Total beats: {beat_count}
- Total duration: {total_duration:.1f}s
- Camera usage: {json.dumps(camera_stats)}
- Verdicts vs pipeline: {json.dumps(verdict_stats)}{groups_text}{skipped_text}

Context: Recipe videos are cut to music. The editor chooses cuts, durations, and camera angles that serve both the instructional content (showing each step clearly) and the rhythm of the music track. Standard editing rhythm rules apply — cuts on beats, holding through phrases, building energy through acceleration, breathing room after dense sequences.

Summarize the editor's approach in 3-5 sentences. Cover:
- Overall pacing (fast/slow, consistent/varied) and how it maps to recipe sections (opener → prep → technique → transformation → plating)
- Camera preference patterns (when front vs overhead, and why)
- Editorial rhythm (cut frequency, acceleration/deceleration, music-driven timing)
- Use of effects (speed ramps, stop-motion, zooms) and what purpose they serve
- Any notable editorial choices (skipped beats, flash cuts, etc.)

Be concise and specific. Write as one editor describing another's style."""


def generate_obsidian_output(
    recipe_name: str,
    global_notes: str,
    beat_annotations: List[dict],
    output_path: str,
):
    """Write the Obsidian markdown annotation file."""
    today = date.today().isoformat()

    lines = [
        "---",
        "project: ASI-Evolve",
        "type: working-file",
        f'source: "auto-analyzed editorial judgment"',
        f"date: {today}",
        "status: draft",
        "tags: [pipeline, editorial-judgment, asi-evolve]",
        f"recipe: {recipe_name}",
        "---",
        "",
        f"# {recipe_name.replace('_', ' ').title()} — Editorial Annotations",
        "",
        "## Global Notes",
        global_notes,
        "",
        "## Beat Annotations",
        "",
    ]

    for ann in beat_annotations:
        camera = ann["camera"]
        duration = ann["duration"]
        in_point = ann["in_point"]
        filename = ann["filename"]
        verdict = ann["verdict"]
        beat_desc = ann.get("beat_description", "")
        beat_type = ann.get("beat_type", "")
        pipeline_info = ann.get("pipeline_info", "")
        effects_info = ann.get("effects_info", "")
        nested_info = ann.get("nested_info", "")
        mogrt_overlaps = ann.get("mogrt_overlaps", [])
        recipe_section = ann.get("recipe_section", "")
        reasoning = ann.get("reasoning", {})

        beat_label = f"Beat {ann['beat_index']}"
        if ann.get("is_stop_motion"):
            beat_label = f"Beats {ann.get('beat_indices', [ann['beat_index']])} (stop-motion)"
        lines.append(f"### {beat_label} — {beat_desc}")

        meta_parts = [f"{filename}", f"{camera}", f"{duration:.1f}s", beat_type]
        if recipe_section:
            meta_parts.append(recipe_section)
        lines.append(f"> {' | '.join(meta_parts)} | Verdict: {verdict}")
        if pipeline_info:
            lines.append(f"> Pipeline: {pipeline_info}")
        if effects_info:
            lines.append(f"> Effects: {effects_info}")
        if nested_info:
            lines.append(f"> Nesting: {nested_info}")
        if mogrt_overlaps:
            lines.append(f"> Overlays: {'; '.join(mogrt_overlaps)}")
        lines.append("")
        lines.append(f"- **Camera:** {camera} | {reasoning.get('camera_reasoning', 'TODO')}")
        lines.append(f"- **Duration:** {duration:.1f}s | {reasoning.get('duration_reasoning', 'TODO')}")
        lines.append(f"- **In-point:** {in_point:.1f}s | {reasoning.get('inpoint_reasoning', 'TODO')}")
        if effects_info and reasoning.get("effects_reasoning"):
            lines.append(f"- **Effects:** {reasoning['effects_reasoning']}")
        if ann.get("is_stop_motion") and reasoning.get("stopmotion_reasoning"):
            lines.append(f"- **Stop-motion:** {reasoning['stopmotion_reasoning']}")
        lines.append(f"- **Verdict:** {verdict}")
        lines.append(f"- **Confidence:** {reasoning.get('confidence', 'medium')}")
        lines.append(f"- **Dan's correction:**")
        lines.append("")

    content = "\n".join(lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)
    print(f"Wrote annotations to {output_path}")


def generate_json_output(
    recipe_name: str,
    global_notes: str,
    beat_annotations: List[dict],
    output_path: str,
):
    """Write the structured JSON annotation file for the scorer."""
    data = {
        "recipe": recipe_name,
        "global_notes": global_notes,
        "beats": [],
    }

    for ann in beat_annotations:
        reasoning = ann.get("reasoning", {})
        beat_entry = {
            "beat_index": ann["beat_index"],
            "beat_description": ann.get("beat_description", ""),
            "beat_type": ann.get("beat_type", ""),
            "recipe_section": ann.get("recipe_section", ""),
            "filename": ann["filename"],
            "camera": {
                "choice": ann["camera"],
                "reasoning": reasoning.get("camera_reasoning", ""),
            },
            "duration": {
                "seconds": ann["duration"],
                "reasoning": reasoning.get("duration_reasoning", ""),
            },
            "in_point": {
                "seconds": ann["in_point"],
                "reasoning": reasoning.get("inpoint_reasoning", ""),
            },
            "verdict": ann["verdict"],
            "confidence": reasoning.get("confidence", "medium"),
            "pipeline_info": ann.get("pipeline_info", ""),
            "effects": ann.get("effects_info", ""),
            "nested": ann.get("nested_info", ""),
            "mogrt_overlaps": ann.get("mogrt_overlaps", []),
            "correction": None,
        }
        if ann.get("is_stop_motion"):
            beat_entry["is_stop_motion"] = True
            beat_entry["beat_indices"] = ann.get("beat_indices", [])
            beat_entry["stop_motion_clip_count"] = ann.get("stop_motion_clip_count", 0)
            if reasoning.get("effects_reasoning"):
                beat_entry["effects_reasoning"] = reasoning["effects_reasoning"]
            if reasoning.get("stopmotion_reasoning"):
                beat_entry["stopmotion_reasoning"] = reasoning["stopmotion_reasoning"]
        elif reasoning.get("effects_reasoning"):
            beat_entry["effects_reasoning"] = reasoning["effects_reasoning"]
        data["beats"].append(beat_entry)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote JSON annotations to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze editorial judgment from approved recipe edits")
    parser.add_argument("--recipe", required=True, help="Recipe name (e.g., basil_pesto)")
    parser.add_argument("--approved", required=True, help="Path to approved edit JSON")
    parser.add_argument("--manifest", required=True, help="Path to pipeline manifest JSON")
    parser.add_argument("--scan", required=True, help="Path to pipeline scan.json")
    parser.add_argument("--beats", required=True, help="Path to pipeline beats.json")
    parser.add_argument("--frame-analysis", required=True, help="Path to /watch-video Pass 1 markdown")
    parser.add_argument("--output", required=True, help="Output path for Obsidian .md file")
    parser.add_argument("--json-output", help="Output path for JSON annotations (default: annotations/{recipe}.json)")
    parser.add_argument("--annotation", help="Path to existing annotation JSON (for beat_groups)")
    parser.add_argument("--model", default="sonnet", help="Claude model to use (default: sonnet)")
    args = parser.parse_args()

    # Load data
    print(f"Loading data for {args.recipe}...", flush=True)
    with open(args.approved) as f:
        approved = json.load(f)
    with open(args.manifest) as f:
        pipeline = json.load(f)
    with open(args.beats) as f:
        beats_data = json.load(f)

    v1_prefix = detect_v1_prefix(pipeline)
    beats_list = beats_data.get("beats", [])

    # Load /watch-video frame analysis
    print(f"Loading frame analysis from {args.frame_analysis}...", flush=True)
    frame_analysis = load_frame_analysis(args.frame_analysis)
    print(f"  Loaded {len(frame_analysis)} frame descriptions")

    # Load beat groups from existing annotation if available
    annotation_path = args.annotation or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "annotations", f"{args.recipe}.json"
    )
    beat_groups, skipped_beats = load_beat_groups(annotation_path)
    if beat_groups:
        print(f"  Loaded {len(beat_groups)} beat groups, {len(skipped_beats)} skipped beats")

    # Match approved beats to pipeline beats
    matches = match_approved_to_pipeline(approved, pipeline)
    timeline = approved.get("timeline", [])
    production_layers = approved.get("production_layers", {})
    editorial_techniques = approved.get("editorial_techniques", {})

    # Compute total timeline duration for section inference
    if timeline:
        total_timeline_duration = max(
            e.get("timeline_out_sec", 0) for e in timeline
        )
    else:
        total_timeline_duration = 0

    # Build zone map from production layers for beat grouping.
    # Zones: title_card (beauty opener), mogrt (ingredient text), gap (no overlay).
    # Clips under the same zone = one editorial beat.
    grouped_timeline = _group_clips_by_zone(timeline, production_layers, editorial_techniques)

    # Analyze each editorial beat
    effective_count = len(grouped_timeline)
    group_types = {}
    for g in grouped_timeline:
        group_types[g["type"]] = group_types.get(g["type"], 0) + 1
    group_summary = ", ".join(f"{v} {k}" for k, v in group_types.items())
    print(f"Analyzing {effective_count} beats ({len(timeline)} raw clips → {group_summary})...", flush=True)

    beat_annotations = []
    camera_stats = {"front": 0, "overhead": 0}
    verdict_stats = {}
    total_duration = 0

    for gi, grouped in enumerate(grouped_timeline):
        g_type = grouped["type"]

        if g_type in ("beauty_opener", "mogrt_zone", "stop_motion_group"):
            # Multi-clip grouped beat
            entries = grouped["entries"]
            first_entry = entries[0]
            a_clip = first_entry.get("v1") or first_entry.get("v2")
            if not a_clip:
                continue

            beat_idx = grouped["beat_index"]
            timeline_in = grouped["timeline_in_sec"]
            timeline_out = grouped["timeline_out_sec"]
            duration = timeline_out - timeline_in
            total_duration += duration

            # Summarize clips in this group
            clip_summaries = []
            group_cameras = []
            group_effects = []
            for entry in entries:
                ec = entry.get("v1") or entry.get("v2") or {}
                cam = detect_camera(ec.get("file", ""), v1_prefix)
                group_cameras.append(cam)
                camera_stats[cam] = camera_stats.get(cam, 0) + 1
                cdur = entry.get("timeline_out_sec", 0) - entry.get("timeline_in_sec", 0)
                fx = describe_effects(ec)
                if fx:
                    group_effects.append(fx)
                clip_summaries.append(
                    f"{ec.get('file', '?')} ({cam}, {cdur:.1f}s){' [' + fx[:30] + ']' if fx else ''}"
                )

            camera = max(set(group_cameras), key=group_cameras.count) if group_cameras else "front"
            filename = a_clip.get("file", "?")
            in_point = a_clip.get("in", 0)

            # Build description based on group type, using frame analysis for content
            group_frame_descs = [f for f in frame_analysis
                                 if timeline_in - 0.3 <= f["time_sec"] <= timeline_out + 0.3]
            content_summary = ""
            if group_frame_descs:
                subjects = []
                for f in group_frame_descs:
                    subj = f.get("subject", "")
                    if subj and subj not in subjects:
                        subjects.append(subj)
                content_summary = " → ".join(subjects[:3])

            if g_type == "beauty_opener":
                beat_desc = f"beauty opener ({grouped['clip_count']} shots): {content_summary}" if content_summary else f"beauty opener ({grouped['clip_count']} shots under title card)"
                beat_type = "beauty_opener"
                recipe_section = "beauty opener (scroll-stopper, 2-3 hero shots)"
                verdict = "editorial_group"
            elif g_type == "stop_motion_group":
                beat_desc = f"stop-motion ({grouped['clip_count']} clips, avg {grouped['avg_duration_frames']:.0f}f): {content_summary}" if content_summary else f"stop-motion ({grouped['clip_count']} clips, avg {grouped['avg_duration_frames']:.0f}f each)"
                beat_type = "stop_motion"
                recipe_section = infer_recipe_section(timeline_in, total_timeline_duration, "stop_motion")
                verdict = "added"
            else:  # mogrt_zone
                beat_desc = f"ingredient ({grouped['clip_count']} clips): {content_summary}" if content_summary else f"ingredient beat ({grouped['clip_count']} clips under text overlay)"
                beat_type = "ingredient"
                recipe_section = "ingredient dump (text overlay marks this step)"

            verdict_stats[verdict] = verdict_stats.get(verdict, 0) + 1

            visual_context = get_visual_context(frame_analysis, timeline_in, timeline_out, margin=0.5)
            scan_desc = load_scan_descriptions(args.scan, filename, in_point)
            mogrt_overlaps = find_overlapping_mogrts(timeline_in, timeline_out, production_layers)
            prev_info, next_info = _get_neighbor_info(gi, grouped_timeline, v1_prefix)

            clips_block = "\n".join(f"  - {s}" for s in clip_summaries)
            effects_info = "; ".join(group_effects) if group_effects else ""

            prompt = build_beat_analysis_prompt(
                beat_idx=beat_idx, approved_clip=a_clip, camera=camera,
                duration=duration, verdict=verdict, beat_description=beat_desc,
                beat_type=beat_type,
                pipeline_clip_info=f"{grouped['clip_count']} clips:\n{clips_block}",
                scan_description=scan_desc, visual_context=visual_context,
                prev_beat_info=prev_info, next_beat_info=next_info,
                beat_group_info="",
                effects_info=effects_info,
                mogrt_overlaps=mogrt_overlaps,
                recipe_section=recipe_section,
                is_stop_motion=(g_type == "stop_motion_group"),
                stop_motion_info=beat_desc if g_type == "stop_motion_group" else "",
            )

            print(f"  Beat {beat_idx}: {beat_desc} ({g_type})", flush=True)
            response = call_claude(prompt, model=args.model)
            reasoning = parse_reasoning_response(response)

            beat_annotations.append({
                "beat_index": beat_idx,
                "beat_indices": grouped["beat_indices"],
                "filename": filename,
                "camera": camera,
                "duration": duration,
                "in_point": in_point,
                "verdict": verdict,
                "beat_description": beat_desc,
                "beat_type": beat_type,
                "pipeline_info": "",
                "is_grouped": True,
                "group_type": g_type,
                "clip_count": grouped["clip_count"],
                "clip_summaries": clip_summaries,
                "effects_info": effects_info,
                "mogrt_overlaps": mogrt_overlaps,
                "recipe_section": recipe_section,
                "reasoning": reasoning,
            })
            continue

        # Normal (single-clip) beat
        entry = grouped["entry"]
        a_clip = entry.get("v1") or entry.get("v2")
        if not a_clip or not a_clip.get("file"):
            continue

        beat_idx = entry["beat_index"]
        filename = a_clip["file"]
        camera = detect_camera(filename, v1_prefix)
        duration = entry.get("timeline_out_sec", 0) - entry.get("timeline_in_sec", 0)
        in_point = a_clip.get("in", 0)
        timeline_in = entry.get("timeline_in_sec", 0)
        timeline_out = entry.get("timeline_out_sec", 0)

        camera_stats[camera] = camera_stats.get(camera, 0) + 1
        total_duration += duration

        # Get pipeline match and verdict
        p_match = matches.get(beat_idx)
        verdict = determine_verdict(a_clip, p_match, v1_prefix)
        verdict_stats[verdict] = verdict_stats.get(verdict, 0) + 1

        # Pipeline clip info
        pipeline_info = ""
        if p_match:
            p_entry = p_match["pipeline_entry"]
            p_track = p_match["matched_track"]
            p_clip = p_entry.get(p_track, {})
            if p_clip and p_clip.get("file"):
                p_cam = detect_camera(p_clip["file"], v1_prefix)
                pipeline_info = f"{p_clip['file']} @ {p_clip.get('in', 0):.1f}s ({p_cam})"

        # Beat description: prefer matched pipeline beat, else derive from frame analysis
        beat_desc = ""
        beat_type = ""
        if p_match:
            # Use the matched pipeline beat's description, not raw index
            p_idx = None
            for pi, pe in enumerate(pipeline.get("timeline", [])):
                if pe is p_match["pipeline_entry"]:
                    p_idx = pi
                    break
            if p_idx is not None and p_idx < len(beats_list):
                beat_desc = beats_list[p_idx].get("beat", "")
                beat_type = beats_list[p_idx].get("type", "")
            if not beat_desc:
                beat_desc = p_match["pipeline_entry"].get("step", "")
                beat_type = p_match["pipeline_entry"].get("beat_type", "")
        if not beat_desc:
            # No pipeline match or no description — derive from frame analysis
            desc_frames = [f for f in frame_analysis
                           if timeline_in - 0.3 <= f["time_sec"] <= timeline_in + 0.5]
            if desc_frames:
                beat_desc = desc_frames[0].get("subject", "") or desc_frames[0].get("notes", "")
            if not beat_desc:
                beat_desc = f"{filename} @ {timeline_in:.1f}s"

        visual_context = get_visual_context(frame_analysis, timeline_in, timeline_out)
        scan_desc = load_scan_descriptions(args.scan, filename, in_point)
        effects_info = describe_effects(a_clip)
        nested_info = describe_nested(a_clip)
        mogrt_overlaps = find_overlapping_mogrts(timeline_in, timeline_out, production_layers)
        recipe_section = infer_recipe_section(timeline_in, total_timeline_duration, beat_desc or beat_type)
        prev_info, next_info = _get_neighbor_info(gi, grouped_timeline, v1_prefix)

        prompt = build_beat_analysis_prompt(
            beat_idx=beat_idx, approved_clip=a_clip, camera=camera,
            duration=duration, verdict=verdict, beat_description=beat_desc,
            beat_type=beat_type,
            pipeline_clip_info=pipeline_info or "(no pipeline match)",
            scan_description=scan_desc, visual_context=visual_context,
            prev_beat_info=prev_info, next_beat_info=next_info,
            beat_group_info="",
            effects_info=effects_info, nested_info=nested_info,
            mogrt_overlaps=mogrt_overlaps, recipe_section=recipe_section,
        )

        extra = []
        if effects_info:
            extra.append(effects_info[:40])
        extra_str = f" [{', '.join(extra)}]" if extra else ""
        print(f"  Beat {beat_idx}: {beat_desc[:50]}... ({verdict}){extra_str}", flush=True)
        response = call_claude(prompt, model=args.model)
        reasoning = parse_reasoning_response(response)

        beat_annotations.append({
            "beat_index": beat_idx,
            "filename": filename,
            "camera": camera,
            "duration": duration,
            "in_point": in_point,
            "verdict": verdict,
            "beat_description": beat_desc,
            "beat_type": beat_type,
            "pipeline_info": pipeline_info,
            "effects_info": effects_info,
            "nested_info": nested_info,
            "mogrt_overlaps": mogrt_overlaps,
            "recipe_section": recipe_section,
            "reasoning": reasoning,
        })

    # Generate global analysis
    print("Generating global style analysis...")
    global_prompt = generate_global_analysis_prompt(
        args.recipe, len(timeline), total_duration, camera_stats, verdict_stats,
        beat_groups, skipped_beats,
    )
    global_notes = call_claude(global_prompt, model=args.model)

    # Write outputs
    generate_obsidian_output(args.recipe, global_notes, beat_annotations, args.output)

    json_output = args.json_output or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "annotations", f"{args.recipe}.json"
    )
    generate_json_output(args.recipe, global_notes, beat_annotations, json_output)

    # Summary
    print(f"\n--- Summary ---")
    print(f"Recipe: {args.recipe}")
    print(f"Beats analyzed: {len(beat_annotations)}")
    print(f"Camera stats: {camera_stats}")
    print(f"Verdicts: {verdict_stats}")
    print(f"Total duration: {total_duration:.1f}s")
    print(f"\nOutputs:")
    print(f"  Obsidian: {args.output}")
    print(f"  JSON: {json_output}")


if __name__ == "__main__":
    main()
