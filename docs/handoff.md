# Recipe Pipeline — Session Handoff (2026-04-25)

**Date:** 2026-04-25
**Branch:** `main`
**Last commits:**
- ASI-Evolve `615c506` — feat: 6 new recipe annotations + surgical frame extractor
- Brain `6f7f320` — docs: commit to Premiere Pro medium + pattern library stub

**Role:** BUILDER

---

## Session goal

Reach a 15-recipe annotated corpus, then resolve where to take the editing-agent pipeline architecturally. Direction locked to Premiere Pro as the medium.

## What Was Done

### Phase 1: Corpus expansion (15 recipes)
- Fixed two parser/annotation bugs surfaced by steak_tacos:
  - **V2-only beats recovery** in `xml_to_manifest.py` (12 missing beats restored on steak_tacos)
  - **Camera detection via prefix convention** (replaced session-derived prefix with hardcoded B19I/AI2I rules — shared between parser and annotation script)
- Re-annotated steak_tacos with the fixes (41 beats, 90.41 composite)
- Annotated 6 more recipes via surgical frame extraction (XML-driven dense regions where stop-motion happens, 2fps elsewhere): baked_potato_soup, baked_lobster_tail, congee, crab_rangoon, cucumber_tea, french_onion_mac
- Built `extract_frames_smart.py` — 2fps baseline + 12fps in dense regions (appearance compilations), driven by manifest's stop_motion_sequences + nest-internal scan
- Final corpus scores: tune mean 86.48 → 85.50 over 15 recipes; range 71.51 (crab_rangoon) to 92.12 (flaky_pie_crust)

### Phase 2: Investigation — export format fidelity

Working through what the editing-agent pipeline actually needs revealed export-format limitations:

- **XMEML drops adjustment-layer Transform effects entirely.** Confirmed on steak_tacos: 9 adjustment-layer clipitems, only 2 (V7 Lumetri grades) carried filter data. The 6 V3 + 1 V5 Transform effects came back empty.
- **AAF preserves effect TYPES (`Transform`, `Lumetri Color`) and time spans, but parameters are missing for adjustment-layer Transforms.** Strictly better than XMEML for adjustment-layer awareness, but still loses keyframe values.
- **AAF drops masks entirely.** XMEML drops them too. Only `.prproj` has them.
- **`.prproj` has everything AND is fully readable.** Verified by extracting Transform effect parameters from steak_tacos: ObjectRef chain resolves cleanly, all 12 Transform parameters (Anchor Point, Position [animated], Scale [animated], etc.) accessible, keyframes follow same encoding as the documented speed-ramp solution.

### Phase 3: Direction lock — Premiere Pro is the medium

- Updated `Editing Agent - Roadmap.md` with 2026-04-25 direction lock: prproj becomes primary input, XMEML kept as fallback
- Created `Knowledge/API Integration/Premiere Effect Pattern Library — Recipe Corpus.md` — canonical catalog stub with population schema, format requirements, and the explicit "see it before replicate it" framing
- Reshaped tasks:
  - **#16** → build prproj reader with full parameter extraction + populate pattern library across all 15 recipes. Reading is the unblocker — verified feasible today.
  - **#17** → prproj WRITER for round-trip recreation. Deferred; only needed when pipeline produces editor-openable projects.
  - **#18** → deleted; mask discovery folded into #16 (same method, no separate session needed).

## Current State

**What works:**
- 15 recipes annotated (Brain `Projects/ASI-Evolve/Annotations/`) with corresponding JSONs (`experiments/recipe_pipeline/annotations/`)
- Rule scorer (`score_rules.py`) with 5 rules + verdict-token Rule 4
- `xml_to_manifest.py` handles MOGRTs + Essential Graphics + V2-only beats + correct camera detection
- `extract_frames_smart.py` produces surgical frame coverage for Pass 1 captioning
- Annotation pipeline (`analyze_editorial_judgment.py`) supports `--no-manifest` mode, structured `[flourish: organic|functional]` verdict tokens, existing approved-edit JSONs

**What's partially done:**
- Pattern library doc is a stub awaiting reader output. Schema and population process are explicit; data isn't there.

