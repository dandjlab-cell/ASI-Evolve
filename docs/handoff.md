# ASI-Evolve Strategy Track — Session Handoff 2026-05-13/14

**Date:** 2026-05-14
**Branch:** `refactor/writer-modules` (no code changes this session — strategy track only)
**Last code commit:** `6f0247e` docs(asi): reframe phase 4 as polish-reduction; onboard Codex
**Role:** BUILDER (next session)
**Predecessor handoff:** none directly — the prior `handoff.md` (May 2 beauty-pick) was historical; this overwrites it.

---

## The project in one sentence

**ASI-Evolve is the scorer + harness layer that measures roughcut-ai pipeline output against Dan's editor reference style.** Recipe content (footage-driven bucket). Code repo: `/Users/dandj/DevApps/ASI-Evolve/`; canonical scoring file: `experiments/recipe_pipeline/score_rules.py`. Strategy hub: vault at `/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/`.

---

## What was done this session (strategy track only — zero code)

The session built out the complete strategy framework for adding new scoring dimensions, anchored on a specific bet: **adapt watershed techniques from speech synthesis, music generation, and music-to-dance generation to score the editorial rhythm of recipe edits.** The rhythm lives in the **visual signal** (motion peaks, action phases, camera settles, cut placements), not audio.

### Artifacts created in the vault

`/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/` (Obsidian vault):

- **`_Strategy.md`** — hub pointer at the project root (new)
- **`Editing Agent - Roadmap.md`** — pre-existing, **updated** for V-JEPA2 set-aside cleanup + new fitness framing
- **`Strategy/`** — entire folder is new, contains:
  - `Strategic Directive — Decomposed Cinematic Scoring.md` — verbatim directive + Amendment 01 + Corrections section (C1, C2, C3)
  - `Directive Crosswalk — Current Pipeline.md` — every directive dimension mapped to existing scorer rules + gaps + per-dimension portability table + Borrowed-technique column with slugs (codex R4–R6 refined)
  - `Next Steps — Prioritized Mutations.md` — what to build, in what order; 5 gate categories (Always-on / Schema-contract-gated / Commercially-gated / Threshold-gated / Off-the-shelf-spike-gated); **Watershed-Technique Wire-Through (Layers 1–3)** section defining canonical slugs + Layer 2 emitted-data schema + Layer 3 calibration linkage
  - `Reconciliation — Directive vs Editing Agent Roadmap.md` — multi-track strategy stack; 6 codex review rounds logged with full audit trail
  - `Adjacent-Field Techniques — What We're Borrowing.md` — six watershed techniques mapped to scoring dimensions; back-pointer table; codex R4+R5 corrections folded
  - `External Input — 2026-05-11 ChatGPT Editor Stack Triage.md` — triage of an external ChatGPT "Editing AI model stack" proposal (4 KEEP + 4 REJECT + ~7 duplicative)
  - `Business Strategy Frame — Why This Technical Bet Matters.md` — connects technical strategy to Path A business strategy (Adobe 36-month window, manifesto, content type buckets)
  - `References/` — 9 paper / lineage notes:
    - `Learning to Cut by Watching Movies (Pardo 2021).md`
    - `MovieCuts (Pardo 2022).md` (with codex R3+R5 corrections re: recipe vs MovieCuts Match Cut)
    - `ESA — Energy-Based Shot Assembly (2025).md`
    - `REMI — Pop Music Transformer (Huang & Yang 2020).md`
    - `MotionBeat (2025).md` (with codex R1 verification of Soft-DTW)
    - `Music-to-Dance — EDGE Bailando FACT.md`
    - `Netflix Match Cutting (2022).md`
    - `Speech Synthesis — Prosody Decomposition Lineage.md` (new lineage note)
    - `Music Generation — Breakthrough Lineage Beyond REMI.md` (new lineage note)

### User memory entries created/updated (`~/.claude/projects/-Users-dandj-DevApps-ASI-Evolve/memory/`)

- `MEMORY.md` — index updated with 2 new entries
- `project_vjepa2_dropped.md` — V-JEPA2 set-aside decision (2026-05-11)
- `feedback_external_research_triage.md` — process discipline for handling external research

