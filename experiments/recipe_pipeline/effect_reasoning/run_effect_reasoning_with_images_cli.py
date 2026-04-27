#!/usr/bin/env python3
"""
run_effect_reasoning_with_images_cli.py — Test B (CLI flavor):
Like run_effect_reasoning.py but interleaves image-file references at every
editorial-boundary frame, so the Claude Code session uses its Read tool to
ingest the actual frame images as it analyzes.

Why CLI not SDK: we authenticate via the user's `claude` CLI (OAuth / Max),
not via ANTHROPIC_API_KEY.

Usage:
  python run_effect_reasoning_with_images_cli.py --recipe steak_tacos
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from run_effect_reasoning import compact_effects  # reuse text-block builder

PROMPT_TEMPLATE = (Path(__file__).parent / "PROMPT.md").read_text()

REPO_ROOT = Path("/Users/dandj/DevApps/ASI-Evolve")
FRAME_BASE = Path("/Users/dandj/DevApps/storyboard-gen/docs/watch-video")
OUT_BASE = Path("/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/Annotations")

MAX_FRAMES = 35
DEDUP_WINDOW_S = 0.4
FRAMES_PER_SECOND = 2.0


def collect_event_times(prproj_dump: dict) -> list[tuple[float, str]]:
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
    if not events:
        return []
    groups: list[list[tuple[float, str]]] = [[events[0]]]
    for t, lbl in events[1:]:
        if t - groups[-1][-1][0] <= DEDUP_WINDOW_S:
            groups[-1].append((t, lbl))
        else:
            groups.append([(t, lbl)])
    if len(groups) <= max_frames:
        return [(g[0][0], [lbl for _, lbl in g]) for g in groups]

    def score(g):
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


def find_nearest_frame(time_s: float, frames_dir: Path,
                        index_path: Optional[Path] = None) -> Optional[Path]:
    """Prefer 12fps dense-region frames when available via the index;
    fall back to 2fps frame nearest the target time."""
    if index_path and index_path.exists():
        try:
            idx = json.loads(index_path.read_text())
            best, best_d = None, 1e9
            for entry in idx.get("frames", []):
                d = abs(entry["time_seconds"] - time_s)
                # Prefer 12fps frames when within a region; weight by fps_layer
                weight = d / max(1, entry.get("fps_layer", 2))
                if weight < best_d:
                    best, best_d = entry, weight
            if best:
                return Path(best["path"])
        except Exception:
            pass
    frame_idx = round(time_s * FRAMES_PER_SECOND) + 1
    frame_path = frames_dir / f"frame_{frame_idx:04d}.jpg"
    if frame_path.exists():
        return frame_path
    candidates = sorted(frames_dir.glob("frame_*.jpg"))
    return candidates[-1] if candidates and frame_idx > len(candidates) else (candidates[0] if candidates else None)


def build_prompt(args, prproj_dump: dict) -> str:
    effects_block = compact_effects(prproj_dump)
    frames_dir = Path(args.frames_dir) if args.frames_dir else FRAME_BASE / f"{args.recipe}_frames_2fps"
    index_path = FRAME_BASE / f"{args.recipe}_frame_index.json"

    events = collect_event_times(prproj_dump)
    selected = dedup_and_select(events, args.max_frames)

    frame_lines: list[str] = []
    frame_lines.append("Below are the rendered final-cut frames at every meaningful editorial boundary in this recipe.\n")
    frame_lines.append("**You MUST read each image with the Read tool before reasoning about its moment.** Do not skip frames — the visual evidence is the point of this analysis.\n")
    sent = 0
    for t, labels in selected:
        fp = find_nearest_frame(t, frames_dir, index_path)
        if not fp or not fp.exists():
            continue
        frame_lines.append(f"\n**t={t:.2f}s** — events: {'; '.join(labels[:6])}")
        frame_lines.append(f"  Read this frame: `{fp}`")
        sent += 1

    print(f"  Will request {sent} frame Reads (using {'frame_index' if index_path.exists() else '2fps fallback'})", file=sys.stderr)

    prompt = (PROMPT_TEMPLATE
              .replace("{prproj_effects_block}", effects_block)
              .replace("{frame_analysis_block}", "\n".join(frame_lines))
              .replace("{existing_annotation_block}", "(intentionally omitted — derive editorial reasoning from PRPROJ_EFFECTS and the EMBEDDED FRAME IMAGES you Read above)"))
    return prompt


def call_claude(prompt: str, model: str, add_dirs: list[str] | None = None) -> str:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    cmd = ["claude", "-p", "--output-format", "json", "--strict-mcp-config", "--model", model,
           "--permission-mode", "acceptEdits"]
    if add_dirs:
        cmd += ["--add-dir"] + add_dirs
    print(f"  Calling claude CLI ({model}, prompt={len(prompt)} chars, add_dirs={add_dirs})...", file=sys.stderr)
    result = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True, cwd="/tmp",
        env=env, timeout=1800,
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[:500]}", file=sys.stderr)
        return ""
    try:
        return json.loads(result.stdout).get("result", "")
    except json.JSONDecodeError:
        return result.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipe", required=True)
    ap.add_argument("--frames-dir")
    ap.add_argument("--max-frames", type=int, default=MAX_FRAMES)
    ap.add_argument("--model", default="claude-opus-4-7")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out-suffix", default=" (image mode)")
    args = ap.parse_args()

    dump_path = REPO_ROOT / f"experiments/recipe_pipeline/prproj_dumps/{args.recipe}_effects.json"
    if not dump_path.exists():
        print(f"ERROR: {dump_path} missing", file=sys.stderr); sys.exit(1)

    prproj_dump = json.load(open(dump_path))
    prompt = build_prompt(args, prproj_dump)
    print(f"Prompt size: {len(prompt)} chars")

    workdir = Path(__file__).parent
    (workdir / f"{args.recipe}.image-prompt.md").write_text(prompt)

    if args.dry_run:
        print("--dry-run: skipping Claude call")
        return

    frames_dir_2fps = args.frames_dir or str(FRAME_BASE / f"{args.recipe}_frames_2fps")
    frames_dir_12fps = str(FRAME_BASE / f"{args.recipe}_frames_12fps")
    add_dirs = [frames_dir_2fps]
    if Path(frames_dir_12fps).exists():
        add_dirs.append(frames_dir_12fps)
    response = call_claude(prompt, args.model, add_dirs=add_dirs)
    if not response:
        print("ERROR: empty response", file=sys.stderr); sys.exit(2)

    out_path = OUT_BASE / f"{args.recipe} — Effect Reasoning{args.out_suffix}.md"
    header = (f"---\n"
              f"project: ASI-Evolve\n"
              f"type: working-file\n"
              f"source: \"effect-reasoning Opus pass (image mode via Claude CLI Read)\"\n"
              f"recipe: {args.recipe}\n"
              f"date: 2026-04-26\n"
              f"status: draft\n"
              f"tags: [pipeline, editorial-reasoning, effects, asi-evolve, image-mode]\n"
              f"---\n\n")
    out_path.write_text(header + response)
    print(f"Wrote reasoning to {out_path}")


if __name__ == "__main__":
    sys.exit(main())
