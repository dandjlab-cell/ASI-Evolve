#!/usr/bin/env python3
"""
Parse Premiere Pro FCP XML into the same JSON structure as pipeline manifests.

Extracts clip placements from V1/V2 tracks with filenames, in/out points,
timeline positions, speed effects, scale/motion, and nested sequences.
This is the "ground truth" for scoring evolved configs.

Editorial techniques detected:
  - Speed remap: slow motion (constant), speed ramps (keyframed)
  - Scale: punch-in/crop (vs 50% baseline for 4K-on-1080p), animated zoom
  - Nested sequences: overhead slow-zoom pattern (nest + keyframed scale)
  - Stop motion: consecutive ultra-short clips (<3 frames)
  - Camera alternation: front↔overhead rhythm

Usage:
    python xml_to_manifest.py input.xml output.json
    python xml_to_manifest.py input.xml  # prints to stdout
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 4K footage on 1080p timeline = 50% scale baseline.
# Anything within this range is just "fit to frame", not editorial.
SCALE_BASELINE = 50
SCALE_TOLERANCE = 5  # 45-55% is normal framing

# Clips shorter than this (in frames) are candidates for stop-motion
STOP_MOTION_THRESHOLD_FRAMES = 6


def parse_premiere_xml(xml_path: str) -> Dict:
    """Parse a Premiere FCP XML export into a manifest-compatible dict.

    Returns:
        {
            "source": "premiere_xml",
            "source_file": "...",
            "sequence_settings": {"width": ..., "height": ..., "fps": ...},
            "timeline": [...],
            "editorial_techniques": {...},
            "production_layers": {...}
        }
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Find the main sequence
    sequence = root.find(".//sequence")
    if sequence is None:
        raise ValueError(f"No <sequence> found in {xml_path}")

    # Build file ID → filename lookup (nested clips use file refs)
    file_lookup = _build_file_lookup(root)

    # Sequence settings
    fps = _parse_fps(sequence)
    width = _text_int(sequence, ".//format/samplecharacteristics/width", 1920)
    height = _text_int(sequence, ".//format/samplecharacteristics/height", 1080)

    # Extract video tracks
    video_tracks = sequence.findall(".//video/track")
    if not video_tracks:
        raise ValueError("No video tracks found in sequence")

    # Parse clips from editorial tracks (V1, V2) only for timeline.
    # Upper tracks (V3+) are production layers (graphics, titles, watermarks).
    track_clips = {}
    production_layers = _detect_production_layers(video_tracks, fps, file_lookup)

    for i, track in enumerate(video_tracks):
        track_name = f"V{i + 1}"
        if i >= 2:
            # V3+ are production layers, not editorial — skip for timeline
            continue
        clips = _parse_track_clips(track, fps, file_lookup)
        if clips:
            track_clips[track_name] = clips

    # Pair clips by timeline position (V1 + V2 that overlap in time)
    timeline = _pair_tracks(track_clips, fps)

    # Detect editorial techniques from V1/V2 clips
    all_clips = []
    for clips in track_clips.values():
        all_clips.extend(clips)
    techniques = _detect_techniques(all_clips, fps)

    # Also scan V3+ for any video clips with editorial effects
    # (e.g., an alt angle on V3 with a speed ramp)
    for i, track in enumerate(video_tracks):
        if i < 2:
            continue
        upper_clips = _parse_track_clips(track, fps, file_lookup)
        if upper_clips:
            upper_techniques = _detect_techniques(upper_clips, fps)
            for key in ("speed_ramps", "slow_motion", "animated_zooms"):
                techniques[key].extend(upper_techniques.get(key, []))

    return {
        "source": "premiere_xml",
        "source_file": str(xml_path),
        "sequence_settings": {
            "width": width,
            "height": height,
            "fps": fps,
        },
        "timeline": timeline,
        "editorial_techniques": techniques,
        "production_layers": production_layers,
    }


def _build_file_lookup(root) -> Dict[str, str]:
    """Build a mapping of file element IDs to filenames.

    Premiere XML defines <file id="file-37"> with name/pathurl once,
    then references it as <file id="file-37"/> (empty element) elsewhere.
    Nested sequence clips always use these references.
    """
    lookup = {}
    for file_elem in root.findall(".//file"):
        fid = file_elem.get("id")
        if not fid:
            continue
        name = file_elem.findtext("name")
        if not name:
            pathurl = file_elem.findtext("pathurl")
            if pathurl:
                name = Path(pathurl.replace("file://", "").replace("%20", " ")).name
        if name:
            lookup[fid] = name
    return lookup


