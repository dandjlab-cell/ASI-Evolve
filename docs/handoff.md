# ASI-Evolve — Session Handoff 2026-05-16 → 2026-05-18

**Date:** 2026-05-18
**Branch:** `refactor/writer-modules`
**Last commit (this repo):** `9472167` feat(asi): editorial vocabulary correction + RAFT signed-delta smell tests
**Last commit (Brain vault):** `a2d18fe` asi-evolve: editorial vocabulary + motion-signal supersedure notes
**Role:** BUILDER

---

## Project in one line

ASI-Evolve = scorer + harness measuring roughcut-ai pipeline output against Dan's editor reference style for recipe content. Strategy hub: `~/DevApps/Brain/Projects/ASI-Evolve/`.

---

## ⚠️ READ FIRST — the editorial vocabulary now exists

The thing that blocked everything previously (bare `beat_type` was too coarse, mid-edit/late-edit were annotator placeholders) is now resolved. The canonical reference is:

→ **[Editorial Move Vocabulary — Canonical Moves and Sub-Variants](../../Brain/Projects/ASI-Evolve/Editorial%20Move%20Vocabulary%20—%20Canonical%20Moves%20and%20Sub-Variants.md)**

Final taxonomy (codex-approved across 5 rounds; locked):

| Supertype | Sub-variants | Notes |
|---|---|---|
| **Beauty** | moment / take / placement / framing | Absorbs the former `plating` supertype as the `plating-assembly` moment. `beauty_opener` + `beauty_close` are the SAME supertype at different `placement` values. |
| **Ingredient dump** | V1_action / V2_appear | Confirmed by N=42 RAFT data. V1 = cut-to-action (71% peak-present). V2 = stop-motion-vibe / appear-in-bowl (14%). |
| **Active Cooking** | `prep` / `transformative` / `instruction` (with `needs_mogrt: bool` axis) / `tips` / `timing-marker` (with `on_frame: bool` + `destination` axis: oven, fridge, drain, etc.) | Renamed from `technique`. Absorbs former `prep` and `transformation` supertypes. |
| **Money shot** | (none in v1, rare) | Standalone, content-based, can land anywhere. Distinct from Beauty. |

**Dead supertypes** (do NOT surface in any UI / scoring): `plating / finishing`, `prep / knife work`, `technique / active cooking` (renamed), `transformation`. **Placeholders** (NOT editorial moves): `mid-edit`, `late-edit (likely transformation or money shots)` — these are annotator placeholder buckets, 74 of 329 untyped beats.

---

## What was done this session (2026-05-16 → 2026-05-18)

1. **Built smell-test scripts** on N=42 RAFT cache (basil_pesto + chicken_thighs). Discovered the ingredient_dump V1/V2 split that broke the bare-beat_type stratification.
2. **Established the 4-supertype taxonomy** through 5 iterative codex-approved rounds. Wrote the canonical vault note (`Editorial Move Vocabulary — Canonical Moves and Sub-Variants.md`).
3. **Flagged prior findings as suspect** — every `beat_type`-stratified result needs redo on `(supertype, sub_variant)`. The `mogrt_minimum_hold` finding (no beat_type dependency) is the only Layer-2-ready scoring rule that survives.
4. **Rewrote the Beat Review UI plan body** to match the new taxonomy (v2; codex-approved at Round 2). Plan file: `~/.claude/plans/asi-evolve-handoff-written-misty-clock.md`.
5. **Built two HTML explainers** at `docs/strategy-explainer.html` (editorial) and `docs/strategy-map.html` (interactive node graph).
6. **Committed both repos.** ASI-Evolve at `9472167`. Brain at `a2d18fe` (just the 2 ASI-related vault notes; 8 unrelated dirty files in Brain were not touched).

---

## Current state