**What's not yet built:**
- `prproj_reader.py` (task #16, the next-session opener)
- Per-effect discovery docs in `Knowledge/API Integration/` (Adjustment Layer Transform, Mask, Lumetri Color)
- 15 recipe `.prproj` dumps
- `flat_timeline` / `dense_regions` parser refactor (task #15) — blocked by #16

**Known gaps in the corpus:**
- 5 recipes have hidden nest-internal appearance compilations not yet captured in beat groupings: cranberry_jalapeno_dip, peppermint_bark, pin_wheel, crab_rangoon, french_onion_mac. These will surface naturally once the parser reads `flat_timeline` from prproj output.
- baked_lobster_tail has a parser anomaly (beat 55 nest at 736s, far past video end). Cosmetic; flag and filter when encountered.

## Key Files Changed (this session)

| File | What |
|---|---|
| `experiments/recipe_pipeline/xml_to_manifest.py` | V2-only beat recovery + shared `camera_from_filename()` helper |
| `experiments/recipe_pipeline/analyze_editorial_judgment.py` | Camera detection updated to use prefix convention |
| `experiments/recipe_pipeline/extract_frames_smart.py` | NEW — surgical 2fps+12fps frame extraction with nest-aware dense regions |
| `experiments/recipe_pipeline/approved_edits/{6 new}.json` | NEW — parsed manifests for the 6 new recipes |
| `experiments/recipe_pipeline/annotations/{6 new}.json` | NEW — annotation outputs |
| `experiments/recipe_pipeline/annotations/steak_tacos.json` | UPDATED — re-run after V2-only fix |
| `Brain/Projects/ASI-Evolve/Annotations/{7 new .md files}` | NEW — Obsidian-side annotations |
| `Brain/Projects/ASI-Evolve/Editing Agent - Roadmap.md` | UPDATED — 2026-04-25 direction lock |
| `Brain/Knowledge/API Integration/Premiere Effect Pattern Library — Recipe Corpus.md` | NEW — pattern catalog stub |

## Decisions Made

| Decision | Reasoning |
|---|---|
| **Premiere Pro is the medium** | Only `.prproj` preserves full editorial fidelity (adjustment-layer Transform keyframes, masks, full parameter state). Confirmed today via direct extraction. XMEML and AAF both drop critical data. |
| **Reading over writing — for now** | Reading prproj is straightforward (verified ObjectRef chain resolution works). Writing valid prproj is hard. Reading unblocks editing-agent work; writing only matters when pipeline produces editor-openable projects (deferred to task #17). |
| **Pattern library as the catalog** | "See it before replicate it." Every recipe gets a full parameter dump AND a comparative entry. Patterns emerge from data, not theory. Foundation for eventual replication when M3 generator needs training data. |
| **Detection-only for adjustment-layer Transforms in initial reader** | Annotation quality doesn't materially benefit from parameter values. Dense frame sampling + VLM observation captures editorial signal. Parameters add ~10% margin (mostly for style signature precision and replication). |
| **Discovery #18 (masks) folded into #16** | Same method, same reverse-engineering process. No reason for a separate session — handle as part of building the reader. |
| **Tasks #15, #10 blocked by #16** | The parser refactor + style signature work want clean `flat_timeline` from full-fidelity input. Doing them on XMEML now would require redoing on prproj later. |
| **Third-party parsers (PRPROJ-READER, prproj-rs) flagged for evaluation, not assumed useful** | Both are external GitHub projects, never tested by us. Task #16 starts with a 30-min feasibility check and documents the outcome regardless (so we don't re-evaluate them in 6 months). |
| **Defer cloud-migration thread** | Cloud migration plan exists in `Brain/Projects/RoughCut/Recipe Pipeline — Cloud Migration Status.md` but is parallel to editing-agent work. Not on the critical path for next session. |

## What's Next (next session priority order)

1. **Task #16 — Build prproj reader.** Stage 1: 30-min feasibility check on PRPROJ-READER and prproj-rs (clone, run on `Recipe XMLs/STEAK TACO.prproj`, document outcome). Stage 2: build `prproj_reader.py` that extracts full parameter fidelity. Stage 3: write per-effect discovery docs in vault. Stage 4: run on all 15 recipes, populate pattern library.
2. **Task #15 — Parser refactor** (unblocked once reader works). Build `flat_timeline`, `dense_regions`, `appearance_compilations`, `span_effects` on top of the prproj-derived JSON. ~4 hours after the reader lands.
3. **Task #10 — Style Signature v1** (blocked by #15). Mining patterns from `flat_timeline` data.
4. **Task #13 — Discrimination test** (independent of others, can run any time). Construct bad variants of basil_pesto/chicken_thighs, score, measure scorer's discriminative power.
5. **Task #14 — Close the loop on basil_pesto** (independent). Find roughcut-ai pipeline output for basil_pesto, annotate, score, compare to Dan's approved edit.
6. **Task #17 — prproj WRITER** (deferred). Round-trip generation when pipeline output for editors becomes a goal.

## Known Issues

- **baked_lobster_tail timeline anomaly** — beat 55 nest at 736-775s is far past the actual recipe duration (~60s). Other 54 beats are normal. Worth filtering or flagging.
- **5 recipes' nested appearance compilations not yet visible** to scorer beat grouping (will surface after parser refactor on prproj input). Their current scores reflect partial visibility.
- **basil_pesto flourish tags** — backfill classifier tagged all 4 speed ramps as functional including the pesto pour. Dan paused on revisiting; flagged for after Style Signature v1 gives us norms.
- **Concurrency cap on parallel Opus image-reading agents** — ~3-4 agents max. Documented in feedback memory; respect waves of 3 for any future Pass 1 work.
- **Subagent Write permission** — agents can't `Write` to paths outside session cwd. Pre-create output files; agents use `Edit`.
- **Cloud migration plan exists in parallel** — `Brain/Projects/RoughCut/Recipe Pipeline — Cloud Migration Status.md`. Not blocking editing-agent work; pick up separately if/when capacity matters.

## Quick Start for Next Session

```bash
# Read the canonical context (in this order):
cat "/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/Editing Agent - Roadmap.md"
cat "/Users/dandj/DevApps/Brain/Knowledge/API Integration/Premiere Effect Pattern Library — Recipe Corpus.md"
cat "/Users/dandj/DevApps/Brain/Knowledge/API Integration/Premiere prproj Reverse Engineering Method.md"
cat "/Users/dandj/DevApps/Brain/Knowledge/API Integration/Premiere Speed Ramp via prproj.md"

# Start task #16 — feasibility check (~30 min):
mkdir -p /tmp/prproj-eval && cd /tmp/prproj-eval
git clone https://github.com/sergeiventurinov/PRPROJ-READER
git clone https://github.com/supercuts/prproj-rs
# Try parsing STEAK TACO.prproj with each. Record outcome regardless of result.

# Verified-readable test case (Transform extraction confirmed working):
ls -la "/Users/dandj/DevApps/ASI-Evolve/Recipe XMLs/STEAK TACO.prproj"

# Already-decompressed reference (gzipped XML, 49k lines):
ls -la /tmp/steak_tacos_prproj.xml
```

## Files referenced for context

- `Brain/Projects/ASI-Evolve/Editing Agent - Roadmap.md` — master plan with 2026-04-25 direction lock
- `Brain/Knowledge/API Integration/Premiere prproj Reverse Engineering Method.md` — established method, ClassID table
- `Brain/Knowledge/API Integration/Premiere Speed Ramp via prproj.md` — first proven extraction (template for future effect docs)
- `Brain/Knowledge/API Integration/Premiere Pro API Complete Reference.md` — what's exposed via API (try API first)
- `Brain/Knowledge/API Integration/Premiere Effect Pattern Library — Recipe Corpus.md` — canonical catalog stub
- `Recipe XMLs/STEAK TACO.prproj` — verified-readable test case
- `Recipe XMLs/steak_tacos XML.aaf` — AAF reference (preserves effect types but not transform parameters)
- `Recipe XMLs/steak_tacos XML.xml` — XMEML reference (drops adjustment-layer Transforms entirely)
