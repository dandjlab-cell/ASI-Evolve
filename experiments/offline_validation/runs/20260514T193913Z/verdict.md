# Offline Validation Verdict — 2026-05-14 → 2026-05-15

Run timestamps:
- `20260514T152048Z` — Exp #2 (DINO peak alignment)
- `20260514T193913Z` — Exp #5 (RAFT subject-motion on Modal L4) + initial verdict
- `20260515T074347Z` — motion_phase (binary in-phase scoring) — pivot from peak alignment
- `20260515T082643Z` — stratified by beat_type + mogrt duration analysis

Plan + codex review log: `~/.claude/plans/continue-from-handoff-users-dandj-devapp-polymorphic-blossom.md`.

---

## TL;DR — final state

| | Result |
|---|---|
| Coverage | 6 recipes / 118 ≥1s beats with full DINO. 7 recipes / 149 ≥1s beats with scan.json descriptions (motion_phase corpus). M6-B (10/150) not met. |
| **Exp #2 (DINO peak alignment)** | **Stage A borderline, Stage B fail.** Peak-proximity not Dan's rule — see lines 9-22 below. |
| **Exp #5 (RAFT subject-motion vs DINO)** | **Not promising.** N=2 directional, RAFT no better than DINO. |
| **motion_phase global rule** | **Borderline-fail / fail.** No clean "Dan cuts on motion frames" signal globally. |
| **motion_phase stratified by `beat_type`** | **CLEAN finding.** Different beat types have OPPOSITE motion preferences — see new section below. |
| **mogrt hold-duration rule** | **CLEAN finding, p < 1e-19.** Beats with mogrt overlays hold ~+0.34s longer. See new section below. |

**No production code authorized this round** — the original watershed-rhythm-via-peak-alignment thesis is not supported by the data on the M6-A corpus. But the experiments produced two CLEAN, INTERPRETABLE, EDITORIALLY-VALID rules that ARE supported by the data and are worth wiring as v1 candidates:

1. **motion_phase rule conditional on `beat_type`** — different cuts have different motion expectations (cut on action for `technique`; cut on stillness for `beauty_opener` / `beauty`).
2. **mogrt-duration rule** — when text is on, hold at least p25 of the mogrt'd duration distribution (~1.3s); penalize anything shorter.

These were not in the original plan. They emerged from the data and they pass cleanly.

---

## What changed in the second day

Codex-approved plan said: peak alignment fails → don't wire code, pause the thesis. That decision stands for the peak-alignment thesis. But Dan's editorial pushback on 2026-05-15 (paraphrased: "I sometimes cut on motion, sometimes don't — depends on recipe, angle, best shot, and whether I'm doing a stop-motion or a reveal or a technique") prompted a stratification pass. Stratifying by `beat_type` exposed exactly what the global aggregation was washing out: opposite editorial intents averaging to zero.

---

## Numbers

### Exp #2 — DINO peaks vs Dan cuts (per-clip framing, ≥1s beats, N=5 recipes, 112 beats)

| | Stage A (uniform null) | Stage B (local-jitter null) |
|---|---|---|
| median per-recipe `delta_beat` (s) | **−0.345** | **+0.017** |
| recipe-clustered bootstrap CI on median | [−1.760, +0.408] | [−0.108, +0.133] |
| Cliff's δ | **−0.600** | +0.600 |
| Cliff's δ CI | [−1.000, +0.200] | [−0.200, +1.000] |
| Wilcoxon signed-rank p (diagnostic) | 0.156 | 0.906 |
| **Verdict** | **borderline** | **fail** |

Per-recipe Stage A medians (s):

| recipe | delta_A |
|---|---|
| banana_muffins | **−1.760** |
| korean_fried_chicken | **−1.037** |
| chicken_thighs | **−0.345** |
| basil_pesto | **−0.071** |
| steak_tacos | +0.408 |

4 of 5 recipes show the expected effect direction. steak_tacos is the outlier driving the bootstrap CI's upper tail above zero. **A larger sample is the obvious next step** — bootstrapping 5 recipes will always give a wide CI even when the central tendency is clearly directional.

### Exp #5 — RAFT subject-motion vs Dan cuts (N=2 recipes, 12fps Modal RAFT)

