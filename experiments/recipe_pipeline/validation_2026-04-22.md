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

## Scores

| Recipe | Split | Composite | R1 Dump Hold | R2 Camera Runs | R3 MOGRT/Text Readability | R4 Flourish | R5 Duration Comp |
|---|---|---|---|---|---|---|---|
| basil_pesto | tune | **90.91** | 1.00 | 0.73 | 1.00 | 0.75 | 1.00 |
| chicken_thighs | tune | **80.67** | 0.67 | 0.78 | 0.95 | 0.75 | 1.00 |
| cranberry_jalapeno_dip | tune | **73.12** | 1.00 | 0.49 | 0.91 | 0.00 | 1.00 |
| pin_wheel | tune | **86.94** | 1.00 | 0.63 | 0.87 | 0.80 | 1.00 |
| puppy_chow | tune | **92.00** | 1.00 | 0.60 | 1.00 | 1.00 | 1.00 |
| sweet_potato_pie | tune | **79.17** | 1.00 | 0.60 | 0.79 | 0.43 | 1.00 |
| flaky_pie_crust | **holdout** | **89.12** | 1.00 | 0.61 | 1.00 | 0.80 | 1.00 |
| peppermint_bark | **holdout** | **84.95** | 1.00 | 0.79 | 0.92 | 0.50 | 0.89 |

## Aggregate comparison

| Metric | Tune (n=6) | Holdout (n=2) | Δ |
|---|---|---|---|
| Composite mean | 83.80 | **87.04** | **+3.24** |
| R1 Dump Hold | 0.95 | 1.00 | +0.05 |
| R2 Camera Runs | 0.64 | 0.70 | +0.06 |
| R3 MOGRT/Text Readability | 0.92 | 0.96 | +0.04 |
| R4 Flourish Detection | 0.62 | 0.65 | +0.03 |
| R5 Duration Compensation | 1.00 | 0.95 | –0.05 |

## Verdict

**PASS — scorer generalizes.** Holdout mean is **+3.24 points above** tune mean, well within the ±10-point acceptable threshold. No single-rule collapse on holdouts. Rule 3 (MOGRT text readability) — the rule we were most worried about — handled the new `text_overlays` format cleanly (0.92–1.00 on both holdouts).

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
