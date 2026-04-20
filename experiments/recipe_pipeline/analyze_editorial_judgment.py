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
) -> str:
    """Build the LLM prompt for analyzing one beat's editorial reasoning."""
    return f"""Analyze this editorial decision from a recipe video edit.

## Beat {beat_idx}: {beat_description}
- **Beat type:** {beat_type}
- **Camera chosen:** {camera} (front = eye-level technique camera, overhead = top-down ingredient/plating camera)
- **Duration:** {duration:.1f}s
- **Source in-point:** {approved_clip.get('in', 0):.1f}s into the source clip
- **Verdict vs pipeline:** {verdict}
- **Pipeline's choice:** {pipeline_clip_info}
{f"- **Beat group:** {beat_group_info}" if beat_group_info else ""}

## What the final export shows at this beat (frame-by-frame from /watch-video):
{visual_context}

## What the source clip shows (VLM descriptions from scan):
{scan_description if scan_description else "(no scan data available)"}

## Edit context:
- Previous beat: {prev_beat_info}
- Next beat: {next_beat_info}

## Your task:
For this beat, explain the editor's likely reasoning across three dimensions. Be specific and grounded in what's visible in the frame descriptions above. Write as if you're the editor explaining your choice to another editor.

1. **Camera reasoning** — Why {camera} for this moment? What does this camera angle show that the other wouldn't? (1-2 sentences)
2. **Duration reasoning** — Why hold for {duration:.1f}s? Is this long/short relative to the beat type? What determines the hold length? (1-2 sentences)
3. **In-point reasoning** — Why cut in at this specific moment in the source clip? What's happening visually at this frame? (1-2 sentences)
4. **Confidence** — How certain are you about this reasoning? (high/medium/low)

Format your response as:
CAMERA: [reasoning]
DURATION: [reasoning]
INPOINT: [reasoning]
CONFIDENCE: [high/medium/low]"""


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
        "confidence": "medium",
    }

    for line in response.split("\n"):
        line = line.strip()
        if line.upper().startswith("CAMERA:"):
            result["camera_reasoning"] = line[7:].strip()
        elif line.upper().startswith("DURATION:"):
            result["duration_reasoning"] = line[9:].strip()
        elif line.upper().startswith("INPOINT:") or line.upper().startswith("IN-POINT:") or line.upper().startswith("IN_POINT:"):
            val = re.sub(r'^IN[-_]?POINT:\s*', '', line, flags=re.IGNORECASE)
            result["inpoint_reasoning"] = val.strip()
        elif line.upper().startswith("CONFIDENCE:"):
            conf = line[11:].strip().lower()
            if conf in ("high", "medium", "low"):
                result["confidence"] = conf

    return result


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