def _detect_production_layers(
    video_tracks: list, fps: float, file_lookup: Dict[str, str]
) -> Dict:
    """Detect non-editorial production layers: adjustment layers, MOGRTs,
    watermarks, title cards, end cards.

    These are on upper tracks and aren't part of the editorial cut —
    they're production finishing.
    """
    layers = {
        "adjustment_layers": [],
        "mogrts": [],
        "title_cards": [],
        "end_cards": [],
        "watermarks": [],
        "other_graphics": [],
    }

    for i, track in enumerate(video_tracks):
        track_name = f"V{i + 1}"
        for clip in track.findall("clipitem"):
            file_elem = clip.find(".//file")
            if file_elem is None:
                continue

            fid = file_elem.get("id", "")
            fname = file_elem.findtext("name") or file_lookup.get(fid, "")
            if not fname:
                pathurl = file_elem.findtext("pathurl")
                if pathurl:
                    fname = Path(pathurl.replace("file://", "").replace("%20", " ")).name

            start = _text_int(clip, "start", 0)
            end = _text_int(clip, "end", 0)
            if end <= start:
                continue

            tl_in = round(start / fps, 3)
            tl_out = round(end / fps, 3)
            fname_lower = fname.lower() if fname else ""

            entry = {
                "file": fname,
                "track": track_name,
                "timeline_in_sec": tl_in,
                "timeline_out_sec": tl_out,
                "duration_sec": round((end - start) / fps, 3),
            }

            # Classify by filename/extension patterns
            if "adjustment" in fname_lower or fname_lower.endswith(".prproj"):
                # Adjustment layers (Lumetri color, etc.)
                lumetri = clip.find('.//filter/effect[effectid="Lumetri"]')
                if lumetri is not None:
                    entry["has_lumetri"] = True
                layers["adjustment_layers"].append(entry)
            elif fname_lower.endswith(".mogrt"):
                # Motion graphics templates (ingredient text cards, etc.)
                if tl_in < 5.0:
                    layers["title_cards"].append(entry)
                else:
                    layers["mogrts"].append(entry)
            elif fname_lower.endswith((".png", ".psd", ".ai", ".eps")):
                # Static graphics
                if "watermark" in fname_lower or "logo" in fname_lower or "bug" in fname_lower:
                    layers["watermarks"].append(entry)
                elif tl_in < 5.0:
                    layers["title_cards"].append(entry)
                elif tl_out >= _get_sequence_duration(clip, fps) - 3.0:
                    layers["end_cards"].append(entry)
                else:
                    layers["other_graphics"].append(entry)

    # Remove empty categories
    return {k: v for k, v in layers.items() if v}


def _get_sequence_duration(clip, fps: float) -> float:
    """Approximate sequence duration from clip's ancestor sequence."""
    # Walk up to find sequence duration — rough heuristic
    # Just return a large number if we can't determine it
    return 999.0


def _parse_fps(sequence) -> float:
    """Extract frame rate from sequence timebase."""
    timebase = _text_int(sequence, ".//rate/timebase", 24)
    ntsc = _text(sequence, ".//rate/ntsc")
    if ntsc and ntsc.upper() == "TRUE":
        return timebase * 1000 / 1001  # e.g. 24 -> 23.976
    return float(timebase)


def _parse_track_clips(track, fps: float, file_lookup: Dict[str, str] = None) -> List[Dict]:
    """Parse all clipitem elements from a track."""
    file_lookup = file_lookup or {}
    clips = []
    for clip in track.findall("clipitem"):
        parsed = _parse_clip(clip, fps, file_lookup)
        if parsed:
            clips.append(parsed)
    return clips


