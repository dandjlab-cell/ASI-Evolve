#!/usr/bin/env python3
"""
Surgical frame extractor for recipe videos.

Given an approved-edit manifest (parsed XML), extracts:
  - 2fps baseline across the whole video
  - 12fps ONLY within "dense regions" (outer stop_motion_sequences +
    nest-internal rapid-cut spans, both converted to absolute timeline times)

Merges both into a single frame directory with sequential names ordered by
time, plus a frame_times.json mapping frame_num → time_sec. Pass 1 agents
read frames in order and reference frame_times.json for accurate timestamps.

Usage:
    python extract_frames_smart.py <video.mp4> <manifest.json> <out_dir>
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def collect_dense_regions(manifest: dict) -> list:
    """Return sorted list of (start_sec, end_sec) covering all rapid-cut regions.

    Sources:
    1. editorial_techniques.stop_motion_sequences[] (outer timeline detection)
    2. Any timeline entry whose v1 or v2 is a nest — scan its inner_clips for
       clusters of short (<0.3s) consecutive clips, emit as regions with
       absolute times (nest.timeline_in_sec + inner.timeline_in_sec).

    Overlapping regions are merged.
    """
    regions = []

    # Source 1: outer stop-motion detection
    et = manifest.get("editorial_techniques", {})
    for sm in et.get("stop_motion_sequences", []):
        s = sm.get("timeline_in_sec")
        e = sm.get("timeline_out_sec")
        if s is not None and e is not None and e > s:
            regions.append((float(s), float(e)))

    # Source 2: walk nests for hidden rapid-cut inner clips
    for entry in manifest.get("timeline", []):
        for track in ("v1", "v2"):
            clip = entry.get(track)
            if not clip or not clip.get("nested"):
                continue
            nest_base = entry.get("timeline_in_sec", 0.0)
            inner = clip.get("inner_clips", [])
            if not inner:
                continue
            # Find runs of 3+ consecutive short inner clips
            short_flags = [
                (ic.get("timeline_out_sec", 0) - ic.get("timeline_in_sec", 0)) < 0.3
                for ic in inner
            ]
            i = 0
            while i < len(short_flags):
                if not short_flags[i]:
                    i += 1
                    continue
                j = i
                while j < len(short_flags) and short_flags[j]:
                    j += 1
                run_len = j - i
                if run_len >= 3:
                    abs_start = nest_base + inner[i].get("timeline_in_sec", 0)
                    abs_end = nest_base + inner[j - 1].get("timeline_out_sec", 0)
                    regions.append((abs_start, abs_end))
                i = j

    # Merge overlapping / adjacent regions
    regions.sort()
    merged = []
    for s, e in regions:
        if merged and s <= merged[-1][1] + 0.1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def ffmpeg_extract(video_path: str, out_dir: Path, fps: float, start: float = 0.0, duration: float = None):
    """Run ffmpeg to extract frames at a given fps, optionally within a time range."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y"]
    if start > 0:
        cmd += ["-ss", f"{start:.3f}"]
    if duration is not None:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += [
        "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "2",
        str(out_dir / "frame_%04d.jpg"),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("manifest")
    ap.add_argument("out_dir")
    ap.add_argument("--baseline-fps", type=float, default=2.0)
    ap.add_argument("--dense-fps", type=float, default=12.0)
    args = ap.parse_args()

    manifest = json.load(open(args.manifest))
    regions = collect_dense_regions(manifest)
    print(f"Dense regions found: {len(regions)}")
    for s, e in regions:
        print(f"  {s:6.2f}s - {e:6.2f}s  ({e-s:.2f}s span)")

    out = Path(args.out_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    baseline_dir = out / "_baseline"
    dense_dir = out / "_dense"

    # 1. Extract 2fps baseline
    print(f"\nExtracting {args.baseline_fps}fps baseline...")
    ffmpeg_extract(args.video, baseline_dir, args.baseline_fps)
    baseline_frames = sorted(baseline_dir.glob("*.jpg"))
    print(f"  baseline frames: {len(baseline_frames)}")

    # Collect (time_sec, source_path, source_type)
    all_frames = []
    for i, p in enumerate(baseline_frames):
        t = i / args.baseline_fps
        all_frames.append((t, p, "baseline"))

    # 2. Extract dense regions at 12fps
    for ri, (rs, re_) in enumerate(regions):
        region_dir = dense_dir / f"region_{ri:02d}"
        duration = re_ - rs
        ffmpeg_extract(args.video, region_dir, args.dense_fps, start=rs, duration=duration)
        dense_frames = sorted(region_dir.glob("*.jpg"))
        for i, p in enumerate(dense_frames):
            t = rs + i / args.dense_fps
            # Skip dense frames that already have a baseline frame within 0.1s
            close_to_baseline = any(
                abs(t - bt) < (0.5 / args.dense_fps)
                for (bt, _, src) in all_frames
                if src == "baseline"
            )
            if not close_to_baseline:
                all_frames.append((t, p, "dense"))

    # Sort by time and rename into a clean sequential set
    all_frames.sort(key=lambda x: x[0])
    frame_times = {}
    for i, (t, src_path, src_type) in enumerate(all_frames, start=1):
        dest = out / f"frame_{i:04d}.jpg"
        shutil.copy(src_path, dest)
        frame_times[f"frame_{i:04d}"] = {"time_sec": round(t, 3), "source": src_type}

    # Clean up scratch subdirs
    if baseline_dir.exists():
        shutil.rmtree(baseline_dir)
    if dense_dir.exists():
        shutil.rmtree(dense_dir)

    # Write frame_times.json
    (out / "frame_times.json").write_text(json.dumps(frame_times, indent=2))

    print(f"\nTotal frames in {out}: {len(all_frames)}")
    baseline_n = sum(1 for _, _, s in all_frames if s == "baseline")
    dense_n = len(all_frames) - baseline_n
    print(f"  baseline: {baseline_n}   dense: {dense_n}")
    print(f"Wrote frame_times.json")


if __name__ == "__main__":
    main()