### Codex review rounds (6 total this session)

| Round | Verdict | Findings | Where logged |
|---|---|---|---|
| R1 | APPROVED | 5 MEDIUM + 5 LOW (paper accuracy, V-JEPA2 alignment) | `Reconciliation` note |
| R2 | APPROVED | 5 MEDIUM + 5 LOW (V-JEPA2 cleanup, MovieCuts taxonomy) | `Reconciliation` note |
| R3 | APPROVED | 4 MEDIUM + 3 LOW (business-frame incorporation, bucket-portability) | `Reconciliation` note |
| R4 | **NOT APPROVED → APPROVED** | 1 HIGH (EDGE/FACT citation error) + 5 MEDIUM + 4 LOW | `Reconciliation` note |
| R5 | **NOT APPROVED → APPROVED** | 1 HIGH (stale body text contradicting corrected table) + 4 MEDIUM + 4 LOW | `Reconciliation` note |
| R6 | APPROVED | 0 unresolved CRITICAL/HIGH/MEDIUM/LOW | `Reconciliation` note |

---

## Current state

**Strategy documentation: complete and codex-approved through R6.**

**Code implementation: NOT started.** Zero changes to `score_rules.py` or any other file in the ASI-Evolve code repo this session.

**Roughcut state (referenced, not modified):** v16 is the latest branch (`feat/recipe-pipeline-v16-modal` at `8a3ebfe` in the worktree `roughcut-ai/.claude/worktrees/v16-smoke/` or `.claude/worktrees/continue-from-handoff-atomic-snail/`). Five PRs merged: pair_verification module (PR2), Drive registry (PR3), pair_verification→Phase 1 (PR4), `NO_AUDIO_FAIL_CLOSED_FLOOR = 0.10` calibration (PR5). V15 frozen as rollback. **Dan is currently resolving v16 audio sync issues** — v16 is the active dev branch but pairs.json files in `runs/{recipe}/` are still v15-shape (no `pass_a0_status` field yet).

**The 12 "shot-first" polish-reduction plans** (shot-first-body-file-fence, shot-first-non-action-classifier, beauty-picker-vlm-floor, etc.) are **in design, not in v16 yet.** They're on top of v16, in design notes that the user mentioned but I haven't read directly.

---

## Key decisions made (the "why" that context windows forget)

| Decision | Reasoning |
|---|---|
| **V-JEPA2 set aside entirely** (not "v3 supplemental") | Heavy compute + unproven value + conflicts with directive's explicit-metrical-grid thesis. Triple-validated: ASI directive Constraint #4 + codex reviews + roughcut's own `docs/plans/vjepa2-watch.md` + `~/DevApps/Brain/Knowledge/VLM/V-JEPA2 Applicability for Recipe Pipeline.md` atomic lesson. Revisit conditions documented in `Reconciliation` Tension 1. |
| **Bailando is a PRINCIPLE, not an audio technique** | Late-session correction. Bailando's watershed contribution is "explicit beat-alignment objective beats implicit discovery." Modality-agnostic. For recipes, the "beat" is a visual event (motion peak / action transition / camera settle / cut placement), not an audio onset. This corrects earlier framing where `bailando_beat_align` was locked to §1.5 audio onset alignment. |
| **The rhythm lives in the visual signal for recipe content** | Recipe audio = ambient kitchen + sparse dialogue. No music. The editorial rhythm exists in DINO distance peaks, action phases, camera settles, cut placements — all signals already cached by roughcut today. Audio onset alignment (§1.5) is bucket-portable but **deprioritized for recipes**. |
| **§1.5 audio rhythm gating should NOT use v16's `pass_a0_status`** | Separate problems. v16's `pass_a0_status` = camera A↔B sync state. Bailando audio-onset = "is there rhythmic audio to score against." Conflation that needs fixing in the Next Steps + Layer 2 schema documentation. **PENDING — not yet corrected in the vault notes.** See "Hot pending items" below. |
| **Path A defense window: 36 months from 2026 → 2029** | Per `Future of AI Editing — Big Picture 2026-05-06.md`. Adobe MAX 2026 (Oct 2026) ships "Your Style v1" (horizontal). v2 (per-show, 2027) + v3 (house-corpus, 2028-2029) progressively close the gap. The 40%→85% vertical-depth gap is "the entire game." |
| **Boardroom Agreement #54: ship at 80%, not 95%** | Per `The Edit Never Ends Manifesto`. Pace behind commercial validation, not in parallel. v2 scoring spine ships against current roughcut output; calibration re-tunes as roughcut PRs land. |
| **Watershed wire-through Layer 2 emitted-data schema** | Every scoring rule output carries `borrowed_technique`, `basis_technique`, `adaptation_role`, `source_type`, `paper`, `paper_note`, `implementation`, `calibration` fields. Polish-gradient report groups deltas by `borrowed_technique` slug so "is the X bet paying off" is answerable from data, not analogy. |
| **RAFT is set up (Dan stated) and unlocks subject-vs-camera motion disentanglement** | The biggest single win RAFT offers is `subject_motion_magnitude` (residual after camera-motion removal). Cleaner peaks for action-phase scoring than DINO distance alone. Spec'd in the final messages of this session. |
| **Test concepts as offline notebook experiments BEFORE wiring code** | The directive's "diff-based learning" principle says train on AI-vs-Dan deltas. Apply that to OUR strategy: test each watershed-borrowed technique as a notebook experiment against cached data + Dan's 18 annotated recipes BEFORE writing the scoring rule. If the bet doesn't show up in data, don't ship the code. |

