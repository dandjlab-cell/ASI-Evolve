# RAFT signed-peak-distance × beat_type (N=42)

_Generated 2026-05-16T10:26:14.077835+00:00_

**Hypothesis under test:** *Dan cuts just before the action happens, and cuts when it ends.*

## Method

Recomputed peak distance with sign: `signed_delta = cut_out_s − nearest_peak_time_s`.

- **Negative** signed_delta → cut happened BEFORE peak (action not yet at maximum motion)
- **Positive** signed_delta → cut happened AFTER peak (action has finished)
- **Zero** → cut on the peak

Peaks detected via `scipy.signal.find_peaks(curve, prominence=np.percentile(curve, 75))` — same config as exp05_raft_subject_vs_camera.py:53.

**Status: DIRECTIONAL ONLY.** N=42 across 2 recipes; per-beat_type samples 1-21.

## Overall (all 42 beats)

- Median signed_delta: **+0.322s**
- Cut BEFORE peak: 12 of 42 (28.6%)
- Cut AFTER peak: 30 of 42 (71.4%)
- Cut ON peak: 0

## By beat_type

| beat_type | n | median signed_delta (s) | % before | % after | per-recipe medians |
|---|---|---|---|---|---|
| `UNTYPED` | 21 | +0.345 | 38.1% | 61.9% | basil_pesto=+0.35s (n=11), chicken_thighs=+0.43s (n=10) |
| `ingredient` | 13 | +0.173 | 30.8% | 69.2% | basil_pesto=+0.77s (n=5), chicken_thighs=-0.92s (n=8) |
| `beauty_opener` | 3 | +0.322 | 0.0% | 100.0% | basil_pesto=+0.30s (n=1), chicken_thighs=+1.41s (n=2) |
| `beauty` | 2 | +0.433 | 0.0% | 100.0% | chicken_thighs=+0.43s (n=2) |
| `beauty_close` | 1 | +0.884 | 0.0% | 100.0% | basil_pesto=+0.88s (n=1) |
| `technique` | 1 | +0.195 | 0.0% | 100.0% | chicken_thighs=+0.19s (n=1) |
| `title_card` | 1 | +1.471 | 0.0% | 100.0% | chicken_thighs=+1.47s (n=1) |

## Reading guide

If Dan's hypothesis holds, we'd expect:

- A **bimodal** distribution overall — many cuts well before peaks (cut-before) AND many cuts well after peaks (cut-after), with FEW cuts on the peak itself.
- For **action-heavy beat_types** (ingredient drops, technique work): cuts cluster AFTER peaks (`% after` high, median positive) — *cut when the action ends*.
- For **anticipatory beat_types** (beauty_opener establishing a shot before the action arrives): cuts cluster BEFORE peaks (`% before` high, median negative) — *cut just before the action happens*.

## What this does NOT prove

- Same N=42 limit as the unsigned smell test. Tiny per-type samples.
- 'Nearest peak' can flip sign for a cut that lands equidistant between two peaks. With prominence=75th-percentile and dense peaks (e.g. 148 peaks in 204s for basil_pesto AI2I5202), inter-peak intervals are short and this is a real source of noise.
- Does not distinguish 'cut before THIS action's start' vs 'cut after PREVIOUS action's end' when the cut lands in dead time between two motion peaks. Operationalization needs work.

## What this could suggest (if directions hold)

- A median signed_delta significantly different from zero (in either direction) for a beat_type with n ≥ ~10 would be the first hint that the cut-before/cut-after axis is editorially structured.
- A `% before` or `% after` skewed strongly away from 50/50 for a beat_type means cuts are temporally biased relative to peaks — directional support for the hypothesis.
- Per-recipe medians agreeing in sign within a beat_type strengthens the directional read.

## What unblocks the real test

1. **RAFT curves for the 16 missing recipes.** Existing `run_exp05_modal.py`, expand `DRIVE_FOLDER_IDS`.
2. **329 untyped beats labeled** via the Beat Review UI.

After both, re-run with this same operationalization on N ≈ 600.
