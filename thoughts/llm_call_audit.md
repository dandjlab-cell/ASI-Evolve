# ASI-Evolve LLM Call Audit

All external LLM calls flow through a single gateway: `utils/llm.py:LLMClient`. The OpenAI Python client is the only HTTP dependency (`from openai import OpenAI`, line 11). Every agent holds a reference to the same `LLMClient` instance, injected via `pipeline/base.py:BaseAgent.__init__()`.

## Summary Table

| # | File | Function | Line | Method | Call Name | Condition | Template |
|---|------|----------|------|--------|-----------|-----------|----------|
| 1 | `pipeline/researcher/researcher.py` | `_generate_diff()` | 95 | `llm.generate()` | `researcher_diff` | Always (diff mode) | `researcher_diff.jinja2` |
| 2 | `pipeline/researcher/researcher.py` | `_generate_full()` | 154 | `llm.extract_tags()` | `researcher_full` | Always (full rewrite mode) | `researcher.jinja2` |
| 3 | `pipeline/researcher/researcher.py` | `_generate_full()` | 156 | `llm.generate()` | `researcher_full_debug` | Only on tag extraction failure (fallback) | Same prompt as #2 |
| 4 | `pipeline/engineer/engineer.py` | `_run_judge()` | 246 | `llm.extract_tags()` | `engineer_judge` | `judge.enabled=true` in config | `judge.jinja2` (user-provided) |
| 5 | `pipeline/analyzer/analyzer.py` | `run()` | 52 | `llm.extract_tags()` | `analyzer` | Always (when analyzer enabled) | `analyzer.jinja2` |
| 6 | `pipeline/manager/manager.py` | `run()` | 33 | `llm.extract_tags()` | `manager` | `manager=true` in config, runs once | `manager.jinja2` |

## The Gateway: `utils/llm.py`

### `LLMClient` class (line 17)

**Constructor** (line 28): Takes `api_key`, `base_url`, `model`, `timeout`, `retry_times`, `retry_delay`, plus `**extra_params` (temperature, max_tokens, etc.). Creates `OpenAI(api_key, base_url, timeout)` at line 54.

**`chat()` (line 93)**: The single point where HTTP calls happen.
- Input: `messages: List[Dict[str, str]]`, optional `json_mode`, `model` override, `call_name`, `**kwargs`
- Calls `self.client.chat.completions.create(**params)` at **line 128**
- Returns `LLMResponse(content, raw_response, usage, model, call_time)`
- Retry loop: up to `retry_times` (default 3), with `retry_delay` (default 5s) between attempts
- Logs every call to thread-local `log_dir` as JSON if set

**`generate()` (line 171)**: Convenience wrapper. Builds `[{system}, {user}]` messages from `prompt` + optional `system_prompt`, delegates to `chat()`.

**`extract_tags()` (line 196)**: Calls `generate()`, then regex-parses `<tag>...</tag>` pairs from response text. Returns `Dict[str, Any]`. Raises `ValueError` if no tags found.

### `create_llm_client()` (line 289)

Factory function. Reads `config["api"]` block, splits into framework params vs extra params (temperature, max_tokens, seed, top_p), returns `LLMClient`.

### `LLMResponse` dataclass (`utils/structures.py:138`)

```python
@dataclass
class LLMResponse:
    content: str              # The text response
    raw_response: Any = None  # OpenAI response object
    usage: Dict[str, int]     # {prompt_tokens, completion_tokens, total_tokens}
    model: str = ""
    call_time: float = 0.0
```

This is the output contract. All consumers access `.content` for the text.

---

## Call Site Details

### Call #1: Researcher — Diff Mode

