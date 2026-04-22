# ASI-Evolve — Session Handoff

**Date:** 2026-04-22
**Branch:** `main`
**Last commit:** `e8e21c5` feat: scorer improvements — justified switches, duration compensation, flourish signals
**Role:** BUILDER

---

## What Was Done

- Ran v5 annotations (both recipes) — fixed frame-analysis descriptions for "added" beats
- Re-ran both recipes with **Opus** (was Sonnet) — reasoning quality dramatically better
- Encoded Dan's 4 editorial rules into annotation prompts (anchor-first, dynamic anchors, dump hold, flourishes)
- Added dump sequence context to per-beat prompts (position in run, camera history)
- Built `score_rules.py` — rule-based editorial scorer (5 rules)
- Dan reviewed chicken thighs dump sequence and gave beat-by-beat corrections (logged in Obsidian annotations)
- Iterated scorer to handle justified switches (flourish/nested), duration compensation
- Created `Editorial Rules - Dan's Camera Logic.md` in Brain vault
- **6 new recipe XMLs exported** from December (cranberry jalapeño dip, flaky pie crust, peppermint bark, pinwheel, puppy chow, sweet potato pie)

## Current State

**Working:**
- `analyze_editorial_judgment.py` — Opus annotations with editorial rules in prompt, dump sequence context
- `score_rules.py` — 5 rule checks, justified switch detection, two-pass alternation analysis
- Baseline scores: basil_pesto 90.9, chicken_thighs 80.7 (avg 85.8)
- Both recipe annotations complete with Dan's corrections on chicken thighs dump sequence

**6 new XMLs ready to process** at `Recipe XMLs/`:
| Recipe | XML Size | Notes |
|--------|----------|-------|
| Cranberry Jalapeño Dip v2 | 638KB | |
| Flaky Pie Crust v2 | 423KB | |
| Peppermint Bark v3 | 428KB | |
| Pin Wheel v2 | 678KB | |
| Puppy Chow v2 | 345KB | |
| Sweet Potato Pie v2 | 601KB | |

**IMPORTANT:** These December recipes:
- Will NOT have pipeline manifests (no `--manifest`, `--scan`, `--beats` args)
- Some may NOT have MOGRTs for ingredient text — they use a **text file** instead
- Will NOT have `/watch-video` frame analysis (would need to run)
- The annotation script needs to work without pipeline comparison (verdict = "unknown")

**Not started:**
- Processing the 6 new XMLs through `xml_to_manifest.py`
- Running `/watch-video` frame analysis on the new recipes' source footage
- Adapting the annotation script for no-manifest mode
- Holdout validation (need 6+ recipes to split train/holdout)

## Key Files Changed

| File | What Changed |
|------|-------------|
| `experiments/recipe_pipeline/analyze_editorial_judgment.py` | Editorial rules block in prompt, dump sequence context, Opus default |
| `experiments/recipe_pipeline/score_rules.py` | NEW — 5-rule editorial scorer with justified switch detection |
| `experiments/recipe_pipeline/annotations/basil_pesto.json` | Opus v6 annotations |
| `experiments/recipe_pipeline/annotations/chicken_thighs.json` | Opus v6 annotations |
| `Brain/Projects/ASI-Evolve/Editorial Rules - Dan's Camera Logic.md` | NEW — Dan's 4 rules + corrections + scorer gap list |
| `Brain/Projects/ASI-Evolve/Annotations/chicken_thighs.md` | Dan's corrections on beats 3-10 (dump sequence) |
| `Brain/Knowledge/Knowledge Map.md` | Added Editorial Craft section |

## Decisions Made

| Decision | Reasoning |
|----------|-----------|
| Opus over Sonnet for annotations | Sonnet explained every camera choice independently. Opus reasons about sequences, runs, and rules. Worth the extra time/cost. |
| Two-pass justified switch detection | Speed ramp = flourish detour, nested = held block. Strip these from camera sequence before checking alternation. |
| Duration compensation as a rule | Dan holds longer after switches to give viewer re-orientation time. Measurable in the data. |
| Flourish signals expanded | Word-bag approach is fragile (overfitting risk). Need VLM-based detection long-term. |
| Score Dan's approved edits as baseline | If the scorer doesn't give Dan's own edits high scores, the rules are wrong. Iterate until baseline is >85. |

## What's Next

1. **Process 6 new XMLs** — run `xml_to_manifest.py` on each. Will need to handle missing MOGRTs (text file instead of .aegraphic overlays).
2. **Adapt annotation script for no-manifest mode** — skip pipeline comparison, set all verdicts to "unknown", still do zone grouping + frame analysis + Opus reasoning.
3. **Run /watch-video frame analysis** on the new recipes' source footage (need to locate footage on external drive).
4. **Annotate 6 new recipes** with Opus — brings total to 8 annotated recipes.
5. **Holdout split** — use 6 for tuning, hold out 2 for validation. If scorer works on holdout, rules generalize.
6. **Replace word-bag flourish detection** with VLM-based check (frame analysis: is there unattended change between frames?).
7. **Encode rules into pipeline assembly prompts** — the actual payoff. Pipeline respects dump holds, finds flourishes, sizes MOGRT to text.

## Known Issues

- Flourish detection uses a word signal list — fragile, will overfit. Needs VLM grounding.
- `score_rules.py` dump sequence detection only looks for `beat_type == "ingredient"` — recipes without MOGRTs (text file overlays) won't trigger dump detection unless adapted.
- Chicken thighs dump hold still flags beat 11→12 (post-nest pepper→salt) — minor, may be valid.
- No `/watch-video` frame analysis exists for the 6 new recipes yet.
- 12 additional XMLs Dan can export — most without manifests. Scale opportunity.
- Annotation JSON stores `effects` key but some code paths check `effects_info` — normalize.

## Quick Start for Next Session

```bash
cd ~/DevApps/ASI-Evolve/experiments/recipe_pipeline

# Step 1: Parse the 6 new XMLs
for xml in "../../Recipe XMLs/"*.xml; do
    python xml_to_manifest.py "$xml" --output approved_edits/
done

# Step 2: Check which have MOGRTs vs text overlays
# Step 3: Locate source footage on external drive for /watch-video
# Step 4: Adapt analyze_editorial_judgment.py for no-manifest mode
# Step 5: Run Opus annotations on new recipes
# Step 6: Score all 8 recipes, establish holdout split
```
