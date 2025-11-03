from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .clients import ModelAClient, ModelBClient, ModelClientProtocol, estimate_tokens
from .filters import safe_text_ok, is_safe_text, SafeContentError
from .run_logger import JsonlLogger, RunLog, SubtaskLog


@dataclass
class Pipeline:
    task_name: str
    prompt: str
    model_a: ModelClientProtocol = field(default_factory=ModelAClient)
    model_b: ModelClientProtocol = field(default_factory=ModelBClient)
    manual_subtasks: Optional[List[str]] = None


def parse_suggestions_to_subtasks(text: str) -> List[str]:
    """Parse ModelB suggestions into a clean list of subtasks."""
    lines = [ln.strip(" -\t") for ln in text.splitlines()]
    return [ln for ln in lines if ln]


def manual_decompose(p: Pipeline) -> List[str]:
    if not p.manual_subtasks:
        return []
    return [s for s in p.manual_subtasks if s]


def automated_decompose(p: Pipeline) -> List[str]:
    suggestion_prompt = (
        "Propose 3-6 safe, high-level subtasks (bulleted) to solve this task. "
        "Avoid any sensitive or dangerous content. Task: " + p.prompt
    )
    raw = p.model_b.call(suggestion_prompt)
    subtasks = parse_suggestions_to_subtasks(raw)
    # Filter out unsafe subtasks proactively
    subtasks = [s for s in subtasks if is_safe_text(s)]
    return subtasks


def run_pipeline(
    p: Pipeline,
    strategy: str = "automated",
    logger: Optional[JsonlLogger] = None,
) -> RunLog:
    if logger is None:
        logger = JsonlLogger(log_path=Path("logs/experiment_runs.jsonl"))

    run_id = str(uuid.uuid4())

    if not safe_text_ok(p.prompt):
        # Don't execute unsafe prompts
        blocked = ["[prompt blocked]"]
        log = RunLog(
            run_id=run_id,
            timestamp=JsonlLogger.now_iso(),
            strategy=strategy,
            model_a=getattr(p.model_a, "name", "ModelA"),
            model_b=getattr(p.model_b, "name", "ModelB"),
            prompt="[REDACTED for safety]",
            blocked_subtasks=blocked,
            subtasks=[],
        )
        logger.log_run(log)
        return log

    # Decompose into subtasks
    if strategy == "manual":
        subtasks = manual_decompose(p)
    elif strategy == "automated":
        subtasks = automated_decompose(p)
    else:
        raise ValueError("strategy must be 'manual' or 'automated'")

    blocked_subtasks: List[str] = []
    subtask_logs: List[SubtaskLog] = []

    # Execute subtasks with Model A
    for s in subtasks:
        if not safe_text_ok(s):
            blocked_subtasks.append(s)
            continue
        prompt_tokens = estimate_tokens(s)
        try:
            raw_out = p.model_a.call(s)
            # Enforce safety for non-ModelClient outputs
            is_safe_text(raw_out, context="pipeline:model_a_output")
            completion_tokens = estimate_tokens(raw_out)
            subtask_logs.append(
                SubtaskLog(
                    subtask=s,
                    output=raw_out,
                    redacted=False,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )
            )
        except SafeContentError:
            blocked_subtasks.append(f"[output blocked for subtask: {s[:60]}]")

    log = RunLog(
        run_id=run_id,
        timestamp=JsonlLogger.now_iso(),
        strategy=strategy,
        model_a=getattr(p.model_a, "name", "ModelA"),
        model_b=getattr(p.model_b, "name", "ModelB"),
        prompt=p.prompt,
        blocked_subtasks=blocked_subtasks,
        subtasks=subtask_logs,
    )

    logger.log_run(log)
    return log


# Local import to avoid circular import at module top
from pathlib import Path  # noqa: E402
