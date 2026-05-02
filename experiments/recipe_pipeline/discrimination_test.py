#!/usr/bin/env python3
"""
discrimination_test.py — Phase 3 of the master plan.

Construct deliberately-bad variants of an annotation JSON and measure whether
`score_rules.py` distinguishes them from the baseline. Validates the scorer's
discrimination power: when a known violation is introduced, does the relevant
rule's score drop measurably?

Variants generated (per the user's session 2026-05-02 scoping):

  rapid_camera_alternation
      Toggle camera.choice F→O→F→O on every ingredient/technique beat.
      Tests R2 (dump camera hold) and overall camera_run_quality.

  missing_flourishes
      Strip "speed" / "ramp" keywords from `effects` field on all beats.
      Tests R4 (flourish detection).

  shuffled_beats
      Random-shuffle beat order (deterministic seed). Tests broad structural
      disorder — should disrupt run-based rules.

  padded_process_moments
      For ~50% of ingredient/technique beats, insert an extra "process pad"
      beat after with offset source-time and shorter duration. Models the
      common AI-pipeline failure of picking adjacent moments instead of the
      editorial peak. Tests over-inclusion / pacing detection.

Outputs:
  experiments/recipe_pipeline/discrimination/<recipe>_<variant>.json
  ~/DevApps/Brain/Projects/ASI-Evolve/Phase 3 — Discrimination Test <recipe>.md

Usage:
    python3 experiments/recipe_pipeline/discrimination_test.py chicken_thighs
    python3 experiments/recipe_pipeline/discrimination_test.py chicken_thighs --no-vault-note
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import random
import re
import sys
from datetime import date
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent
ANNOTATIONS_DIR = REPO_ROOT / "annotations"
VARIANTS_DIR = REPO_ROOT / "discrimination"

# Make score_rules importable from this directory.
sys.path.insert(0, str(REPO_ROOT))
from score_rules import score_annotation  # noqa: E402

logger = logging.getLogger("discrimination_test")


# ---------------------------------------------------------------------------
# Beat helpers
# ---------------------------------------------------------------------------

def is_ingredient_or_technique(beat: dict) -> bool:
    bt = (beat.get("beat_type") or "").lower()
    if bt in ("ingredient", "technique"):
        return True
    sec = (beat.get("recipe_section") or "").lower()
    return "ingredient" in sec


def get_camera_choice(beat: dict) -> str | None:
    cam = beat.get("camera")
    if isinstance(cam, dict):
        return cam.get("choice")
    return cam


# ---------------------------------------------------------------------------
# Variant builders — each takes annotation, returns mutated copy
# ---------------------------------------------------------------------------

def build_rapid_camera_alternation(annotation: dict) -> dict:
    """Toggle camera.choice F↔O on every ingredient/technique beat.
    Existing labels overwritten; non-ingredient beats untouched.
    """
    ann = copy.deepcopy(annotation)
    toggle = "front"
    n_toggled = 0
    for b in ann["beats"]:
        if not is_ingredient_or_technique(b):
            continue
        cam = b.get("camera")
        if not isinstance(cam, dict):
            cam = {"choice": None, "reasoning": ""}
            b["camera"] = cam
        cam["choice"] = toggle
        cam["reasoning"] = "[discrimination test] forced rapid alternation"
        toggle = "overhead" if toggle == "front" else "front"
        n_toggled += 1
    ann["_variant"] = "rapid_camera_alternation"
    ann["_variant_meta"] = {"n_toggled": n_toggled}
    return ann


def build_missing_flourishes(annotation: dict) -> dict:
    """Strip 'speed' / 'ramp' keyword tokens from every field where R4 looks
    for them: effects, effects_info, recipe_section, beat_description,
    effects_reasoning. Earlier version only stripped from `effects` and was
    a no-op on recipes whose ramps were documented in recipe_section text
    (chicken_thighs, basil_pesto, etc.) — fixed 2026-05-03.
    """
    ann = copy.deepcopy(annotation)
    n_stripped = 0
    pat = re.compile(r"\b(speed[\w_-]*|ramp[\w_-]*)\b[^,;|.()]*", re.IGNORECASE)
    fields_to_clean = ("effects", "effects_info", "recipe_section",
                       "beat_description", "effects_reasoning")
    for b in ann["beats"]:
        touched = False
        for field in fields_to_clean:
            v = b.get(field, "")
            if not isinstance(v, str) or not pat.search(v):
                continue
            new_v = pat.sub("", v)
            new_v = re.sub(r"[,;|()]\s*[,;|()]", ",", new_v)
            new_v = new_v.strip(", ;|()")
            b[field] = new_v
            touched = True
        if touched:
            n_stripped += 1
    ann["_variant"] = "missing_flourishes"
    ann["_variant_meta"] = {"n_stripped": n_stripped}
    return ann


def build_shuffled_beats(annotation: dict, seed: int = 42) -> dict:
    """Random-shuffle beat order with deterministic seed."""
    ann = copy.deepcopy(annotation)
    rng = random.Random(seed)
    rng.shuffle(ann["beats"])
    for i, b in enumerate(ann["beats"]):
        b["beat_index"] = i
    ann["_variant"] = "shuffled_beats"
    ann["_variant_meta"] = {"seed": seed}
    return ann


def build_padded_process_moments(annotation: dict, seed: int = 42,
                                  padding_rate: float = 0.5,
                                  offset_seconds: float = 2.0,
                                  duration_factor: float = 0.6) -> dict:
    """Insert 'process pad' beats interleaved with original ingredient/technique
    beats. Each pad copies neighbor metadata, offsets source-time by +offset_seconds,
    shrinks duration to duration_factor× original — modeling the AI failure of
    picking adjacent moments instead of editorial peak.
    """
    ann = copy.deepcopy(annotation)
    rng = random.Random(seed)
    new_beats: list[dict] = []
    n_inserted = 0
    for b in ann["beats"]:
        new_beats.append(b)
        if not is_ingredient_or_technique(b):
            continue
        if rng.random() >= padding_rate:
            continue

        in_point = b.get("in_point", {})
        out_point = b.get("out_point", {})
        duration = b.get("duration", {})
        inp = in_point.get("seconds") if isinstance(in_point, dict) else None
        outp = out_point.get("seconds") if isinstance(out_point, dict) else None
        dur = duration.get("seconds") if isinstance(duration, dict) else None
        if inp is None or outp is None:
            continue

        extra = copy.deepcopy(b)
        new_in = inp + offset_seconds
        new_dur = max(0.25, (dur or (outp - inp)) * duration_factor)
        new_out = new_in + new_dur
        extra["in_point"] = {"seconds": round(new_in, 3),
                             "reasoning": "[discrimination test] process moment AFTER editorial pick"}
        extra["out_point"] = {"seconds": round(new_out, 3)}
        extra["duration"] = {"seconds": round(new_dur, 3),
                             "reasoning": "[discrimination test] process pad shorter than editorial"}
        extra["recipe_section"] = (extra.get("recipe_section") or "") + " (process pad)"
        # Preserve effects but clear flourish markers (process pads aren't flourishes).
        extra["effects"] = re.sub(r"\bspeed[\w_]*\b[^,;|]*", "",
                                  extra.get("effects", ""), flags=re.IGNORECASE).strip(", ;|")
        new_beats.append(extra)
        n_inserted += 1

    ann["beats"] = new_beats
    for i, b in enumerate(ann["beats"]):
        b["beat_index"] = i
    ann["_variant"] = "padded_process_moments"
    ann["_variant_meta"] = {
        "n_inserted": n_inserted,
        "seed": seed,
        "padding_rate": padding_rate,
        "offset_seconds": offset_seconds,
        "duration_factor": duration_factor,
    }
    return ann


VARIANTS: dict[str, Callable[[dict], dict]] = {
    "rapid_camera_alternation": build_rapid_camera_alternation,
    "missing_flourishes": build_missing_flourishes,
    "shuffled_beats": build_shuffled_beats,
    "padded_process_moments": build_padded_process_moments,
}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def render_report(recipe: str, baseline: dict, variants: dict[str, dict],
                  variant_meta: dict[str, dict]) -> str:
    out: list[str] = []
    today = date.today().isoformat()
    out.append("---")
    out.append("project: ASI-Evolve")
    out.append("type: phase-3-discrimination-test")
    out.append(f"date: {today}")
    out.append(f"recipe: {recipe}")
    out.append("status: v1")
    out.append("tags: [asi-evolve, phase-3, discrimination, scorer]")
    out.append("related:")
    out.append('  - "[[Editing Agent - Roadmap]]"')
    out.append('  - "[[Editorial Rules - Dan\'s Camera Logic]]"')
    out.append('  - "[[Editing Agent — Style Signature v1]]"')
    out.append("source: experiments/recipe_pipeline/discrimination_test.py")
    out.append("---")
    out.append("")
    out.append(f"# Phase 3 — Discrimination Test ({recipe})")
    out.append("")
    out.append(
        f"Constructs deliberately-bad variants of `annotations/{recipe}.json` "
        f"and measures whether `score_rules.py` distinguishes them from the "
        f"baseline. Validates the scorer's discrimination power: when a known "
        f"violation is introduced, does the relevant rule's score drop measurably?"
    )
    out.append("")
    out.append(
        "This is the Phase 3 deliverable in [[Editing Agent - Roadmap]] — the "
        "first measured demonstration that the scorer detects badness, not just "
        "rewards Dan-likeness. Feeds Phase 5 (rule extension — only rules that "
        "discriminate are worth keeping) and the medium-horizon M2 critic-fine-tune."
    )
    out.append("")

    # Composite table
    out.append("## Baseline + variants — composite scores")
    out.append("")
    out.append("| Variant | Beats | Composite | Δ baseline |")
    out.append("|---|---|---|---|")
    out.append(f"| **baseline** | {baseline['beat_count']} | **{baseline['composite']}** | — |")
    for name, s in variants.items():
        delta = s["composite"] - baseline["composite"]
        out.append(f"| {name} | {s['beat_count']} | {s['composite']} | {delta:+.2f} |")
    out.append("")

    # Per-rule table
    out.append("## Per-rule scores by variant")
    out.append("")
    rules = list(baseline["rules"].keys())
    out.append("| Rule | baseline | " + " | ".join(variants.keys()) + " |")
    out.append("|---" + "|---" * (len(variants) + 1) + "|")
    for r in rules:
        bs = baseline["rules"][r]["score"]
        cells = [f"{bs:.3f}"]
        for s in variants.values():
            vs = s["rules"][r]["score"]
            d = vs - bs
            cells.append(f"{vs:.3f} ({d:+.3f})")
        out.append(f"| `{r}` | " + " | ".join(cells) + " |")
    out.append("")

    # Discrimination matrix
    out.append("## Discrimination matrix")
    out.append("")
    out.append("Which rules detected each violation (score drop > 0.05)? Which failed to fire?")
    out.append("")
    out.append("| Variant | Detected by | Did NOT detect |")
    out.append("|---|---|---|")
    for name, s in variants.items():
        detected, missed = [], []
        for r in rules:
            bs = baseline["rules"][r]["score"]
            vs = s["rules"][r]["score"]
            if (bs - vs) > 0.05:
                detected.append(f"`{r}` (-{bs - vs:.2f})")
            else:
                missed.append(f"`{r}`")
        out.append(f"| {name} | {', '.join(detected) or '— *(no rule detected)*'} | {', '.join(missed) or '—'} |")
    out.append("")

    # Variant constructions
    out.append("## Variant constructions")
    out.append("")
    out.append(f"All variant JSONs at `experiments/recipe_pipeline/discrimination/{recipe}_<variant>.json`. "
               f"Reproduce via `python3 experiments/recipe_pipeline/discrimination_test.py {recipe}`.")
    out.append("")
    out.append("| Variant | Construction | Targets |")
    out.append("|---|---|---|")
    out.append(f"| `rapid_camera_alternation` | toggled camera F↔O on {variant_meta['rapid_camera_alternation']['n_toggled']} ingredient/technique beats | R2 (dump camera hold), camera_run_quality |")
    out.append(f"| `missing_flourishes` | stripped speed/ramp keywords from {variant_meta['missing_flourishes']['n_stripped']} beat effects fields | R4 (flourish detection) |")
    out.append(f"| `shuffled_beats` | random-shuffled beat order (seed={variant_meta['shuffled_beats']['seed']}) | structural disorder, all run-based rules |")
    pp = variant_meta['padded_process_moments']
    out.append(f"| `padded_process_moments` | inserted {pp['n_inserted']} 'process pad' beats (offset +{pp['offset_seconds']}s, duration ×{pp['duration_factor']}) | over-inclusion, AI-pipeline failure mode |")
    out.append("")

    # Interpretation
    out.append("## Interpretation")
    out.append("")
    out.append("**Composite score is a directional signal, not a verdict.** Per Editorial Rule 4's binary-with-neutral-floor design, missing flourishes drops only to 0.7 (neutral, not punitive). A variant that touches one rule should produce a small composite delta; a variant that touches multiple rules should produce a larger delta. Use the per-rule table above to attribute the signal.")
    out.append("")
    out.append("**Rules that fail to discriminate are red flags.** If a known violation produces no score drop on the rule designed to catch it, either the rule's logic is wrong or the violation was constructed in a way that bypasses the rule's heuristic. Either way, that rule's signal-to-noise is poor and it shouldn't drive evolution.")
    out.append("")
    out.append("**Padded-process is the most realistic failure mode.** It models what the actual AI pipeline does wrong (picks moments adjacent to the editorial peak rather than the peak itself). If the scorer doesn't discriminate this variant, it can't be the fitness function for production work — that's a Phase 5 rule-extension prompt.")
    out.append("")

    # Followups
    out.append("## Followups")
    out.append("")
    out.append("- If a rule failed to detect its target violation: investigate whether the rule's heuristic is too lenient OR the variant construction inadvertently bypasses it. Tighten one or the other.")
    out.append("- For `padded_process_moments` specifically: if existing rules don't discriminate, design a **`process_padding`** rule for Phase 5. Likely shape: median beat duration / inter-beat-interval anomaly relative to corpus median (now available in [[Editing Agent — Style Signature v1]]).")
    out.append("- Run this test on a second recipe (e.g. `pin_wheel`) to confirm discrimination generalizes, not just chicken_thighs-specific.")
    out.append("- V-JEPA2 supplemental check (per master roadmap): do the bad variants land farther from Dan's embedding cluster than the baseline? Cheap pretrained-only experiment.")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("recipe", help="Recipe slug (e.g. chicken_thighs)")
    p.add_argument("--annotations-dir", type=Path, default=ANNOTATIONS_DIR)
    p.add_argument("--variants-dir", type=Path, default=VARIANTS_DIR)
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

    base_path = args.annotations_dir / f"{args.recipe}.json"
    if not base_path.is_file():
        logger.error("annotation not found: %s", base_path)
        return 2
    baseline_ann = json.loads(base_path.read_text())

    args.variants_dir.mkdir(parents=True, exist_ok=True)
    baseline_score = score_annotation(baseline_ann)
    logger.info("baseline composite: %s (%d beats)",
                baseline_score["composite"], baseline_score["beat_count"])

    variant_scores: dict[str, dict] = {}
    variant_meta: dict[str, dict] = {}
    for name, builder in VARIANTS.items():
        variant_ann = builder(baseline_ann)
        path = args.variants_dir / f"{args.recipe}_{name}.json"
        path.write_text(json.dumps(variant_ann, indent=2))
        score = score_annotation(variant_ann)
        variant_scores[name] = score
        variant_meta[name] = variant_ann.get("_variant_meta", {})
        delta = score["composite"] - baseline_score["composite"]
        logger.info("  %-26s composite=%6.2f  Δ=%+6.2f  beats=%d  → %s",
                    name, score["composite"], delta, score["beat_count"], path.name)

    if not args.no_vault_note:
        md = render_report(args.recipe, baseline_score, variant_scores, variant_meta)
        note_path = args.vault_note_dir / f"Phase 3 — Discrimination Test {args.recipe}.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(md)
        logger.info("wrote vault note: %s (%d bytes)", note_path, note_path.stat().st_size)

    return 0


if __name__ == "__main__":
    sys.exit(main())