def _parse_clip(clip, fps: float, file_lookup: Dict[str, str] = None) -> Optional[Dict]:
    """Parse a single clipitem element, including effects and nesting."""
    file_lookup = file_lookup or {}

    # Skip disabled clips
    enabled = _text(clip, "enabled")
    if enabled and enabled.upper() == "FALSE":
        return None

    # Check for nested sequence first
    nested_seq = clip.find("sequence")
    if nested_seq is not None:
        return _parse_nested_clip(clip, nested_seq, fps, file_lookup)

    # Get the source file name — try direct, then lookup by ID
    file_elem = clip.find(".//file")
    if file_elem is None:
        return None

    filename = _text(file_elem, "name")
    if not filename:
        pathurl = _text(file_elem, "pathurl")
        if pathurl:
            filename = Path(pathurl.replace("file://", "").replace("%20", " ")).name
    if not filename:
        fid = file_elem.get("id")
        if fid:
            filename = file_lookup.get(fid)
    if not filename:
        return None

    # Skip non-video files (audio, graphics, etc.)
    if not any(filename.lower().endswith(ext) for ext in
               (".mov", ".mp4", ".mxf", ".avi", ".m4v")):
        return None

    # Timeline position (in frames)
    start_frame = _text_int(clip, "start", 0)
    end_frame = _text_int(clip, "end", 0)

    # Source in/out points (in frames)
    in_frame = _text_int(clip, "in", 0)
    out_frame = _text_int(clip, "out", 0)

    if end_frame <= start_frame:
        return None

    result = {
        "file": filename,
        "in": round(in_frame / fps, 3),
        "out": round(out_frame / fps, 3),
        "timeline_in_sec": round(start_frame / fps, 3),
        "timeline_out_sec": round(end_frame / fps, 3),
        "duration_sec": round((end_frame - start_frame) / fps, 3),
        "duration_frames": end_frame - start_frame,
    }

    # Extract effects
    effects = _parse_effects(clip, fps)
    if effects:
        result["effects"] = effects

    return result


def _parse_nested_clip(clip, nested_seq, fps: float, file_lookup: Dict[str, str] = None) -> Optional[Dict]:
    """Parse a clipitem that contains a nested sequence."""
    file_lookup = file_lookup or {}
    seq_name = nested_seq.findtext("name", "unnamed_nest")

    start_frame = _text_int(clip, "start", 0)
    end_frame = _text_int(clip, "end", 0)
    in_frame = _text_int(clip, "in", 0)
    out_frame = _text_int(clip, "out", 0)

    if end_frame <= start_frame:
        return None

    # Parse inner clips from the nested sequence (use file_lookup for refs)
    inner_clips = []
    for track in nested_seq.findall(".//video/track"):
        for inner_clip in track.findall("clipitem"):
            parsed = _parse_clip(inner_clip, fps, file_lookup)
            if parsed:
                inner_clips.append(parsed)

    # Extract effects on the nest itself (scale zoom, etc.)
    effects = _parse_effects(clip, fps)

    result = {
        "file": f"[NEST] {seq_name}",
        "nested": True,
        "nest_name": seq_name,
        "in": round(in_frame / fps, 3),
        "out": round(out_frame / fps, 3),
        "timeline_in_sec": round(start_frame / fps, 3),
        "timeline_out_sec": round(end_frame / fps, 3),
        "duration_sec": round((end_frame - start_frame) / fps, 3),
        "duration_frames": end_frame - start_frame,
        "inner_clips": inner_clips,
    }

    if effects:
        result["effects"] = effects

    return result


def _parse_effects(clip, fps: float) -> Optional[Dict]:
    """Extract editorial effects from a clipitem's filter chain.

    Returns dict with speed, scale, position info — or None if no
    editorial effects found (only default values).
    """
    effects = {}

    for filt in clip.findall("filter"):
        effect = filt.find("effect")
        if effect is None:
            continue
        eid = effect.findtext("effectid", "")

        if eid == "timeremap":
            speed_info = _parse_timeremap(effect, fps)
            if speed_info:
                effects["speed"] = speed_info

        elif eid == "basic":
            motion_info = _parse_basic_motion(effect, fps)
            if motion_info:
                effects["motion"] = motion_info

    return effects if effects else None


def _parse_timeremap(effect, fps: float) -> Optional[Dict]:
    """Parse timeremap effect for speed changes and ramps."""
    speed_val = None
    variable_speed = False
    reverse = False
    ramp_keyframes = []

    for param in effect.findall("parameter"):
        pid = param.findtext("parameterid", "")

        if pid == "speed":
            speed_val = _text_float(param, "value")

        elif pid == "variablespeed":
            variable_speed = _text(param, "value") == "1"

        elif pid == "reverse":
            reverse = _text(param, "value") == "TRUE"

        elif pid == "graphdict":
            for kf in param.findall("keyframe"):
                when = _text_int(kf, "when", 0)
                val = _text_int(kf, "value", 0)
                kf_type = None
                if kf.find("speedkfstart") is not None:
                    kf_type = "start"
                elif kf.find("speedkfin") is not None:
                    kf_type = "ramp_in"
                elif kf.find("speedkfout") is not None:
                    kf_type = "ramp_out"
                elif kf.find("speedkfend") is not None:
                    kf_type = "end"
                ramp_keyframes.append({
                    "frame": when,
                    "time_sec": round(when / fps, 3),
                    "value": val,
                    "type": kf_type,
                })

    if speed_val is None or speed_val == 100:
        return None

    result = {
        "speed_percent": speed_val,
        "reverse": reverse,
    }

    if variable_speed or (ramp_keyframes and _has_speed_variation(ramp_keyframes)):
        result["type"] = "speed_ramp"
        result["keyframes"] = ramp_keyframes
    else:
        result["type"] = "constant"

    return result


