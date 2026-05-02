# ASI-Evolve Beauty Pick Iteration — Session Handoff

**Date:** 2026-05-02
**Branch:** `refactor/writer-modules`
**Last commits:**
- ASI-Evolve `0e34228` — visual shot-type classification (corpus 0.263 → 0.315)
- ASI-Evolve `132efea` — nested + multicam VideoSequenceSource recurse in prproj_reader
- ASI-Evolve `890acb0` — document tuning experiments (per-clip cap reverted)
- ASI-Evolve `102a761` — ASI iteration harness (runner, scorer, prompts, drivers)
- roughcut-ai `490ab8c` — audio_cues parser CLIP_<cid> prefix fix

**Role:** BUILDER

---

## Project elevator pitch (one sentence)

ASI-Evolve is the prompt-iteration / harness repo for [[Recipe Pipeline]] (roughcut-ai); this branch contains the beauty-pick prompt iteration harness — runner that calls Opus on cached scan candidates, scorer that compares against editor truth, and ~10 supporting modules (truth-set extraction, shot-type classification cache, etc.).

## Why this work matters (business context)

The Recipe Pipeline delivers AT's (Apartment Therapy) AI-assisted rough cuts under a **$5K/mo AI services retainer through end of 2026** ($40K total, ring-fenced by Karis). Beauty pick is one of the highest-leverage stages — it picks the hero shots that anchor the editorial. Better picks = less editor cleanup time = better unit economics on every recipe AT runs through the pipeline. Iteration here is about closing the gap between AI choices and Dan's editor instincts so the 85% timeline gets closer to 95%.

This is also the wedge for clients 2-10. Pipeline maintenance is the bottleneck on scaling; tighter prompts mean less per-client tuning. See [[Boardroom Agreements]] and [[AT AI Services — Scope and Status]] for the broader strategy.

## Architecture: ASI-Evolve ↔ roughcut-ai

Two repos work in tandem:

- **`~/DevApps/roughcut-ai/`** — production pipeline. Runs on Modal with Gemini 2.5 Pro. Has real per-recipe cost (~$5/recipe scan + processing). Lives behind `--all-gemini` flag at scale. Builds 85% Premiere timelines for AT.
- **`~/DevApps/ASI-Evolve/`** (this repo) — prompt iteration harness. Calls Opus via the user's Claude CLI subscription (no API key, no per-call cost). Reads roughcut-ai's CACHED outputs (`runs/modal/{recipe}/scan.json`), runs prompt variants against editor truth, scores. **Free to iterate as much as we want.** Winning prompts get committed back to roughcut-ai via PR.

This session shipped one such PR: the `audio_cues.py` parser fix in roughcut-ai (commit `490ab8c`) was discovered by the ASI iteration loop after we noticed audio_cues.json was empty. The fix is now live in production.

## What Was Done This Session (2026-05-01 → 2026-05-02)

End-to-end build and tuning of the beauty-pick iteration harness. **Corpus composite went 0.131 → 0.315 (2.4× lift). KFC alone: 0.131 → 0.570 (4.4× lift).** Approaching the practical ceiling (~0.55-0.60 corpus on this scorer).

