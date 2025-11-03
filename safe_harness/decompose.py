from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .clients import ModelClient, UnsafeOutputError, estimate_tokens
from .filters import safe_text_ok, is_safe_text, SafeContentError


def safe_aggregator(solutions: List[str]) -> Tuple[str, bool]:
    """Combine solutions into a final answer, enforcing safety.

    Returns (final_answer, success). If any combined text is unsafe,
    returns a redacted placeholder and success=False.
    """
    text = "\n\n".join(solutions)
    if not safe_text_ok(text):
        return "[REDACTED for safety]", False
    # Keep the aggregation minimal and safe
    return text, True


def automated_decompose(task_prompt: str, weak_model: ModelClient, strong_model: ModelClient):
    """Decompose a task with a weak model and solve subtasks with a strong model.

    Returns a structured dict:
      {
        'subtasks': [...],
        'solutions': [...],
        'success': bool,
        'logs': {...},
      }
    """
    logs: Dict[str, object] = {
        "blocked_subtasks": [],
        "subtask_token_estimates": [],
        "solution_token_estimates": [],
        "latency_sec": {"weak": [], "strong": []},
    }

    # Check task safety
    if not safe_text_ok(task_prompt):
        logs["blocked"] = True
        return {
            "subtasks": [],
            "solutions": [],
            "success": False,
            "logs": logs,
        }

    # Propose subtasks
    subtasks = weak_model.propose_subtasks(task_prompt, max_items=6)
    logs["latency_sec"]["weak"].append(getattr(weak_model, "last_latency_sec", 0.0))

    safe_subtasks: List[str] = []
    for st in subtasks:
        if not safe_text_ok(st):
            logs["blocked_subtasks"].append(st)
            continue
        safe_subtasks.append(st)
        logs["subtask_token_estimates"].append(estimate_tokens(st))

    solutions: List[str] = []
    for st in safe_subtasks:
        try:
            out = strong_model.solve_subtask(st)
            # generate() already checks output safety; redundant check added for defense-in-depth
            if not is_safe_text(out):
                logs.setdefault("redacted", True)
                solutions.append("[REDACTED for safety]")
            else:
                solutions.append(out)
        except (UnsafeOutputError, SafeContentError):
            logs.setdefault("redacted", True)
            solutions.append("[REDACTED for safety]")
        finally:
            logs["latency_sec"]["strong"].append(getattr(strong_model, "last_latency_sec", 0.0))
            logs["solution_token_estimates"].append(estimate_tokens(solutions[-1]))

    final_answer, ok = safe_aggregator(solutions)
    logs["final_answer_preview_chars"] = final_answer[:120]

    return {
        "subtasks": safe_subtasks,
        "solutions": solutions,
        "success": bool(ok and len(safe_subtasks) == len(solutions) and len(solutions) > 0),
        "logs": logs,
    }