def _has_speed_variation(keyframes: List[Dict]) -> bool:
    """Check if speed ramp keyframes indicate actual variable speed.

    Constant speed has keyframes but the intervals between them are uniform.
    Variable speed has non-uniform intervals (ramp_in and ramp_out differ).
    """
    if len(keyframes) < 4:
        return False
    # Check if ramp_in and ramp_out frames are different from a linear interpolation
    ramp_in = next((kf for kf in keyframes if kf["type"] == "ramp_in"), None)
    ramp_out = next((kf for kf in keyframes if kf["type"] == "ramp_out"), None)
    if ramp_in and ramp_out:
        # If ramp_in and ramp_out are close together, there's a sharp speed change
        gap = ramp_out["frame"] - ramp_in["frame"]
        return gap < 100  # tight ramp = editorial speed change
    return False


def _parse_basic_motion(effect, fps: float) -> Optional[Dict]:
    """Parse Basic Motion effect for scale and position."""
    result = {}

    for param in effect.findall("parameter"):
        pid = param.findtext("parameterid", "")

        if pid == "scale":
            keyframes = param.findall("keyframe")
            val = _text_float(param, "value", 100.0)

            if keyframes:
                kf_data = []
                for kf in keyframes:
                    when = _text_int(kf, "when", 0)
                    kf_val = _text_float(kf, "value", val)
                    kf_data.append({
                        "frame": when,
                        "time_sec": round(when / fps, 3),
                        "value": kf_val,
                    })
                result["scale"] = {
                    "type": "animated",
                    "keyframes": kf_data,
                    "start_value": kf_data[0]["value"],
                    "end_value": kf_data[-1]["value"],
                }
            elif not _is_baseline_scale(val):
                result["scale"] = {
                    "type": "static",
                    "value": val,
                    "editorial_note": _describe_scale(val),
                }

        elif pid == "center":
            keyframes = param.findall("keyframe")
            if keyframes:
                kf_data = []
                for kf in keyframes:
                    when = _text_int(kf, "when", 0)
                    h = kf.findtext("value/horiz", "0")
                    v = kf.findtext("value/vert", "0")
                    kf_data.append({
                        "frame": when,
                        "time_sec": round(when / fps, 3),
                        "horiz": float(h),
                        "vert": float(v),
                    })
                result["position"] = {
                    "type": "animated",
                    "keyframes": kf_data,
                }
            else:
                h_text = _text(param, "value/horiz")
                v_text = _text(param, "value/vert")
                if h_text and v_text:
                    h, v = float(h_text), float(v_text)
                    if abs(h) > 0.01 or abs(v) > 0.01:
                        result["position"] = {
                            "type": "static",
                            "horiz": h,
                            "vert": v,
                        }

    return result if result else None


def _is_baseline_scale(val: float) -> bool:
    """Check if scale is just 4K-on-1080p fit (50% ± tolerance)."""
    return abs(val - SCALE_BASELINE) <= SCALE_TOLERANCE


def _describe_scale(val: float) -> str:
    """Describe what a non-baseline scale means editorially."""
    if val > SCALE_BASELINE + SCALE_TOLERANCE:
        return f"punch-in/crop ({val}% vs {SCALE_BASELINE}% baseline)"
    elif val < SCALE_BASELINE - SCALE_TOLERANCE:
        return f"pulled-out/wider ({val}% vs {SCALE_BASELINE}% baseline)"
    return "baseline"


