# ASI-Evolve — Session Handoff 2026-05-14 → 2026-05-15

**Date:** 2026-05-15 (+ 2026-05-16 corrections appended throughout)
**Branch:** `refactor/writer-modules` (uncommitted spike work + dirty files from earlier — see "Git state" below)
**Predecessor handoff:** the 2026-05-13/14 handoff at the top of `git log` (`8ea74bc`) — that handoff queued the offline experiments; this one reports what they found.

---

## ⚠️ READ THIS FIRST — 2026-05-16 corrections

The findings table below references stratifications by bare `beat_type`. **Those stratifications are SUSPECT.** Bare `beat_type` is too coarse — the real editorial structure lives in `recipe_section` text + parenthetical sub-variants + `beat_description`. The canonical reference for the correct editorial vocabulary is now:

→ **[Editorial Move Vocabulary — Canonical Moves and Sub-Variants](../../Brain/Projects/ASI-Evolve/Editorial%20Move%20Vocabulary%20—%20Canonical%20Moves%20and%20Sub-Variants.md)**

That vault note documents:
- ~8 canonical editorial moves that recur across all 18 recipes
- The `ingredient_dump` V1 (cut-to-action) vs V2 (stop-motion-vibe / appear-in-bowl) sub-variant split, confirmed by RAFT-peak-presence data
- That `mid-edit` and `late-edit` are **annotator placeholder buckets, NOT editorial moves**
- Which prior findings still survive (mogrt_minimum_hold; technique-vs-tool conceptual framing) and which need redo (every beat_type-stratified analysis + per-recipe variance)
- The known `camera_mapping.json` prefix-rule bug on chicken_thighs B19I6669

**Before running any motion-signal analysis or building UI labeling flows, read that vault note.** Do not redo this session's discovery process.

---

## Project in one line

ASI-Evolve = scorer + harness measuring roughcut-ai pipeline output against Dan's editor reference style. Recipe content. Strategy hub: `~/DevApps/Brain/Projects/ASI-Evolve/`.

---

## What this session actually delivered

A complete spike of 4 hypotheses about how Dan cuts recipes, plus the surfacing of the actual UX blocker. The spike originally reported 2 clean findings worth wiring, but only one (`mogrt_minimum_hold`) survives 2026-05-16's editorial-vocabulary correction — see "READ THIS FIRST" callout above and the table below.

| Hypothesis | Verdict | Operational result |
|---|---|---|
| **Exp #2** — Dan cuts near DINO motion peaks | Stage A borderline, Stage B fail | Peak-proximity not Dan's rule |
| **Exp #5** — RAFT subject-motion peaks tighter than DINO | Not promising (N=2 on Modal L4) | Peak-alignment-as-technique unviable at this N; RAFT-as-feature-source for stratified rules untested (separate, viable question). See [Brain vault: Motion Signal — Conditional Not Blanket](../../Brain/Projects/ASI-Evolve/Motion%20Signal%20—%20Conditional%20Not%20Blanket.md) |
| **motion_phase global** — Dan cuts on `active`/`just_finished` frames | Borderline-fail / fail | Global rule not Dan's rule either |
| **motion_phase stratified by `beat_type`** | ~~CLEAN finding~~ → **SUSPECT (2026-05-16)** | Stratified by bare `beat_type`, which is too coarse. The technique +27pp / beauty_opener −35pp lifts may hide sub-variant variance. Needs redo on `(canonical_move, sub_variant)` — see [Editorial Move Vocabulary — Canonical Moves and Sub-Variants](../../Brain/Projects/ASI-Evolve/Editorial%20Move%20Vocabulary%20—%20Canonical%20Moves%20and%20Sub-Variants.md). |
| **mogrt hold-duration** — beats with text overlay hold longer | **CLEAN, p < 1e-19** | Median +0.34s lift, 11/13 recipes positive. *Still valid* — no beat_type dependency. |

**Authoritative verdict + numbers:** `experiments/offline_validation/runs/20260514T193913Z/verdict.md`.

---

## Production-candidate scoring rules emerging from this work

**Status as of 2026-05-16:** Only `mogrt_minimum_hold` is ready to wire. The `motion_phase_by_beat_type` rule is **superseded** pending re-stratification on `(canonical_move, sub_variant)` — see [Editorial Move Vocabulary — Canonical Moves and Sub-Variants](../../Brain/Projects/ASI-Evolve/Editorial%20Move%20Vocabulary%20—%20Canonical%20Moves%20and%20Sub-Variants.md).

1. **`mogrt_minimum_hold`** — Read manifest's mogrt overlap metadata + beat `timeline_out − timeline_in`. Penalize anything shorter than ~1.3s (the with-mogrt p25 from corpus). No model dependency, no peak detection. Cheap, defensible, statistically clean.

