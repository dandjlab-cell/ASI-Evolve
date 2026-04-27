# Recipe Pipeline — Session Handoff (2026-04-27)

**Date:** 2026-04-27
**Branch:** `main`
**Last commits:**
- ASI-Evolve `9422103` — prproj reader + effect reasoning + A/B diff harness
- ASI-Evolve `b22fbae` — session handoff doc
- Brain `e648860` — ASI-Evolve session: vocabulary v2, prproj writer plan, full effect decoder

**Role:** BUILDER

---

## Session goal

Lock down the vocabulary of editorial intents (across all 17 corpus recipes), decode every effect parameter format we'd need to write a fresh Premiere project from scratch, and decide the production-system architecture for the manifest writer.

## What Was Done

### Vocabulary work
- Built `recipe-analyze` skill at `~/.claude/skills/recipe-analyze/` — orchestrates `prproj_reader` → frame extraction → Opus editorial reasoning → pattern library refresh
- Reran all 17 recipes through image-mode editorial reasoning (Opus reads actual rendered frames at every cut + effect boundary)
- Generated **Editorial Intents Vocabulary v1** at `Brain/Projects/ASI-Evolve/Editorial Intents Vocabulary v1.md` — 7 categories, 26 entries, each with Definition + Realization + Recipes-cited + Counter-examples
- Refined Stop-Motion category based on Dan's feedback:
  - Two distinct patterns (`no-hands-addition` normal-paced vs `frame-staccato-stop-motion` 2-frame-per-clip)
  - Shared constraints: locked overhead, hands don't block action (off-camera reach OK)
  - Frame-staccato has ~5-frame entry hold + 2-frame body + ~5-frame exit hold (canonical structure)
  - Exit hold extends past 5 frames when chaining into a Transform zoom-in (chained-effect rule)
- Added `masked-hand-over-staccato` entry — composite of object-aware mask on hand layer + frame-staccato underneath. Steak_tacos sheet-pan moment is the canonical example.

### Decoder work
- Added speed-ramp extraction to `prproj_reader.py` — TimeRemapping + PlaybackSpeed now flow through to dumps
- Verified all Mask2 Type values (was guessing before):
  - `0` = system companion mask
  - `1` = Ellipse Mask Tool
  - `2` = Rectangle Mask Tool
  - `3` = Pen Mask Tool
  - `4` = Object Mask Tool (Sensei)
- Verified Lumetri pid → UI panel mapping via A/B tests:
  - pid 20 = Basic Correction Saturation
  - pid 31 = Creative Saturation
  - pid 90 = HSL Secondary Saturation
  - pid 51 = Vignette Amount
- Decoded project skeleton XML for the writer (3 A/B pairs):
  - Bin / nested bin (`BinProjectItem` ClassID `dbfd6653-...`)
  - Media import (`MasterClip` + `Media` + `VideoMediaSource` + `VideoStream` + `ClipProjectItem` + `ClipLoggingInfo`)
  - Empty sequence (~50 elements: Sequence + TrackGroups + per-track ClipTracks + audio mixer)
  - Nested-sequence-as-clip (via `VideoSequenceSource` instead of `VideoMediaSource`)
- All ClassIDs documented in `Brain/Knowledge/API Integration/Effect Replication Recipes.md`

### Architecture decision
- **Prproj-direct is the primary path** for the production manifest writer
- UXP can't do speed ramps (per Adobe API: "Set speed: NO"); UXP can't do MOGRT text (per existing vault notes); both are core editorial elements
- Server-deployable, no Premiere needed at build time, no plugin install for editors
- Confirmed V1/V2 sync happens upstream (`audio_sync.py` cross-correlates audio → pairs.json with offsets → `build_editlist.py` grounding picks pre-aligned source coords). Recipe writer is dumb placement: V1 on track 1, V2 on track 2, both at same `timeline_in`. No offset math.
- **The detailed plan for next session is at `Brain/Projects/ASI-Evolve/Prproj-Direct Writer Plan.md`**

## Current State

**What works end-to-end:**
- Reader: any `.prproj` → JSON dump with cuts, effects, masks, speed ramps, MOGRT text, Lumetri params, Mirror, Replicate
- `recipe-analyze` skill: prproj → 2fps + 12fps frames → Opus editorial reasoning → pattern library refresh
- Vocabulary clustering: 17 OBSERVATIONS sections → curated 26-entry intent catalog
- A/B diff harness: any two prprojs → byte-level diffs in matching ArbVideoComponentParams