---

## What's next — RUN OFFLINE EXPERIMENTS BEFORE WRITING CODE

The user's last direction: **validate watershed-borrowed techniques as offline notebook experiments BEFORE committing to wiring them into `score_rules.py`.** Each experiment uses already-cached roughcut data + Dan's 18 annotated recipes. Zero pipeline runs needed.

### Highest-value experiments (priority order)

#### Experiment #2 — DINO peaks vs Dan cuts (single most load-bearing)

Test whether Dan's cuts cluster near DINO cosine-distance peaks more often than random.

- Load `~/DevApps/roughcut-ai/runs/{recipe}/dino_cache.json` for each of the 18 annotated recipes
- Run `scipy.signal.find_peaks` on the DINO distance array
- Load Dan's cut times from the corresponding annotation in `experiments/recipe_pipeline/annotations/{recipe}.json`
- Histogram of `min(|cut - peak|)` for Dan's cuts vs the same metric on randomly-placed cuts
- **Pass condition:** Dan's cuts have a statistically significant tighter alignment to DINO peaks than random
- **If passes:** §1.6 motion-peak alignment + §1.7 visual rest + action-phase scoring all gain empirical justification. Bailando-principle with DINO as signal source is validated.
- **If fails:** Need RAFT for sharper signal (see Experiment #5) OR rhythm isn't where I think it is.

#### Experiment #5 — RAFT subject-vs-camera disentanglement

Since RAFT is already set up, validate the "biggest single win" claim.

- Run RAFT on 2-3 recipe video clips (basil_pesto, chicken_thighs are well-annotated)
- Per-frame outputs: `flow_magnitude`, `flow_direction`, `camera_motion.translation`, `subject_motion_magnitude`
- Compare `subject_motion_magnitude` peaks against Dan's cut times — same histogram as Experiment #2
- **Pass condition:** RAFT's `subject_motion_magnitude` has sharper / more aligned peaks than DINO distance
- **If passes:** RAFT is worth caching as `raft_cache.json` per recipe; ASI consumes the residual-subject-motion peak signal for action-phase scoring
- **If fails:** DINO is good enough; RAFT adds nothing for v2

**These two run in parallel.** Half-day each, max. Both use cached data + already-set-up tools.

### Subsequent experiments (after the load-bearing two pass)

| # | Experiment | What it tests |
|---|---|---|
| 1 | Pacing curve correlation signal test | Do Dan-recipes correlate with each other more than with shuffles? |
| 3 | Soft-DTW vs Euclidean on cut-frequency curves | Empirical validation of MotionBeat's loss choice |
| 8 | Pareto frontier visualization | Plot Phase 4 fitness gradient outputs in 2D dimension-pair space |
| 4 | Bailando soft-σ on Whisper utterance starts | Does Dan cluster cuts near speech segments? Cheap proxy for §1.5 |
| 6 | Dan Discriminator feasibility | sklearn LogReg on cached DINO embeddings, AUC > 0.7 target |
| 7 | Manual MovieCuts taxonomy labeling | 50 transitions × 3 recipes, build Dan's target distribution |
| 9 | Operator-dimension dry-run | Load manifest, apply `shot_extend()`, recompute ASL match, validate Amendment 01 §1 |

Each is a notebook-shaped Python experiment, no pipeline required.

### After experiments pass (only then write code)

1. **Step 0** in `score_rules.py` — add `_validate_rule_output()` enforcing Layer 2 schema (`borrowed_technique`, `paper`, `paper_note`, `implementation`, `calibration`, etc.); backfill legacy 7 rules with `recipe_specific` slug; switch to all-rules enforcement when `LEGACY_RULE_IDS` exhausted. Per Watershed Wire-Through section of `Next Steps — Prioritized Mutations.md`.
2. **§1.1 ASL match** + **§1.2 Duration variance** — `fastspeech2_variance_adaptor` scalar predictors, ~1 hour total
3. **§1.4 Cut frequency curve** — `tslearn.metrics.soft_dtw`, `motionbeat_soft_dtw` slug
4. **§1.6 + §1.7 + Action-phase alignment** — consume `dino_cache.json` + `classify_broll.py` output; `bailando_beat_align` slug for alignment-scoring stage, `motionbeat_pulse_extraction` for feature stage
5. **§1.3 Pacing curve** — `fact_future_n_supervision` slug; Pearson + Spearman over N-shot resampled series

---

## Hot pending items (not yet fixed in the vault)

These were surfaced near end-of-session but **NOT yet folded into the strategy notes.** Next session should land them before starting experiments OR document them as deliberate deferred-to-experiments items.

1. **§1.5 + Layer 2 schema have a stale `audio_state ← pass_a0_status` conflation.** I added this mid-session; the conflation is: v16's `pass_a0_status` indicates camera A↔B sync state (whether we can trust the manifest timeline), NOT whether there's rhythmic audio to score against. These are different upstream signals. **Fix:** remove `audio_state` field from Layer 2 schema; demote §1.5 to "bucket-portable, recipe-deprioritized"; apply `bailando_beat_align` slug to the *visual-rhythm* dimensions (§1.6, §1.7, action-phase) — not just §1.5. This is documented in the codex log conceptually but the actual schema/text edit DIDN'T LAND in `Next Steps — Prioritized Mutations.md` or the Crosswalk. 

2. **RAFT spec lives only in conversation context** — the per-frame schema (`flow_magnitude`, `flow_direction`, `camera_motion`, `subject_motion_magnitude`) was specified in the last messages but **NOT written into `Next Steps — Prioritized Mutations.md` or the Crosswalk**. Should be added when revising §1.6 + action-phase to consume RAFT output. Maps to slug `pretrained_floor:raft`. Either land in the strategy notes OR start with experiments and document RAFT post-validation.

3. **The 9 offline experiments are NOT yet captured in a Strategy note.** They live only in conversation context. Worth a dedicated `Strategy/Offline Experiment Plan.md` note before starting (or track in the experiment notebooks themselves).

### Process discipline learning (from codex R5)

**When correcting a summary table or section header, sweep the body sections of the same document for the same terms.** I caught this twice mid-session — codex flagged stale body text after I fixed the summary table. Saved as memory `feedback_external_research_triage.md` but the pattern itself ("table-vs-body drift") worth surfacing here too.

---

## Known issues / watch-outs

### Coordination with roughcut

- v16 is still being shaken out for audio sync (Dan's words)
- The 12 polish-reduction plans (`shot-first-*`, `beauty-picker-*`, etc.) are on top of v16, in design — they will land progressively and richer roughcut output will arrive; **the offline experiments do not depend on this** but the eventual scoring rule calibrations will re-tune as v16 audio + polish-reduction settles
- v15 is frozen as rollback target

### Things NOT to do

- Don't propose V-JEPA2 work. Triple-validated set-aside.
- Don't conflate Bailando with audio. It's the alignment principle, modality-agnostic.
- Don't write code in `score_rules.py` before running the offline experiments. The experiments validate whether the watershed bets are real before we commit to wiring them.
- Don't fix the random pre-session dirty files in `ASI-Evolve/` (CODEX.md, README.md, score_pipeline_output.py changes, etc.). They're not from this session.
- Don't touch the Brain vault's unrelated dirty files (Renewed Homes, NQ AI Sidekick, Daily/, etc.).

---

## Key files to read FIRST (priority order for next session)

1. **`~/DevApps/Brain/Projects/ASI-Evolve/_Strategy.md`** — hub pointer; lists all strategy notes with one-line descriptions
2. **`~/DevApps/Brain/Projects/ASI-Evolve/Strategy/Business Strategy Frame — Why This Technical Bet Matters.md`** — frames *why* the technical bet matters (Path A, Adobe window, boardroom discipline)
3. **`~/DevApps/Brain/Projects/ASI-Evolve/Strategy/Strategic Directive — Decomposed Cinematic Scoring.md`** — the verbatim directive + Amendment 01 + Corrections section
4. **`~/DevApps/Brain/Projects/ASI-Evolve/Strategy/Adjacent-Field Techniques — What We're Borrowing.md`** — six watershed techniques (REMI / FastSpeech 2 / Bailando / MotionBeat / FACT / EDGE) mapped to scoring dimensions; back-pointer table
5. **`~/DevApps/Brain/Projects/ASI-Evolve/Strategy/Next Steps — Prioritized Mutations.md`** — the Watershed-Technique Wire-Through (Layers 1–3) section + §1.1–§1.7 spec + the boardroom-discipline gates
6. **`~/DevApps/Brain/Projects/ASI-Evolve/Strategy/Directive Crosswalk — Current Pipeline.md`** — every dimension's borrowed-technique slug + paired operator + bucket-portability
7. **`~/DevApps/Brain/Projects/ASI-Evolve/Strategy/Reconciliation — Directive vs Editing Agent Roadmap.md`** — full 6-round codex audit trail at the bottom
8. **`~/DevApps/ASI-Evolve/experiments/recipe_pipeline/score_rules.py`** — current 7-rule scorer (will get Step 0 added later)
9. **`~/DevApps/ASI-Evolve/CODEX.md`** line 146 — institutional knowledge that already identified `motion_phase` consumption as the right action-boundary fix
10. **`~/DevApps/roughcut-ai/runs/{recipe}/dino_cache.json`** — sample structure for experiment #2

---

## Quick Start for next session

```bash
# Read the strategy hub first
cat "/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/_Strategy.md"

# Then start Experiment #2 + #5 in parallel.
# Experiment #2: DINO peaks vs Dan cuts
cd /Users/dandj/DevApps/ASI-Evolve
mkdir -p experiments/offline_validation

# Inspect dino_cache.json schema for a known-annotated recipe:
python3 -c "import json; d=json.load(open('/Users/dandj/DevApps/roughcut-ai/runs/basil_pesto/dino_cache.json')); print(list(d.keys())[:5])"

# Verify annotation file exists for that recipe:
ls /Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline/annotations/basil_pesto*.json

# Then build:
# experiments/offline_validation/exp02_dino_peaks_vs_dan_cuts.ipynb (or .py)
#   - load dino_cache.json for 3 recipes (basil_pesto, chicken_thighs, korean_fried_chicken)
#   - scipy.signal.find_peaks on cosine distance array
#   - load Dan's cut times from annotations/{recipe}.json
#   - histogram of min(|cut - peak|) for Dan's cuts vs random baseline
#   - report whether Dan-cuts-near-peaks is statistically significant (KS test or t-test)

# Experiment #5: RAFT subject-vs-camera (requires RAFT setup, which Dan stated is done)
# experiments/offline_validation/exp05_raft_subject_vs_camera.ipynb (or .py)
#   - run RAFT on 1-2 recipes' source video
#   - extract per-frame: flow_magnitude, flow_direction, camera_motion, subject_motion_magnitude
#   - compare subject_motion_magnitude peaks vs DINO peaks vs Dan's cut times
```

Before writing experiments: **read 4 + 5** (Adjacent-Field Techniques + Next Steps Watershed Wire-Through section) from the priority list above. They define what the experiments are testing.

After experiments pass: ship Step 0 + the v1/v2 cheap-wire scoring spine. All slugs and implementation choices already documented.

---

## Watch-out: credentials / external state

- No new credentials needed for this work
- ASI reads from `~/DevApps/roughcut-ai/runs/{recipe}/` — cross-repo file reads (existing pattern in `score_pipeline_output.py`)
- Brain vault is at `~/DevApps/Brain/` — separate git repo with many unrelated dirty files; DO NOT touch anything outside `Projects/ASI-Evolve/`
- **RAFT model weights / invocation: location uncertain.** Dan stated "we have RAFT set up" in conversation. **Pre-handoff grep across `~/DevApps/ASI-Evolve/` and `~/DevApps/roughcut-ai/tools/` + `docs/` for `raft|RAFT` returned only false-positive substring matches** (in words like "draft", "crafting"). No standalone RAFT module found. **Next session must ask Dan first** — possible locations to check: a separate repo (e.g., `~/DevApps/raft/` or similar), an unpushed branch, a conda env, or a Modal/Runpod-side setup not in the local checkouts. Do NOT assume it's wired before confirming.

## Annotation file schema (for Experiment #2)

Sample: `~/DevApps/ASI-Evolve/experiments/recipe_pipeline/annotations/basil_pesto.json`

Top-level keys: `recipe`, `global_notes`, `source_narrative`, `beats`

Per-beat keys (relevant for experiments):
- `beat_index` — int, sequential
- `beat_type` — string (e.g. `ingredient`, `beauty_opener`, `title_card`, `technique`, `beauty`, `stop_motion`, `beauty_close`)
- `recipe_section` — string
- `filename` — source clip filename (maps to roughcut source files)
- `in_point` — start time within source file (seconds)
- `duration` — beat duration (seconds)
- `out_point` — `in_point + duration`
- `camera` — `front` / `overhead` / `unknown`
- `verdict`, `confidence` — Dan's editorial judgment annotations
- `effects`, `nested`, `mogrt_overlaps` — overlay / nest metadata

For Experiment #2 ("Dan's cuts"): each beat boundary is effectively a cut. The cumulative timeline position of each cut = sum of prior beat durations. Map to the corresponding DINO-cache time index per `filename`.

## Offline experiments — strategy-note status

**The 9 offline experiments (described in detail in §"What's next" above) are NOT yet captured as a dedicated Strategy/ note.** They live only in this handoff and the prior conversation context. Recommendation for next session, in order of preference:

1. **Create `~/DevApps/Brain/Projects/ASI-Evolve/Strategy/Offline Experiment Plan.md`** before starting — consolidate all 9 experiments with hypothesis + pass condition + downstream impact + cached-data paths. ~20 min to write.
2. **OR** track each experiment's hypothesis + pass condition inline in the notebook header — acceptable for a single-session iteration but harder to revisit.

Either works; option 1 is more durable.

---

## Where data outputs live

- Strategy notes: `~/DevApps/Brain/Projects/ASI-Evolve/Strategy/` (8 notes + 9 references)
- Hub pointer: `~/DevApps/Brain/Projects/ASI-Evolve/_Strategy.md`
- Code scoring rules: `~/DevApps/ASI-Evolve/experiments/recipe_pipeline/score_rules.py`
- Dan's annotations: `~/DevApps/ASI-Evolve/experiments/recipe_pipeline/annotations/{recipe}.json`
- Roughcut artifacts: `~/DevApps/roughcut-ai/runs/{recipe}/{dino_cache,scan,pairs,audio_cues,manifest}.json`
- Roughcut v16 worktrees: `~/DevApps/roughcut-ai/.claude/worktrees/v16-smoke/` and `.../continue-from-handoff-atomic-snail/`
- User memory: `~/.claude/projects/-Users-dandj-DevApps-ASI-Evolve/memory/MEMORY.md` (+ supporting files)
- New experiments target: `~/DevApps/ASI-Evolve/experiments/offline_validation/` (folder to be created)