2. ~~**`motion_phase_by_beat_type`**~~ → **DO NOT WIRE YET (2026-05-16).** This rule was built on bare-`beat_type` stratification, which we now know collapses across editorial sub-variants. The `ingredient` bucket alone contains at least two distinct sub-variants (V1 cut-to-action and V2 stop-motion-vibe) with opposite motion signatures — RAFT peak present for V1 (71% of sample) vs absent for V2 (14% of sample). The other beat_types likely have similar splits. **Before wiring this rule, redo the stratification on `(canonical_move, sub_variant)` per [Editorial Move Vocabulary — Canonical Moves and Sub-Variants](../../Brain/Projects/ASI-Evolve/Editorial%20Move%20Vocabulary%20—%20Canonical%20Moves%20and%20Sub-Variants.md).** Until that's done, the per-beat_type lifts (technique +27pp, beauty_opener −35pp) may be artifacts of sub-variant mix, not stable editorial rules.

---

## The actual blocker Dan surfaced at end of session

Dan's words (paraphrased): *"For more annotation work I'd need to see what I edited, not read text about it. The UX is broken — I'm being asked to label data from text descriptions about cuts I made months ago. We have finished videos, frame extracts, XMLs. This should be presented in a way where I can easily explain what's happening and the editorial decisions. I have a formula to how I edit these."*

**This is the real next-session priority.** The follow-ups in `verdict.md` rank "label the untyped 329 beats" (54% of corpus) as HIGH — but Dan can't reasonably do that without an editor-facing review UI. The current "annotation" pipeline goes XML → JSON → Brain vault text, which is one-directional. There's no way to scroll through the finished cut, see what was happening at each beat, type a `beat_type` + an editorial-reason note, and have it land back into the JSON.

**What we have that could be the foundation:**
- **Finished MP4s** for the 7 motion_phase-corpus recipes (verified locations under `/Volumes/2TB Footage/01_Projects/Kitchn/2026_March/04 Exports/{Recipe Name}/{...}FINAL.mp4`). Example: `Basil Pesto FINAL.mp4`, `11 Korean Fried Chicken_FINAL.mp4`, `Grilled Steak Tacos FINAL v2.mp4`.
- **Per-recipe annotation JSON** (18 files at `experiments/recipe_pipeline/annotations/*.json`) — has every beat's timeline position, source clip, mogrt overlap, recipe_section, current beat_type (if any).
- **Frame extracts** at `experiments/recipe_pipeline/frames/{recipe}/frame_*.jpg` — extracted at smart fps (2fps baseline + 12fps in dense regions, per `extract_frames_smart.py`).
- **UXP probe scaffolding** at `experiments/recipe_pipeline/uxp_probe/` — an existing Premiere UXP panel skeleton that talks to a live Premiere project. ~12 probe rounds of history in `.before-round*` files.
- **Source XMLs** at `/Volumes/2TB Footage/01_Projects/Kitchn/2026_March/02 Footage/{Recipe}_FINAL.xml` and approved edits at `experiments/recipe_pipeline/approved_edits/`.

