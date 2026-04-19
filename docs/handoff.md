# ASI-Evolve — Session Handoff

**Date:** 2026-04-19
**Branch:** `main`
**Last commit:** `3b76653` docs: recipe pipeline evolution design sketch
**Role:** BUILDER

---

## What Was Done

- Forked GAIR-NLP/ASI-Evolve to `dandjlab-cell/ASI-Evolve`, cloned to `~/DevApps/ASI-Evolve/`
- Phase 1: Audited all 6 LLM call sites across 4 agents. Single gateway at `utils/llm.py:LLMClient`
- Phase 2: Replaced OpenAI SDK with Claude CLI subprocess backend. Single file change (`utils/llm.py`). Removed `openai` dependency.
- Solved CLAUDE.md/MCP contamination: `cwd=/tmp` + `--strict-mcp-config` + `--tools ""` = clean invocations (0 cache tokens, 6x cost reduction)
- Smoke-tested `generate()` and `extract_tags()` from terminal — both work end-to-end
- Designed recipe pipeline evolution: evolve prompts + weights + timing constants against Dan's approved Premiere XMLs
- All docs mirrored to Brain vault at `Projects/ASI-Evolve/`

## Current State

- **Working:** LLMClient with Claude CLI backend. `generate()`, `extract_tags()` verified. Pushed to fork.
- **Not yet tested:** Full ASI-Evolve pipeline (researcher → engineer → analyzer loop). Circle packing demo not yet run end-to-end.
- **Not yet built:** Recipe pipeline evolution experiment (needs cache infrastructure, slim runner, scoring function)

## Key Files Changed

| File | What changed |
|------|-------------|
| `utils/llm.py` | Replaced OpenAI client with `claude -p` subprocess via stdin |
| `config.yaml` | Simplified API block (model, timeout, retry, claude_path) |
| `experiments/circle_packing_demo/config.yaml` | Same API simplification |
| `requirements.txt` | Removed `openai>=1.0.0` |
| `thoughts/llm_call_audit.md` | Phase 1 audit — all call sites mapped |
| `thoughts/cli_json_format.md` | CLI JSON response format documentation |
| `thoughts/roughcut_recipe_evolution.md` | Recipe pipeline evolution design |

## Decisions Made

| Decision | Reasoning |
|----------|-----------|
| Claude CLI subprocess (not Anthropic SDK) | Zero API keys, uses Dan's CC subscription, no external dependencies |
| Stdin piping (not command args) | Avoids ARG_MAX limits and shell escaping with code snippets |
| `cwd=/tmp` + `--strict-mcp-config` | Prevents CLAUDE.md and MCP server contamination (10K+ token overhead) |
| Default model = opus | Research framework — output quality > cost. Dan is on subscription. |
| Evolve config module, not pipeline code | Pipeline is 3,684 lines of production code. Evolving prompts + weights is safer, faster, and human-readable. |
| Cache expensive stages, re-run only LLM decisions | Full pipeline = 45 min/recipe. Decision stages only = 2 min/recipe. Makes evolution feasible (4 hrs vs 90 hrs). |

## What's Next

1. **Run circle_packing_demo end-to-end** — validate the full ASI-Evolve loop works with Claude CLI backend
2. **Identify 6-8 finished recipe edits** — need footage + Dan's final Premiere XMLs as ground truth
3. **Build cache extraction** — pull scan.json, audio_sync.json, clip_narratives.json from existing pipeline runs
4. **Build slim pipeline runner** — extract decision stages from `build_editlist.py` into standalone script
5. **Extend manifest_diff** — add numeric scoring (precision, recall, timing accuracy, camera match rate)
6. **Wire recipe evolution experiment** — create ASI-Evolve experiment dir with prompts + eval.sh

## Known Issues

- `--model haiku` maps to sonnet (haiku may not be available on Dan's plan)
- `--tools ""` doesn't parse correctly in zsh multi-line pipes — keep commands on single lines
- Can't test Claude CLI subprocess from within Claude Code sessions (nested session restriction) — test from regular terminal
- Circle packing demo hasn't been run yet — may surface issues with the CLI backend under real load

## Quick Start for Next Session

```bash
cd ~/DevApps/ASI-Evolve
# Read the design sketch
cat thoughts/roughcut_recipe_evolution.md
# Validate the loop works — run circle packing demo
python3 main.py --experiment circle_packing_demo --steps 2
```
