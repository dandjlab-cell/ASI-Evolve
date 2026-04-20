"""LLM client utilities — Claude CLI subprocess backend."""

import json
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .logger import get_logger
from .structures import LLMResponse


class LLMClient:
    """
    LLM client that delegates to the Claude Code CLI via subprocess.

    Each call spawns `claude -p` with the prompt piped via stdin.
    No API keys or external SDK dependencies required.
    """

    def __init__(
        self,
        model: str = "opus",
        timeout: int = 300,
        retry_times: int = 3,
        retry_delay: int = 5,
        claude_path: str = "claude",
        **extra_params,
    ):
        self.model = model
        self.timeout = timeout
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.claude_path = claude_path

        resolved = shutil.which(claude_path)
        if not resolved:
            raise FileNotFoundError(
                f"Claude CLI not found: '{claude_path}'. "
                "Install Claude Code or set 'claude_path' in config."
            )
        self.claude_path = resolved

        self.logger = get_logger()
        self._thread_local = threading.local()
        self._clean_env = self._build_clean_env()

    @staticmethod
    def _build_clean_env() -> dict:
        """Build an environment dict safe for subprocess invocation."""
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        return env

    def set_log_dir(self, log_dir: Optional[Path]):
        """
        Set the log directory for the current worker/thread.

        Args:
            log_dir: Directory to store LLM call logs, or `None` to disable.
        """
        if log_dir:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            self._thread_local.log_dir = log_dir
            self._thread_local.call_counter = 0
        else:
            self._thread_local.log_dir = None
            self._thread_local.call_counter = 0

    def _get_log_dir(self) -> Optional[Path]:
        """Return the active thread-local log directory."""
        return getattr(self._thread_local, "log_dir", None)

    def _get_call_counter(self) -> int:
        """Return the active thread-local call counter."""
        return getattr(self._thread_local, "call_counter", 0)

    def _increment_call_counter(self):
        """Increment the thread-local call counter."""
        if not hasattr(self._thread_local, "call_counter"):
            self._thread_local.call_counter = 0
        self._thread_local.call_counter += 1

    def chat(
        self,
        messages: List[Dict[str, str]],
        json_mode: bool = False,
        model: Optional[str] = None,
        call_name: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Send a request to the Claude CLI.

        Args:
            messages: Chat messages (system/user/assistant).
            json_mode: Ignored (kept for interface compatibility).
            model: Optional model override.
            call_name: Optional label for call logging.
            **kwargs: Ignored (kept for interface compatibility).

        Returns:
            Structured `LLMResponse`.
        """
        model = model or self.model

        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        user_parts = [m["content"] for m in messages if m["role"] != "system"]

        # Prevent Claude from generating tool_call XML instead of content
        system_parts.append(
            "You have NO tools available. Do NOT generate <tool_call> or "
            "<function_call> blocks. Respond with plain text and the XML tags "
            "specified in the prompt (<name>, <motivation>, <code>, <analysis>, etc.)."
        )
        system_prompt = "\n\n".join(system_parts)
        prompt = "\n\n".join(user_parts)

        cmd = [
            self.claude_path, "-p",
            "--model", model,
            "--output-format", "json",
            "--no-session-persistence",
            "--tools", "",
            "--strict-mcp-config",
        ]

        cmd.extend(["--system-prompt", system_prompt])

        last_error = None
        for attempt in range(self.retry_times):
            try:
                start_time = time.time()
                result = subprocess.run(
                    cmd,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    env=self._clean_env,
                    cwd="/tmp",
                )
                call_time = time.time() - start_time

                if result.returncode != 0:
                    raise RuntimeError(
                        f"claude CLI exited {result.returncode}: "
                        f"{result.stderr[:500]}"
                    )

                cli_output = json.loads(result.stdout)

                if cli_output.get("is_error"):
                    raise RuntimeError(
                        f"claude CLI error: {cli_output.get('result', 'unknown')}"
                    )

                content = cli_output.get("result", "")

                cli_usage = cli_output.get("usage", {})
                usage = {
                    "prompt_tokens": cli_usage.get("input_tokens", 0),
                    "completion_tokens": cli_usage.get("output_tokens", 0),
                    "total_tokens": (
                        cli_usage.get("input_tokens", 0)
                        + cli_usage.get("output_tokens", 0)
                    ),
                    "cost_usd": cli_output.get("total_cost_usd", 0.0),
                }

                response = LLMResponse(
                    content=content,
                    raw_response=cli_output,
                    usage=usage,
                    model=model,
                    call_time=call_time,
                )

                self.logger.log_llm_call({
                    "model": model,
                    "usage": usage,
                    "call_time": call_time,
                })

                log_dir = self._get_log_dir()
                if log_dir:
                    self._log_call_to_file(messages, response, call_name, attempt)

                return response

            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{self.retry_times}): {e}"
                )
                if attempt < self.retry_times - 1:
                    time.sleep(self.retry_delay)

        raise last_error

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        call_name: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Convenience wrapper for a single user prompt.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            json_mode: Whether to request JSON output.
            call_name: Optional label for call logging.
            **kwargs: Additional request overrides.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self.chat(messages, json_mode=json_mode, call_name=call_name, **kwargs)

    def extract_tags(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        call_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Extract XML-like tags from an LLM response.

        Example:
            <name>...</name>
            <motivation>...</motivation>
        """
        response = self.generate(prompt, system_prompt, json_mode=False, call_name=call_name, **kwargs)
        content = response.content.strip()

        result = {}

        tag_pattern = r"<(\w+)>"
        pos = 0
        while True:
            match = re.search(tag_pattern, content[pos:])
            if not match:
                break

            tag_name = match.group(1)
            tag_start = pos + match.end()

            end_tag = f"</{tag_name}>"
            end_pos = content.find(end_tag, tag_start)

            if end_pos == -1:
                pos = tag_start
                continue

            tag_content = content[tag_start:end_pos].strip()
            result[tag_name] = tag_content
            pos = end_pos + len(end_tag)

        if not result:
            self.logger.error("Failed to extract tags from response")
            self.logger.error(f"Response content (full, {len(content)} chars):\n{content[:1000]}...")
            raise ValueError("No valid tags found in LLM response")

        self.logger.debug(f"Extracted {len(result)} tags: {list(result.keys())}")
        return result

    def _log_call_to_file(
        self,
        messages: List[Dict[str, str]],
        response: LLMResponse,
        call_name: Optional[str],
        attempt: int,
    ):
        """Persist one LLM call to a JSON log file."""
        log_dir = self._get_log_dir()
        if not log_dir:
            return

        self._increment_call_counter()
        call_counter = self._get_call_counter()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

        if call_name:
            filename = f"llm_call_{call_counter:03d}_{call_name}_{timestamp}.json"
        else:
            filename = f"llm_call_{call_counter:03d}_{timestamp}.json"

        log_file = log_dir / filename

        finish_reason = None
        if isinstance(response.raw_response, dict):
            finish_reason = response.raw_response.get("stop_reason")

        log_data = {
            "call_number": call_counter,
            "timestamp": datetime.now().isoformat(),
            "call_name": call_name,
            "attempt": attempt + 1,
            "model": response.model,
            "usage": response.usage,
            "call_time": response.call_time,
            "messages": messages,
            "response": {
                "content": response.content,
                "finish_reason": finish_reason,
            },
        }

        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to write LLM call log: {e}")


def create_llm_client(config: Dict[str, Any]) -> LLMClient:
    """Create an `LLMClient` from the top-level config dictionary."""
    api_config = config.get("api", {})

    return LLMClient(
        model=api_config.get("model", "opus"),
        timeout=api_config.get("timeout", 300),
        retry_times=api_config.get("retry_times", 3),
        retry_delay=api_config.get("retry_delay", 5),
        claude_path=api_config.get("claude_path", "claude"),
    )
