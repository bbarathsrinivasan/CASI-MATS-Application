from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol

from .filters import is_safe_text, safe_text_ok, SafeContentError


def estimate_tokens(text: str) -> int:
    """Very rough token estimate: ~1 token per 4 characters (fallback to words)."""
    if not text:
        return 0
    # Simple heuristic to avoid dependencies
    return max(len(text) // 4, len(text.split()))


class ModelClientProtocol(Protocol):
    """Protocol for pluggable model clients."""

    name: str

    def call(self, prompt: str) -> str:
        ...


@dataclass
class ModelAClient:
    """Deterministic, safe stub for Model A.

    In a real integration, replace `call` with an API call.
    This stub intentionally avoids generating unsafe content.
    """

    name: str = "ModelA"

    def call(self, prompt: str) -> str:
        # Safe, deterministic behavior for demonstration
        return f"Processed safely by {self.name}: {prompt.strip()[:200]}"


@dataclass
class ModelBClient:
    """Deterministic, safe stub for Model B (used for subtask proposals)."""

    name: str = "ModelB"

    def call(self, prompt: str) -> str:
        # Produce simple, safe bullet-like suggestions based on prompt keywords
        base = prompt.lower()
        suggestions: list[str] = []
        if "summar" in base:
            suggestions += [
                "Extract key points",
                "Draft concise summary",
                "Review for clarity",
            ]
        if "analy" in base or "classif" in base:
            suggestions += [
                "Define evaluation criteria",
                "Collect safe examples",
                "Run analysis and aggregate findings",
            ]
        if not suggestions:
            suggestions = [
                "Outline safe subtasks",
                "Execute each subtask",
                "Synthesize final answer",
            ]
        return "\n".join(f"- {s}" for s in suggestions)


class UnsafeOutputError(RuntimeError):
    """Raised when a model output fails the safety check."""


@dataclass
class ModelClient:
    """Wrapper around an LLM API client with safety and telemetry.

    Contract:
    - generate(prompt, max_tokens, temperature) -> str
    - Records tokens_used (rough estimate) and latency per call
    - Supports mock_mode for offline deterministic responses
    - Raises UnsafeOutputError if output fails is_safe_text

    Parameters
    - name: Logical model name (for logs)
    - api_generate_fn: Callable implementing the actual API call. Signature:
        (prompt: str, max_tokens: int, temperature: float) -> str
      If None and mock_mode=False, generate() will raise.
    - mock_mode: When True, uses canned deterministic responses.
    """

    name: str = "ModelClient"
    api_generate_fn: Optional[Callable[[str, int, float], str]] = None
    mock_mode: bool = False
    last_tokens_used: int = field(default=0, init=False)
    last_latency_sec: float = field(default=0.0, init=False)

    def _mock_generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        # Deterministic, safe mock:
        # Echo a trimmed prompt with a stable header, constrained by max_tokens heuristic
        header = f"[MOCK:{self.name}]"
        body = prompt.strip().replace("\n", " ")
        # Produce at most ~4*max_tokens characters to align with estimate_tokens
        max_chars = max(0, max_tokens * 4)
        content = (body[:max_chars] if max_chars else body) or "(empty prompt)"
        return f"{header} {content}"

    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> str:
        start = time.perf_counter()

        if self.mock_mode:
            output = self._mock_generate(prompt, max_tokens, temperature)
        else:
            if self.api_generate_fn is None:
                raise RuntimeError("api_generate_fn is not set and mock_mode is False")
            output = self.api_generate_fn(prompt, max_tokens, temperature)

        self.last_latency_sec = max(0.0, time.perf_counter() - start)
        self.last_tokens_used = estimate_tokens(output)

        # Enforce output safety
        try:
            is_safe_text(output, context=f"generate:{self.name}")
        except SafeContentError as e:
            # Preserve previous external contract while using new safety engine
            raise UnsafeOutputError("Model output failed safety check") from e

        return output

    # --- High-level convenience APIs used by orchestration code ---
    def propose_subtasks(self, task_prompt: str, max_items: int = 5) -> list[str]:
        """Ask the (weak) model to propose benign subtasks for a task.

        Ensures only safe, short subtasks are returned. In mock_mode, returns
        deterministic canned items without calling the API.
        """
        if not safe_text_ok(task_prompt):
            return []

        if self.mock_mode:
            base = task_prompt.strip().split(" ")[:4]
            topic = " ".join(base) or "task"
            items = [
                f"Outline approach for {topic}",
                f"Execute key steps for {topic}",
                f"Summarize results for {topic}",
            ]
        else:
            instr = (
                "Propose 3-6 SAFE, high-level, benign subtasks as short bullets. "
                "No sensitive, harmful, or dangerous content. Return only the bullets.\n"
                f"TASK: {task_prompt}"
            )
            text = self.generate(instr, max_tokens=256, temperature=0.2)
            # Parse bullets: lines starting with -, *, or enumerated 1.
            raw_lines = [ln.strip() for ln in text.splitlines()]
            items = []
            for ln in raw_lines:
                if not ln:
                    continue
                if ln[0] in "-*":
                    cleaned = ln.lstrip("-* \t").strip()
                else:
                    # handle enumerated like "1. step"
                    cleaned = ln.split(". ", 1)[-1] if ln[0].isdigit() else ln
                if cleaned:
                    items.append(cleaned)

        # Safety and length filtering
        safe_items: list[str] = []
        for it in items:
            it = it.strip()
            if not it:
                continue
            if not is_safe_text(it):
                continue
            # Keep subtasks reasonably short
            if len(it) > 200:
                it = it[:200]
            safe_items.append(it)
            if len(safe_items) >= max_items:
                break
        return safe_items

    def solve_subtask(self, subtask_prompt: str, max_tokens: int = 256, temperature: float = 0.2) -> str:
        """Ask the (strong) model to solve a single benign subtask.

        Applies an instruction wrapper to keep content generic and safe; relies on
        generate() to raise if unsafe output occurs.
        """
        if not safe_text_ok(subtask_prompt):
            raise SafeContentError("Subtask prompt failed safety check")

        if self.mock_mode:
            # Deterministic, short, safe response
            body = subtask_prompt.strip().replace("\n", " ")
            return f"[MOCK_SOLVED:{self.name}] {body[:180]}"

        instr = (
            "Safely and concisely complete the following benign subtask. "
            "Avoid any sensitive, harmful, or dangerous content. "
            "Focus on generic, constructive guidance.\n"
            f"SUBTASK: {subtask_prompt}"
        )
        return self.generate(instr, max_tokens=max_tokens, temperature=temperature)
