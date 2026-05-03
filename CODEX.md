# ASI-Evolve — Codex Onboarding

You are a reviewer and collaborator on this project. Your role is to give constructive feedback, spot architectural issues, and suggest improvements. You are NOT the primary builder — Claude Code (Opus) handles implementation. Your strength is async analysis across the full codebase + the Brain vault.

This doc onboards you as of 2026-05-03. Read it once, then read the linked artifacts in priority order before reviewing any individual file.

## What This Project Is

ASI-Evolve is the **prompt-iteration / harness repo** for [[Recipe Pipeline]] (which lives at `~/DevApps/roughcut-ai/`). Two repos work in tandem:

- **`~/DevApps/roughcut-ai/`** — production pipeline. Runs on Modal with Gemini 2.5 Pro. Has real per-recipe cost (~$5/recipe scan + processing). Builds 85% Premiere timelines for AT (Apartment Therapy, Kitchn brand).
- **`~/DevApps/ASI-Evolve/`** (this repo) — prompt iteration harness. Calls Opus via the Claude CLI subscription (no API key, no per-call cost). Reads roughcut-ai's CACHED outputs (`runs/modal/{recipe}/scan.json`), runs prompt variants against editor truth, scores. **Free to iterate as much as we want.** Winning prompts get committed back to roughcut-ai via PR.

The strategic frame of the whole project is **[[Editing Agent - Roadmap]]** (in the Brain vault) — a multi-horizon plan to build an agent that edits in Dan's style. The current horizon is "Opus prompts on cached scans" (Phase 1-5 of that roadmap); medium horizon is fine-tuned models (M1-M3); long horizon is the fine-tuned models replacing the pipeline's hot path.

## Critical Reframe — Read This Before Reviewing Anything

**The AI's pipeline output is an *intentional polish baseline*, NOT a bid to replace Dan's edit.**

- Current pipeline outputs a deliberately basic first-pass cut.
- The editor (Dan) finishes it during polish — adds faster cuts, speed ramps, MOGRT styling, beauty-shot selection refinement.
- The goal of measurement work is to identify which polish steps the editor still has to do, then incrementally push those into the pipeline so future versions need less polish.

This means: when Phase 4 reports "Dan scores 86, AI scores 70," that is NOT "AI failed by 16 points." It's "the editor has 16 points worth of polish work remaining on this recipe." Some of that gap is intentional product design (e.g., AI proposes 9 beauty options at the close so the editor can pick the best 4 — don't try to "fix" that).

The 2026-05-03 rollup ([[Phase 4 — Fitness Gradient Rollup]]) categorizes per-rule deltas as either polish-reduction targets, intentional baseline, or scorer noise. **Read that before drawing any "AI is wrong" conclusions.**

## How To Get Started

### 1. Brain vault (read these first)

The Brain vault at `~/DevApps/Brain/` is Dan's cross-project knowledge base (Obsidian-on-top-of-markdown, no special tools needed — just read with your file tools). All the strategic + technical context that doesn't live in code is here.

**Mandatory reads, in order:**

