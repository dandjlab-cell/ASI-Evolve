# ASI-Evolve — Session Handoff

**Date:** 2026-04-20
**Branch:** `main`
**Last commit:** `a853a94` fix: camera scoring uses filename prefix
**Role:** BUILDER

---

## What Was Done (Session 16)

- Fixed macOS ARM segfault (`TOKENIZERS_PARALLELISM=false`, `OMP_NUM_THREADS=1`, deprecated embedding API)
- Fixed `init_cognition.py` bootstrap, ran cognition init (12 knowledge items)
- **Circle packing demo validated**: step 0→0.96, step 1→2.60, step 2→2.61 (98.9% of 2.635 target)
- Fixed Claude generating `<tool_call>` instead of content tags (added "no tools" system prompt)
- Built recipe pipeline evolution experiment (`experiments/recipe_pipeline/`)
- Parsed real Premiere XMLs (basil pesto, chicken thighs) → baseline scores 50.6 / 46.6
- Fixed camera scoring to use filename prefix (Premiere exports single-track)
- Built web dashboard with drag-and-drop XML upload

## Current State

- **Working:** Full ASI-Evolve loop (circle packing validated). Recipe scoring infrastructure. Dashboard.
- **Baseline scores:** basil_pesto=50.6, chicken_thighs=46.6 (composite, 0-100)
- **Approved XMLs:** 2 of 5 recipes parsed (basil_pesto, chicken_thighs)
- **Not yet built:** Slim pipeline runner (runs decision stages with evolved config)

## Key Files

| File | Purpose |
|------|---------|
| `utils/llm.py` | Claude CLI backend (+ "no tools" system prompt fix) |
| `main.py` | Entry point (+ macOS ARM threading fix) |
| `dashboard.py` | Web UI for experiments |
| `Open Dashboard.command` | Double-click launcher |
| `experiments/recipe_pipeline/score.py` | 4-metric scoring (precision/recall/timing/camera) |
| `experiments/recipe_pipeline/xml_to_manifest.py` | Premiere FCP XML → manifest JSON |
| `experiments/recipe_pipeline/evaluator.py` | ASI-Evolve-compatible eval harness |
| `experiments/recipe_pipeline/initial_program` | Seed config (current pipeline defaults) |
| `experiments/recipe_pipeline/approved_edits/` | Dan's exported XMLs → JSON |
| `experiments/recipe_pipeline/cached_recipes/` | Symlinks to roughcut-ai/runs/* |
| `Recipe XMLs/` | Raw Premiere XML exports from Dan |

## What's Next

1. **Export remaining XMLs** — korean fried chicken, cucumber sandwich, banana muffins
2. **Build slim pipeline runner** — extracts decision stages from `build_editlist.py` into standalone script that takes cached data + evolved config → manifest
3. **Wire recipe evolution end-to-end** — run ASI-Evolve with recipe experiment (start with 5-step validation)
4. **Future: editorial judgment** — evolve not just "which clip" but "why this clip" (camera choice heuristics, hold duration, pacing)
5. **Future: manifest skills** — speed ramping, stop motion (2-frame per shot), transitions — output capabilities the evolved config can trigger

## Baseline Scores (real XMLs)

| Recipe | Precision | Recall | Timing | Camera | Composite |
|--------|-----------|--------|--------|--------|-----------|
| Basil Pesto | 17.5% | 47.6% | 75.9% | 100% | 50.6 |
| Chicken Thighs | 10.5% | 40.0% | 79.5% | 100% | 46.6 |

Key insight: pipeline over-generates (57 clips vs 15-21 used). Precision is the main lever.

## Known Issues

- `--tools ""` doesn't suppress tool-call generation (fixed with system prompt, but fragile)
- Dashboard background processes don't persist from Claude Code — use `Open Dashboard.command`
- Banana muffins uses different camera prefix (`A057` not `B19I`) — v1 prefix detection handles this
