from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class SubtaskLog:
    subtask: str
    output: str
    redacted: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class RunLog:
    run_id: str
    timestamp: str
    strategy: str
    model_a: str
    model_b: str
    prompt: str
    blocked_subtasks: List[str] = field(default_factory=list)
    subtasks: List[SubtaskLog] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


class JsonlLogger:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_run(self, run: RunLog) -> None:
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(run.to_json() + "\n")

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