**What a minimal "review UX" looks like** (open design — Dan hasn't picked):
- Local web page or UXP panel, one per recipe
- Lists each beat sequentially with its current metadata
- Per beat: shows in/out frame thumbnails, the mogrt text (if any), the recipe_section, the source clip ID
- Plays the corresponding slice of the FINAL.mp4 at the beat's timeline_in→timeline_out
- Lets Dan: pick a `beat_type` from a dropdown, type a free-text "why this cut" note
- Saves back to a sidecar JSON or merges into the existing annotation file

**Open questions for Dan next session:**
1. Web (browser) or UXP (in Premiere)? UXP gets you live Premiere integration but needs Premiere open. Web is portable.
2. Review-existing-edits-and-annotate? Or annotate-while-editing-new-recipes?
3. The "formula" Dan mentioned — would it be more useful to dictate it FIRST (so we know what beat_types / decision dimensions to provide as picker options), or surface it inductively as he annotates?

---

## What's deployed / what's pending

### Local
- `experiments/offline_validation/` — full spike machinery. All scripts are runnable from there with `.venv/bin/python3`.
  - `preflight.py` → `recipe_run_map.json` (coverage state)
  - `data_loaders.py`, `stats.py` — shared
  - `exp02_dino_peaks_vs_dan_cuts.py` — peak alignment (Exp #2)
  - `exp05_raft_subject_vs_camera.py` — RAFT stats over Modal-cached curves (Exp #5)
  - `modal_exp05_raft.py` + `run_exp05_modal.py` — Modal pipeline (parallel-capable for future N=5+)
  - `motion_phase_classifier.py` — regex classifier
  - `exp_motion_phase_vs_dan_cuts.py` — global motion_phase
  - `exp_stratified_by_beat_type.py` — stratified + mogrt analysis (the clean-finding script)
- `experiments/offline_validation/runs/` — 4 timestamped output dirs (results JSON + plots + verdict.md)
- `experiments/offline_validation/.cache/exp05_curves/` — 27 RAFT subject-motion curves cached locally (don't need to re-pull from Modal)
- `experiments/offline_validation/.cache/exp05_raft/basil_pesto/` — partial 12fps frame extracts from the killed-then-resumed run (basil_pesto only, 11 of 13 clips). **Safe to delete** — Modal redid everything.

### Modal
- Volume `asi-exp05` — RAFT subject-motion JSONs for basil_pesto (13 clips) + chicken_thighs (14 clips). Already pulled locally; can keep or delete.
- Volume `roughcut-artifacts` — 27 recipes processed by roughcut. **6 of the 18 ASI-annotated recipes are on Modal** (basil_pesto, chicken_thighs, banana_muffins as `easy_banana_muffins` with DIFFERENT footage, korean_fried_chicken, steak_tacos partial, creamy_potato_soup new). The other 21 Modal recipes (salmon_pasta, coleslaw, etc.) aren't in our annotation set.
- Modal app: `experiments/offline_validation/modal_exp05_raft.py` — uses your existing `gdrive-oauth` secret + L4 GPU. Reuses `roughcut-ai/runpod/download_footage.py` for Drive pull.

### Brain vault
- `~/DevApps/Brain/Projects/ASI-Evolve/Strategy/*.md` — codex-approved through R6 in the prior session; strategy framework unchanged.
- **Added 2026-05-16:** `~/DevApps/Brain/Projects/ASI-Evolve/Motion Signal — Conditional Not Blanket.md` — finding doc that separates *peak-alignment-as-technique* (recipe-conditional, evidence in §1/§2) from *motion-phase-scoring-as-technique* (beat-type-conditional, evidence in §3, uses VLM categorical signal) from *RAFT-as-feature-source* (untested, hypothesis in Open Questions §1, smell test in §4). This supersedes any earlier "RAFT shelved" / "RAFT mooted" framing.
- Hot-pending items #1, #3 from prior handoff are still pending (§1.5 audio conflation, Strategy/Offline Experiment Plan.md). Item #2 (RAFT spec backfill) is **not mooted** — it's reframed as RAFT-as-feature-source for stratified categorical rules; the spec should now describe RAFT magnitude → threshold → categorical phase label feeding `motion_phase × beat_type`, not RAFT for peak-alignment.

---

## Coverage state

From `experiments/offline_validation/recipe_run_map.json` (re-run after creamy_potato_soup pull):

```
qualifying recipes: 6 / 18
qualifying ≥1s beats with DINO cache: 118
coverage tier: M6_A  (M6-A: 5 recipes / 60 beats — MET)
                     (M6-B: 10 recipes / 150 beats — NOT MET)
```

Motion_phase corpus is 7 (adds french_onion_mac which has scan.json but no dino_cache).

Of the 12 recipes still missing roughcut runs, only `creamy_potato_soup` had a Drive folder ID registered in `roughcut-ai/recipes_full.json`. The other 11 need IDs added before Modal can pull them.

---

## Codex review log

Plan: `~/.claude/plans/continue-from-handoff-users-dandj-devapp-polymorphic-blossom.md`. Approved at Round 3 (3 rounds total — caught a real off-by-0.5s peak-time bug + a coverage gate that was unreachable on the current cache state). Full audit trail in the plan file's "Codex Review Log" section. No additional codex rounds this session (didn't introduce new design decisions worth reviewing — the spikes followed the approved plan, the stratification + mogrt analyses were data-driven extensions).

---

## Git state at handoff

Branch: `refactor/writer-modules` (HEAD = `8ea74bc` from the prior session).

**Uncommitted changes:**
- Modified (carryover from before this session, not touched this session):
  - `CODEX.md`, `README.md`, `experiments/recipe_pipeline/prproj_dumps/{basil_pesto,chicken_thighs}_effects.json`, `experiments/recipe_pipeline/score_pipeline_output.py`, `experiments/recipe_pipeline/uxp_probe/{index.html, index.js, manifest.json}`
- Untracked (from this session):
  - `experiments/offline_validation/` ← all spike work
- Untracked (carryover from before):
  - Many files including `docs/asi-current-contract.md`, `docs/asi-pipeline-map.md`, `experiments/recipe_pipeline/{cached_recipes,frames,prproj_dumps,...}` — see `git status` for full list

**Suggested commit for this session's work:**
- `experiments/offline_validation/**` — the whole offline_validation spike
- Updated `docs/handoff.md` (this file)
- Possibly also the carryover `prproj_dumps/*.json` if those are wanted as commits

Don't commit before reviewing the dirty-files list — there are pre-session changes mixed in.

---

## Quick-start for next session

```bash
cd /Users/dandj/DevApps/ASI-Evolve

# Read the verdict first
cat experiments/offline_validation/runs/20260514T193913Z/verdict.md

# Optionally re-run the experiments (all idempotent, use cached curves):
.venv/bin/python3 experiments/offline_validation/preflight.py
.venv/bin/python3 experiments/offline_validation/exp02_dino_peaks_vs_dan_cuts.py
.venv/bin/python3 experiments/offline_validation/exp05_raft_subject_vs_camera.py
.venv/bin/python3 experiments/offline_validation/exp_motion_phase_vs_dan_cuts.py
.venv/bin/python3 experiments/offline_validation/exp_stratified_by_beat_type.py

# Inspect a sample motion_phase classification result on real data:
.venv/bin/python3 experiments/offline_validation/motion_phase_classifier.py
```

To kick off the editor-UX conversation Dan raised, the next session should start with the 3 open questions in the "blocker" section above. Until those are answered, don't try to push more auto-classification work — Dan needs to see the actual edit to provide ground truth.

---

## Things NOT to do next session

- Don't propose more **peak-alignment** experiments as a *global* scoring rule. The data killed the blanket-rule version on the current corpus (per-recipe deltas sign-flip; see [Motion Signal — Conditional Not Blanket](../../Brain/Projects/ASI-Evolve/Motion%20Signal%20—%20Conditional%20Not%20Blanket.md) §1).
- **Do not conflate "peak-alignment failed" with "RAFT failed."** Peak-alignment is the technique that's recipe-conditional; RAFT was just the tool feeding one variant of it. RAFT-as-feature-source for stratified categorical rules (e.g. RAFT magnitude → threshold → phase label feeding `motion_phase × beat_type`) is **unblocked work**, not blocked. Unblocking step: backfill RAFT curves for the 16 missing recipes via `run_exp05_modal.py` (existing infra; ~30-60 min L4 time).
- Don't try to auto-classify `(empty)` beat_types using VLM descriptions before talking with Dan about the editor UX. Dan explicitly said "the UX is broken" — programmatic labeling without his editorial input is exactly the thing that's been frustrating him.
- Don't touch the carryover dirty files. They predate this session.
- Don't touch the Brain vault — strategy framework is codex-approved and stable.

---

## Key context for future-you

- Dan has a **formula** for how he edits recipes that he hasn't articulated yet. The stratified beat_type finding is consistent with that formula being real (different rules for different beat moves). The right move is: build the UX that lets him articulate it against the visual evidence. The data will then have the labels needed to wire scoring rules.
- ~~The two clean findings (mogrt-hold + motion_phase-by-beat_type) are honest empirical results. They survived stratification and a real null. Don't lose them.~~ → **Updated 2026-05-16:** only `mogrt_minimum_hold` survives unchanged (no beat_type dependency). The `motion_phase_by_beat_type` finding is suspect — it was stratified on bare `beat_type` which collapses across editorial sub-variants with opposite motion signatures. Needs redo on `(canonical_move, sub_variant)`. See [Editorial Move Vocabulary — Canonical Moves and Sub-Variants](../../Brain/Projects/ASI-Evolve/Editorial%20Move%20Vocabulary%20—%20Canonical%20Moves%20and%20Sub-Variants.md).
- The "Dan cuts on motion peaks" framing was wrong at the global level — but motion DOES matter conditionally on beat intent. The pivot in this session was from "motion as global rule" to "motion as one signal interpreted differently per beat_type." That framing should carry forward.
- Modal RAFT pipeline is built and works. If a new motion-related hypothesis surfaces, the infrastructure is there.
- **Session 2026-05-16 follow-up:** the carry-forward framing above was clarified into a permanent finding doc. See [Motion Signal — Conditional Not Blanket](../../Brain/Projects/ASI-Evolve/Motion%20Signal%20—%20Conditional%20Not%20Blanket.md). It separates peak-alignment-as-technique (recipe-conditional, evidence in §1/§2) from RAFT-as-feature-source (untested as a blanket categorical signal, hypothesis in §Open Questions §1). A directional smell test on the existing N=42 RAFT data is recorded at `experiments/offline_validation/runs/20260516T092835Z/exp05_stratified_smell.md`.