Levers tried (in order, with what stuck):
1. **Cap + stratification + transcript injection** (initial shim) — corpus 0.131 → 0.217
2. **Audio_cues parser fix in roughcut-ai** (CLIP_<cid> mirroring bug) — fix shipped, $0.21/recipe was being wasted before
3. **Production VLM v2 gate** — corpus → 0.262
4. **REDO-only audio integration** (Dan's insight: crew_positive is baseline noise; crew_redo is the high-signal cue) — corpus → 0.274, KFC → 0.403
5. **Nested + multicam recurse in prproj_reader** — better truth, eliminated null source_filenames
6. **Visual shot-type classification per candidate** (the win) — corpus → 0.315, KFC → 0.570

Levers tested and reverted:
- Hard pick cap "exactly 4-6 picks" — corpus dropped 0.274 → 0.239, missed editor's long tail
- Per-clip cap (cap=15) — KFC variance exploded ±0.029 → ±0.208
- Image mode at cap=10 — tied corpus, asymmetric per-recipe wins/losses
- Corpus-average shot-type prompt rules — KFC +0.063 / basil_pesto -0.062, net flat
- NMS=3.0 (production default) — hurts the picker even when reachability stays at 80%

## What "editor truth" is and how the scorer works

**Truth source.** Dan's actual finished prproj edits at `experiments/PREMIERE PROJECTS/RECIPES/*.prproj` are the ground truth. The `/recipe-analyze` skill (Stage 5 + 6 at `~/.claude/skills/recipe-analyze/scripts/`) parses both the prproj XML and Dan's hand-written narrative annotations (`Brain/Projects/ASI-Evolve/Annotations/{recipe} — Effect Reasoning (image mode).md`) to identify which clips and timestamps Dan cut to as beauty moments. Output: `truth_sets/{recipe}/beauty.json` with picks like `{clip_id, t_in, t_out, category, label}`.

**Scorer.** `scorers/beauty_pick.py` computes a weighted composite:

```
composite = 0.5 · clip_overlap     (did the picker pick a clip Dan used?)
          + 0.4 · time_match       (was the pick within Dan's used SPAN ±5s?)
          + 0.1 · category_balance (did open/final ratio match Dan's?)
```

Span-based time matching: a pick at any time within `[t_in - 5s, t_out + 5s]` of Dan's used range counts. This is more generous than strict-nearest matching.

So **"corpus 0.315"** literally means: across the 5-recipe corpus, the picker's choices match Dan's actual cuts 31.5% of the way toward perfect alignment on this composite. Theoretical ceiling at our current reachability is ~0.55-0.60 — beyond that requires upstream work (better truth, finer frame sampling, fine-tuning).

**Why these 5 recipes.** basil_pesto, chicken_thighs, korean_fried_chicken, creamy_potato_soup, easy_banana_muffins all have cached Modal Phase 2 outputs in `~/DevApps/roughcut-ai/runs/modal/`. The other 12 corpus recipes don't (yet) — adding one means triggering a Modal scan run first via the roughcut-ai agent (~$1/recipe).

## Active prompt summary

`prompts/beauty_pick_text_fewshot.jinja2` is the current best. What it tells the picker:
- Role: food video editor selecting beauty moments for `{{dish_name}}`
- Receives `{{num_candidates}}` candidates each with `clip_id`, `t`, `camera`, `shot_type`, `score`, optional `[audio: REDO]` flag, VLM description
- Few-shot leave-one-out examples from OTHER recipes' truth picks (4 examples, no leakage)
- Editorial framework: overhead/wide = establishing context, close-up = DETAIL or YUM, macro = TEXTURE, medium = ACTION, reveal = pull-back
- Audio: REDO flag means the take was a mid-take (skip), absence is neutral
- Output: 4-8 picks as JSON (free-form reasoning before the JSON block is allowed and helps debugging)

## Current State

### What works end-to-end

```bash
cd /Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline

# 3-run averaged benchmark on 5-recipe corpus, parallel fan-out
python3 run_n_average.py --prompt prompts/beauty_pick_text_fewshot.jinja2 -n 3
# ~3 min wall, $0 (Opus subscription)

# Single-run benchmark / mutation loop
python3 iterate_beauty_pick.py --benchmark
python3 iterate_beauty_pick.py --generations 3 --variants-per-gen 2

# Image mode benchmark
python3 run_image_mode_avg.py -n 3
```

The picker reads:
- VLM beauty_score (from production roughcut-ai v2 scan)
- Audio REDO flag (crew_redo cues from audio_cues.json)
- Shot type per candidate (close / medium / wide / overhead / macro / reveal)
- Few-shot leave-one-out examples from other recipes' truth sets

Best result, 3-run averaged on `prompts/beauty_pick_text_fewshot.jinja2`:
- **Corpus 0.315** (best of session)
- **KFC 0.570** (best of session, 4.4× session-start)
- basil_pesto 0.547, time_match 0.42 on KFC (3.5× prior)

### What's still weak

| Recipe | Composite | Bottleneck |
|---|---|---|
| basil_pesto | 0.547 | None major; near ceiling |
| **chicken_thighs** | **0.221** | Score saturation on AI2I5461 (4+ frames at 1.00 crowd out lower-scored truth) |
| korean_fried_chicken | 0.570 | None major; near ceiling |
| **creamy_potato_soup** | **0.057** | Picker still 0% clip_overlap (truth on AI2I49xx, picker prefers other clips). Nested-clip truth picks need motion strip to pin down moment |
| easy_banana_muffins | 0.181 | Editor uses cold-open hero on uncommon clip (A057_xxx), picker doesn't surface it |

## Key Files Changed (this session)

| Path | Change |
|---|---|
| `experiments/recipe_pipeline/runners/beauty_pick_runner.py` | Full runner — v2 path, NMS, REDO-only audio, shot_type, few-shot, image mode, batched mode |
| `experiments/recipe_pipeline/scorers/beauty_pick.py` | Composite scorer with span-based time match |
| `experiments/recipe_pipeline/prompts/beauty_pick_text_fewshot.jinja2` | Active best prompt (shot-type-aware editorial guidance) |
| `experiments/recipe_pipeline/iterate_beauty_pick.py` | Mutation loop driver (parallel fan-out across 5 recipes) |
| `experiments/recipe_pipeline/run_n_average.py` | N-run averaging for noise-denoising |
| `experiments/recipe_pipeline/run_image_mode_avg.py` | Image mode equivalent |
| `experiments/recipe_pipeline/build_shot_type_cache.py` | One-time per-recipe shot-type classification (~25 min wall) |
| `experiments/recipe_pipeline/classify_shot_types.py` | Diagnostic comparing editor truth vs picker shot-type distributions |
| `experiments/recipe_pipeline/shot_type_diagnostic.py` | Regex-based diagnostic (inconclusive — VLM doesn't tag shot type in prose) |
| `experiments/recipe_pipeline/prproj_reader.py` | Added `resolve_source_info()` (filename + inner_source_in_ticks); recurses into nested + multicam VideoSequenceSource |
| `experiments/recipe_pipeline/truth_sets/{recipe}/beauty.json` | Truth sets for 5 corpus recipes (after multi-cut span-aware extraction) |
| `experiments/recipe_pipeline/truth_sets/{recipe}/shot_types.json` | Per-candidate shot-type cache (~300 entries each) |
| roughcut-ai `tools/manifest_gen/audio_cues.py` | Parser tolerates `CLIP_<cid>` prefix from LLM output |

## Decisions Made

| Decision | Reasoning |
|---|---|
| Per-candidate structured tags > per-corpus prompt rules | Proved 3× this session (audio asymmetry, NMS, shot type). Rules help one recipe and hurt another by similar magnitude; tags let picker compose recipe-specific patterns organically. See [[Per-Candidate Tags Beat Per-Corpus Rules]]. |
| Drop crew_positive as a flag, keep only crew_redo | Crew is positive on ~90% of takes whether they're keepers or not. crew_redo is high signal — explicitly says "the take just finished was NOT the keeper." |
| NMS_WINDOW_S = 1.5 (vs production 3.0) | Production NMS=3.0 collapses hero clusters that the picker uses as a "this region is hot" discrimination signal. KFC composite dropped 0.298 → 0.245 with NMS=3.0; held at 0.290 with 1.5. |
| No per-clip cap on v2 path | Tested cap=8 (reachability dropped 74% → 63%) and cap=15 (KFC variance exploded). Editor patterns differ per recipe — single global cap can't satisfy both KFC's "many picks on one clip" and chicken_thighs' "picks across many clips". |
| Image mode at cap=10, not cap=30 | At cap=30, Opus skims/anchors instead of reading all images. Cap=10 has Opus actually Read each frame; corpus tied with text mode. |
| Free-form picker output, JSON block at end (batched mode) | JSON-only system prompt is brittle; free-form lets picker reason aloud (great for debugging) without breaking parsing. |

## What's Next

### Immediate (likely 30-min wins)

1. **Push the branch.** Currently local on `refactor/writer-modules`.
2. **Inform roughcut-ai agent of the shot-type result.** Hand-off prompt at `~/DevApps/Brain/Projects/RoughCut/Handoff to roughcut-ai — *.md` (3 prior handoffs already pushed). Worth pinging them that visual shot-type classification gave the biggest single lift.
3. **Decide whether to ship Round 2 prproj writer** (V2 + MOGRT text emit) — that was the next item before beauty-pick rabbit-holed. Plan still at `~/DevApps/Brain/Projects/ASI-Evolve/Prproj-Direct Writer Plan.md`.

### Lever ideas worth testing if continuing beauty pick

1. **Motion strip per candidate** (~5-10 frames at 1s spacing per candidate, sent to image-mode picker). Could close the basil_pesto / chicken_thighs time_match gap. Implementation: extend `_frame_path_for_candidate` to return a list, prompt asks picker to read N frames per candidate. Cap drops to ~10 candidates.
2. **Recipe-aware per-clip cap.** Compute per-recipe truth-distribution metadata at truth-extract time, use to set cap dynamically. KFC pattern (B19I6339 has 4+ truth picks) wants cap=N; chicken_thighs pattern (truth across 5 clips) wants cap=K.
3. **Editor-feedback fine-tuning loop.** Long horizon (months of feedback data needed); only meaningful at scale.

### What NOT to do

- **Don't add corpus-average prompt rules** ("prefer X for Y category"). Tested twice this session (shot type, audio keeper); both hurt as many recipes as they helped. Use per-candidate tags instead.
- **Don't bump CANDIDATE_CAP higher than 300** without per-clip stratification — picker drowns at higher caps. Tested cap=1500 earlier, corpus dropped.
- **Don't re-test image mode at high caps.** Cap=30 confirmed worse than cap=10 (Opus skims).

## Known Issues

- **Branch is `refactor/writer-modules`** but the writer-refactor work is from a much earlier session; today's commits are on top. Worth either renaming the branch or merging soon to clarify.
- **`creamy_potato_soup` truth picks** include 3 entries on AI2I4961 at low source-times (0-1s) which may be artifacts of the nested-clip recurse — first inner clip's source-time is always picked even if the actual moment is one of the other 6 inner clips. Acceptable for now but worth revisiting with motion strip work.
- **Opus stochasticity** is real (±0.05 across same-prompt runs). Always use 3-run averaging for benchmark claims; single-shot is noisy.
- **Per-clip cap on v2 path is OFF** by design (commit `890acb0`). Don't re-enable without recipe-aware logic.

## Expected benchmark values (regression check)

If you run `run_n_average.py -n 3` on `prompts/beauty_pick_text_fewshot.jinja2`, expected ranges (3-run avg, ±0.05 noise):

| Recipe | Expected ± noise | Time match (KFC is the leader) |
|---|---|---|
| basil_pesto | 0.50 ± 0.05 | 0.10 ± 0.05 |
| chicken_thighs | 0.22 ± 0.05 | 0.08 ± 0.05 |
| **korean_fried_chicken** | **0.55 ± 0.05** | **0.40 ± 0.10** |
| creamy_potato_soup | 0.05 ± 0.02 | 0.00 (1-pick truth, ceiling-bound) |
| easy_banana_muffins | 0.18 ± 0.03 | 0.12 ± 0.05 |
| **Corpus** | **0.30 ± 0.04** | — |

If your run lands inside these bands, you're matching the handoff state. If it's substantially below (corpus < 0.25 OR KFC < 0.45), something regressed — check:
1. shot-type cache files exist (`truth_sets/{recipe}/shot_types.json` for all 5)
2. audio_cues.json files in `runs/modal/{recipe}/` are non-empty (post-fix)
3. The runner's `_attach_shot_types` and `_attach_audio_signals` are still being called in `_build_production_candidates`
4. `NMS_WINDOW_S = 1.5` (not 3.0) and `NMS_MIN_SCORE = 0.9` in the runner

## Auxiliary state (don't be surprised by these files)

- **`prompts/iter/`** — mutation loop's per-variant prompt files. Generated by `iterate_beauty_pick.py`. Each file is a variant tested in some past generation. Safe to ignore for benchmark work; safe to delete if cluttered.
- **`runs/beauty_pick_iteration_history.json`** — mutation loop's history (generations, variants, scores). Re-runs of `iterate_beauty_pick.py` overwrite it. Persists across runs.
- **`truth_sets/{recipe}/shot_types.json`** — cached shot classifications. Built one-time by `build_shot_type_cache.py`. ~25 min total wall to rebuild from scratch. Should not need rebuilding unless candidate pools change.

## Open call to consider: PR the picker prompt back to roughcut-ai?

The current `prompts/beauty_pick_text_fewshot.jinja2` outperforms the production prompt by a corpus margin of +0.10–0.15 on Opus. **If we want production to use this prompt** (which would shift production from Gemini to Opus, or test the prompt on Gemini), it should land as a PR to roughcut-ai's `prompt_templates.py:beauty_pick_selection`. Caveat: prompt was validated on Opus; Gemini may behave differently. The transfer-validation gate in the spec (Brain `VLM Beauty Score — Spec.md`) describes how to test that.

This decision is queued, not actioned. Ask Dan before pushing.

## First-run sanity checks (especially on a fresh machine)

Before doing real work, verify the prerequisites:

```bash
# 1. Brain vault present + readable
test -f ~/DevApps/Brain/MEMORY.md && echo "✓ vault" || echo "✗ vault missing — clone Brain repo first"

# 2. roughcut-ai cached scans present (5 expected)
ls ~/DevApps/roughcut-ai/runs/modal/*/scan.json 2>/dev/null | wc -l
# Expected: 5. If 0, scans need backfilling — escalate to roughcut-ai agent

# 3. Editor truth prprojs present
ls "$HOME/DevApps/ASI-Evolve/experiments/PREMIERE PROJECTS/RECIPES/"*.prproj 2>/dev/null | wc -l
# Expected: 5+ FINAL prprojs

# 4. /recipe-analyze skill installed (only needed if extending truth)
test -f ~/.claude/skills/recipe-analyze/SKILL.md && echo "✓ recipe-analyze skill" || echo "✗ skill missing"

# 5. Truth + shot-type caches present
ls experiments/recipe_pipeline/truth_sets/*/beauty.json | wc -l       # Expected: 17
ls experiments/recipe_pipeline/truth_sets/*/shot_types.json | wc -l   # Expected: 5

# 6. Claude CLI ≥ 2.x
claude --version
```

If any check fails: stop and resolve before iterating. Don't waste a session on broken inputs. If a backfill (Modal scans) is needed, the credentials live in `roughcut-ai/.env` — that's a roughcut-ai problem, not an ASI problem.

## How to decide: continue beauty pick OR pivot to Round 2 writer?

Both are valid next moves. Decision criteria:

**Continue beauty pick if:**
- Dan asks specifically about beauty pick / says "push further on the picker"
- Composite ≤0.40 corpus is unacceptable for the AT use case (it currently sits at 0.315 — workable but not great)
- You have ~1-2 hours to test the motion-strip lever (the highest-leverage remaining option)

**Pivot to Round 2 writer if:**
- Dan asks about shipping deliverables / V2 / MOGRTs / "the writer"
- AT timeline pressure (Karis weekly status routine, end-of-month deliverables)
- Beauty pick at 0.315 is "good enough for now" — the bigger user-facing impact comes from being able to express V2-track + MOGRT text in the writer output
- Editorial fidelity (speed ramps, MOGRT, multi-track) is currently blocked on the writer being only V1

Default if Dan doesn't specify: **pivot to Round 2 writer.** Beauty pick is at a reasonable plateau (2.4× session-start, 4.4× on KFC) and the next +0.10 lift requires multi-day work (motion strip, recipe-aware caps, fine-tuning). Round 2 writer is a 1-2 day shippable that unlocks editorial fidelity for the entire pipeline. Better unit of progress for the AT timeline.

Plan for Round 2 at `~/DevApps/Brain/Projects/ASI-Evolve/Prproj-Direct Writer Plan.md` — has round-by-round build plan, current status (Round 1 shipped + refactored), known XML gotchas.

## Quick Start for Next Session

```bash
# Pull and confirm state
cd /Users/dandj/DevApps/ASI-Evolve
git checkout refactor/writer-modules
git log --oneline -5

# Verify the 3-run benchmark still works
cd experiments/recipe_pipeline
python3 run_n_average.py --prompt prompts/beauty_pick_text_fewshot.jinja2 -n 3
# Expected: corpus ≈ 0.315, KFC ≈ 0.57, basil ≈ 0.55, ~3 min wall

# Read the full session arc
cat ~/DevApps/Brain/Projects/RoughCut/Beauty\ Pick\ Prompt\ Iteration\ —\ 2026-04-29.md

# If continuing beauty pick, the highest-leverage next lever is motion strip
# (see "Lever ideas worth testing" above)

# If pivoting to Round 2 prproj writer:
cat ~/DevApps/Brain/Projects/ASI-Evolve/Prproj-Direct\ Writer\ Plan.md
```

## Where things live (paths, services, credentials)

| Asset | Location |
|---|---|
| Cached candidate scans (production) | `~/DevApps/roughcut-ai/runs/modal/{recipe}/scan.json` (5 recipes) |
| Editor FINAL prprojs | `~/DevApps/ASI-Evolve/experiments/PREMIERE PROJECTS/RECIPES/{Recipe}.prproj` |
| Truth sets | `~/DevApps/ASI-Evolve/experiments/recipe_pipeline/truth_sets/{recipe}/{beauty,beats,text}.json` |
| Shot-type cache | `~/DevApps/ASI-Evolve/experiments/recipe_pipeline/truth_sets/{recipe}/shot_types.json` |
| Iteration history | `~/DevApps/ASI-Evolve/experiments/recipe_pipeline/runs/beauty_pick_iteration_history.json` |
| Frame JPEGs (for image-mode) | `~/DevApps/roughcut-ai/runs/modal/{recipe}/scan_frames/[scan_frames/]_dino_<cid>/frame_NNNN.jpg` |
| /recipe-analyze skill (used to generate truth) | `~/.claude/skills/recipe-analyze/` |

**Credentials:** None required for the harness — Opus calls go through the user's Claude CLI subscription auth (no API key). Production roughcut-ai runs use Gemini through Modal (out of scope for ASI iteration).

**External services:** None during iteration. roughcut-ai pipeline backfills (audio_cues, scans) require Modal credentials but that's a separate workflow.

**Brain vault access:** the vault is a regular file tree at `~/DevApps/Brain/` (Obsidian on top). Read notes directly with the Read tool — no login required. The skill `obsidian-cli` is registered if you want CLI-style ops; not needed for read-only.

**If cached scans are missing** (e.g. fresh laptop / different machine):
```bash
ls ~/DevApps/roughcut-ai/runs/modal/*/scan.json   # 5 should exist
```
If missing, ping the roughcut-ai agent to re-run Phase 1 / Phase 2 on the 5 ASI corpus recipes (basil_pesto, chicken_thighs, korean_fried_chicken, creamy_potato_soup, easy_banana_muffins). Backfill cost ~$5 total. Recipe selection criterion: must have FINAL prproj at `experiments/PREMIERE PROJECTS/RECIPES/`.

**Branch naming.** `refactor/writer-modules` is misleading — the writer-refactor work is from a much earlier session (commit `2094548` and prior). Today's beauty-pick commits land on top of it but don't relate. **Decision for next session:** either rename this branch to `feature/beauty-pick-shot-type` or rebase onto main and merge the writer-refactor work cleanly. Don't ship as-is — the branch name will confuse code review.

## Brain vault — read these first if you have 5 minutes

The Brain vault at `~/DevApps/Brain/` is Dan's cross-project knowledge base (Obsidian). It carries all the strategic + technical context that doesn't live in code. **Read it directly with the Read tool — no Obsidian needed for read-only.**

**Mandatory reads for any session continuing this work:**

| File | Why |
|---|---|
| `~/DevApps/Brain/MEMORY.md` | Project routing table, current priorities, learned preferences, AT engagement context |
| `~/DevApps/Brain/Projects/RoughCut/Beauty Pick Prompt Iteration — 2026-04-29.md` | Full arc of this work — every experiment, every number, every reverted lever, the architectural lessons |
| `~/DevApps/Brain/Projects/ASI-Evolve/Prproj-Direct Writer Plan.md` | Plan for the OTHER active workstream (Round 2 V2 + MOGRTs); decide whether to continue beauty pick or pivot here |

**Reusable patterns extracted this session:**

| File | What it teaches |
|---|---|
| `~/DevApps/Brain/Knowledge/LLM Patterns/Per-Candidate Tags Beat Per-Corpus Rules.md` | Why universal prompt rules fail vs structured per-candidate tags. Proved 3× this session (audio asymmetry, NMS calibration, shot type) |
| `~/DevApps/Brain/Knowledge/LLM Patterns/LLMs Mirror The Format You Show Them.md` | Why the audio_cues parser was silently broken for months ($0.21/recipe wasted) — input header pattern + example output keys = LLM mirrors prefix into JSON keys |

**Editorial / strategic context:**

| File | Why |
|---|---|
| `~/DevApps/Brain/Knowledge/Editorial Craft/Editorial Rules - Dan's Camera Logic.md` | Editor's anchor-shot/shot-type framework that informed today's shot-type diagnostic |
| `~/DevApps/Brain/Clients/Apartment Therapy/AT AI Services — Scope and Status.md` | The retainer this work serves, weekly status routine for Karis |
| `~/DevApps/Brain/Projects/RoughCut/Architecture — Lessons from Claude Code Paper.md` | Why we're investing in harness work (1.6%/98.4% rule) |

**Companion documentation specific to today's work:**

- 3 handoffs to the roughcut-ai agent at `~/DevApps/Brain/Projects/RoughCut/Handoff to roughcut-ai — *.md` (audio_cues fix, VLM beauty_score spec, NMS findings)
- `~/DevApps/Brain/Projects/RoughCut/VLM Beauty Score — Spec.md` (the architectural spec we shipped)
- `~/DevApps/Brain/Knowledge/API Integration/Premiere prproj Multicam Detection.md` (the reader work the nested/multicam recurse built on)

**How to navigate:** the `[[wikilinks]]` in vault notes resolve to other notes — follow them like Obsidian would. Use `Read` on the resolved path. The `Knowledge Map.md` at the vault root is the index.

If you're continuing in a different direction (not beauty pick), check `MEMORY.md` first — it has the cross-project routing including [[Renewed Homes 2026]], [[NQ AI Sidekick]], and other active work.