Summarize the editor's approach in 2-3 sentences. Cover:
- Overall pacing (fast/slow, consistent/varied)
- Camera preference patterns
- Beat grouping patterns (multi-clip sequences, editorial rhythm)
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
        reasoning = ann.get("reasoning", {})

        lines.append(f"### Beat {ann['beat_index']} — {beat_desc}")
        lines.append(f"> {filename} ({camera}, {duration:.1f}s, {beat_type}) | Verdict: {verdict}")
        if pipeline_info:
            lines.append(f"> Pipeline: {pipeline_info}")
        lines.append("")
        lines.append(f"- **Camera:** {camera} | {reasoning.get('camera_reasoning', 'TODO')}")
        lines.append(f"- **Duration:** {duration:.1f}s | {reasoning.get('duration_reasoning', 'TODO')}")
        lines.append(f"- **In-point:** {in_point:.1f}s | {reasoning.get('inpoint_reasoning', 'TODO')}")
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
        data["beats"].append({
            "beat_index": ann["beat_index"],
            "beat_description": ann.get("beat_description", ""),
            "beat_type": ann.get("beat_type", ""),
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
            "correction": None,
        })

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

    # Analyze each beat
    print(f"Analyzing {len(timeline)} beats...", flush=True)
    beat_annotations = []
    camera_stats = {"front": 0, "overhead": 0}
    verdict_stats = {}
    total_duration = 0

    for i, entry in enumerate(timeline):
        a_clip = entry.get("v1") or entry.get("v2")
        if not a_clip or not a_clip.get("file"):
            continue

        beat_idx = entry["beat_index"]
        filename = a_clip["file"]
        camera = detect_camera(filename, v1_prefix)
        duration = entry.get("timeline_out_sec", 0) - entry.get("timeline_in_sec", 0)
        in_point = a_clip.get("in", 0)

        camera_stats[camera] = camera_stats.get(camera, 0) + 1
        total_duration += duration

        # Get pipeline match and verdict
        p_match = matches.get(beat_idx)
        verdict = determine_verdict(a_clip, p_match, v1_prefix)
        verdict_stats[verdict] = verdict_stats.get(verdict, 0) + 1

        # Pipeline clip info string
        pipeline_info = ""
        if p_match:
            p_entry = p_match["pipeline_entry"]
            p_track = p_match["matched_track"]
            p_clip = p_entry.get(p_track, {})
            if p_clip and p_clip.get("file"):
                p_cam = detect_camera(p_clip["file"], v1_prefix)
                pipeline_info = f"{p_clip['file']} @ {p_clip.get('in', 0):.1f}s ({p_cam})"

        # Beat description from beats.json
        beat_desc = ""
        beat_type = ""
        if beat_idx < len(beats_list):
            beat_desc = beats_list[beat_idx].get("beat", "")
            beat_type = beats_list[beat_idx].get("type", "")
        # Fallback: use pipeline manifest step
        if not beat_desc and p_match:
            beat_desc = p_match["pipeline_entry"].get("step", "")
            beat_type = p_match["pipeline_entry"].get("beat_type", "")

        # Visual context from /watch-video frame analysis
        timeline_in = entry.get("timeline_in_sec", 0)
        timeline_out = entry.get("timeline_out_sec", 0)
        visual_context = get_visual_context(frame_analysis, timeline_in, timeline_out)

        # Scan descriptions
        scan_desc = load_scan_descriptions(args.scan, filename, in_point)

        # Beat group context
        group = find_beat_group(beat_idx, beat_groups)
        beat_group_info = ""
        if group:
            beat_group_info = (
                f"{group['group']}: {group['description']} "
                f"(beats {group['beats']}, this is beat {beat_idx})"
            )

        # Context: previous and next beats
        prev_info = "start of video"
        next_info = "end of video"
        if i > 0:
            prev = timeline[i - 1]
            prev_clip = prev.get("v1") or prev.get("v2")
            if prev_clip:
                prev_cam = detect_camera(prev_clip["file"], v1_prefix)
                prev_dur = prev.get("timeline_out_sec", 0) - prev.get("timeline_in_sec", 0)
                prev_info = f"{prev_clip['file']} ({prev_cam}, {prev_dur:.1f}s)"
        if i < len(timeline) - 1:
            nxt = timeline[i + 1]
            nxt_clip = nxt.get("v1") or nxt.get("v2")
            if nxt_clip:
                nxt_cam = detect_camera(nxt_clip["file"], v1_prefix)
                nxt_dur = nxt.get("timeline_out_sec", 0) - nxt.get("timeline_in_sec", 0)
                next_info = f"{nxt_clip['file']} ({nxt_cam}, {nxt_dur:.1f}s)"

        # Build prompt
        prompt = build_beat_analysis_prompt(
            beat_idx=beat_idx,
            approved_clip=a_clip,
            camera=camera,
            duration=duration,
            verdict=verdict,
            beat_description=beat_desc,
            beat_type=beat_type,
            pipeline_clip_info=pipeline_info or "(no pipeline match)",
            scan_description=scan_desc,
            visual_context=visual_context,
            prev_beat_info=prev_info,
            next_beat_info=next_info,
            beat_group_info=beat_group_info,
        )

        # Call Claude (text-only — visual context comes from frame analysis descriptions)
        print(f"  Beat {beat_idx}: {beat_desc[:50]}... ({verdict})", flush=True)
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
