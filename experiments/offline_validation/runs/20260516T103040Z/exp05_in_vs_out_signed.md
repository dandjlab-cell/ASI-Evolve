# RAFT signed-delta — cut-IN vs cut-OUT × beat_type (N=42)

_Generated 2026-05-16T10:30:40.777898+00:00_

**Hypothesis under test:** *The clip starts just before the peak of the action. So I cut INTO a shot just moments before the action happens, and cut OUT when it ends.*

## Predicted vs observed signs

| signal | predicted | observed (median) | direction |
|---|---|---|---|
| `in_signed_delta`  | NEGATIVE (cut-in before peak) | +0.059s | opposite |
| `out_signed_delta` | POSITIVE (cut-out after peak) | +0.322s | consistent |

## Overall (all 42 beats)

**Cut IN** (clip start):
- median +0.059s
- before peak: 19/42 (45.2%)
- after peak:  23/42 (54.8%)

**Cut OUT** (clip end):
- median +0.322s
- before peak: 12/42 (28.6%)
- after peak:  30/42 (71.4%)

## By beat_type — cut-IN signed-delta

| beat_type | n | median (s) | % before | % after | before/after |
|---|---|---|---|---|---|
| `UNTYPED` | 21 | +0.114 | 38.1% | 61.9% | 8/13 |
| `ingredient` | 13 | -0.021 | 53.8% | 46.2% | 7/6 |
| `beauty_opener` | 3 | +0.260 | 0.0% | 100.0% | 0/3 |
| `beauty` | 2 | -0.066 | 50.0% | 50.0% | 1/1 |
| `beauty_close` | 1 | -0.180 | 100.0% | 0.0% | 1/0 |
| `technique` | 1 | -0.012 | 100.0% | 0.0% | 1/0 |
| `title_card` | 1 | -0.026 | 100.0% | 0.0% | 1/0 |

## By beat_type — cut-OUT signed-delta

| beat_type | n | median (s) | % before | % after | before/after |
|---|---|---|---|---|---|
| `UNTYPED` | 21 | +0.345 | 38.1% | 61.9% | 8/13 |
| `ingredient` | 13 | +0.173 | 30.8% | 69.2% | 4/9 |
| `beauty_opener` | 3 | +0.322 | 0.0% | 100.0% | 0/3 |
| `beauty` | 2 | +0.433 | 0.0% | 100.0% | 0/2 |
| `beauty_close` | 1 | +0.884 | 0.0% | 100.0% | 0/1 |
| `technique` | 1 | +0.195 | 0.0% | 100.0% | 0/1 |
| `title_card` | 1 | +1.471 | 0.0% | 100.0% | 0/1 |

## Per-beat side-by-side (sorted by beat_type, then recipe)

