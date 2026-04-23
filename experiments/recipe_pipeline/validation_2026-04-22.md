# Scorer Generalization Validation — 2026-04-22

## Setup

- **8 recipes annotated** via Opus + /watch-video frame grounding (2 baselines + 6 new).
- **Scorer rules were developed against basil_pesto + chicken_thighs** (MOGRT-based ingredient overlays). Those two are effectively the scorer's training set.
- **6 new recipes use Premiere-native Essential Graphics** (`<effectid>GraphicAndType</effectid>`) for ingredient overlays, not imported `.aegraphic` MOGRTs — a structurally different overlay pattern.
- **Pipeline changes this session:** `xml_to_manifest.py` detects Essential Graphics into a new `text_overlays` category; `analyze_editorial_judgment.py` gained a `--no-manifest` flag and merges `text_overlays` into MOGRT zones for beat grouping.

## Holdout split

- `random.seed(8)` → `random.sample(6 new recipes, 2)` produces:
  - **Holdout (2):** `flaky_pie_crust`, `peppermint_bark`
  - **Tune (6):** `basil_pesto`, `chicken_thighs`, `cranberry_jalapeno_dip`, `pin_wheel`, `puppy_chow`, `sweet_potato_pie`

The holdouts are drawn from the **new text-overlay recipes**, never from basil_pesto/chicken_thighs, so this tests generalization to the new structural pattern.

## Scores (final — Rule 4 tag-based with neutral floor)

| Recipe | Split | Composite | R1 Dump Hold | R2 Camera Runs | R3 MOGRT/Text | **R4 Flourish** | R5 Duration |
|---|---|---|---|---|---|---|---|
| basil_pesto | tune | **90.16** | 1.00 | 0.73 | 1.00 | 0.70 | 1.00 |
| chicken_thighs | tune | **84.42** | 0.67 | 0.78 | 0.95 | **1.00** | 1.00 |
| cranberry_jalapeno_dip | tune | **83.62** | 1.00 | 0.49 | 0.91 | 0.70 | 1.00 |
| pin_wheel | tune | **89.94** | 1.00 | 0.63 | 0.87 | **1.00** | 1.00 |
| puppy_chow | tune | **87.50** | 1.00 | 0.60 | 1.00 | 0.70 | 1.00 |
| sweet_potato_pie | tune | **83.24** | 1.00 | 0.60 | 0.79 | 0.70 | 1.00 |
| flaky_pie_crust | **holdout** | **92.12** | 1.00 | 0.61 | 1.00 | **1.00** | 1.00 |
| peppermint_bark | **holdout** | **87.96** | 1.00 | 0.79 | 0.92 | 0.70 | 0.89 |

_Bolded R4 = 1.00: recipe meets the "at least one organic flourish" aspiration. Others = 0.70 neutral._

## Rule 4 — neutral floor design (Dan's call, 2026-04-22)

Rule 4 measures whether organic flourishes are present. Dan's call: **flourishes are great to have but sometimes legitimately missed** (footage may not contain a slow-reveal moment, or the editor may use ramps only for timing). Future evolved edits **should always have some kind of flourish**.

Implementation:
- `≥ 1 organic flourish` (regardless of total ramp count) → **1.00** (aspiration met)
- `0 organic flourishes` (no ramps at all, OR all ramps functional) → **0.70** (neutral — not punitive, but a 0.3 gradient that evolution can seek by finding flourish opportunities)

This fixes the prior behavior where recipes with 0 flourishes scored 0.00 (harsh) and recipes with 0 ramps scored 1.00 (accidentally perfect via the "nothing to assess" default).

**Who meets the aspiration (3 of 8):**
- chicken_thighs beat 32: caramelized grill marks
- flaky_pie_crust beat 0: baked pie crust hero reveal
- pin_wheel beat 6: macro powdered sugar pile

**Who doesn't (5 of 8):**
- basil_pesto (4 ramps, all functional — the pesto pour flourishes got classified as functional in backfill; worth a human check)
- cranberry_jalapeno_dip (1 functional ramp — mixer timing nudge)
- peppermint_bark (all functional — including the white chocolate ribbon pour)
- puppy_chow (0 ramps entirely — no ramps to judge)
- sweet_potato_pie (7 ramps, all functional timing tools)

## Aggregate comparison

| Metric | Tune (n=6) | Holdout (n=2) | Δ |
|---|---|---|---|
| Composite mean | **86.48** | **90.04** | **+3.56** |
| R1 Dump Hold | 0.95 | 1.00 | +0.05 |
| R2 Camera Runs | 0.64 | 0.70 | +0.06 |
| R3 MOGRT/Text Readability | 0.92 | 0.96 | +0.04 |
| R4 Flourish Detection | 0.80 | 0.85 | +0.05 |
| R5 Duration Compensation | 1.00 | 0.95 | –0.05 |

## Verdict

**PASS.** Holdout mean is **+3.56 points above** tune mean — well within the ±10-point acceptable threshold. No single-rule collapse. Rule 3 remains stable (0.92–1.00 across holdouts; the text_overlays adaptation works). Rule 4 now returns honest, actionable signal: recipes that meet the flourish aspiration score 1.00, recipes that don't score 0.70 (neutral, not punished), and the 0.3 gradient is exactly the fitness signal prompt evolution can optimize against.

