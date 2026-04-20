#!/usr/bin/env python3
"""
Aggregate editorial annotations into a style profile for prompt injection.

Reads all annotation JSONs and produces editorial_style.md — a human-readable
summary of Dan's editorial patterns that feeds into the Researcher/Analyzer prompts.

Usage:
    python aggregate_style.py                    # reads annotations/*.json
    python aggregate_style.py --dir annotations/ --output editorial_style.md
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def load_annotations(annotations_dir: str) -> List[dict]:
    """Load all annotation JSON files from a directory."""
    annotations = []
    for f in sorted(Path(annotations_dir).glob("*.json")):
        with open(f) as fh:
            annotations.append(json.load(fh))
    return annotations


def aggregate(annotations: List[dict]) -> dict:
    """Aggregate patterns across all annotated recipes."""
    camera_rules = []
    duration_rules = []
    inpoint_rules = []
    pipeline_failures = []
    beat_type_stats = defaultdict(lambda: {"front": 0, "overhead": 0, "durations": []})

    for ann in annotations:
        for beat in ann.get("beats", []):
            cam = beat.get("camera", {})
            dur = beat.get("duration", {})
            ip = beat.get("in_point", {})
            verdict = beat.get("verdict", "")
            beat_type = beat.get("beat_type", "unknown")
            confidence = beat.get("confidence", "medium")

            # Use correction if present, otherwise LLM reasoning
            cam_reasoning = beat.get("correction") if beat.get("correction") and "camera" in beat.get("correction", "").lower() else cam.get("reasoning", "")
            dur_reasoning = dur.get("reasoning", "")
            ip_reasoning = ip.get("reasoning", "")

            # Collect reasoning strings (skip empty/TODO)
            if cam_reasoning and "TODO" not in cam_reasoning:
                camera_rules.append({
                    "reasoning": cam_reasoning,
                    "choice": cam.get("choice", ""),
                    "beat_type": beat_type,
                    "confidence": confidence,
                })
            if dur_reasoning and "TODO" not in dur_reasoning:
                duration_rules.append({
                    "reasoning": dur_reasoning,
                    "seconds": dur.get("seconds", 0),
                    "beat_type": beat_type,
                })
            if ip_reasoning and "TODO" not in ip_reasoning:
                inpoint_rules.append({
                    "reasoning": ip_reasoning,
                    "beat_type": beat_type,
                })

            # Pipeline failures
            if verdict in ("camera_swapped", "trimmed", "removed", "added"):
                pipeline_failures.append({
                    "verdict": verdict,
                    "beat_type": beat_type,
                    "description": beat.get("beat_description", ""),
                    "pipeline_info": beat.get("pipeline_info", ""),
                    "correction": beat.get("correction"),
                })

            # Beat type stats
            if cam.get("choice"):
                beat_type_stats[beat_type][cam["choice"]] += 1
            if dur.get("seconds"):
                beat_type_stats[beat_type]["durations"].append(dur["seconds"])

    return {
        "camera_rules": camera_rules,
        "duration_rules": duration_rules,
        "inpoint_rules": inpoint_rules,
        "pipeline_failures": pipeline_failures,
        "beat_type_stats": dict(beat_type_stats),
        "recipe_count": len(annotations),
        "total_beats": sum(len(a.get("beats", [])) for a in annotations),
    }


def render_markdown(agg: dict) -> str:
    """Render aggregated data as editorial_style.md."""
    lines = [
        "## Editor's Style Profile",
        f"*Aggregated from {agg['recipe_count']} recipe(s), {agg['total_beats']} beats*",
        "",
    ]

    # Camera selection rules
    lines.append("### Camera Selection Rules")
    front_reasons = [r for r in agg["camera_rules"] if r["choice"] == "front"]
    overhead_reasons = [r for r in agg["camera_rules"] if r["choice"] == "overhead"]

    if overhead_reasons:
        lines.append("**Overhead (top-down) for:**")
        seen = set()
        for r in overhead_reasons:
            short = r["reasoning"][:120]
            if short not in seen:
                seen.add(short)
                lines.append(f"- {short} ({r['beat_type']})")
        lines.append("")

    if front_reasons:
        lines.append("**Front (eye-level) for:**")
        seen = set()
        for r in front_reasons:
            short = r["reasoning"][:120]
            if short not in seen:
                seen.add(short)
                lines.append(f"- {short} ({r['beat_type']})")
        lines.append("")

    # Beat type camera stats
    stats = agg.get("beat_type_stats", {})
    if stats:
        lines.append("**Camera preference by beat type:**")
        for bt, s in sorted(stats.items()):
            f = s.get("front", 0)
            o = s.get("overhead", 0)
            total = f + o
            if total > 0:
                lines.append(f"- {bt}: front {f}/{total} ({f/total*100:.0f}%), overhead {o}/{total} ({o/total*100:.0f}%)")
        lines.append("")

    # Pacing rules
    lines.append("### Pacing Rules")
    if stats:
        for bt, s in sorted(stats.items()):
            durs = s.get("durations", [])
            if durs:
                avg = sum(durs) / len(durs)
                mn, mx = min(durs), max(durs)
                lines.append(f"- {bt}: avg {avg:.1f}s (range {mn:.1f}-{mx:.1f}s, n={len(durs)})")
    lines.append("")

    seen = set()
    for r in agg["duration_rules"]:
        short = r["reasoning"][:120]
        if short not in seen:
            seen.add(short)
            lines.append(f"- [{r['beat_type']}, {r['seconds']:.1f}s] {short}")
    lines.append("")

    # In-point rules
    lines.append("### In-point / Action Timing Rules")
    seen = set()
    for r in agg["inpoint_rules"]:
        short = r["reasoning"][:120]
        if short not in seen:
            seen.add(short)
            lines.append(f"- [{r['beat_type']}] {short}")
    lines.append("")

    # Known pipeline failures
    if agg["pipeline_failures"]:
        lines.append("### Known Pipeline Failures")
        by_verdict = defaultdict(list)
        for f in agg["pipeline_failures"]:
            by_verdict[f["verdict"]].append(f)

        for verdict, failures in sorted(by_verdict.items()):
            lines.append(f"**{verdict}** ({len(failures)} beats):")
            for f in failures[:5]:  # Cap at 5 per type
                desc = f.get("description", "")[:60]
                pi = f.get("pipeline_info", "")[:60]
                lines.append(f"- {desc} — pipeline: {pi}")
            if len(failures) > 5:
                lines.append(f"- ... and {len(failures) - 5} more")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Aggregate editorial annotations into style profile")
    parser.add_argument("--dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "annotations"),
                        help="Directory with annotation JSON files")
    parser.add_argument("--output", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "editorial_style.md"),
                        help="Output markdown file")
    args = parser.parse_args()

    annotations = load_annotations(args.dir)
    if not annotations:
        print(f"No annotation files found in {args.dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(annotations)} annotation file(s)")
    agg = aggregate(annotations)
    md = render_markdown(agg)

    with open(args.output, "w") as f:
        f.write(md)
    print(f"Wrote style profile to {args.output}")
    print(f"  {len(agg['camera_rules'])} camera rules")
    print(f"  {len(agg['duration_rules'])} duration rules")
    print(f"  {len(agg['inpoint_rules'])} in-point rules")
    print(f"  {len(agg['pipeline_failures'])} pipeline failures")


if __name__ == "__main__":
    main()