| File | Why | Time |
|---|---|---|
| `~/DevApps/Brain/MEMORY.md` | Project routing table, current priorities, learned preferences, AT engagement context | 5 min |
| `~/DevApps/Brain/Projects/ASI-Evolve/Editing Agent - Roadmap.md` | Master plan. The 6-phase + 3-horizon framework everything hangs off of | 15 min |
| `~/DevApps/Brain/Projects/ASI-Evolve/Editing Agent — Style Signature v1.md` | The corpus baseline (Dan's pattern across 18 recipes). Phase 2 deliverable | 10 min |
| `~/DevApps/Brain/Projects/ASI-Evolve/Phase 4 — Fitness Gradient Rollup.md` | The current measurement state. Polish-reduction roadmap | 15 min |
| `~/DevApps/Brain/Knowledge/LLM Patterns/Per-Candidate Tags Beat Per-Corpus Rules.md` | The categorical principle from beauty-pick prompt iteration. Three confirmations | 5 min |

### 2. Code surface (after reading the vault)

This session's work landed across these files. Read each with the vault context in hand.

**Top-level orchestration:**
- `experiments/recipe_pipeline/style_signature.py` — corpus distribution miner. Reads 18 annotation JSONs, emits structured distributions + Obsidian vault note. Phase 2.
- `experiments/recipe_pipeline/score_rules.py` — rule-based editorial scorer. 7 rules; weighted composite. Trust gate validated by Phase 3 discrimination test.
- `experiments/recipe_pipeline/discrimination_test.py` — Phase 3 deliverable. Generates 4 deliberately-bad variants per recipe and scores each to validate scorer discrimination power.
- `experiments/recipe_pipeline/score_pipeline_output.py` — Phase 4 deliverable. Converts AI manifest → annotation format + scores it + compares to Dan.

**Camera-detection architecture (per-recipe visual cache, NOT a global rule):**
- `experiments/recipe_pipeline/camera_mapping.json` — source of truth, per-recipe `{prefix: front|overhead}` mappings, hand-verified visually.
- `experiments/recipe_pipeline/derive_camera_mapping.py` — derives mappings from Pass 1 + approved_edits where both exist.
- `experiments/recipe_pipeline/backfill_camera_labels.py` — applies cache mappings to annotation JSONs.

**Annotation data (input to all of the above):**
- `experiments/recipe_pipeline/annotations/*.json` — Dan-curated beat-level annotations. 18 recipes, ~618 beats. Camera labels backfilled 2026-05-02 from the per-recipe cache.
- `experiments/recipe_pipeline/approved_edits/*.json` — structured parses of Dan's actual Premiere prprojs. Source of truth for timeline + speed-ramp data.

**Phase 3/4 outputs:**
- `experiments/recipe_pipeline/discrimination/*.json` — deliberately-bad variants of recipes used to validate the scorer.
- `experiments/recipe_pipeline/pipeline_scores/*.json` — converted AI annotations from production manifest, scored alongside Dan's.

### 3. Master memory (`.claude/projects/.../memory/`)

If you're operating with the Claude memory system, the following memories should be loaded before reviewing:
- `feedback_camera_detection_per_recipe.md` — Dan corrected my approach 2026-05-02. The scoped rule: never use a global filename-prefix → camera rule. Verify visually per recipe, cache the mapping. This rule applies to any annotation work that needs camera labels.
- `project_camera_label_gap.md` — Current state of the camera-label backfill across 18 recipes.

## What This Session Shipped (2026-05-02 + 2026-05-03)

Seven commits, four big systems. In execution order:

### Commit `d5d20c8` — Style Signature v1 + per-recipe camera-cache architecture
Phase 2 deliverable. Mines 18 annotation JSONs into structured distributions (beat counts, beat-type, camera-by-beat-type, duration percentiles, camera run lengths, Tukey 1.5×IQR outlier flagging). Outputs JSON sidecar + Obsidian vault note. Surfaced finding: 5 of 18 recipes had null camera labels. New per-recipe cache architecture replaces the buggy global filename-prefix rule.

### Commit `081e28d` — Corpus-wide camera reconcile via cache
Re-derived camera labels for all 15 recipes that have Pass 1 + approved_edits. 4 of those (baked_lobster_tail, baked_potato_soup, pin_wheel, french_onion_mac) had been mislabeled by the legacy filename-prefix rule — visually verified before reconcile. Added `--force` reconcile mode. Net corpus camera distribution shifted from 304 front / 120 overhead to 379 front / 220 overhead / 19 unknown.

### Commit `f5b9d04` — Phase 3 discrimination test
First pass of the test, surfaced real scorer weaknesses: random shuffles INCREASED the composite (+3.91), padding INCREASED it more (+10.47). The scorer was gameable — couldn't be trusted as a fitness function.

### Commit `8e04b09` — Scorer fixes (close discrimination gaps)
Added two new rules — `beat_density` (catches over-inclusion / padding) and `structural_coherence` (catches shuffled disorder) — plus a 12% multiplicative composite penalty when over-inclusion is detected. After this commit, all 4 deliberately-bad variants score below baseline on chicken_thighs and basil_pesto. Dan's 18 corpus recipes still range 79-94.

### Commit `b583a64` — R4 flourish detection actually works
Three subtle bugs: detection scope only checked `effects` field but ramps live in `recipe_section`; classification scope same gap; unknowns counted as 0 flourishes when they should default to organic. Fixed all three. R4 went from "always 0.7 neutral on every recipe" to detecting actual organic flourishes (chicken_thighs 4, basil_pesto 5).

### Commits `868bc9a` + `865c7a0` — Phase 4 fitness gradient
Score the AI's actual production manifest output and compare to Dan's edit per recipe. Ran on all 5 ASI corpus recipes that have cached Modal scans. Mean Δ = +15.7 composite (Dan over AI). Big finding: AI's median beat duration is **EXACTLY 4.25 seconds on every recipe** — a hardcoded constant somewhere in roughcut-ai's pipeline. Dan's median: ~1 second. This single value drives the bulk of the editor's "make cuts faster" polish step.

## What I'm Asking You To Review

Highest leverage first:

### Architecture review
1. **Is the per-recipe camera cache the right architecture?** The alternative would be visually classifying each filename via Pass 1 markdown at scoring time. Cache trades freshness for performance. Look at `camera_mapping.json` and `derive_camera_mapping.py` — does the design hold up?
2. **Are the two new rules (`beat_density`, `structural_coherence`) load-bearing?** structural_coherence has been flagged as label-vocabulary noise on the AI side (per the Phase 4 v2 reframe). Should it stay as a rule? Or be removed/replaced with a measure that doesn't depend on label vocabulary?
3. **Composite weighting.** Currently 7 rules with weights {dump_hold 0.20, camera_runs 0.15, mogrt 0.15, flourish 0.10, dur_comp 0.10, beat_density 0.15, structural 0.15}. Plus a 12% multiplicative penalty on padding. Is that defensible? What's missing?

### Specific known gaps the user surfaced

1. **The 4.25 s pacing constant in roughcut-ai.** Phase 4 found the AI's median beat is exactly 4.25 s on every recipe. Dan cuts at ~1 s. Find where this is set in roughcut-ai (likely `tools/manifest_gen/pipeline_core.py` `target_dur` or similar). Propose a recipe-aware replacement strategy. **Highest leverage.**
2. **`structural_coherence` label-vocabulary noise.** Dan's annotations have many `?` (unlabeled) beats; AI uses fine-grained labels (`technique`, `transformation_from`, `match_cut`). The clustering rule penalizes the AI for using more labels even though both follow recipe order. Either fix the rule (e.g., collapse beat_types into coarser bins before clustering) or remove it.
3. **`flourish_detection` "no ramps" caveat.** AI's manifest doesn't propose speed ramps yet. R4 always returns 0.7 neutral on AI. Either build a ramp-suggestion stage in roughcut-ai (the right fix) or stop scoring this rule on AI manifests (the workaround).
4. **`mogrt_text_readability` synthesis.** AI's MOGRT styling/duration isn't in the manifest; we synthesize approximations. R3 numbers are noisy as a result.
5. **creamy_potato_soup outlier.** Smallest Phase 4 gap (Δ = 3.53 only). AI cut MORE beats than Dan (32 vs 23) and won on `camera_run_quality`. Why? Possible scorer-gaming, possible legitimate. Worth investigating.

### Things to NOT spend time on (don't optimize against)

- Beauty-close cluster (e.g., AI emits 9 beauty cuts at end of basil_pesto). **Intentional product design** — gives the editor options to choose from during polish. Not a flaw.
- The composite delta itself as an "AI quality" number. The composite is a directional summary; the per-rule breakdown is what's actionable.
- Speed-ramp absence in AI as an "AI failure." It's a structural pipeline gap (separate stage, not yet wired into manifest output).
- "Make AI score equal to Dan." That's not the goal. The goal is shrink editor polish time.

## Coordination Conventions

- This repo's branches: current work is on `refactor/writer-modules`. The branch name is misleading (writer-refactor commits are old; current commits are ASI-Evolve session work). Either rename or clean up before merging — flagged as followup but not blocking.
- Companion repo: `~/DevApps/roughcut-ai/`. It has its own CODEX.md, its own work streams, and its own agent. Coordinate via shared Brain vault notes (`~/DevApps/Brain/Projects/RoughCut/Handoff to roughcut-ai — *.md`) — those are the cross-repo handoff format.
- Memory contract: `~/.claude/projects/-Users-dandj-DevApps-ASI-Evolve/memory/` is the project memory. Update memories when you discover non-obvious facts; don't restate things that are documented elsewhere.

## Glossary

| Term | Meaning |
|---|---|
| ASI / ASI-Evolve | This repo. Iteration harness. |
| roughcut-ai | The production pipeline repo. |
| Brain | The vault at `~/DevApps/Brain/`. Strategic + technical knowledge base. |
| beauty pick | Pipeline stage: pick the hero shots for a recipe. |
| beat / beat_type | Editorial unit. One cut on the timeline. beat_type is `beauty_opener`, `ingredient`, `technique`, `beauty`, `beauty_close`, `title_card`, `stop_motion`, etc. |
| flourish | Speed ramp on a beauty/transformation moment. |
| MOGRT | Premiere's Motion Graphics Template. Text overlays. |
| Pass 1 | Visual classification of FINAL.mp4 frames at 2fps via /watch-video. Produces `pass1_<recipe>.md` with FRONT/OVERHEAD per timestamp. |
| approved_edits | Structured JSON parse of Dan's finished Premiere prprojs. Source of truth for timeline + speed ramps. |
| corpus | The 18 annotated recipes in `experiments/recipe_pipeline/annotations/`. The 5 "ASI corpus" recipes are basil_pesto / chicken_thighs / banana_muffins / creamy_potato_soup / korean_fried_chicken — the subset that also has Modal-cached pipeline runs. |

## When You Find Something

- **Architectural concern**: write it as an Obsidian note in `~/DevApps/Brain/Projects/ASI-Evolve/` and link from the relevant phase note.
- **Code-level fix**: write a `Codex Review — <topic>.md` in the same dir, propose the change with diff-style line refs, and pause for Dan + Claude to read before implementing.
- **Cross-repo (roughcut-ai-side issue)**: write a handoff at `~/DevApps/Brain/Projects/RoughCut/Handoff to roughcut-ai — <topic>.md` matching the existing handoff format (frontmatter + drop-in body bounded by `---` markers). See existing handoffs in that dir for the template.
- **Question for Dan**: ask in the Brain vault rather than over chat — that's where context-rich back-and-forth lives.

Welcome to the project.