## Scoring history

| Stage | Tune mean | Hold mean | Δ | Notes |
|---|---|---|---|---|
| Original (field-path bug) | 83.80 | 87.03 | +3.23 | Rule 4 keyword-matching descriptions only |
| Fix A (field path) | 86.00 | 88.53 | +2.54 | Rule 4 could read reasoning but negation-fragile |
| Fix B (tag-based, strict 0/N) | 78.11 | 78.79 | +0.68 | Honest but punitive — zero flourishes = 0.00 |
| **Fix C (tag-based, neutral floor)** | **86.48** | **90.04** | **+3.56** | Honest AND aligned with editorial intent |

## Rule 4 fix history (sessions 23 → 23b)

Two bugs chained, found the same session:

1. **Field-path bug (`score_rules.py:270-272`).** Scorer read `beat["reasoning"]["effects_reasoning"]` — no such key. Field actually lives at top-level `beat["effects_reasoning"]`. Rule 4 was keyword-matching on `beat_description` alone, ignoring Opus's actual reasoning. **Fixed** by direct lookup.

2. **Keyword-match negation fragility (exposed by fix 1).** After fix 1, the scorer saw Opus's reasoning — but `bag-of-words keyword matching` can't read negation. A phrase like *"this is functional, not an organic flourish — a 1% timing nudge, not a transformation reveal like butter melting"* matches on `flourish`, `organic`, `transformation`, `melt` and gets classified positively. Scores inflated across most recipes (tune 83.80 → 86.00). **Fixed** by:
   - Updated beat prompt: Opus must now emit `[flourish: organic]` or `[flourish: functional]` token at end of `effects_reasoning` when a speed ramp is present.
   - Updated `score_rules.py`: reads the verdict token directly; keyword matching kept as fallback for legacy annotations without the tag.
   - Backfilled existing 8 annotations via `backfill_flourish_tags.py` — short classification Opus calls per ramp beat (28 tags added).

After both fixes: **only 3 organic flourishes total across 8 recipes** — chicken_thighs (caramelized grill marks), flaky_pie_crust (baked crust hero reveal), pin_wheel (macro powdered sugar pile). Everything else is attended action or 1-3% timing nudges. Scores reflect this.

## Open question for Dan (Rule 4 design)

Should a recipe with **zero real organic flourishes** score 0 on Rule 4? The current rule is `# organic / # ramps`. Recipes where every ramp is a functional timing nudge (sweet_potato_pie, cranberry_jalapeno_dip, peppermint_bark) all score 0 — not because the edit is bad, but because ramps were used for timing instead of flourish.

Possible alternative: `# organic / max(# ramps, N_ramp_opportunities)` — but measuring "opportunities" needs shot-catalog data (what transformation moments were in the footage). Deferred until we have opportunity data.

**Text overlay adaptation works.** Flaky_pie_crust (5 text_overlays, 3 MOGRTs) and peppermint_bark (5 text_overlays, 4 MOGRTs) both scored within the tune-set range. The `text_overlays` plumbing added this session preserves Rule 3 signal without per-recipe tuning.

## Non-blocking observations (flagged, not failures)

1. **Cranberry_jalapeno_dip Rule 4 = 0.00.** Flourish detection fires zero times on this recipe. Looking at the annotation, the script didn't emit speed-ramp effects strings into the `effects` field for any beat — worth checking whether the parser captured speed remaps for this XML, vs whether the recipe genuinely has no speed ramps to detect. Diagnostic, not a scorer bug.

2. **R2 Camera Run Quality systematically lower on new recipes.** Baselines score 0.73–0.78; new recipes score 0.49–0.79. The rule rewards longer camera runs and front-ending — the new recipes may legitimately have more alternation patterns (pin_wheel has 23 camera alternations on 67 clips). Not overfit in the harmful direction; just reveals that the rule's sweet spot was defined around basil/chicken's style.

3. **Sweet_potato_pie** (79.17) is the lowest-scoring new recipe. R4 = 0.43 and R3 = 0.79 both drag the composite. The XML has 12 text_overlays in 24 clips — denser overlay/beat ratio than others. Not a pipeline issue; worth a human look before the next tuning round.

## Rule 1 (Dump Hold) asymmetry

Chicken_thighs baseline still scores 0.67 on Rule 1 because of the known beat-11→12 "rapid alternation overhead→front (held only 1 beat)" flag — this is the scorer's original edge case and is preserved on re-run, as expected. All 6 new recipes score 1.00 on Rule 1, meaning the dump detection logic picks up text-overlay ingredient beats correctly.

## Artifacts

- Annotations (markdown, human-editable): `/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/Annotations/{recipe}.md` (8 files)
- Annotation JSONs (scorer input): `/Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline/annotations/{recipe}.json` (8 files)
- Parsed manifests with `text_overlays` category: `/Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline/approved_edits/{recipe}.json` (6 new)
- Pass 1 frame analyses: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pass1_{recipe}.md` (6 new)

## Reproducibility

```bash
cd /Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline
python score_rules.py --dir annotations/
```

Holdout seed: `random.seed(8)` over `sorted(['cranberry_jalapeno_dip','flaky_pie_crust','peppermint_bark','pin_wheel','puppy_chow','sweet_potato_pie'])` → `['flaky_pie_crust','peppermint_bark']`.
