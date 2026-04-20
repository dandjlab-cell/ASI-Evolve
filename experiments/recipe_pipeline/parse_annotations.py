#!/usr/bin/env python3
"""
Parse Obsidian editorial annotation files into structured JSON.

Reads the markdown format produced by analyze_editorial_judgment.py
(with Dan's corrections applied) and outputs JSON for the scorer.

Dan's corrections override LLM-generated reasoning:
  - If "Dan's correction:" has content, it replaces the LLM reasoning
  - The correction field in JSON captures what Dan changed

Usage:
    python parse_annotations.py annotations/basil_pesto.md -o annotations/basil_pesto.json
    python parse_annotations.py --dir ~/DevApps/Brain/Projects/ASI-Evolve/Annotations/
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional


def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter from markdown text."""
    match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not match:
        return {}

    fm = {}
    for line in match.group(1).split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            val = val.strip().strip('"').strip("'")
            # Handle list values like [tag1, tag2]
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip() for v in val[1:-1].split(",")]
            fm[key.strip()] = val
    return fm


def parse_annotation_file(md_path: str) -> dict:
    """Parse a single annotation markdown file into structured JSON."""
    with open(md_path) as f:
        text = f.read()

    frontmatter = parse_frontmatter(text)

    # Extract global notes (between ## Global Notes and ## Beat Annotations)
    global_match = re.search(
        r'## Global Notes\s*\n(.*?)(?=\n## |\Z)',
        text, re.DOTALL
    )
    global_notes = global_match.group(1).strip() if global_match else ""

    # Split on beat headings — capture title on the heading line only,
    # body is everything until the next ### Beat or ## section
    beat_pattern = re.compile(
        r'### Beat (\d+) — ([^\n]+)\n(.*?)(?=\n### Beat |\n## |\Z)',
        re.DOTALL
    )
    beats = []

    for match in beat_pattern.finditer(text):
        beat_idx = int(match.group(1))
        beat_header = match.group(2).strip()
        beat_body = match.group(3)

        beat = _parse_beat(beat_idx, beat_header, beat_body)
        beats.append(beat)

    return {
        "recipe": frontmatter.get("recipe", Path(md_path).stem),
        "source_file": str(md_path),
        "global_notes": global_notes,
        "beats": beats,
    }


def _parse_beat(beat_idx: int, header: str, body: str) -> dict:
    """Parse a single beat section."""
    beat = {
        "beat_index": beat_idx,
        "beat_description": header,
        "camera": {"choice": "", "reasoning": ""},
        "duration": {"seconds": 0.0, "reasoning": ""},
        "in_point": {"seconds": 0.0, "reasoning": ""},
        "verdict": "",
        "confidence": "medium",
        "pipeline_info": "",
        "correction": None,
    }

    for line in body.split("\n"):
        line = line.strip()
        if not line.startswith("- **"):
            continue

        # Parse "- **Key:** value" (bold wraps the colon: **Camera:** not **Camera**:)
        key_match = re.match(r'^- \*\*(.+?):\*\*\s*(.*)', line)
        if not key_match:
            # Also try **Key**: format
            key_match = re.match(r'^- \*\*(.+?)\*\*:\s*(.*)', line)
        if not key_match:
            continue

        key = key_match.group(1).strip().lower()
        value = key_match.group(2).strip()

        if key == "camera":
            choice, _, reasoning = value.partition("|")
            cam = choice.strip().lower()
            if cam in ("front", "overhead"):
                beat["camera"]["choice"] = cam
            beat["camera"]["reasoning"] = reasoning.strip()

        elif key == "duration":
            dur_match = re.match(r'([\d.]+)s', value)
            if dur_match:
                beat["duration"]["seconds"] = float(dur_match.group(1))
            _, _, reasoning = value.partition("|")
            beat["duration"]["reasoning"] = reasoning.strip()

        elif key == "in-point" or key == "in_point" or key == "inpoint":
            ip_match = re.match(r'([\d.]+)s', value)
            if ip_match:
                beat["in_point"]["seconds"] = float(ip_match.group(1))
            _, _, reasoning = value.partition("|")
            beat["in_point"]["reasoning"] = reasoning.strip()

        elif key == "verdict":
            beat["verdict"] = value.strip().lower()

        elif key == "confidence":
            conf = value.strip().lower()
            if conf in ("high", "medium", "low"):
                beat["confidence"] = conf

        elif key == "pipeline note":
            beat["pipeline_info"] = value

        elif key == "dan's correction" or key == "correction":
            correction = value.strip()
            if correction and correction.lower() not in ("", "none", "n/a"):
                beat["correction"] = correction

    return beat


def merge_corrections(parsed: dict) -> dict:
    """Apply Dan's corrections to override LLM reasoning.

    If a beat has a correction, parse it for dimension-specific overrides.
    Format: "Camera: actually because X. Duration: should be Y."
    Or just a freeform string that applies to the most relevant dimension.
    """
    for beat in parsed.get("beats", []):
        correction = beat.get("correction")
        if not correction:
            continue

        # Try to parse structured corrections
        cam_match = re.search(r'[Cc]amera:\s*(.+?)(?=[.;]|[A-Z]\w+:|$)', correction)
        dur_match = re.search(r'[Dd]uration:\s*(.+?)(?=[.;]|[A-Z]\w+:|$)', correction)
        ip_match = re.search(r'[Ii]n-?point:\s*(.+?)(?=[.;]|[A-Z]\w+:|$)', correction)

        if cam_match:
            beat["camera"]["reasoning"] = cam_match.group(1).strip()
        if dur_match:
            beat["duration"]["reasoning"] = dur_match.group(1).strip()
        if ip_match:
            beat["in_point"]["reasoning"] = ip_match.group(1).strip()

        # If no structured format, the correction is a general note
        # Keep it in the correction field for the aggregator to use

    return parsed


def main():
    parser = argparse.ArgumentParser(description="Parse editorial annotation markdown into JSON")
    parser.add_argument("input", nargs="?", help="Path to annotation .md file")
    parser.add_argument("-o", "--output", help="Output JSON path")
    parser.add_argument("--dir", help="Parse all .md files in directory")
    args = parser.parse_args()

    if args.dir:
        md_dir = Path(args.dir)
        out_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "annotations"
        out_dir.mkdir(exist_ok=True)

        for md_file in sorted(md_dir.glob("*.md")):
            print(f"Parsing {md_file.name}...")
            parsed = parse_annotation_file(str(md_file))
            parsed = merge_corrections(parsed)
            out_path = out_dir / f"{md_file.stem}.json"
            with open(out_path, "w") as f:
                json.dump(parsed, f, indent=2)
            print(f"  → {out_path} ({len(parsed['beats'])} beats)")

    elif args.input:
        parsed = parse_annotation_file(args.input)
        parsed = merge_corrections(parsed)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(parsed, f, indent=2)
            print(f"Wrote {len(parsed['beats'])} beats to {args.output}")
        else:
            print(json.dumps(parsed, indent=2))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