**What's documented:**
- Effect Replication Recipes — every parameter for every effect we use, with verified values from steak_tacos
- Stop-motion vocabulary fully refined (4 entries with shared constraints + 5-2-5 frame rule)
- Speed ramp encoding (per `Premiere Speed Ramp via prproj.md`)
- MOGRT text encoding (`textEditValue` UTF-16 JSON inside ArbVideoComponentParam)
- Mask Type discriminator (0/1/2/3/4 mapping verified)
- Bin/Media/Sequence/NestedSequence ClassIDs

**What's not yet built:**
- The prproj-direct writer (`manifest_to_prproj.py`) — round-by-round plan exists, build is next session
- Mirror Reflection Angle visual semantics (storage verified; visual mapping needs in-Premiere observation — 5 min check on existing test prprojs)
- Replicate Count visual semantics (same — 5 min check)

## Key Files Changed

| File | What |
|---|---|
| `experiments/recipe_pipeline/prproj_reader.py` | Speed ramp extraction added; Mask vertex decode; full param dumps for Transform/Lumetri/Mirror/Replicate |
| `experiments/recipe_pipeline/effect_reasoning/run_effect_reasoning.py` | Compact effects table for Opus prompts; speed-ramp column added |
| `experiments/recipe_pipeline/effect_reasoning/run_effect_reasoning_with_images_cli.py` | Image-mode reasoning runner — uses frame_index for 12fps dense-region frames |
| `experiments/recipe_pipeline/effect_reasoning/cluster_vocabulary.py` | NEW — synthesizes OBSERVATIONS into the editorial-intent vocabulary |
| `experiments/recipe_pipeline/prproj_ab_diff/diff_arb_payloads.py` | A/B diff harness — used to decode Mask Type, Lumetri pids, MOGRT text |
| `experiments/recipe_pipeline/prproj_dumps/*.json` | 18 effect dumps (17 recipes + 1 legacy duplicate) |
| `~/.claude/skills/recipe-analyze/SKILL.md` | NEW — orchestrator skill doc |
| `~/.claude/skills/recipe-analyze/scripts/orchestrate.sh` | NEW — chains reader → frames → reasoning → library refresh |
| `~/.claude/skills/recipe-analyze/scripts/extract_frames_for_prproj.py` | NEW — 2fps baseline + 12fps in dense regions identified from effects JSON |
| `~/.claude/skills/recipe-analyze/scripts/refresh_pattern_library.py` | NEW — auto-refreshes the cross-recipe headline-stats table |
| `Brain/Knowledge/API Integration/Effect Replication Recipes.md` | NEW — canonical reference; every effect's full param spec |
| `Brain/Knowledge/API Integration/Premiere Adjustment Layer Transform via prproj.md` | UPDATED — Uniform Scale semantics corrected |
| `Brain/Knowledge/API Integration/Premiere Mask2 via prproj.md` | UPDATED — full Type → tool table |
| `Brain/Knowledge/API Integration/Premiere prproj Reverse Engineering Method.md` | UPDATED — extended ClassID table with bin/media/sequence elements |
| `Brain/Projects/ASI-Evolve/Editorial Intents Vocabulary v1.md` | NEW — 7-category, 26-entry vocabulary |
| `Brain/Projects/ASI-Evolve/Prproj-Direct Writer Plan.md` | NEW — round-by-round build plan for next session |
| `Brain/Projects/ASI-Evolve/Test Prprojs Needed.md` | UPDATED — closed (all primary tests done) |
| `Brain/Projects/ASI-Evolve/Annotations/{recipe} — Effect Reasoning (image mode).md` | 17 NEW files — Opus reasoning per recipe |

## Decisions Made

