# Claude CLI JSON Output Format

Verified 2026-04-19 via manual testing from regular terminal.

## Clean Invocation Pattern

```bash
echo "prompt" | claude -p \
  --system-prompt "system prompt here" \
  --output-format json \
  --no-session-persistence \
  --tools "" \
  --strict-mcp-config \
  --model sonnet
```

**Critical flags for isolation:**
- `cwd` must be a directory with no CLAUDE.md (use `/tmp` or experiment dir)
- `--strict-mcp-config` prevents global MCP servers from loading (n8n, etc.)
- `--tools ""` disables all built-in tools
- `--no-session-persistence` prevents session clutter
- Must unset `CLAUDECODE` env var to allow nested invocation

Without isolation: 10K+ cache creation tokens of CLAUDE.md + MCP bloat per call.
With isolation: 0 cache creation tokens, ~1,842 input tokens (base system prompt only).

## JSON Response Structure

```json
{
    "type": "result",
    "subtype": "success",
    "is_error": false,
    "duration_ms": 2192,
    "duration_api_ms": 2152,
    "num_turns": 1,
    "result": "The actual response text goes here",
    "stop_reason": "end_turn",
    "session_id": "uuid",
    "total_cost_usd": 0.006186,
    "usage": {
        "input_tokens": 1842,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "output_tokens": 44,
        "server_tool_use": {
            "web_search_requests": 0,
            "web_fetch_requests": 0
        },
        "service_tier": "standard"
    },
    "modelUsage": {
        "claude-sonnet-4-6": {
            "inputTokens": 1842,
            "outputTokens": 44,
            "cacheReadInputTokens": 0,
            "cacheCreationInputTokens": 0,
            "webSearchRequests": 0,
            "costUSD": 0.006186,
            "contextWindow": 200000,
            "maxOutputTokens": 32000
        }
    }
}
```

## Key Fields for LLMClient

| Field | Maps to | Notes |
|-------|---------|-------|
| `result` | `LLMResponse.content` | The response text |
| `stop_reason` | Logged as `finish_reason` | Values: `end_turn`, others TBD |
| `usage.input_tokens` | `LLMResponse.usage["prompt_tokens"]` | Map to OpenAI naming |
| `usage.output_tokens` | `LLMResponse.usage["completion_tokens"]` | Map to OpenAI naming |
| `total_cost_usd` | `LLMResponse.usage["cost_usd"]` | Bonus: per-call cost tracking |
| Full JSON dict | `LLMResponse.raw_response` | For logging |

## Model Aliases

| Alias | Resolves to | Verified |
|-------|------------|----------|
| `sonnet` | `claude-sonnet-4-6` | Yes |
| `opus` | `claude-opus-4-6` | Yes (default when no --model) |
| `haiku` | `claude-sonnet-4-6` | Mapped to sonnet (haiku may not be available) |

**Note:** `--model haiku` resolved to sonnet in testing. Use full model IDs if haiku is needed.

## Cost Comparison (trivial "Say hello" prompt)

| Configuration | Cache Creation | Cost |
|--------------|---------------|------|
| No isolation (from ~/) | 10,477 tokens | $0.039 |
| From /tmp (no CLAUDE.md) | 4,987 tokens | $0.022 |
| /tmp + --strict-mcp-config | 0 tokens | $0.006 |

~6x cost reduction with full isolation.
