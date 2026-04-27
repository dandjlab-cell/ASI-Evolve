#!/usr/bin/env python3
"""
run_effect_reasoning_with_images.py — Test B: send actual frame images to Opus
alongside the prproj effects + frame text descriptions.

Frame selection strategy:
  - At every cut boundary in the prproj (clip in/out times)
  - At every adjustment-layer effect start/end
  - At every mask + composite stack boundary
  - Dedup frames within 0.4s of each other
  - Cap at MAX_FRAMES (default 35) — drop low-priority frames if over

Each frame is a 2fps render from `storyboard-gen/docs/watch-video/{recipe}_frames_2fps/`.
The script picks the nearest 2fps frame index (each frame is at index*0.5s).

Output:
  Brain/Projects/ASI-Evolve/Annotations/{recipe} — Effect Reasoning (image mode).md

Usage:
  ANTHROPIC_API_KEY=... python run_effect_reasoning_with_images.py --recipe steak_tacos
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional

import anthropic

PROMPT_TEMPLATE = (Path(__file__).parent / "PROMPT.md").read_text()

REPO_ROOT = Path("/Users/dandj/DevApps/ASI-Evolve")
FRAME_BASE = Path("/Users/dandj/DevApps/storyboard-gen/docs/watch-video")
OUT_BASE = Path("/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/Annotations")

MAX_FRAMES = 35
DEDUP_WINDOW_S = 0.4
FRAMES_PER_SECOND = 2.0  # 2fps render


def collect_event_times(prproj_dump: dict) -> list[tuple[float, str]]:
    """Return (timeline_seconds, label) for every interesting boundary."""
    events: list[tuple[float, str]] = []
    INTRINSIC = {"Motion", "Opacity", "Vector Motion"}

    def walk(fc_list, ci):
        for fc in fc_list:
            mn = fc.get("match_name") or ""
            name = fc.get("display_name") or mn
            is_intrinsic = name in INTRINSIC and not ci.get("is_adjustment_layer")
            if not is_intrinsic and ci.get("in_seconds") is not None:
                tag = name
                if fc.get("instance_name"):
                    tag += f"({fc['instance_name']})"
                events.append((ci["in_seconds"], f"{tag} starts"))
                events.append((ci["out_seconds"], f"{tag} ends"))
            walk(fc.get("sub_components", []), ci)

    for t in prproj_dump["primary_sequence"]["tracks"]:
        for ci in t["clip_items"]:
            in_s, out_s = ci.get("in_seconds"), ci.get("out_seconds")
            if in_s is None:
                continue
            label = f"V{t['track_index']+1} cut"
            if ci.get("is_adjustment_layer"):
                label += " (adj)"
            events.append((in_s, f"{label} in"))
            events.append((out_s, f"{label} out"))
            walk(ci["filter_components"], ci)
    return sorted(events, key=lambda x: x[0])


def dedup_and_select(events: list[tuple[float, str]], max_frames: int) -> list[tuple[float, list[str]]]:
    """Group events within DEDUP_WINDOW_S, keep at most max_frames groups."""
    if not events:
        return []
    groups: list[list[tuple[float, str]]] = [[events[0]]]
    for t, lbl in events[1:]:
        if t - groups[-1][-1][0] <= DEDUP_WINDOW_S:
            groups[-1].append((t, lbl))
        else:
            groups.append([(t, lbl)])

    if len(groups) <= max_frames:
        out = [(g[0][0], [lbl for _, lbl in g]) for g in groups]
        return out

    # Too many — score each group by importance (effect events > cut events; non-V1 > V1)
    def score(g: list[tuple[float, str]]) -> int:
        s = 0
        for _, lbl in g:
            if any(k in lbl for k in ("Transform", "Mask", "Mirror", "Replicate", "Lumetri")):
                s += 5
            if "(adj)" in lbl:
                s += 3
            if "V5" in lbl or "V7" in lbl or "V4" in lbl:
                s += 2
            s += 1
        return s

    scored = sorted(enumerate(groups), key=lambda x: -score(x[1]))
    keep = sorted(i for i, _ in scored[:max_frames])
    return [(groups[i][0][0], [lbl for _, lbl in groups[i]]) for i in keep]


def find_nearest_frame(time_s: float, frames_dir: Path) -> Optional[Path]:
    """Frame N (1-indexed) is at (N-1)/FRAMES_PER_SECOND seconds."""
    frame_idx = round(time_s * FRAMES_PER_SECOND) + 1
    candidates = sorted(frames_dir.glob("frame_*.jpg"))
    if not candidates:
        return None
    if 1 <= frame_idx <= len(candidates):
        return frames_dir / f"frame_{frame_idx:04d}.jpg"
    return candidates[-1] if frame_idx > len(candidates) else candidates[0]


def encode_image(path: Path) -> dict:
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/jpeg", "data": data},
    }


def compact_effects_text(prproj_dump: dict) -> str:
    """Same compact effects table as the text-only runner — small enough to keep."""
    from run_effect_reasoning import compact_effects  # reuse
    return compact_effects(prproj_dump)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipe", required=True)
    ap.add_argument("--frames-dir", help="Override frames dir (default: storyboard-gen/docs/watch-video/{recipe}_frames_2fps)")
    ap.add_argument("--max-frames", type=int, default=MAX_FRAMES)
    ap.add_argument("--model", default="claude-opus-4-7")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out-suffix", default=" (image mode)")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).parent))

    dump_path = REPO_ROOT / f"experiments/recipe_pipeline/prproj_dumps/{args.recipe}_effects.json"
    if not dump_path.exists():
        print(f"ERROR: prproj dump not found at {dump_path}", file=sys.stderr)
        sys.exit(1)
    prproj_dump = json.load(open(dump_path))

    frames_dir = Path(args.frames_dir) if args.frames_dir else FRAME_BASE / f"{args.recipe}_frames_2fps"
    if not frames_dir.exists():
        print(f"ERROR: frames dir not found at {frames_dir}", file=sys.stderr)
        sys.exit(1)

    # Collect + dedup boundary events.
    events = collect_event_times(prproj_dump)
    selected = dedup_and_select(events, args.max_frames)
    print(f"Collected {len(events)} boundary events → {len(selected)} dedup groups (max {args.max_frames})")

    # Build the multimodal message content.
    effects_text = compact_effects_text(prproj_dump)

    intro = (PROMPT_TEMPLATE
             .replace("{prproj_effects_block}", effects_text)
             .replace("{frame_analysis_block}", "(see image frames embedded below)")
             .replace("{existing_annotation_block}", "(intentionally omitted — use the embedded frames + effects table)"))
    intro += "\n\n## Embedded frames\n\nEach frame below is a still from the rendered final cut at the indicated timeline second, captioned with the editorial events that begin/end nearby.\n"

    content: list[dict] = [{"type": "text", "text": intro}]
    sent_frames = 0
    for t, labels in selected:
        frame_path = find_nearest_frame(t, frames_dir)
        if not frame_path or not frame_path.exists():
            continue
        caption = f"\n\n**Frame at t={t:.2f}s** ({frame_path.name}) — events: {'; '.join(labels[:6])}"
        content.append({"type": "text", "text": caption})
        content.append(encode_image(frame_path))
        sent_frames += 1

    print(f"Sending {sent_frames} frames + {len(intro)} chars of text")

    if args.dry_run:
        print("--dry-run: skipping API call")
        return

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=args.model,
        max_tokens=8000,
        messages=[{"role": "user", "content": content}],
    )

    response = "".join(block.text for block in message.content if hasattr(block, "text"))

    out_path = OUT_BASE / f"{args.recipe} — Effect Reasoning{args.out_suffix}.md"
    header = (f"---\n"
              f"project: ASI-Evolve\n"
              f"type: working-file\n"
              f"source: \"effect-reasoning Opus pass (image mode, {sent_frames} frames)\"\n"
              f"recipe: {args.recipe}\n"
              f"date: 2026-04-26\n"
              f"status: draft\n"
              f"tags: [pipeline, editorial-reasoning, effects, asi-evolve, image-mode]\n"
              f"---\n\n")
    out_path.write_text(header + response)

    usage = message.usage
    print(f"\nWrote reasoning to {out_path}")
    print(f"Tokens: input={usage.input_tokens}, output={usage.output_tokens}")


if __name__ == "__main__":
    sys.exit(main())