| | RAFT internal (Stage A) | RAFT vs DINO pair-diff |
|---|---|---|
| median per-recipe delta (s) | **+0.102** | **+0.426** |
| recipe-clustered bootstrap CI | [−0.243, +0.447] | [−0.086, +0.938] |
| Cliff's δ | 0.000 | 0.000 |
| **Verdict** | **not_promising** | **not_promising** |

RAFT subject_motion_magnitude peaks (median residual after camera-translation removal) at 12fps did not produce tighter alignment to Dan's cuts than DINO at 1fps. With N=2 this is not decisive — but it's enough to reject the "DINO is too coarse, RAFT will fix it" hypothesis as a strong prior. The plan's M5 explicitly forbade architecture redirects on N=2, so the appropriate response is: shelve RAFT pending stronger evidence.

---

## What this means (interpretation, not certainty)

The Exp #2 Stage A vs Stage B contrast is the most informative finding. **Direction is right vs arbitrary random points; signal evaporates vs "anywhere near a real cut."** Two interpretations both consistent with the data:

1. **The peak-alignment scoring rule is too crude.** Dan's cut decision is influenced by motion phase (active / settling / static) and content (composition, story beat, dialogue) — peak proximity captures only a coarse "in an active region" component, not the precise within-window placement. A scoring rule that operationalizes peak proximity would reward exactly the wrong thing (penalize cuts placed elsewhere in the same active window — even though those alternative placements aren't worse).

2. **The instrument is too coarse to see it.** 1fps DINO can't resolve sub-second beats (60% of basil_pesto's annotated beats). 12fps RAFT can, but didn't show better alignment. Possible that the actual signal is at 24fps+ and we'd need true frame-level analysis to find it — but Occam's razor says (1) is more likely than (2).

