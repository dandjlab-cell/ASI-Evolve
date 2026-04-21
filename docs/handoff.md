# ASI-Evolve — Session Handoff

**Date:** 2026-04-21
**Branch:** `main`
**Last commit:** `2c6e197` feat: zone-based beat grouping, MOGRT detection, frame-analysis descriptions, tighter prompts
**Role:** BUILDER

---

## What Was Done

- Re-ran `xml_to_manifest.py` with session-19 rewrite: basil pesto 21->33 clips, chicken thighs 15->39 clips (file ID lookup resolves nested/referenced clips)
- Fixed MOGRT detection in parser: `.aegraphic` files (Premiere's MOGRT export format) now captured. 8 ingredient MOGRTs in basil pesto, 13 in chicken thighs
- Fixed title card threshold: MOGRTs starting at 0.0s = title cards, anything after = ingredient text
- Rewrote `analyze_editorial_judgment.py` with zone-based beat grouping:
  - Title card zone (0-3.9s) = beauty opener beat (all clips grouped as one)
  - MOGRT zones = ingredient beats (clips under same text overlay grouped)
  - Stop-motion clips (consecutive <=6 frames) = collapsed into one beat
  - Remaining = standalone beats
- Beat descriptions now derived from `/watch-video` frame analysis when no pipeline match (was using stale `beats.json` index, which misaligned)
- Fixed LLM response parser: Sonnet returns `**CAMERA:**` (bold markdown), parser now strips `*` and `_` markers
- Tightened prompts: 1 sentence per reasoning field, music/rhythm context, no hedging
- Added effects context per clip: speed ramps, scale/zoom, nested sequences passed to LLM prompt
- Added MOGRT overlay context: ingredient text card presence flagged in prompt
- Added recipe section inference: beauty opener -> ingredient dump -> prep -> technique -> transformation -> money shot -> beauty close
- Ran v4 annotations (with all fixes): basil pesto 29 beats, chicken thighs 30 beats
- Ran `aggregate_style.py`: 59 beats combined
- Created Brain note: `Knowledge/API Integration/Premiere FCP XML Structure.md`
- Updated `Knowledge/Knowledge Map.md` with new note
- Cleaned up duplicate `Basil Pesto FINAL.json` from approved_edits/

## Current State

**Working:**
- `xml_to_manifest.py` — fully extracts clips, effects, MOGRTs, production layers from FCP XML
- `analyze_editorial_judgment.py` — zone-based grouping, effects context, frame-analysis descriptions, fixed parser
- v4 annotation outputs exist for both recipes (JSON + Obsidian markdown)
- `aggregate_style.py` — aggregates across recipes

**Needs re-running (IMPORTANT):**
- The v4 annotations used the fixed parser BUT the beat descriptions for "added" clips still fell back to `beats.json` index (wrong). A v5 fix was made to derive descriptions from frame analysis instead. **The v5 annotations have NOT been run yet.** This is the first thing to do next session.

**Not started:**
- Dan has not reviewed/corrected any annotations yet (the "Dan's correction:" fields are all empty)
- MOGRT text content is NOT in FCP XML — only template name and timecodes. The actual ingredient text lives in `.aegraphic` binaries on the footage drive.

## Key Files Changed

| File | What Changed |
|------|-------------|
| `experiments/recipe_pipeline/xml_to_manifest.py` | `.aegraphic` MOGRT detection, title card threshold fix (<0.5s) |
| `experiments/recipe_pipeline/analyze_editorial_judgment.py` | Zone-based grouping, effects/MOGRT/section context, frame-analysis descriptions, bold-markdown parser fix, tighter prompts |
| `experiments/recipe_pipeline/approved_edits/basil_pesto.json` | Regenerated (33 clips, editorial_techniques, production_layers) |
| `experiments/recipe_pipeline/approved_edits/chicken_thighs.json` | Regenerated (39 clips, editorial_techniques, production_layers) |
| `experiments/recipe_pipeline/annotations/basil_pesto.json` | v4 annotations (29 beats) — needs v5 re-run |
| `experiments/recipe_pipeline/annotations/chicken_thighs.json` | v4 annotations (30 beats) — needs v5 re-run |
| `experiments/recipe_pipeline/editorial_style.md` | Re-aggregated (59 beats) |
| `Brain/Knowledge/API Integration/Premiere FCP XML Structure.md` | NEW — FCP XML reference (file IDs, timeremap, scale, nested, stop-motion, production layers) |
| `Brain/Knowledge/Knowledge Map.md` | Added FCP XML Structure link |

## Decisions Made

| Decision | Reasoning |
|----------|-----------|
| Zone-based grouping over per-clip analysis | Dan's "beats" are editorial units, not clip placements. Title card = beauty opener group, MOGRT = ingredient group. Saves LLM calls and produces correct beat numbering. |
| Frame-analysis descriptions for unmatched clips | `beats.json` indices don't align with approved edit clip indices. Frame analysis at the clip's timecode describes what's actually on screen. |
| Keep Sonnet (not Opus) for annotation calls | Cost/speed: ~30 calls per recipe. Sonnet quality is adequate when prompts are specific. Can upgrade low-confidence beats to Opus later. |
| MOGRTs can't provide ingredient text | FCP XML only exports template name + timecodes, not MOGRT parameter values. Text lives in `.aegraphic` binary. Timecodes are sufficient for grouping. |
| Filter watermarks from overlay context | Watermarks span the full timeline — not editorial signals. Only MOGRTs and title cards passed to LLM. |
| Beauty opener always uses title card boundary | Non-negotiable grouping rule per Dan: clips under title card = one beat, don't try to match to pipeline beats. |

## What's Next

1. **Run v5 annotations** — the frame-analysis description fix is committed but not run. Execute both recipes:
   ```bash
   cd ~/DevApps/ASI-Evolve/experiments/recipe_pipeline
   python analyze_editorial_judgment.py \
       --recipe basil_pesto \
       --approved approved_edits/basil_pesto.json \
       --manifest ~/DevApps/roughcut-ai/runs/basil_pesto/basil_pesto_manifest.json \
       --scan ~/DevApps/roughcut-ai/runs/basil_pesto/scan.json \
       --beats ~/DevApps/roughcut-ai/runs/basil_pesto/beats.json \
       --frame-analysis ~/DevApps/storyboard-gen/docs/watch-video/pass1_basil_pesto.md \
       --output ~/DevApps/Brain/Projects/ASI-Evolve/Annotations/basil_pesto.md \
       --json-output annotations/basil_pesto.json \
       --model sonnet
   ```
   (Same for chicken_thighs with corresponding paths)
2. **Re-run `aggregate_style.py`** after v5 annotations complete
3. **Dan reviews annotations** in Obsidian — fill in "Dan's correction:" fields where LLM reasoning is wrong
4. **Consider Opus pass** on low-confidence beats if Sonnet quality is insufficient after review
5. **Deferred:** Update `aggregate_style.py` to use new fields (effects, recipe_section, MOGRT context)

## Known Issues

- v4 annotations have wrong beat descriptions for "added" clips (uses `beats.json` index instead of frame analysis). v5 code fix is committed but annotations not re-run.
- Some late-edit beats show `...` for description — these are clips with no pipeline match AND no frame analysis coverage (usually the very end of the video where frame analysis at 2fps doesn't reach)
- The global style analysis prompt still produces 4-5 paragraphs. Could tighten further.
- `editorial_group` verdict is used for both beauty opener and MOGRT zones — might want to distinguish these in the aggregator

## Quick Start for Next Session

```bash
cd ~/DevApps/ASI-Evolve/experiments/recipe_pipeline
# Run v5 annotations (both recipes, ~5 min each)
python analyze_editorial_judgment.py --recipe basil_pesto --approved approved_edits/basil_pesto.json --manifest ~/DevApps/roughcut-ai/runs/basil_pesto/basil_pesto_manifest.json --scan ~/DevApps/roughcut-ai/runs/basil_pesto/scan.json --beats ~/DevApps/roughcut-ai/runs/basil_pesto/beats.json --frame-analysis ~/DevApps/storyboard-gen/docs/watch-video/pass1_basil_pesto.md --output ~/DevApps/Brain/Projects/ASI-Evolve/Annotations/basil_pesto.md --json-output annotations/basil_pesto.json --model sonnet
# Then aggregate
python aggregate_style.py --dir annotations/ --output editorial_style.md
```
