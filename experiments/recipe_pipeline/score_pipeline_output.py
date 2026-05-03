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
    out.append("type: phase-4-polish-gradient")
    out.append(f"date: {today}")
    out.append(f"recipe: {recipe}")
    out.append("status: v2")
    out.append("tags: [asi-evolve, phase-4, polish-gradient, scorer, roughcut-ai]")
    out.append("related:")
    out.append('  - "[[Editing Agent - Roadmap]]"')
    out.append('  - "[[Editing Agent — Style Signature v1]]"')
    out.append('  - "[[Phase 4 — Fitness Gradient Rollup]]"')
    out.append("source: experiments/recipe_pipeline/score_pipeline_output.py")
    out.append("---")
    out.append("")
    out.append(f"# Phase 4 — Polish Gradient ({recipe})")
    out.append("")
    out.append(
        "**Reframe (Dan, 2026-05-03):** the AI's manifest is an *intentional polish baseline*, "
        "not a bid to replace Dan's edit. The current pipeline outputs a deliberately basic "
        "first-pass cut so the editor can finish it. The goal of comparing AI to Dan is to "
        "find which polish steps the editor still has to do — and incrementally push those "
        "into the pipeline so future versions need less polish."
    )
    out.append("")
    out.append(
        f"This note compares AI ({recipe}) to Dan's approved edit using `score_rules.py` "
        f"(post-2026-05-03 fixes validated by Phase 3 discrimination test). The composite "
        f"delta is informational; the per-rule breakdown is what's actionable. Some rules "
        f"identify *real polish-reduction targets* (pacing, flourishes, selection); others "
        f"reflect *intentional product choices* (beauty optionality, basic baseline) and "
        f"should NOT be treated as flaws to fix."
    )
    out.append("")

    # Composite + beat count summary
    delta = dan_score["composite"] - ai_score["composite"]
    out.append("## Headline (informational)")
    out.append("")
    out.append("| | Composite | Beat count |")
    out.append("|---|---|---|")
    out.append(f"| Dan (approved) | {dan_score['composite']} | {dan_beat_count} |")
    out.append(f"| AI (pipeline baseline) | {ai_score['composite']} | {ai_beat_count} |")
    out.append(f"| Δ (Dan − AI) | {delta:+.2f} | {dan_beat_count - ai_beat_count:+d} |")
    out.append("")
    out.append(
        "Composite delta is a directional summary, not a verdict. AI is intentionally "
        "below Dan; the question is *which gap components are polish-reduction targets* "
        "and which reflect product design."
    )
    out.append("")

    # Categorize rules into three buckets:
    #   real_targets   — rules where AI loses for editor-polish reasons
    #   intentional    — rules where AI loses by design
    #   inconclusive   — small delta or known noise
    rules = list(dan_score["rules"].keys())

    # Polish-reduction targets per Dan's 2026-05-03 priorities (faster cuts,
    # flourishes, better selection, footage-aware moment vs close-up).
    real_target_rules = {
        "beat_density": "pacing — faster cuts vs hardcoded ~4.25s median",
        "flourish_detection": "flourishes — pipeline doesn't emit ramps yet",
        "camera_run_quality": "selection — camera variety / hold quality",
    }
    # Caveats / intentional choices acknowledged in product framing.
    caveat_rules = {
        "mogrt_text_readability": "AI mogrts synthesized from manifest text — approximate",
        "structural_coherence": "label-vocabulary noise (Dan's `?` beats vs AI's fine-grained types) — finding overstated; both follow recipe order",
        "dump_camera_hold": "AI has fewer ingredient-dump runs to penalize — gameable",
        "duration_compensation": "fires only on dump-sequence post-switch beats; sparse signal",
    }

    out.append("## Polish-reduction targets (push these closer to Dan)")
    out.append("")
    out.append("| Rule | Dan | AI | Δ | Polish step it represents |")
    out.append("|---|---|---|---|---|")
    for r, label in real_target_rules.items():
        if r not in dan_score["rules"]:
            continue
        ds = dan_score["rules"][r]["score"]
        as_ = ai_score["rules"][r]["score"]
        d = ds - as_
        out.append(f"| `{r}` | {ds:.3f} | {as_:.3f} | {d:+.3f} | {label} |")
    out.append("")

    out.append("## Caveats / intentional baseline (do NOT optimize against)")
    out.append("")
    out.append("| Rule | Dan | AI | Δ | Why this delta is not a polish target |")
    out.append("|---|---|---|---|---|")
    for r, label in caveat_rules.items():
        if r not in dan_score["rules"]:
            continue
        ds = dan_score["rules"][r]["score"]
        as_ = ai_score["rules"][r]["score"]
        d = ds - as_
        out.append(f"| `{r}` | {ds:.3f} | {as_:.3f} | {d:+.3f} | {label} |")
    out.append("")

    # Diagnostic detail for the polish-reduction targets only
    out.append("## Where the polish-reduction targets break down")
    out.append("")
    for r in real_target_rules:
        if r not in dan_score["rules"]:
            continue
        ds = dan_score["rules"][r]["score"]
        as_ = ai_score["rules"][r]["score"]
        if abs(ds - as_) <= 0.05:
            continue
        d = ds - as_
        out.append(f"### `{r}` — Δ {d:+.3f}")
        out.append("")
        d_detail = dan_score["rules"][r].get("detail", "")
        a_detail = ai_score["rules"][r].get("detail", "")
        out.append(f"- Dan: {d_detail or '(no detail)'}")
        out.append(f"- AI: {a_detail or '(no detail)'}")
        out.append("")

    out.append("## Methodology caveats")
    out.append("")
    out.append(
        "- **AI manifest is intentionally a basic baseline.** Editor adds polish: "
        "fine-grained cuts, speed ramps, MOGRT styling, etc. The composite delta "
        "above measures total polish required, not editorial deficit."
    )
    out.append(
        "- **AI's mogrt_overlaps are synthesized from the manifest's `text` field** "
        "for scoring purposes; the AI doesn't separately emit MOGRT styling/duration. "
        "R3 numbers are approximate."
    )
    out.append(
        "- **Camera labels on the AI side are derived from the per-recipe cache** "
        "(`camera_mapping.json`), same lookup as Dan's annotation, so the camera "
        "comparison is apples-to-apples."
    )
    out.append(
        "- **`structural_coherence` is label-vocabulary noise here.** Dan's annotation "
        "has many unlabeled beats (`?`) which form long runs and inflate his clustering "
        "score; AI uses fine-grained beat_types (`technique`/`transformation_from`/etc) "
        "which fragment the same content across labels. Both follow recipe order; the "
        "rule isn't comparing the right thing."
    )
    out.append("")

    out.append(f"See [[Phase 4 — Fitness Gradient Rollup]] for the corpus-wide pattern "
               f"across all 5 ASI recipes and the prioritized polish-reduction roadmap.")
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