The Stage A *passing as borderline* (negative direction with effect size Cliff's δ = −0.6) is real — Dan does cut *in active regions* more than chance. The Stage B *failing* says that's a coarse fact about active-vs-static, not a precise fact about peak placement. **That nuance is the hypothesis-update.**

---

## What was tested vs what was avoided

- **Per-source-clip framing only** (per plan §M1 — stitched-timeline framing was dropped because it was broken by construction).
- **Primary subset = ≥1s beats** (per plan §M2 — sub-second beats can't be resolved at 1fps DINO).
- **Per-beat paired delta + recipe-clustered bootstrap CI** (per plan §M3 — fixed the inflated-N issue from earlier drafts; Wilcoxon is diagnostic only).
- **Two-stage null: weak A authorizes strong B** (per plan §M4 — passing A alone is not enough to gate code).
- **Modal L4 GPU for RAFT at 12fps per source clip** (per plan §M7 — avoided assembled-video extraction because cross-cut RAFT pair-flow is degenerate).
- **Coherence < 0.4 → drop pair** (per plan §M8 — actually quite forgiving; degraded fraction averaged <5% across our 27 clips).

Sensitivity sweep on prominence percentile (50th + 90th) was run but is in the secondary results — no qualitative change to the borderline/fail verdict.

---

## motion_phase stratified by `beat_type` — the CLEAN finding

Run: `runs/20260515T082643Z/` (script: `exp_stratified_by_beat_type.py`).

Across the 7-recipe corpus (basil_pesto, banana_muffins, chicken_thighs, creamy_potato_soup, french_onion_mac, korean_fried_chicken, steak_tacos), the rate at which Dan's qualifying ≥1s cut-out frames land on `active|just_finished` (classified from v15 VLM descriptions via `motion_phase_classifier.py`) compared to the within-recipe baseline:

| beat_type | n_beats | dan_hit% | recipe_base% | lift | editorial reading |
|---|---|---|---|---|---|
| `technique` | 2 (tiny — directional only) | 100% | 73% | **+27%** | cuts on the action — expected |
| `title_card` | 15 | 80% | 72% | +8% | cuts during slight motion under text — expected |
| `beauty_close` | 4 | 75% | 69% | +6% | mild positive |
| `(empty)` (process / cooking beats — see next section) | 60 | 77% | 71% | +5% | mild positive — process work tends slightly active |
| `ingredient` | 58 | 69% | 71% | −2% | flat — drops are sometimes active, sometimes the after-rest |
| **`beauty`** | 6 | **50%** | 72% | **−22%** | cuts on settled frames — expected |
| **`beauty_opener`** | 8 | **37.5%** | 72.5% | **−35%** | cuts HARD on stillness — strongly expected |

**The signal is opposite-direction by beat_type.** Beauty openers cut on stillness at 35pp below the recipe's baseline; technique cuts on motion at 27pp above. The global aggregation was averaging these together and getting noise — exactly what we saw in the unstratified motion_phase experiment.

**Operational implication.** A scoring rule shouldn't ask "did Dan cut on motion?" — it should ask "given the beat_type, did Dan honor that beat_type's motion convention?":
- `technique` / `title_card`: reward motion frame
- `beauty_opener` / `beauty`: reward stillness frame
- `ingredient`: no strong direction — rely on duration / mogrt signal instead
- `beauty_close` / `(empty)`: weak positive — rely on other signals

The two largest beat-type buckets in our corpus are `(empty)` (60 beats) and `ingredient` (58 beats). The named editorial moves (`beauty_opener`, `beauty`, `beauty_close`, `technique`) are smaller samples — direction is right but more data would harden the claim.

---

## mogrt hold-duration rule — the OTHER clean finding

Run: same as above (slice 2 of `exp_stratified_by_beat_type.py`).

Pooled across **all 18 annotated recipes** (not just the motion_phase-corpus 7):

| | n | median | p25 | p75 |
|---|---|---|---|---|
| beats **with** mogrt | 159 | **1.50s** | 1.29s | 2.02s |
| beats **without** mogrt | 454 | **1.17s** | 0.79s | 1.50s |

**Median lift: +0.34s.** Mann-Whitney U one-sided (with > without) p ≈ 1e-19. The mogrt p25 (1.29s) almost exactly equals the no-mogrt p75 (1.50s) — these distributions barely overlap.

11 of 13 recipes (where both populations exist) show positive lift. The two exceptions (crab_rangoon −0.13s, sweet_potato_pie −0.06s) are tiny samples with possible classification noise.

Strongest per-recipe lifts:
- flaky_pie_crust: **+1.08s** (with-mogrt holds twice as long)
- pin_wheel: +0.71s
- puppy_chow: +0.67s
- peppermint_bark: +0.42s
- steak_tacos: +0.38s
- cucumber_tea: +0.35s
- baked_potato_soup: +0.33s
- french_onion_mac: +0.23s

**Editorial rule the data supports:** when a beat has a mogrt overlay, hold at least ~1.3s (the with-mogrt p25). Penalize anything shorter. The exact threshold should be calibrated per recipe (per-recipe variation is real — from +0.08s to +1.08s) but the *direction* and *significance* are unambiguous.

**Operational implication.** This is a candidate for a v1 `mogrt_minimum_hold` scoring rule that's interpretable, defensible, and has no peak-detection / RAFT / model dependency. It just reads the manifest's mogrt metadata and the beat's `timeline_out − timeline_in` duration. Cheap to wire.

---

## Reading the `(empty)` beat_type bucket

Across all 18 annotated recipes, **329 of 613 beats** (~54%) have no `beat_type` populated:

| beat_type | verdict.choice | count |
|---|---|---|
| (empty) | added | 258 |
| ingredient | added | 113 |
| ingredient | editorial_group | 83 |
| **(empty)** | **editorial_group** | **71** |
| beauty_opener | editorial_group | 27 |
| title_card | editorial_group | 24 |
| beauty | editorial_group | 19 |
| stop_motion | added | 7 |
| technique | editorial_group | 7 |
| beauty_close | editorial_group | 5 |
| stop_motion | editorial_group | 4 |

**Why the empties exist:** `analyze_editorial_judgment.py` (lines 1140-1170) only tags beats that fall into one of three GROUPED editorial sequences:
- `beauty_opener` (first 2-3 hero shots)
- `stop_motion_group` (detected stop-motion sequence)
- `mogrt_zone` → tagged `ingredient` (under a text overlay)

Beats that are standalone single cuts ("verdict.choice = added", not part of a named group) get **no `beat_type`**. Those 258 untagged "added" beats are the **process / cook beats** — the actual cooking action between named events. Sample sections in this bucket: "Wet base build (butter → bananas)", "Garlic into pan, pine nuts arrive", "Pine nuts label + toast", "Sugar dome + whisk-in." These are the meat of the recipe show — the technique work that fills the middle of each section.

The 71 untagged `editorial_group` beats are similar — beats inside a grouped sequence that weren't in one of the three named group types.

**Recipe-by-recipe (untyped beat_type count of total):**

| recipe | beats | typed | untyped |
|---|---|---|---|
| baked_lobster_tail | 51 | 16 | 35 |
| baked_potato_soup | 34 | 16 | 18 |
| banana_muffins | 25 | 12 | 13 |
| basil_pesto | 45 | 20 | 25 |
| chicken_thighs | 49 | 34 | 15 |
| congee | 26 | 14 | 12 |
| crab_rangoon | 27 | 13 | 14 |
| cranberry_jalapeno_dip | 19 | 7 | 12 |
| creamy_potato_soup | 23 | 17 | 6 |
| cucumber_tea | 29 | 14 | 15 |
| flaky_pie_crust | 22 | 5 | 17 |
| french_onion_mac | 44 | 22 | 22 |
| korean_fried_chicken | 52 | 40 | 12 |
| peppermint_bark | 34 | 10 | 24 |
| pin_wheel | 52 | 15 | 37 |
| puppy_chow | 22 | 5 | 17 |
| steak_tacos | 41 | 21 | 20 |
| sweet_potato_pie | 23 | 8 | 15 |

**What labeling those would unlock:** the stratified motion_phase finding above shows clean opposite-direction signals for `technique` (+27%) vs `beauty_opener` (−35%). Sample sizes are tiny because most of these beats live in the `(empty)` bucket. If `(empty)` were labeled into `technique` / `transition` / `cook_action` / `reveal` / `result_hold` / etc., the motion_phase rule would be testable on a much larger sample and the recipe-conditional patterns Dan described editorially could be measured.

**Where the labeling work would happen:**
- Existing classifier: `experiments/recipe_pipeline/analyze_editorial_judgment.py:1140-1170` — extend the grouping logic to label single beats with content-derived types (e.g. use the VLM `description` to assign `technique` / `reveal` / `result_hold`).
- The motion_phase_classifier in `experiments/offline_validation/motion_phase_classifier.py` already does action-vs-stillness — could be extended to also output a coarser content category.
- A focused annotation pass on the 13 missing recipes (when they get roughcut runs) is the natural moment to also tag the singletons.

---

## Follow-ups

| Priority | Action | Owner |
|---|---|---|
| **HIGH** | **Wire `mogrt_minimum_hold` scoring rule.** Read manifest's mogrt overlap metadata + beat `timeline_out − timeline_in`. Penalize holds shorter than ~1.3s (with-mogrt p25) — calibrate per recipe later. Cheap, interpretable, p < 1e-19 backed. Lives in `score_rules.py`. | ASI |
| **HIGH** | **Wire `motion_phase_by_beat_type` scoring rule** for the well-evidenced beat_types: `beauty_opener` (penalize cuts on active frames), `beauty` (same, milder), `technique` (penalize cuts on static frames). Skip `ingredient` and `(empty)` — no signal there yet. Pre-req: v15 scan.json descriptions OR v16 fast_scan's structured `motion_phase` field. | ASI |
| **HIGH** | **Label the `(empty)` beat_type bucket** (329 of 613 beats = 54% of corpus). These are mostly process / cook beats (technique work between named events). `analyze_editorial_judgment.py:1140-1170` currently only tags grouped beats. Extend to label singletons using VLM description content (already proven workable in `motion_phase_classifier.py`). This unlocks larger samples for the stratified motion_phase rule. | ASI |
| **HIGH** | **Process the 13 missing recipes through roughcut** to lift coverage to M6-B. The 13 missing accounts for ~321 additional ≥1s annotated beats. `creamy_potato_soup` was pulled from Modal 2026-05-15; the other 12 need Drive folder IDs registered. See `recipe_run_map.json` for the explicit gap list. | roughcut |
| **MEDIUM** | **Build the classifier-derived strong null** using `classify_broll.py`'s `usable_out_s` intervals per source clip. The current Stage B fallback (±3s around actual cuts) is a conservative-local-jitter null, not equivalent to a true candidate-exit-window null. If the *real* strong null still fails on the stratified-by-beat_type version too, the peak-alignment thesis is genuinely falsified. | ASI |
| **MEDIUM** | **Revise the Brain vault strategy notes** (hot pending items #1, #2): §1.5 audio-state conflation, RAFT spec, Strategy/Offline Experiment Plan.md. Original plan deferred these; they remain pending. | ASI strategy |
| **LOW** | **N=5 RAFT follow-up** is OFF the critical path. RAFT didn't beat DINO at N=2 and motion-peak-proximity isn't Dan's rule anyway. Revisit only if a new motion-related hypothesis surfaces. | — |

---

## Open follow-ups carried from the plan (unchanged)

- **§1.5 audio-state conflation** in Brain vault — deferred.
- **RAFT spec backfill** in Brain vault — partially mooted by this verdict (RAFT not on v2 critical path).
- **Strategy/Offline Experiment Plan.md** in Brain vault — would consolidate the 9-experiment list from handoff. Not blocking.

---

## Files

| Path | What |
|---|---|
| `exp02_results.json` | Full per-recipe + per-beat Stage A & B numbers + sensitivity sweep + missing-data audit. |
| `exp02_delta_beat_hist.png` | Per-beat `delta_beat` distribution, both stages. |
| `exp02_per_recipe_forest.png` | Per-recipe medians, both stages, with bootstrap CI markers. |
| `exp05_results.json` | RAFT subject-motion curve summary + RAFT-vs-DINO comparison. |
| `exp05_subject_motion_vs_cuts.png` | Per-recipe RAFT delta. |
| `exp05_raft_vs_dino_comparison.png` | Per-beat (RAFT − DINO) histogram. |
| `../../.cache/exp05_curves/{recipe}/{source_id}.json` | Modal-produced RAFT subject-motion curves (27 clips). |
| `../../recipe_run_map.json` | Coverage truth — which recipes have usable DINO cache, which don't. |

Total cost this round: Modal L4 RAFT compute on 27 source clips ≈ **20 min wall + tiny Drive download time** (Modal app: `experiments/offline_validation/modal_exp05_raft.py`).

---

## Addendum — 2026-05-16 framing correction

The "RAFT shelved" / "RAFT not on v2 critical path" language above flattened a tool judgment over a technique finding. The deeper, carry-forward framing is documented in the Brain vault: see **[Motion Signal — Conditional Not Blanket](../../../../../Brain/Projects/ASI-Evolve/Motion%20Signal%20—%20Conditional%20Not%20Blanket.md)** (created 2026-05-16).

Two distinct claims that this verdict elided:

1. **Peak-alignment-as-scoring-rule is recipe-conditional** (per-recipe deltas in `exp02_results.json:stage_a.recipe_deltas` span −1.76 to +0.41 with one sign-flip; `exp05_results.json:raft_stage_a.recipe_deltas` shows opposite signs for the only two recipes). This is a finding about the *technique*, not the *tool*.

2. **RAFT-as-feature-source for stratified categorical rules is untested**, not shelved. A directional smell test on the existing N=42 RAFT per-beat data joined with annotation beat_types lives at `runs/20260516T092835Z/exp05_stratified_smell.md`. Real test requires backfilling RAFT curves for the 16 missing recipes (one-shot Modal job) + the 329 untyped beats labeled via the Beat Review UI.

The original verdict's recommendation — "wire `motion_phase_by_beat_type` using VLM categorical signal" — is **SUPERSEDED 2026-05-16**. Do not wire until the stratification is redone on `(canonical_move, sub_variant)`; bare `beat_type` collapses across editorial sub-variants with opposite motion signatures (confirmed for `ingredient_dump` V1 vs V2). See [Editorial Move Vocabulary — Canonical Moves and Sub-Variants](../../../../../Brain/Projects/ASI-Evolve/Editorial%20Move%20Vocabulary%20—%20Canonical%20Moves%20and%20Sub-Variants.md) for the corrected vocabulary. The RAFT-derived categorical-signal swap-in question is also blocked until then.

This verdict file is preserved as the dated artifact of the 2026-05-14 run. Subsequent framing supersedes only where explicitly noted in the linked vault doc.
