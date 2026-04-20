# ASI-Evolve — Session Handoff

**Date:** 2026-04-20
**Branch:** `main`
**Last commit:** `11ce4f3` docs: session handoff 2026-04-20 (session 18)
**Role:** BUILDER

---

## Big Picture (read this first)

The endgame is a fully agentic, automated video editing process. Not a tool — an agent that edits. Dan's editorial decisions are habits and principles, not random choices. ASI-Evolve extracts those habits so they become transferable processes. When the agent encounters new footage, it knows how to tackle it because it internalized the reasoning, not just memorized cuts.

**Iteration speed principle:** The evolution loop must be 10x faster than human iteration. The agent should exhaust its own attempts first — run dozens of generations autonomously. Only surface decisions to Dan when it's genuinely stuck or the correction is high-leverage. Dan's 5 minutes of correction should fix an entire CLASS of mistakes, not one instance. Batch corrections at the rule level ("always overhead for pours"), not the clip level ("use AI2I5202 at 176s").

**Vision doc:** `~/DevApps/Brain/Projects/ASI-Evolve/Editorial Intelligence - Vision.md`

---

## What Was Done

- Built full editorial judgment annotation pipeline: frame extraction → Claude reasoning inference → Obsidian markdown → JSON → style profile → scorer integration → prompt enrichment
- Ran on both approved recipes (basil pesto 21 beats, chicken thighs 15 beats)
- Generated annotations with LLM-inferred reasoning across 3 dimensions (camera, duration, in-point)
- Modified scorer to weight beats by editorial importance and add reasoning alignment dimension
- Wired annotations into Researcher/Analyzer prompts via Jinja2 blocks

## Current State

**Working:**
- `analyze_editorial_judgment.py` runs end-to-end (frame extraction + Claude inference)
- `parse_annotations.py` correctly parses markdown → JSON with correction merging
- `aggregate_style.py` produces editorial_style.md from annotation JSONs
- Scorer accepts annotations, weights beats, checks reasoning alignment — backward compatible
- Evaluator auto-loads from `annotations/` directory
- Prompt templates have guarded `{% if %}` blocks for editorial context

**Broken / Incomplete:**
- Did NOT use /watch-video — used raw ffmpeg (2 frames per beat) instead. Missing dense visual context.
- Beat 0 (beauty) has 3 shots (front-overhead-front) but system treats each clip as individual beat. Multi-shot sequences need group-level annotation.
- ~5/21 basil pesto beats and ~7/15 chicken thighs beats got empty reasoning (Claude CLI timeouts). These show as empty fields in the markdown.
- `editorial_style.md` is verbose — reasoning strings are full paragraphs, should be distilled.

## Key Files Changed

| File | What |
|------|------|
| `experiments/recipe_pipeline/analyze_editorial_judgment.py` | Core: frame extraction + Claude reasoning inference |
| `experiments/recipe_pipeline/parse_annotations.py` | Markdown → JSON parser |
| `experiments/recipe_pipeline/aggregate_style.py` | JSON → editorial_style.md |
| `experiments/recipe_pipeline/score.py` | Added `score_with_annotations()` + `_beat_weight()` + `_score_reasoning_alignment()` |
| `experiments/recipe_pipeline/evaluator.py` | Loads annotations, passes to scorer |
| `experiments/recipe_pipeline/prompts/researcher.jinja2` | `{% if editorial_style %}` block |
| `experiments/recipe_pipeline/prompts/analyzer.jinja2` | `{% if editorial_annotations %}` block |
| `experiments/recipe_pipeline/annotations/basil_pesto.json` | Generated annotation data |
| `experiments/recipe_pipeline/annotations/chicken_thighs.json` | Generated annotation data |
| `experiments/recipe_pipeline/editorial_style.md` | Aggregated style profile |
| `~/DevApps/Brain/Projects/ASI-Evolve/Annotations/basil_pesto.md` | Dan reviews here |
| `~/DevApps/Brain/Projects/ASI-Evolve/Annotations/chicken_thighs.md` | Dan reviews here |

## Decisions Made

| Decision | Reasoning |
|----------|-----------|
| Use Claude sonnet (not opus) for bulk inference | Speed over quality — 21+ calls per recipe, each one is pattern recognition not creative |
| 180s timeout per Claude CLI call | 120s was too short for some beats. Try/except so one timeout doesn't crash the run |
| Reasoning alignment as 15% of composite | Enough to reward prompts that reflect Dan's vocabulary without dominating the score |
| Annotations in Brain vault (Obsidian markdown) | Dan reviews in his normal editing flow, corrections are natural markdown |
| Per-beat weight 1.5x for camera_swapped/added | These are high-signal: Dan actively overrode the pipeline's choice |

## What's Next

1. **Use /watch-video properly** — Run on both FINAL.mp4s for dense frame analysis (every 1-2s, full visual context). Feed that into the reasoning inference instead of 2 frames per beat.
2. **Multi-shot beat grouping** — Beat 0 has 3 shots as one editorial "beat." The annotation system needs to recognize shot sequences and annotate at the group level (why this camera rhythm?).
3. **Dan reviews annotations** — Open `Brain/Projects/ASI-Evolve/Annotations/basil_pesto.md` in Obsidian, correct wrong inferences, fill empty beats.
4. **Distill editorial_style.md** — Current version has full paragraphs. Needs to be condensed into crisp rules for prompt injection.
5. **Run the evolution loop** — With annotations wired in, run actual evolution steps and verify the Researcher uses the style profile to guide mutations.

## Known Issues

- ffmpeg frame extraction works but isn't what was planned (/watch-video gives richer context)
- Some Claude CLI calls timeout silently — produces empty reasoning fields, not errors
- Basil pesto approved edit has all clips on `v1` with `v2: null` (single-track export) — camera scoring infers from filename prefix, works fine
- `cached_recipes/` directory doesn't exist yet — evaluator can't actually run the evolution loop until pipeline manifests are cached there

## Quick Start for Next Session

```bash
cd ~/DevApps/ASI-Evolve

# Review annotations in Obsidian
open ~/DevApps/Brain/Projects/ASI-Evolve/Annotations/basil_pesto.md

# After Dan corrects annotations, re-parse and re-aggregate:
python3 experiments/recipe_pipeline/parse_annotations.py \
  --dir ~/DevApps/Brain/Projects/ASI-Evolve/Annotations/
python3 experiments/recipe_pipeline/aggregate_style.py

# To re-run analysis with /watch-video (next session's main task):
# 1. Run /watch-video on the FINAL.mp4
# 2. Feed dense visual data into analyze_editorial_judgment.py
# 3. Fix multi-shot beat grouping
```