| recipe | beat | beat_type | in_signed (s) | out_signed (s) | duration (s) |
|---|---|---|---|---|---|
| basil_pesto | 5 | `UNTYPED` | +0.16 | -0.30 | 1.38 |
| basil_pesto | 6 | `UNTYPED` | +0.13 | +0.55 | 1.17 |
| basil_pesto | 8 | `UNTYPED` | -0.18 | +0.69 | 1.79 |
| basil_pesto | 9 | `UNTYPED` | -0.04 | +0.00 | 1.13 |
| basil_pesto | 13 | `UNTYPED` | -0.73 | +0.56 | 1.29 |
| basil_pesto | 14 | `UNTYPED` | +0.42 | +0.05 | 1.04 |
| basil_pesto | 15 | `UNTYPED` | +0.51 | +0.35 | 1.17 |
| basil_pesto | 30 | `UNTYPED` | +4.18 | +5.68 | 1.50 |
| basil_pesto | 31 | `UNTYPED` | +3.27 | -2.77 | 1.38 |
| basil_pesto | 41 | `UNTYPED` | -0.54 | -0.16 | 1.37 |
| basil_pesto | 42 | `UNTYPED` | +0.90 | +2.49 | 1.58 |
| chicken_thighs | 15 | `UNTYPED` | +3.17 | -4.74 | 1.67 |
| chicken_thighs | 16 | `UNTYPED` | +0.01 | +1.13 | 1.13 |
| chicken_thighs | 33 | `UNTYPED` | -0.16 | -0.12 | 1.54 |
| chicken_thighs | 34 | `UNTYPED` | +0.11 | +0.99 | 1.13 |
| chicken_thighs | 35 | `UNTYPED` | -0.09 | +1.49 | 1.58 |
| chicken_thighs | 36 | `UNTYPED` | -0.00 | +1.33 | 1.33 |
| chicken_thighs | 41 | `UNTYPED` | -7.20 | -5.57 | 1.63 |
| chicken_thighs | 45 | `UNTYPED` | +0.37 | +1.53 | 1.17 |
| chicken_thighs | 46 | `UNTYPED` | +0.11 | -0.22 | 1.66 |
| chicken_thighs | 48 | `UNTYPED` | +2.93 | -3.94 | 2.88 |
| chicken_thighs | 39 | `beauty` | -0.29 | +0.54 | 1.50 |
| chicken_thighs | 43 | `beauty` | +0.15 | +0.32 | 1.17 |
| basil_pesto | 44 | `beauty_close` | -0.18 | +0.88 | 2.06 |
| basil_pesto | 1 | `beauty_opener` | +0.26 | +0.30 | 1.46 |
| chicken_thighs | 0 | `beauty_opener` | +0.16 | +0.32 | 1.17 |
| chicken_thighs | 1 | `beauty_opener` | +1.20 | +2.49 | 1.29 |
| basil_pesto | 3 | `ingredient` | -0.31 | +0.98 | 1.29 |
| basil_pesto | 23 | `ingredient` | +0.33 | +0.04 | 1.04 |
| basil_pesto | 24 | `ingredient` | -0.33 | +0.17 | 1.16 |
| basil_pesto | 26 | `ingredient` | +6.47 | +7.51 | 1.04 |
| basil_pesto | 34 | `ingredient` | -0.02 | +0.77 | 1.12 |
| chicken_thighs | 3 | `ingredient` | -27.43 | -25.93 | 1.50 |
| chicken_thighs | 4 | `ingredient` | -11.25 | -10.08 | 1.17 |
| chicken_thighs | 6 | `ingredient` | -0.19 | +0.81 | 1.33 |
| chicken_thighs | 7 | `ingredient` | +0.35 | -2.02 | 5.13 |
| chicken_thighs | 8 | `ingredient` | +6.90 | +8.15 | 1.25 |
| chicken_thighs | 9 | `ingredient` | -4.76 | -3.72 | 1.04 |
| chicken_thighs | 18 | `ingredient` | +0.15 | +0.19 | 1.29 |
| chicken_thighs | 29 | `ingredient` | +0.01 | +0.17 | 1.17 |
| chicken_thighs | 13 | `technique` | -0.01 | +0.19 | 1.29 |
| chicken_thighs | 31 | `title_card` | -0.03 | +1.47 | 1.50 |

## How to read the directional finding

**If Dan's hypothesis holds at this sample size:**
- `in_signed_delta` median should be NEGATIVE and `% before` > 50% (clips START before peaks).
- `out_signed_delta` median should be POSITIVE and `% after` > 50% (clips END after peaks).
- The two signs together form an *envelope around the peak*: clip brackets the action.

**Caveats specific to this operationalization:**
- 'Nearest peak' for the IN-point and the OUT-point may be the SAME peak when the beat is short. That's actually what the hypothesis predicts — the clip wraps a single action peak.
- For beats spanning multiple peaks, IN's nearest peak ≠ OUT's nearest peak; the signs are then independent.
- At prominence=75th-percentile, peaks are dense; small signed_deltas dominate.

## What this does NOT prove

- Same N=42 limit. Per-beat_type samples are 1-21.
- Cannot distinguish 'cut into a shot before this action' from 'cut into a shot after the previous action' in dense-peak regions.
- VLM `motion_phase` × `beat_type` is the cleaner-but-different signal at larger N (7 recipes / 149 beats). This RAFT-based test is the only existing-data way to read the IN/OUT-vs-peak axis directly.

## What unblocks the real test

1. **RAFT curves for the 16 missing recipes** (`run_exp05_modal.py` + expanded `DRIVE_FOLDER_IDS`).
2. **329 untyped beats labeled** via the Beat Review UI.

Then re-run this same script on N ≈ 600 with proper per-beat_type sample sizes.