| Component | Status |
|---|---|
| Editorial vocabulary | **v1 locked, codex-approved 5 rounds.** All 4 supertypes defined with sub-variants. |
| Beat Review UI plan | **v2 body, codex-approved Round 2.** Mockups, sidecar schema, verification plan all match the 4-supertype taxonomy. |
| Beat Review UI implementation | **NOT STARTED.** All implementation tasks (#3-#10 in the task list) are blocked on someone (you / next session) running `preflight.py` and building `server.py`. |
| `preflight.py` Step 4 (`beat_index.json`) | **WORKING.** Verified output: 18 recipes, 618 beats, 289 typed, 329 untyped. Does NOT require `/Volumes` mount. |
| `preflight.py` Steps 1-3 (mount/map/extract) | **STUBBED** with `NotImplementedError`. Needs `/Volumes/2TB Footage` mounted and ffmpeg slice extraction. |
| RAFT curves | Only 2 of 18 recipes (`basil_pesto`, `chicken_thighs`). Backfill prompt for the roughcut team is drafted but **not sent** (lives in this session's chat history; not in a doc). |
| Layer 2 scoring rules | None wired. Blocked on labels. `mogrt_minimum_hold` is the only one ready to wire and it's still pending the Step 0 scoring-loop restructure (Amendment 01 step #1). |

---

## Key files changed this session (committed)

| File | What changed |
|---|---|
| `experiments/offline_validation/exp05_stratified_smell_test.py` | New: stratified RAFT by beat_type (initial smell test) |
| `experiments/offline_validation/exp05_signed_delta_test.py` | New: cut-out signed-delta test (71% after peak overall) |
| `experiments/offline_validation/exp05_in_vs_out_signed_test.py` | New: cut-IN vs cut-OUT signed-delta. **Surfaced the ingredient V1/V2 split** by exposing per-beat data |
| `experiments/offline_validation/runs/20260516T0{92835,102614,103040}Z/` | New: smell-test outputs (3 dirs, JSON + MD) |
| `experiments/offline_validation/runs/20260514T193913Z/verdict.md` | Modified: appended framing-correction addendum |
| `experiments/review_ui/preflight.py` | New: Step 4 working; Steps 1-3 stubbed |
| `docs/handoff.md` | This file |
| `docs/strategy-explainer.html` | New: editorial strategy walkthrough |
| `docs/strategy-map.html` | New: interactive system map |
| `Brain/Projects/ASI-Evolve/Editorial Move Vocabulary — Canonical Moves and Sub-Variants.md` | New (committed to Brain repo) |
| `Brain/Projects/ASI-Evolve/Motion Signal — Conditional Not Blanket.md` | New (committed to Brain repo) |
| `~/.claude/plans/asi-evolve-handoff-written-misty-clock.md` | v2 rewrite (not in either git repo — Claude harness file) |

---

## Decisions made (the "why" that context windows forget)

| Decision | Reasoning |
|---|---|
| Bare `beat_type` is too coarse; replace with `(supertype, sub_variant, axes)` | The N=42 RAFT data showed `ingredient_dump` had two opposite-direction sub-variants (V1 71% peak vs V2 14%). Any beat_type-stratified analysis collapsed them to noise. The motion_phase × beat_type "clean finding" in verdict.md is suspect for the same reason. |
| `plating`, `prep`, `transformation` collapse into other supertypes | Dan said so directly. Plating is part of Beauty (`plating-assembly` moment). Prep + transformation are sub-variants of Active Cooking. Reduces the canonical-move count from 7 to 4. |
| Money shot stays separate from Beauty | Dan: "if it's a delicious process moment, it would be in the beginning but wouldn't consider it part of beauty. It's rare and not every recipe will have it." Beauty is positional; Money shot is content. |
| `mid-edit` / `late-edit` are annotator placeholders, NOT editorial moves | Direct data check: 100% `verdict: added`, 97-98% untyped, beat_descriptions are bare clip references like `AI2I4277.mov @ 369.5s`. Annotator hedged because LLM didn't know what to call them. |
| Default UI policy: manual moment tagging | Dan confirmed during the (moment, take, placement) discussion. Auto-clustering V1/V2 takes deferred to v2. |
| `supertype_guess` regex-derived in beat_index.json | Pre-fills the UI's supertype picker from `recipe_section` text. Order matters: placeholder check first, then `money shot` (word-boundary), then `beauty/plating/finishing`, then `ingredient`, then `technique/prep/knife/active cook/transform`. Full Python code block in plan §Step 4. |
| Don't conflate "peak-alignment failed" with "RAFT failed" | Peak-alignment is the technique (recipe-conditional, dead as a global rule). RAFT-as-feature-source for stratified categorical rules is untested but unblocked. See `Motion Signal — Conditional Not Blanket.md` for the framing. |

---

## What's next — prioritized

**P0 — start here next session:**

1. **Decide the next move.** Three viable paths:
   - **(a) Build the Beat Review UI** (tasks #3-#10) per the v2 plan. Unblocks Dan labeling at scale → unblocks Layer 2 scoring. Largest scope (~1-2 days).
   - **(b) Hand off the RAFT-16-recipes backfill prompt** to the roughcut team. ~10 min to copy-paste; runs in parallel. The prompt lives only in this session's chat history — would need to be re-drafted from the Editorial Move Vocabulary note. *Note: roughcut already has `motion_phase` from fast_scan.py; the RAFT backfill is for continuous magnitude curves that complement the VLM categorical signal.*
   - **(c) Inventory `Money_shot` sub-variants** if any exist beyond the single bucket. Read-only, ~30 min. Dan flagged this as potentially unnecessary (rare, only 3 recipes).

**P1 — after the UI is up:**

2. Run `preflight.py --map-only` (needs `/Volumes/2TB Footage` mounted) to build `recipe_export_map.json` for all 18 slugs.
3. Run `preflight.py --extract` to pre-encode 618 beat slices (~10-25 min ffmpeg).
4. Launch the UI: `uvicorn experiments.review_ui.server:app --reload --port 8765`.
5. Dan labels the 74 placeholder beats first (queue them first; they have the clearest "needs classification" signal).

**P2 — once ~50 beats are re-labeled:**

6. Run `merge_sidecars.py --apply` to fold labels back into source annotations.
7. Adapt `exp_stratified_by_beat_type.py` to read `(supertype, sub_variant)` instead of bare `beat_type`. Re-run on the larger labeled corpus.
8. Wire `motion_phase × (supertype, sub_variant)` scoring rule into `score_rules.py` (Amendment 01 step #1: operator-dimension pairing).

---

## Known issues / gotchas

- **`/Volumes/2TB Footage` mount status varies.** The volume was mounted as of 2026-05-16 afternoon. The Beat Review UI preflight Step 1 hard-fails if missing. UI cannot extract beat slices without it.
- **`camera_mapping.json` prefix-rule bug:** `chicken_thighs` B19I6669 clips labeled `camera: front` by the prefix cache, but `recipe_section` says "overhead bowl". Trust `recipe_section` text over the prefix-derived label. Per the memory rule (`feedback_camera_detection_per_recipe.md`): never use a global filename-prefix rule for camera.
- **Brain vault has 8 unrelated dirty files** (other projects' WIP). Don't bulk-commit Brain — only the 2 ASI notes committed in `a2d18fe`. Use specific paths.
- **Codex CLI hits transient SSL errors** under flaky network. Retry once; usually succeeds on retry.
- **Plan file at `~/.claude/plans/asi-evolve-handoff-written-misty-clock.md`** is NOT in any git repo. It's preserved by the Claude harness. If Claude shuts down without saving, that file is lost. The top warning callout + body v2 + 5 codex-review rounds all live there.
- **Per-recipe peak-alignment variance findings are suspect** because recipes have different sub-variant mixes. See `Motion Signal — Conditional Not Blanket.md` superseded callout.

---

## Quick start for next session

```bash
cd /Users/dandj/DevApps/ASI-Evolve
git log --oneline -5
cat docs/handoff.md  # this file

# Read the canonical taxonomy reference
cat "/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/Editorial Move Vocabulary — Canonical Moves and Sub-Variants.md"

# Read the plan body v2
cat ~/.claude/plans/asi-evolve-handoff-written-misty-clock.md

# Verify Step 4 of preflight still works (no /Volumes needed)
.venv/bin/python3 experiments/review_ui/preflight.py --index-only
# expected: [index] wrote .../beat_index.json — 18 recipes, 618 beats (289 typed, 329 untyped)
```

If proceeding with **path (a) — build the UI** — start by creating `experiments/review_ui/server.py` (FastAPI). The plan body's "Files to create" table + "Sidecar storage model" + "Mockup 2 variants A-G" are the implementation reference. The Python regex code block in plan §Step 4 (`GUESS_RULES`) implements `supertype_guess` and has a canonical test matrix you can lift directly into tests.

---

## External references

- **Strategy hub:** `~/DevApps/Brain/Projects/ASI-Evolve/`
  - `Editorial Move Vocabulary — Canonical Moves and Sub-Variants.md` — **canonical taxonomy reference; read end-to-end before any UI / scoring work**
  - `Motion Signal — Conditional Not Blanket.md` — technique-vs-tool framing; supersedure callout on beat_type-stratified findings
  - `Strategy/Strategic Directive — Decomposed Cinematic Scoring.md` — the watershed thesis (voice synth + music gen decomposition pattern applied to editing)
  - `Strategy/Next Steps — Prioritized Mutations.md` — Amendment 01 sequencing; Watershed-Technique Wire-Through discipline
- **Plan file:** `~/.claude/plans/asi-evolve-handoff-written-misty-clock.md` (v2 body, codex-approved Round 2)
- **Verdict + addendum:** `experiments/offline_validation/runs/20260514T193913Z/verdict.md` (the 2026-05-14 spike verdict, with a 2026-05-16 framing-correction addendum at the bottom)
- **Smell-test outputs:** `experiments/offline_validation/runs/20260516T0*/` (this session's N=42 work)
- **Modal volumes:** `asi-exp05` (27 RAFT curves), `roughcut-artifacts` (27 recipes; 6 overlap with our 18)
- **Roughcut take pipeline** (different problem, not directly reusable): `roughcut-ai/tools/nbq/` — built for dialogue/host content (ep110, ep602). Visual scoring (`score_visuals.py`) and the per-take scoring math may be adaptable, but the script-alignment + speaker-role classification doesn't apply to silent recipe footage.

---

## Credentials / external setup required

- **Modal:** `gdrive-oauth` secret already set up (used by `modal_exp05_raft.py` for Drive pulls). Just need `modal token` valid for the user.
- **`/Volumes/2TB Footage` mount:** SMB share at `smb://<server>/2TB%20Footage`. Mount via Finder ⌘K or `open smb://...`. The exact server hostname is in the Mac's Keychain.
- **No API keys** required for ASI-Evolve itself. The Codex CLI needs `~/.codex/auth.json` (already provisioned) and `~/.claude/settings.json` global permissions for `Bash(codex exec*)`, `Bash(codex review*)`, `Bash(codex --version*)`.
- **Python env:** `.venv` in repo root, Python 3.x. Dependencies for the Review UI (per plan): `fastapi`, `uvicorn[standard]`, plus system `ffmpeg` and `ffprobe`.

---

## Data outputs — where they live

| Output | Path |
|---|---|
| Annotation source files | `experiments/recipe_pipeline/annotations/{recipe}.json` (18 files, 882K) |
| Sidecar review labels (after Review UI launches) | `experiments/recipe_pipeline/annotations/{recipe}.review.json` (schema v2, one per recipe) |
| RAFT curves (cached) | `experiments/offline_validation/.cache/exp05_curves/{recipe}/{clip_id}.json` (27 clips, 2 recipes only) |
| Frame extracts | `experiments/recipe_pipeline/frames/{recipe}/frame_{seconds:.3f}.jpg` (2 of 18 recipes only) |
| Beat clip extracts (after preflight runs) | `experiments/offline_validation/.cache/beat_clips/{recipe}/{beat_index:04d}.mp4` |
| Beat index (already generated) | `experiments/offline_validation/.cache/beat_index.json` |
| Extract manifest (status tracking) | `experiments/review_ui/.extract_manifest.json` (created by preflight Step 3) |
| Recipe → FINAL.mp4 mapping (built by preflight) | `experiments/review_ui/recipe_export_map.json` |
| Smell-test results | `experiments/offline_validation/runs/20260516T0*/*.{json,md}` |

---

## What's NOT to do next session

- Don't redo this session's discovery process. The 4-supertype taxonomy is locked. Bare beat_type is too coarse. Read the vault note first; don't re-derive.
- Don't propose more peak-alignment-as-global-rule experiments. The technique is recipe/sub-variant conditional, not blanket. See `Motion Signal — Conditional Not Blanket.md`.
- Don't conflate RAFT (the tool) with peak-alignment (the technique). They're separate questions.
- Don't touch the carryover dirty files (CODEX.md, README.md, prproj_dumps, score_pipeline_output.py, uxp_probe). They predate this session.
- Don't commit the 8 unrelated Brain vault dirty files. Only the 2 ASI notes were committed this session.
- Don't use the bare-`beat_type` field as a primary stratification key. Always use `(supertype, sub_variant)`.