| Decision | Reasoning |
|---|---|
| **Prproj-direct as primary writer architecture** | UXP can't do speed ramps (Adobe API: "Set speed: NO"). Recipes use them constantly. Without prproj-direct, an entire editorial layer is unencodable. Plus: server-deployable, no plugin install, deterministic. |
| **Stop-Motion is its own vocabulary category, with TWO distinct patterns** | Dan corrected the conflation: `no-hands-addition` (normal pace, defined by hand-presence) is orthogonal to `frame-staccato-stop-motion` (defined by 2-frame-per-clip cut rate). Both can stack. |
| **5-frame bookends are non-negotiable for staccato sequences** | Without them the staccato feels jarring on entry/exit. Exit hold extends past 5 when chaining into a zoom transition. |
| **MOGRT counts are tooling noise, NOT editorial signature** | Saved as feedback memory previously — Dan added MOGRTs because manifest can't get text in any other way. Don't infer text-style preferences from Capsule density. |
| **Verified Mask Type table over assumed** | Had been guessing Type=4=object-aware from correlation. Ran A/B tests (`MASK_PEN`, `MASK_ELLIPSE`) → confirmed 0=companion, 1=Ellipse, 2=Rectangle, 3=Pen, 4=Object. |
| **V1/V2 sync is upstream concern, not writer concern** | Read `roughcut-ai/premiere-plugin/lib/ppro-api.js:596-684` — recipe pipeline writer doesn't consume `audio_offset_s`. Sync was applied during manifest generation by `audio_sync.py`. By manifest-write time, source coords already represent the same wall-clock moment. |
| **Object-aware mask geometry stays editor's responsibility** | Sensei generates the Tracker payloads on-click. Manifest emits Type=4 placeholder + marker; editor clicks Object Mask Tool; Sensei populates everything. We don't need to decode the FlatBuffers tracker format. |
| **Image-mode reasoning beats text-only reasoning** | Image mode caught visual details (red garlic press, hand-presence patterns, mask-isolated hand exits) that text descriptors lost. Quality lift validated end-to-end across all 17 recipes. |
| **Vocabulary clustering used `--no-annotation` flag for Opus calls** | Existing per-beat annotation caused Opus to anchor to its prose framing instead of deriving from effects + frames. Removing it dramatically improved precision (verified on steak_tacos title-card section bug). |

## What's Next

1. **Build round 1 of the prproj-direct writer** — `manifest_to_prproj.py` that takes basil_pesto's existing manifest + ffprobe + emits a working prproj with bins + media + sequence + V1 clips. Spec is in `Brain/Projects/ASI-Evolve/Prproj-Direct Writer Plan.md` §"Round 1".
2. **Verify round 1** — open generated prproj in Premiere, spot-check 3 clips, round-trip read it with the existing `prproj_reader.py` to confirm values match the manifest exactly.
3. **Round 2** — V2 + MOGRTs (proves the prproj-direct MOGRT path UXP can't do).
4. **Round 3** — Effects layer (the editorial-intent vocabulary: Transforms, speed ramps, Lumetri, masks, kaleidoscopes).
5. **Round 4** — Manifest schema v2 design with intent tags per beat.
6. **Side task (~10 min)** — open `MIRROR_ANGLE_0/90` and `REPLICATE_2/3` in Premiere, observe and document the visual semantics. Updates to `Effect Replication Recipes.md`.

## Known Issues

- **steak_tacos vs steak_taco slug duplicate** — `prproj_dumps/` has both. The reader's slugifier produced `steak_taco` from `STEAK TACO.prproj` filename; later we copied to `steak_tacos_effects.json` for consistency. Only impacts directory listings; effect-reasoning files use `steak_tacos`. Cleanup: delete `steak_taco_effects.json`.
- **baked_lobster_tails reports 775s duration** — known parser anomaly from prior handoff (beat 55 nest at 736s far past actual ~60s recipe). Cosmetic; effects extraction is fine.
- **Mirror reflection-angle + Replicate count visual semantics unverified** — storage formats are decoded; what specific values (angle 0 vs 90, count 2 vs 3) DO visually requires opening the test prprojs in Premiere. 5-minute check.

## Quick Start for Next Session

```bash
# Read the canonical context (in this order):
cat "/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/Prproj-Direct Writer Plan.md"
cat "/Users/dandj/DevApps/Brain/Knowledge/API Integration/Effect Replication Recipes.md"
cat "/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/Editorial Intents Vocabulary v1.md"

# Confirm the existing reader still works:
cd /Users/dandj/DevApps/ASI-Evolve
python3 experiments/recipe_pipeline/prproj_reader.py "Recipe XMLs/STEAK TACO.prproj"

# Existing manifest to use as input for round 1 writer:
cat /Users/dandj/DevApps/roughcut-ai/runs/basil_pesto/basil_pesto_manifest.json | python3 -m json.tool | head -50

# Test prprojs available for verification:
ls "/Users/dandj/DevApps/ASI-Evolve/experiments/PREMIERE PROJECTS/TESTS/"

# Round 1 starts here — build manifest_to_prproj.py at:
# /Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline/manifest_to_prproj/
```
