#!/usr/bin/env python3
"""
Parse Premiere Pro FCP XML into the same JSON structure as pipeline manifests.

Extracts clip placements from V1/V2 tracks with filenames, in/out points,
and timeline positions. This is the "ground truth" for scoring evolved configs.

Usage:
    python xml_to_manifest.py input.xml output.json
    python xml_to_manifest.py input.xml  # prints to stdout
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional


def parse_premiere_xml(xml_path: str) -> Dict:
    """Parse a Premiere FCP XML export into a manifest-compatible dict.

    Returns:
        {
            "source": "premiere_xml",
            "source_file": "...",
            "sequence_settings": {"width": ..., "height": ..., "fps": ...},
            "timeline": [
                {
                    "beat_index": 0,
                    "v1": {"file": "B19I6401.mov", "in": 12.0, "out": 16.0},
                    "v2": {"file": "AI2I5184.mov", "in": 39.0, "out": 43.0},
                    "timeline_in_sec": 0.0,
                    "timeline_out_sec": 4.0,
                }
            ]
        }
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Find the main sequence
    sequence = root.find(".//sequence")
    if sequence is None:
        raise ValueError(f"No <sequence> found in {xml_path}")

    # Sequence settings
    fps = _parse_fps(sequence)
    width = _text_int(sequence, ".//format/samplecharacteristics/width", 1920)
    height = _text_int(sequence, ".//format/samplecharacteristics/height", 1080)

    # Extract video tracks
    video_tracks = sequence.findall(".//video/track")
    if not video_tracks:
        raise ValueError("No video tracks found in sequence")

    # Parse clips from each track
    track_clips = {}
    for i, track in enumerate(video_tracks):
        track_name = f"V{i + 1}"
        clips = _parse_track_clips(track, fps)
        if clips:
            track_clips[track_name] = clips

    # Pair clips by timeline position (V1 + V2 that overlap in time)
    timeline = _pair_tracks(track_clips, fps)

    return {
        "source": "premiere_xml",
        "source_file": str(xml_path),
        "sequence_settings": {
            "width": width,
            "height": height,
            "fps": fps,
        },
        "timeline": timeline,
    }


def _parse_fps(sequence) -> float:
    """Extract frame rate from sequence timebase."""
    timebase = _text_int(sequence, ".//rate/timebase", 24)
    ntsc = _text(sequence, ".//rate/ntsc")
    if ntsc and ntsc.upper() == "TRUE":
        return timebase * 1000 / 1001  # e.g. 24 -> 23.976
    return float(timebase)


def _parse_track_clips(track, fps: float) -> List[Dict]:
    """Parse all clipitem elements from a track."""
    clips = []
    for clip in track.findall("clipitem"):
        parsed = _parse_clip(clip, fps)
        if parsed:
            clips.append(parsed)
    return clips


def _parse_clip(clip, fps: float) -> Optional[Dict]:
    """Parse a single clipitem element."""
    # Get the source file name
    file_elem = clip.find(".//file")
    if file_elem is None:
        return None

    # File name from <name> or <pathurl>
    filename = _text(file_elem, "name")
    if not filename:
        pathurl = _text(file_elem, "pathurl")
        if pathurl:
            filename = Path(pathurl.replace("file://", "").replace("%20", " ")).name
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

    return {
        "file": filename,
        "in": round(in_frame / fps, 3),
        "out": round(out_frame / fps, 3),
        "timeline_in_sec": round(start_frame / fps, 3),
        "timeline_out_sec": round(end_frame / fps, 3),
        "duration_sec": round((end_frame - start_frame) / fps, 3),
    }


def _pair_tracks(track_clips: Dict[str, List[Dict]], fps: float) -> List[Dict]:
    """Pair V1 and V2 clips by overlapping timeline positions.

    The pipeline produces paired edits (V1=front camera, V2=overhead).
    In Premiere, Dan places these on tracks 1 and 2. We pair them by
    finding clips that overlap in timeline position.
    """
    v1_clips = track_clips.get("V1", [])
    v2_clips = track_clips.get("V2", [])

    # If only one track, return as single-track entries
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

    # Pair by timeline overlap
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


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} input.xml [output.json]")
        sys.exit(1)

    xml_path = sys.argv[1]
    manifest = parse_premiere_xml(xml_path)

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
        with open(output_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"Wrote {len(manifest['timeline'])} timeline entries to {output_path}")
    else:
        print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