def _detect_techniques(all_clips: List[Dict], fps: float) -> Dict:
    """Detect editorial techniques from the full set of parsed clips."""
    speed_ramps = []
    slow_motion = []
    scale_adjustments = []
    animated_zooms = []
    nested_sequences = []
    stop_motion_sequences = []

    for clip in all_clips:
        effects = clip.get("effects", {})
        file = clip.get("file", "?")
        tl_in = clip.get("timeline_in_sec", 0)
        tl_out = clip.get("timeline_out_sec", 0)

        # Speed
        speed = effects.get("speed")
        if speed:
            entry = {
                "file": file,
                "timeline_in_sec": tl_in,
                "timeline_out_sec": tl_out,
                "speed_percent": speed["speed_percent"],
            }
            if speed["type"] == "speed_ramp":
                entry["keyframes"] = speed.get("keyframes", [])
                speed_ramps.append(entry)
            else:
                slow_motion.append(entry)

        # Scale / zoom
        motion = effects.get("motion", {})
        scale = motion.get("scale")
        if scale:
            entry = {
                "file": file,
                "timeline_in_sec": tl_in,
                "timeline_out_sec": tl_out,
            }
            if scale["type"] == "animated":
                entry["start_value"] = scale["start_value"]
                entry["end_value"] = scale["end_value"]
                entry["keyframes"] = scale["keyframes"]
                animated_zooms.append(entry)
            else:
                entry["value"] = scale["value"]
                entry["editorial_note"] = scale.get("editorial_note", "")
                scale_adjustments.append(entry)

        # Nested
        if clip.get("nested"):
            nested_sequences.append({
                "nest_name": clip.get("nest_name", ""),
                "timeline_in_sec": tl_in,
                "timeline_out_sec": tl_out,
                "inner_clip_count": len(clip.get("inner_clips", [])),
                "effects": {k: v for k, v in effects.items()} if effects else None,
            })

    # Stop-motion detection: consecutive ultra-short clips
    sorted_clips = sorted(all_clips, key=lambda c: c.get("timeline_in_sec", 0))
    stop_motion_sequences = _detect_stop_motion(sorted_clips, fps)

    # Camera alternation
    camera_alternation = _analyze_camera_alternation(sorted_clips)

    return {
        "speed_ramps": speed_ramps,
        "slow_motion": slow_motion,
        "scale_adjustments": scale_adjustments,
        "animated_zooms": animated_zooms,
        "nested_sequences": nested_sequences,
        "stop_motion_sequences": stop_motion_sequences,
        "camera_alternation": camera_alternation,
    }


def _detect_stop_motion(sorted_clips: List[Dict], fps: float) -> List[Dict]:
    """Detect stop-motion sequences: consecutive ultra-short clips."""
    sequences = []
    current_run = []

    for clip in sorted_clips:
        dur_frames = clip.get("duration_frames", 0)
        if dur_frames <= STOP_MOTION_THRESHOLD_FRAMES and dur_frames > 0:
            current_run.append(clip)
        else:
            if len(current_run) >= 2:
                sequences.append({
                    "clip_count": len(current_run),
                    "timeline_in_sec": current_run[0].get("timeline_in_sec", 0),
                    "timeline_out_sec": current_run[-1].get("timeline_out_sec", 0),
                    "avg_duration_frames": round(
                        sum(c.get("duration_frames", 0) for c in current_run) / len(current_run), 1
                    ),
                    "clips": [
                        {"file": c.get("file", "?"), "duration_frames": c.get("duration_frames", 0)}
                        for c in current_run
                    ],
                })
            current_run = []

    # Flush last run
    if len(current_run) >= 2:
        sequences.append({
            "clip_count": len(current_run),
            "timeline_in_sec": current_run[0].get("timeline_in_sec", 0),
            "timeline_out_sec": current_run[-1].get("timeline_out_sec", 0),
            "avg_duration_frames": round(
                sum(c.get("duration_frames", 0) for c in current_run) / len(current_run), 1
            ),
            "clips": [
                {"file": c.get("file", "?"), "duration_frames": c.get("duration_frames", 0)}
                for c in current_run
            ],
        })

    return sequences


def _analyze_camera_alternation(sorted_clips: List[Dict]) -> Dict:
    """Analyze front↔overhead camera alternation pattern."""
    # Detect camera from filename prefix
    cameras = []
    for clip in sorted_clips:
        f = clip.get("file", "")
        if clip.get("nested"):
            # Nested clips inherit camera from inner clips
            inner = clip.get("inner_clips", [])
            if inner:
                f = inner[0].get("file", "")
        if f.startswith("B19I") or f.startswith("B20I") or f.startswith("C"):
            cameras.append("front")
        elif f.startswith("AI2I") or f.startswith("AI3I") or f.startswith("A"):
            cameras.append("overhead")
        else:
            cameras.append("unknown")

    if not cameras:
        return {}

    # Count alternations
    alternations = 0
    runs = []
    current_cam = cameras[0]
    run_length = 1

    for cam in cameras[1:]:
        if cam == current_cam:
            run_length += 1
        else:
            alternations += 1
            runs.append({"camera": current_cam, "run_length": run_length})
            current_cam = cam
            run_length = 1
    runs.append({"camera": current_cam, "run_length": run_length})

    front_count = cameras.count("front")
    overhead_count = cameras.count("overhead")
    total = len(cameras)

    return {
        "total_clips": total,
        "front_count": front_count,
        "overhead_count": overhead_count,
        "front_pct": round(front_count / total * 100, 1) if total else 0,
        "overhead_pct": round(overhead_count / total * 100, 1) if total else 0,
        "alternation_count": alternations,
        "avg_run_length": round(sum(r["run_length"] for r in runs) / len(runs), 1) if runs else 0,
        "max_run_length": max(r["run_length"] for r in runs) if runs else 0,
        "runs": runs,
    }


