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

## Companion Brain notes

- [[Beauty Pick Prompt Iteration — 2026-04-29]] — full session arc, all experiments, all numbers
- [[VLM Beauty Score — Spec]] — original architectural spec (now shipped)
- [[LLMs Mirror The Format You Show Them]] — pattern from the audio_cues parser bug
- [[Per-Candidate Tags Beat Per-Corpus Rules]] — pattern from this session's three structural fixes
- [[Editorial Rules - Dan's Camera Logic]] — editor's shot-type framework (informed the diagnostic)
- [[Premiere prproj Multicam Detection]] — companion reader doc; the recurse this session built on
- [[Recipe Pipeline]] — production pipeline that consumes our prompt winners
- [[ASI-Evolve]] (project hub)

3 prior handoffs to the roughcut-ai agent at `~/DevApps/Brain/Projects/RoughCut/Handoff to roughcut-ai — *.md` document the audio_cues fix, VLM beauty_score spec, NMS findings.
