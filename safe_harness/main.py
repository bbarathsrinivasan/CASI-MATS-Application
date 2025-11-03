from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import Pipeline, run_pipeline
from .run_logger import JsonlLogger


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a safe experiment harness with manual or automated decomposition.")
    parser.add_argument("prompt", type=str, help="The top-level task prompt (safe content only)")
    parser.add_argument("--strategy", choices=["manual", "automated"], default="automated",
                        help="Decomposition strategy to use")
    parser.add_argument("--subtask", action="append", default=[],
                        help="Manual subtask (repeatable). Used only when --strategy=manual")
    parser.add_argument("--log", default=str(Path("logs/experiment_runs.jsonl")),
                        help="Path to JSONL log file")

    args = parser.parse_args()

    p = Pipeline(
        task_name="ad-hoc",
        prompt=args.prompt,
        manual_subtasks=args.subtask if args.strategy == "manual" else None,
    )

    logger = JsonlLogger(Path(args.log))
    run = run_pipeline(p, strategy=args.strategy, logger=logger)

    # Print a compact summary to stdout (safe fields only)
    summary = {
        "run_id": run.run_id,
        "strategy": run.strategy,
        "model_a": run.model_a,
        "model_b": run.model_b,
        "timestamp": run.timestamp,
        "subtasks": [st.subtask for st in run.subtasks],
        "blocked_subtasks": run.blocked_subtasks,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
