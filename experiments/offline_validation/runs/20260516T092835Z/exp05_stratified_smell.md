# RAFT × beat_type smell test (N=42)

_Generated 2026-05-16T09:28:35.637748+00:00_

**Status: DIRECTIONAL ONLY.** N=42 across 2 recipes (basil_pesto, chicken_thighs); per-beat_type samples range from 1 to 21. Not a confirmatory result.

## Method

- Joined `experiments/offline_validation/runs/20260514T193913Z/exp05_results.json:per_beat` (42 beats) with annotation `beat_type` on `(recipe, beat_index)`
- `raft_delta = min_dist_dan_raft_s − median_random_raft_s` (from existing exp05 output)
- **Negative** delta = Dan's cut-out lands *closer* to a RAFT motion-magnitude peak than random
- **Positive** delta = Dan's cut-out lands *farther* from a RAFT peak than random

## Results by beat_type

| beat_type | n | recipes | median raft_delta (s) | direction | per-recipe medians |
|---|---|---|---|---|---|
| `UNTYPED` | 21 | 2 | -0.008 | mixed | basil_pesto=-0.33 (n=11), chicken_thighs=+0.45 (n=10) |
| `ingredient` | 13 | 2 | +0.266 | mixed | basil_pesto=+0.17 (n=5), chicken_thighs=+0.97 (n=8) |
| `beauty_opener` | 3 | 2 | -0.584 | mixed | basil_pesto=-0.58 (n=1), chicken_thighs=-0.26 (n=2) |
| `beauty` | 2 | 1 | -1.211 | closer (all) | chicken_thighs=-1.21 (n=2) |
| `beauty_close` | 1 | 1 | +0.113 | farther (all) | basil_pesto=+0.11 (n=1) |
| `technique` | 1 | 1 | -2.692 | closer (all) | chicken_thighs=-2.69 (n=1) |
| `title_card` | 1 | 1 | +0.984 | farther (all) | chicken_thighs=+0.98 (n=1) |

## What this does NOT prove

- Nothing about whether RAFT *as a categorical feature extractor* would give a blanket rule. That's a different experiment (threshold RAFT magnitude into phase labels, then test).
- Nothing about the conditional pattern at the population level. With only 2 recipes and 1-3 beats in most named types, recipe-conditional variance is indistinguishable from beat_type signal.
- Nothing about whether RAFT would outperform VLM `motion_phase` as the underlying signal feeding the stratified rule.

## What it does suggest

- Whether the median raft_delta differs *in sign* across beat_types within this thin sample.
- Whether the per-recipe split inside a beat_type is wide (consistent with the recipe-conditional finding) or narrow.

## What unblocks the real experiment

1. **RAFT curves for the 16 missing recipes** (one-shot Modal job using existing `run_exp05_modal.py` + expanded `DRIVE_FOLDER_IDS`). ~30-60 min L4 time.
2. **329 untyped beats labeled** via the Beat Review UI currently being built (plan: `~/.claude/plans/asi-evolve-handoff-written-misty-clock.md`).

Once both land, re-run this script across the full 18-recipe / 618-beat corpus instead of N=42.