- **File:** `pipeline/researcher/researcher.py`
- **Function:** `_generate_diff()`, line 95
- **Method:** `self.llm.generate(prompt, call_name="researcher_diff")`
- **Prompt source:** `researcher_diff.jinja2` (always loaded from `utils/prompts/`, not experiment dir — see `prompt.py:88`). If experiment provides `researcher_diff.jinja2`, it's rendered as `user_prompt` and injected into the default template.
- **Prompt inputs:** `task_description`, `context_nodes` (serialized via `to_dict()`), `cognition_items` (serialized), `base_code`
- **Output:** Raw text containing `<name>`, `<motivation>` XML tags + SEARCH/REPLACE diff blocks
- **Parsing:** Diff blocks extracted via regex at line 99 (`extract_diffs()`), then `<name>` and `<motivation>` via inline regex (lines 122-128). Returns `{"name", "motivation", "code", "changes"}`.
- **Caller:** `Researcher.run()` → `_generate_diff()` when `diff_based=True` and `base_code` exists
- **Consumer:** `Pipeline.run_step()` (line 269) → creates `Node` with `name`, `motivation`, `code`
- **Condition:** Always-on when in diff mode (default)
- **Fallback:** If no diff blocks found (line 101), falls through to `_generate_full()` (call #2)

### Call #2: Researcher — Full Rewrite

- **File:** `pipeline/researcher/researcher.py`
- **Function:** `_generate_full()`, line 154
- **Method:** `self.llm.extract_tags(prompt, call_name="researcher_full")`
- **Prompt source:** `researcher.jinja2` (experiment-level first, then `utils/prompts/` default)
- **Prompt inputs:** `task_description`, `context_nodes`, `cognition_items`, `base_code=None`, `diff_based=False`
- **Output:** Dict with keys `name`, `motivation`, `code` (parsed from XML tags by `extract_tags()`)
- **Caller:** `Researcher.run()` when `diff_based=False` or no `base_code`, or as fallback from diff mode
- **Consumer:** Same as #1 — `Pipeline.run_step()` → `Node`
- **Condition:** Always-on in full rewrite mode; also serves as fallback for diff mode failures

### Call #3: Researcher — Full Rewrite Debug (fallback)

- **File:** `pipeline/researcher/researcher.py`
- **Function:** `_generate_full()`, line 156
- **Method:** `self.llm.generate(prompt, call_name="researcher_full_debug")`
- **Prompt source:** Same prompt as #2
- **Output:** Raw `LLMResponse` (used only for error logging)
- **Caller:** Only triggered inside `except ValueError` block (line 155) when `extract_tags()` fails
- **Consumer:** None — response is logged then `raise` re-throws
- **Condition:** Error path only. Never produces usable output.

### Call #4: Engineer — LLM Judge

- **File:** `pipeline/engineer/engineer.py`
- **Function:** `_run_judge()`, line 246
- **Method:** `self.llm.extract_tags(prompt, call_name="engineer_judge")`
- **Prompt source:** `judge.jinja2` — must be user-provided in experiment prompts dir (no default template exists)
- **Prompt inputs:** `code` (the candidate program), `results` (stringified eval results), `task_description`
- **Output:** Dict expected to contain `score` (float 0-100) and `reason`/`reasoning`
- **Parsing:** `score` clamped to [0, 100] at line 251. `reason` logged at line 258.
- **Caller:** `Engineer.run()` at line 84, only when `judge_enabled=True` AND `success=True`
- **Consumer:** `Pipeline.run_step()` — blended score: `final = (1-ratio) * eval_score + ratio * judge_score`
- **Condition:** Conditional. `judge.enabled: false` by default in config.yaml.

### Call #5: Analyzer — Lesson Extraction

- **File:** `pipeline/analyzer/analyzer.py`
- **Function:** `run()`, line 52
- **Method:** `self.llm.extract_tags(prompt, call_name="analyzer")`
- **Prompt source:** `analyzer.jinja2` (experiment-level first, then `utils/prompts/` default)
- **Prompt inputs:** `code`, `results` (JSON stringified), `task_description`, `best_sampled_node` (dict with name/score/motivation/code/results/analysis or None)
- **Output:** Dict expected to contain `analysis` (natural language summary)
- **Caller:** `Pipeline.run_step()` at line 329, after engineer completes
- **Consumer:** Stored on `Node.analysis`. Also fed into `Cognition` for future retrieval.
- **Condition:** Always-on (when analyzer agent enabled, which is the default)

### Call #6: Manager — Meta-Prompt Generation

- **File:** `pipeline/manager/manager.py`
- **Function:** `run()`, line 33
- **Method:** `self.llm.extract_tags(prompt, call_name="manager")`
- **Prompt source:** `manager.jinja2` (default in `utils/prompts/`)
- **Prompt inputs:** `task_description`, `eval_criteria` (from `eval_criteria.md` file)
- **Output:** Dict expected to contain `researcher_prompt` and `analyzer_prompt`
- **Parsing:** Extracted prompts saved as Jinja2 templates to experiment prompts dir (lines 43-45)
- **Caller:** `Pipeline.run_step()` → `_run_manager()` at line 225
- **Consumer:** `PromptManager` is reloaded after manager runs (line 228). Future researcher/analyzer calls use the generated prompts.
- **Condition:** Conditional. `manager: false` by default. Runs exactly once per experiment (guarded by `manager_initialized` flag).

---

## Architecture Summary

```
config.yaml (api block)
    │
    ▼
create_llm_client() ──► LLMClient (single instance)
                              │
                    ┌─────────┼─────────────┐
                    │         │             │
                    ▼         ▼             ▼
              Researcher   Engineer     Analyzer    Manager
              (BaseAgent)  (BaseAgent)  (BaseAgent) (BaseAgent)
                    │         │             │          │
                    │    [subprocess]       │          │
                    │    runs eval.sh       │          │
                    │         │             │          │
                    ▼         ▼             ▼          ▼
              llm.generate  llm.extract   llm.extract llm.extract
              llm.extract    _tags         _tags       _tags
                    │         │             │          │
                    └────┬────┘─────────────┘──────────┘
                         ▼
                  LLMClient.chat()
                         │
                         ▼
              client.chat.completions.create()  ← SINGLE HTTP CALL SITE
                         │
                         ▼
                    LLMResponse
```

## Key Facts for Phase 2 (Replacement)

1. **Single HTTP call site:** `utils/llm.py:128` — `self.client.chat.completions.create(**params)`. Replace this one line (and the OpenAI client setup) to redirect all LLM traffic.

2. **Three public methods** on `LLMClient`:
   - `chat(messages, json_mode, model, call_name, **kwargs) → LLMResponse`
   - `generate(prompt, system_prompt, json_mode, call_name, **kwargs) → LLMResponse` (wrapper around `chat`)
   - `extract_tags(prompt, system_prompt, call_name, **kwargs) → Dict[str, Any]` (wrapper around `generate` + XML parsing)

3. **Output contract:** `LLMResponse` dataclass with `.content` (str), `.raw_response` (Any), `.usage` (dict), `.model` (str), `.call_time` (float). The `raw_response` is only accessed in `_log_call_to_file()` for `finish_reason` (line 278).

4. **No streaming.** All calls are synchronous request-response.

5. **Thread safety:** `LLMClient` uses thread-local storage for logging (`_thread_local`). The pipeline uses `ThreadPoolExecutor` for parallel mode. The replacement must be thread-safe.

6. **Retry logic lives in `LLMClient.chat()`** (lines 125-169). The replacement can keep or replace this.

7. **`json_mode`** is only a parameter — never actually used by any agent (all callers pass default `False` or use `extract_tags` which forces `json_mode=False`).

8. **`extract_tags()` does its own XML parsing** (lines 215-242). This is independent of the LLM — it just needs `.content` from the response.

9. **No judge template ships with the repo.** Experiments must provide their own `judge.jinja2`.

10. **Manager runs once** per experiment lifetime, writes templates to disk, then `PromptManager` reloads them. It's a bootstrap step, not part of the evolution loop.

## Prompt Template Inventory

| Template | Location | Used By | Expected Output Tags |
|----------|----------|---------|---------------------|
| `researcher.jinja2` | `utils/prompts/` (default) | Researcher full rewrite | `<name>`, `<motivation>`, `<code>` |
| `researcher_diff.jinja2` | `utils/prompts/` (default, always) | Researcher diff mode | `<name>`, `<motivation>` + SEARCH/REPLACE blocks |
| `analyzer.jinja2` | `utils/prompts/` (default) | Analyzer | `<analysis>` |
| `manager.jinja2` | `utils/prompts/` (default) | Manager | `<researcher_prompt>`, `<analyzer_prompt>` |
| `judge.jinja2` | experiment prompts dir (user-provided) | Engineer judge | `<score>`, `<reason>` or `<reasoning>` |

## Verified: No Missed Call Sites

Grep for `llm.generate`, `llm.chat`, `llm.extract_tags`, `client.chat.completions.create`, `openai`, and `self.llm.` across the entire repo confirms all LLM interactions are captured in calls #1-#6 above. The only `openai` import is in `utils/llm.py:11`.
