#!/usr/bin/env python3
"""
run_effect_reasoning.py — Per-recipe Opus pass that adds effect-and-angle
reasoning on top of the existing structural annotation.

Inputs:
  - prproj effects JSON (from prproj_reader.py)
  - Pass 1 frame analysis (markdown table at 2fps)
  - Existing per-beat annotation (markdown)

Output:
  Markdown reasoning saved to:
    Brain/Projects/ASI-Evolve/Annotations/{recipe} — Effect Reasoning.md

Usage:
  python run_effect_reasoning.py --recipe steak_tacos
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


PROMPT_TEMPLATE = (Path(__file__).parent / "PROMPT.md").read_text()


def compact_effects(prproj_dump: dict) -> str:
    """Render the prproj dump as a compact, timeline-ordered event list.

    Skips intrinsic per-clip Motion/Opacity (they're the default and ubiquitous);
    surfaces cuts, adjustment-layer effects, Lumetri grades, masks, MOGRT text,
    and stacked-adj-layer composites. Times in timeline seconds.
    """
    lines: list[str] = []
    INTRINSIC_TO_SKIP = {"Motion", "Opacity", "Vector Motion"}

    # Pass 1 — gather per-track items with effect summaries.
    track_items: list[dict] = []
    for t in prproj_dump["primary_sequence"]["tracks"]:
        track_label = f"V{t['track_index'] + 1}"
        for ci in t["clip_items"]:
            in_s = ci.get("in_seconds")
            out_s = ci.get("out_seconds")
            if in_s is None:
                continue
            effects: list[str] = []
            text_strings: list[str] = []
            mask_info: list[str] = []

            def walk(fc_list: list[dict]) -> None:
                for fc in fc_list:
                    name = fc.get("display_name") or fc.get("match_name") or "?"
                    inst = fc.get("instance_name") or ""
                    is_adj = ci.get("is_adjustment_layer", False)
                    if name in INTRINSIC_TO_SKIP and not is_adj:
                        # Still walk in case sub_components exist (e.g. mask under Opacity)
                        walk(fc.get("sub_components", []))
                        continue
                    # Effect summary
                    suffix = f" ({inst})" if inst else ""
                    animated_params = [p.get("name") for p in fc.get("params", [])
                                       if p.get("animated") and p.get("name")]
                    anim_str = f" [animated: {', '.join(animated_params)}]" if animated_params else ""
                    effects.append(f"{name}{suffix}{anim_str}")
                    # Text content
                    for p in fc.get("params", []):
                        dec = p.get("decoded") or {}
                        for tev in dec.get("text_edit_values", []):
                            text_strings.append(tev)
                        if "mask_vertices" in dec:
                            verts = dec["mask_vertices"]
                            shape = "rect-like" if len(verts) == 4 and all(v["is_corner"] for v in verts) else f"{len(verts)}-vertex"
                            mask_info.append(f"static {shape} mask")
                    walk(fc.get("sub_components", []))

            walk(ci["filter_components"])

            track_items.append({
                "track": t["track_index"],
                "track_label": track_label,
                "in": in_s,
                "out": out_s,
                "is_adj": ci.get("is_adjustment_layer", False),
                "source_ref": ci.get("source_object_ref"),
                "effects": effects,
                "text": text_strings,
                "mask": mask_info,
                "playback_speed": ci.get("playback_speed"),
                "speed_ramp": ci.get("speed_ramp"),
            })

    # Pass 2 — render in timeline order.
    track_items.sort(key=lambda x: (x["in"], x["track"]))

    # Timeline cuts header
    lines.append("**Timeline (cuts + effects + masks + MOGRT text + speed, ordered by in-time):**")
    lines.append("")
    lines.append("| Timeline | Track | Adj | Effects | Text overlay | Mask | Speed |")
    lines.append("|---|---|---|---|---|---|---|")
    for it in track_items:
        adj = "ADJ" if it["is_adj"] else ""
        eff = ", ".join(it["effects"]) if it["effects"] else "—"
        txt = " / ".join(it["text"]) if it["text"] else ""
        msk = ", ".join(it["mask"]) if it["mask"] else ""
        speed = ""
        ps = it.get("playback_speed")
        if ps is not None and ps != 1.0:
            speed = f"{int(ps*100)}%"
        if it.get("speed_ramp"):
            kf = it["speed_ramp"].get("keyframes") or []
            speed = f"RAMP ({len(kf)} keyframes)" + (f" base={int(ps*100)}%" if ps and ps != 1.0 else "")
        lines.append(f"| {it['in']:.2f}–{it['out']:.2f}s | {it['track_label']} | {adj} | {eff} | {txt} | {msk} | {speed} |")

    # Pass 3 — surface stacked-adj-layer composites.
    adj_items = [it for it in track_items if it["is_adj"]]
    stacks: list[str] = []
    for i, a in enumerate(adj_items):
        for b in adj_items[i + 1:]:
            if a["track"] == b["track"]:
                continue
            if a["in"] < b["out"] and b["in"] < a["out"]:
                top = b if b["track"] > a["track"] else a
                bot = a if top is b else b
                stacks.append(
                    f"- **{min(a['in'], b['in']):.2f}–{max(a['out'], b['out']):.2f}s**: "
                    f"{top['track_label']} ({', '.join(top['effects']) or 'no effect'}) "
                    f"stacked over {bot['track_label']} ({', '.join(bot['effects']) or 'no effect'})"
                )
    if stacks:
        lines.append("")
        lines.append("**Stacked adjustment-layer composites (overlapping adj clips on different tracks):**")
        lines.extend(stacks)

    return "\n".join(lines)


def load_frame_analysis(recipe: str) -> str:
    """Load the canonical Pass 1 frame analysis if present."""
    base = Path("/Users/dandj/DevApps/storyboard-gen/docs/watch-video")
    primary = base / f"pass1_{recipe}.md"
    if primary.exists():
        return primary.read_text()
    # Fallback: 2fps part 1
    fallback = base / f"pass1_{recipe}_2fps.md"
    if fallback.exists():
        return fallback.read_text()
    parts = sorted(base.glob(f"pass1_{recipe}_2fps_part*.md"))
    if parts:
        return "\n\n".join(p.read_text() for p in parts)
    return f"(no frame analysis found at {base}/pass1_{recipe}*.md)"


def load_existing_annotation(recipe: str) -> str:
    path = Path(f"/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/Annotations/{recipe}.md")
    if path.exists():
        return path.read_text()
    return f"(no existing annotation at {path})"


def call_claude(prompt: str, model: str = "claude-opus-4-7") -> str:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--strict-mcp-config",
        "--model", model,
    ]
    print(f"  Calling claude CLI ({model}, prompt={len(prompt)} chars)...", file=sys.stderr)
    result = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True, cwd="/tmp",
        env=env, timeout=600,
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[:500]}", file=sys.stderr)
        return ""
    try:
        data = json.loads(result.stdout)
        return data.get("result", "")
    except json.JSONDecodeError:
        return result.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipe", required=True, help="Recipe slug (matches prproj_dumps/{slug}_effects.json)")
    ap.add_argument("--prproj-dump", help="Override path to prproj effects JSON")
    ap.add_argument("--output", help="Override output path (default: Brain Annotations/{recipe} — Effect Reasoning.md)")
    ap.add_argument("--dry-run", action="store_true", help="Build prompt only, don't call Claude")
    ap.add_argument("--model", default="claude-opus-4-7")
    ap.add_argument("--no-annotation", action="store_true", help="Skip the existing annotation block (test for anchoring)")
    ap.add_argument("--out-suffix", default="", help="Suffix on output filename (e.g. ' (no-annotation)')")
    args = ap.parse_args()

    dump_path = args.prproj_dump or f"/Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline/prproj_dumps/{args.recipe}_effects.json"
    if not Path(dump_path).exists():
        print(f"ERROR: prproj dump not found at {dump_path}", file=sys.stderr)
        sys.exit(1)

    prproj_dump = json.load(open(dump_path))
    effects_block = compact_effects(prproj_dump)
    frame_block = load_frame_analysis(args.recipe)
    if args.no_annotation:
        annotation_block = "(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)"
    else:
        annotation_block = load_existing_annotation(args.recipe)

    prompt = (PROMPT_TEMPLATE
              .replace("{prproj_effects_block}", effects_block)
              .replace("{frame_analysis_block}", frame_block)
              .replace("{existing_annotation_block}", annotation_block))

    print(f"Prompt size: {len(prompt)} chars")
    print(f"  effects_block: {len(effects_block)} chars")
    print(f"  frame_block:   {len(frame_block)} chars")
    print(f"  annotation:    {len(annotation_block)} chars")

    workdir = Path(__file__).parent
    prompt_out = workdir / f"{args.recipe}.prompt.md"
    prompt_out.write_text(prompt)
    print(f"\nWrote filled prompt to {prompt_out}")

    if args.dry_run:
        print("--dry-run: skipping Claude call")
        return

    response = call_claude(prompt, model=args.model)
    if not response:
        print("ERROR: empty response from Claude", file=sys.stderr)
        sys.exit(2)

    out_path = Path(args.output) if args.output else Path(
        f"/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/Annotations/{args.recipe} — Effect Reasoning{args.out_suffix}.md"
    )
    header = (f"---\n"
              f"project: ASI-Evolve\n"
              f"type: working-file\n"
              f"source: \"effect-reasoning Opus pass\"\n"
              f"recipe: {args.recipe}\n"
              f"date: 2026-04-26\n"
              f"status: draft\n"
              f"tags: [pipeline, editorial-reasoning, effects, asi-evolve]\n"
              f"---\n\n")
    out_path.write_text(header + response)
    print(f"\nWrote reasoning to {out_path}")


if __name__ == "__main__":
    sys.exit(main())