def _pair_tracks(track_clips: Dict[str, List[Dict]], fps: float) -> List[Dict]:
    """Pair V1 and V2 clips by overlapping timeline positions."""
    v1_clips = track_clips.get("V1", [])
    v2_clips = track_clips.get("V2", [])

    if not v2_clips:
        return [
            {
                "beat_index": i,
                "v1": clip,
                "v2": None,
                "timeline_in_sec": clip["timeline_in_sec"],
                "timeline_out_sec": clip["timeline_out_sec"],
            }
            for i, clip in enumerate(v1_clips)
        ]

    timeline = []
    used_v2 = set()

    for i, v1 in enumerate(v1_clips):
        best_v2 = None
        best_overlap = 0

        for j, v2 in enumerate(v2_clips):
            if j in used_v2:
                continue
            overlap = _overlap(v1, v2)
            if overlap > best_overlap:
                best_overlap = overlap
                best_v2 = (j, v2)

        entry = {
            "beat_index": i,
            "v1": v1,
            "timeline_in_sec": v1["timeline_in_sec"],
            "timeline_out_sec": v1["timeline_out_sec"],
        }

        if best_v2 is not None and best_overlap > 0:
            used_v2.add(best_v2[0])
            entry["v2"] = best_v2[1]
        else:
            entry["v2"] = None

        timeline.append(entry)

    return timeline


def _overlap(a: Dict, b: Dict) -> float:
    """Compute timeline overlap between two clips in seconds."""
    start = max(a["timeline_in_sec"], b["timeline_in_sec"])
    end = min(a["timeline_out_sec"], b["timeline_out_sec"])
    return max(0, end - start)


def _text(elem, path: str) -> Optional[str]:
    """Get text content of a child element."""
    child = elem.find(path)
    return child.text if child is not None and child.text else None


def _text_int(elem, path: str, default: int = 0) -> int:
    """Get integer text content of a child element."""
    t = _text(elem, path)
    return int(t) if t else default


def _text_float(elem, path: str, default: float = 0.0) -> float:
    """Get float text content of a child element."""
    t = _text(elem, path)
    try:
        return float(t) if t else default
    except ValueError:
        return default


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} input.xml [output.json]")
        sys.exit(1)

    xml_path = sys.argv[1]
    manifest = parse_premiere_xml(xml_path)

    # Print technique summary
    tech = manifest.get("editorial_techniques", {})
    print(f"Parsed {len(manifest['timeline'])} timeline entries", file=sys.stderr)
    if tech.get("slow_motion"):
        print(f"  {len(tech['slow_motion'])} slow-motion clips", file=sys.stderr)
    if tech.get("speed_ramps"):
        print(f"  {len(tech['speed_ramps'])} speed ramps", file=sys.stderr)
    if tech.get("animated_zooms"):
        print(f"  {len(tech['animated_zooms'])} animated zooms", file=sys.stderr)
    if tech.get("scale_adjustments"):
        print(f"  {len(tech['scale_adjustments'])} scale adjustments (non-baseline)", file=sys.stderr)
    if tech.get("nested_sequences"):
        print(f"  {len(tech['nested_sequences'])} nested sequences", file=sys.stderr)
    if tech.get("stop_motion_sequences"):
        print(f"  {len(tech['stop_motion_sequences'])} stop-motion sequences", file=sys.stderr)
    cam = tech.get("camera_alternation", {})
    if cam:
        print(f"  Camera: {cam.get('front_pct', 0)}% front, {cam.get('overhead_pct', 0)}% overhead, "
              f"{cam.get('alternation_count', 0)} alternations", file=sys.stderr)

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
        with open(output_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"Wrote to {output_path}")
    else:
        print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
