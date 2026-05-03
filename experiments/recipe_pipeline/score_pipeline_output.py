#!/usr/bin/env python3
"""
score_pipeline_output.py — Phase 4 of the master plan.

Score an AI-generated pipeline manifest against the same scorer Dan's
approved edits run through. Compare to Dan's score on the same recipe.
The delta is the first real fitness gradient — the first time we
measure how far the AI is from Dan's editorial bar in numbers.

Reads the roughcut-ai pipeline output at
    ~/DevApps/roughcut-ai/runs/{recipe}/{recipe}_manifest.json
converts each timeline entry to annotation-beat format that
score_rules.py understands, scores it, and compares against the
existing Dan annotation at
    experiments/recipe_pipeline/annotations/{recipe}.json

Conversion notes:
  - camera.choice from v1.file prefix via camera_mapping.json
    (per-recipe mapping; per the user's "verify visually per recipe"
     rule from the camera-detection-bug session 2026-05-02).
  - duration in seconds from timeline_in/timeline_out timecodes,
    parsed at sequence_settings.fps.
  - in_point/out_point in seconds from v1.adjusted_in/adjusted_out.
  - mogrt_overlaps synthesized from `text` field (the AI's MOGRT
    plan): a "beat_label" or "ingredient" text becomes a single
    mogrt_overlap entry with the beat's full duration.
  - beat_description copied from `step`.
  - effects/effects_reasoning intentionally left empty: the AI's
    manifest doesn't propose speed ramps yet (those come from a
    later pipeline stage). R4 will score 0.7 neutral on the AI
    output by design — this is the gap to surface, not a bug.

Usage:
    python3 experiments/recipe_pipeline/score_pipeline_output.py basil_pesto
    python3 experiments/recipe_pipeline/score_pipeline_output.py basil_pesto --no-vault-note
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent
ANNOTATIONS_DIR = REPO_ROOT / "annotations"
PIPELINE_RUNS_ROOT = Path.home() / "DevApps/roughcut-ai/runs"
CAMERA_MAPPING_PATH = REPO_ROOT / "camera_mapping.json"
PIPELINE_SCORES_DIR = REPO_ROOT / "pipeline_scores"

sys.path.insert(0, str(REPO_ROOT))
from score_rules import score_annotation  # noqa: E402

logger = logging.getLogger("score_pipeline_output")


# ---------------------------------------------------------------------------
# Manifest → annotation conversion
# ---------------------------------------------------------------------------

def parse_timecode(tc: str, fps: float) -> float:
    """Parse 'HH:MM:SS:FF' timecode at fps → seconds."""
    parts = tc.split(":")
    if len(parts) != 4:
        raise ValueError(f"bad timecode: {tc!r}")
    h, m, s, f = (int(p) for p in parts)
    return h * 3600 + m * 60 + s + f / fps


def load_camera_mapping(recipe_slug: str) -> dict[str, str]:
    """Return the {prefix: camera} mapping for this recipe, stripped of provenance."""
    raw = json.loads(CAMERA_MAPPING_PATH.read_text())
    entry = raw.get("mappings", {}).get(recipe_slug, {})
    return {k: v for k, v in entry.items() if not k.startswith("_")}


def manifest_entry_to_beat(
    entry: dict,
    fps: float,
    camera_map: dict[str, str],
    beat_index: int,
) -> dict:
    """Convert one AI manifest timeline entry into an annotation-beat dict."""
    v1 = entry.get("v1") or {}
    fn = v1.get("file") or ""
    prefix = fn[:5]
    camera = camera_map.get(prefix, "unknown")

    # Duration from timeline_in/out timecodes
    tl_in_tc = entry.get("timeline_in", "00:00:00:00")
    tl_out_tc = entry.get("timeline_out", "00:00:00:00")
    try:
        tl_in_s = parse_timecode(tl_in_tc, fps)
        tl_out_s = parse_timecode(tl_out_tc, fps)
        duration = max(0.0, tl_out_s - tl_in_s)
    except ValueError:
        tl_in_s = tl_out_s = duration = 0.0

    # in_point/out_point in source seconds (from adjusted)
    src_in = v1.get("adjusted_in", v1.get("in"))
    src_out = v1.get("adjusted_out", v1.get("out"))

    # mogrt_overlaps from text field
    text = entry.get("text") or {}
    mogrt_overlaps = []
    if isinstance(text, dict) and text.get("text"):
        ttype = text.get("type", "text")
        ttext = text.get("text") or text.get("line2") or text.get("line1") or ""
        if ttext:
            mogrt_overlaps.append(
                f"{ttype}: {ttext} (0.0s-{duration:.1f}s)"
            )

    return {
        "beat_index": beat_index,
        "beat_type": entry.get("beat_type") or "unlabeled",
        "recipe_section": entry.get("step", ""),
        "filename": fn,
        "camera": {
            "choice": camera,
            "reasoning": f"derived from camera_mapping.json[{prefix}]",
        },
        "duration": {
            "seconds": round(duration, 3),
            "reasoning": "computed from timeline_in/timeline_out timecodes",
        },
        "in_point": {
            "seconds": float(src_in) if src_in is not None else None,
            "reasoning": "from v1.adjusted_in",
        },
        "out_point": {
            "seconds": float(src_out) if src_out is not None else None,
        },
        "beat_description": entry.get("step", ""),
        "effects": "",
        "effects_reasoning": "",
        "mogrt_overlaps": mogrt_overlaps,
        "verdict": "pipeline_proposed",
        "_source": "pipeline_manifest",
        "_pair_id": entry.get("pair_id"),
        "_v2_file": (entry.get("v2") or {}).get("file"),
    }


def manifest_to_annotation(manifest: dict, recipe_slug: str) -> dict:
    """Convert a full pipeline manifest into an annotation JSON shape."""
    fps = float(manifest.get("sequence_settings", {}).get("fps", 23.976))
    camera_map = load_camera_mapping(recipe_slug)
    if not camera_map:
        logger.warning("no camera mapping found for %s — all beats will be 'unknown'",
                       recipe_slug)
    beats = [
        manifest_entry_to_beat(entry, fps, camera_map, i)
        for i, entry in enumerate(manifest.get("timeline", []))
    ]
    return {
        "recipe": recipe_slug,
        "global_notes": "Converted from pipeline manifest by score_pipeline_output.py",
        "_source_manifest": str(PIPELINE_RUNS_ROOT / recipe_slug / f"{recipe_slug}_manifest.json"),
        "beats": beats,
    }


# ---------------------------------------------------------------------------
# Per-rule comparison report
# ---------------------------------------------------------------------------

def render_report(recipe: str, dan_score: dict, ai_score: dict,
                  ai_beat_count: int, dan_beat_count: int) -> str:
    out: list[str] = []
    today = date.today().isoformat()
    out.append("---")
    out.append("project: ASI-Evolve")
    out.append("type: phase-4-fitness-gradient")
    out.append(f"date: {today}")
    out.append(f"recipe: {recipe}")
    out.append("status: v1")
    out.append("tags: [asi-evolve, phase-4, fitness-gradient, scorer, roughcut-ai]")
    out.append("related:")
    out.append('  - "[[Editing Agent - Roadmap]]"')
    out.append('  - "[[Editing Agent — Style Signature v1]]"')
    out.append('  - "[[Phase 3 — Discrimination Test chicken_thighs]]"')
    out.append("source: experiments/recipe_pipeline/score_pipeline_output.py")
    out.append("---")
    out.append("")
    out.append(f"# Phase 4 — Fitness Gradient ({recipe})")
    out.append("")
    out.append(
        f"First measured comparison between the AI pipeline's proposed edit "
        f"and Dan's approved edit on the same recipe, using the same scorer "
        f"(`score_rules.py`, post-2026-05-03 fixes). The delta is the fitness "
        f"gradient — the signal an evolution loop would optimize against."
    )
    out.append("")
    out.append(
        "Phase 4 deliverable in [[Editing Agent - Roadmap]]. The scorer was "
        "validated by Phase 3 discrimination tests on chicken_thighs and "
        "basil_pesto: all 4 deliberate-violation variants now score below "
        "baseline. Whether the scorer can ALSO distinguish the AI's output "
        "from Dan's is what this note measures."
    )
    out.append("")

    # Composite + beat count summary
    delta = dan_score["composite"] - ai_score["composite"]
    out.append("## Headline")
    out.append("")
    out.append("| | Composite | Beat count |")
    out.append("|---|---|---|")
    out.append(f"| **Dan (approved)** | **{dan_score['composite']}** | {dan_beat_count} |")
    out.append(f"| **AI (pipeline)** | **{ai_score['composite']}** | {ai_beat_count} |")
    out.append(f"| **Δ (Dan − AI)** | **{delta:+.2f}** | {dan_beat_count - ai_beat_count:+d} |")
    out.append("")
    interp = (
        "**Dan scores higher** — the scorer can distinguish the editorial "
        "quality gap. Magnitude is the gradient evolution would optimize."
        if delta > 0.5 else
        ("**Effectively tied** — the scorer cannot distinguish the AI from "
         "Dan on this recipe. Either the AI's output is editorially "
         "equivalent (unlikely) OR the scorer is too coarse to see the "
         "difference (likely; this is a scorer-extension prompt for Phase 5)."
         if abs(delta) <= 0.5 else
         "**AI scores higher than Dan** — the scorer rewards something the AI "
         "does that Dan doesn't. Investigate which rules are pulling AI's "
         "score up and tighten them.")
    )
    out.append(interp)
    out.append("")

    # Per-rule comparison
    out.append("## Per-rule comparison")
    out.append("")
    out.append("| Rule | Dan | AI | Δ (Dan − AI) |")
    out.append("|---|---|---|---|")
    rules = list(dan_score["rules"].keys())
    for r in rules:
        ds = dan_score["rules"][r]["score"]
        as_ = ai_score["rules"][r]["score"]
        d = ds - as_
        marker = " ⭐" if d > 0.05 else (" ⚠️" if d < -0.05 else "")
        out.append(f"| `{r}` | {ds:.3f} | {as_:.3f} | {d:+.3f}{marker} |")
    out.append("")
    out.append("⭐ = rule contributes to Dan's lead. ⚠️ = AI scores higher on this rule (worth investigating).")
    out.append("")

    # Diagnostic detail per rule that differs
    out.append("## Where the gap comes from")
    out.append("")
    for r in rules:
        ds = dan_score["rules"][r]["score"]
        as_ = ai_score["rules"][r]["score"]
        if abs(ds - as_) <= 0.05:
            continue
        d = ds - as_
        out.append(f"### `{r}` — Δ {d:+.3f}")
        out.append("")
        d_detail = dan_score["rules"][r].get("detail", "")
        a_detail = ai_score["rules"][r].get("detail", "")
        out.append(f"- Dan: {d_detail}")
        out.append(f"- AI: {a_detail}")
        out.append("")

    # Caveats
    out.append("## Caveats")
    out.append("")
    out.append(
        "- **AI's manifest doesn't propose speed ramps.** R4 (flourish detection) "
        "will score the AI at 0.7 neutral by construction. This isn't the AI's "
        "output being measured fairly on flourishes — it's the AI not emitting "
        "them at all (a later pipeline stage handles ramps). Treat R4 delta as "
        "a known structural gap, not an editorial-quality signal."
    )
    out.append(
        "- **AI's mogrt_overlaps are synthesized from the manifest's `text` field**, "
        "which only carries content (not style/font/duration). MOGRT readability "
        "is approximated from beat duration alone. R3 deltas should be read with "
        "this in mind."
    )
    out.append(
        "- **Camera labels on the AI side are derived from the per-recipe cache** "
        "(camera_mapping.json), not from the AI's actual output. The AI doesn't "
        "explicitly choose front/overhead — it picks v1/v2 by audio sync, and the "
        "filename prefix is what we map. Same accuracy as Dan's annotation since "
        "both routes go through the cache."
    )
    out.append("")

    out.append("## Followups")
    out.append("")
    out.append("- Score the same comparison on the other 4 ASI corpus recipes "
               "(chicken_thighs, banana_muffins, creamy_potato_soup, "
               "korean_fried_chicken) to see whether the gap is recipe-specific "
               "or structural.")
    out.append("- For each rule where AI > Dan: investigate which property of the "
               "AI's output is gaming the rule. Tighten rule or add a counter-rule.")
    out.append("- For each rule where Dan ≫ AI: that's a real editorial pattern "
               "the AI doesn't produce yet. These become Phase 5 rule-extension "
               "candidates and Phase 6 generation targets.")
    out.append("- Save the converted AI annotation at "
               f"`experiments/recipe_pipeline/pipeline_scores/{recipe}_ai.json` "
               "for inspection / further analysis.")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("recipe", help="Recipe slug (e.g. basil_pesto)")
    p.add_argument("--annotations-dir", type=Path, default=ANNOTATIONS_DIR)
    p.add_argument("--pipeline-runs-root", type=Path, default=PIPELINE_RUNS_ROOT)
    p.add_argument("--manifest", type=Path, default=None,
                   help="Override the pipeline manifest path. Useful when the "
                        "manifest folder name differs from the annotation slug "
                        "(e.g., 'easy_banana_muffins' folder vs 'banana_muffins' "
                        "annotation slug).")
    p.add_argument("--scores-dir", type=Path, default=PIPELINE_SCORES_DIR)
    p.add_argument("--vault-note-dir", type=Path,
                   default=Path.home() / "DevApps/Brain/Projects/ASI-Evolve")
    p.add_argument("--no-vault-note", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    # Load Dan's annotation + score
    dan_path = args.annotations_dir / f"{args.recipe}.json"
    if not dan_path.is_file():
        logger.error("Dan annotation not found: %s", dan_path)
        return 2
    dan_ann = json.loads(dan_path.read_text())
    dan_score = score_annotation(dan_ann)
    logger.info("Dan composite: %s (%d beats)",
                dan_score["composite"], dan_score["beat_count"])

    # Load AI manifest + convert + score
    manifest_path = args.manifest or (
        args.pipeline_runs_root / args.recipe / f"{args.recipe}_manifest.json"
    )
    if not manifest_path.is_file():
        logger.error("pipeline manifest not found: %s", manifest_path)
        return 2
    manifest = json.loads(manifest_path.read_text())
    ai_ann = manifest_to_annotation(manifest, args.recipe)
    ai_score = score_annotation(ai_ann)
    logger.info("AI composite:  %s (%d beats)",
                ai_score["composite"], ai_score["beat_count"])

    # Persist converted AI annotation
    args.scores_dir.mkdir(parents=True, exist_ok=True)
    ai_path = args.scores_dir / f"{args.recipe}_ai.json"
    ai_path.write_text(json.dumps(ai_ann, indent=2))
    logger.info("wrote AI annotation: %s", ai_path)

    # Headline delta
    delta = dan_score["composite"] - ai_score["composite"]
    logger.info("Δ (Dan − AI): %+.2f composite", delta)

    if not args.no_vault_note:
        md = render_report(args.recipe, dan_score, ai_score,
                            ai_beat_count=ai_score["beat_count"],
                            dan_beat_count=dan_score["beat_count"])
        note_path = args.vault_note_dir / f"Phase 4 — Fitness Gradient {args.recipe}.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(md)
        logger.info("wrote vault note: %s (%d bytes)", note_path, note_path.stat().st_size)

    return 0


if __name__ == "__main__":
    sys.exit(main())
