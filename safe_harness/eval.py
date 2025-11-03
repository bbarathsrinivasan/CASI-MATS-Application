from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd
import matplotlib.pyplot as plt

from .clients import ModelClient, estimate_tokens
from .decompose import automated_decompose
from .filters import is_safe_text


@dataclass
class ProxyTask:
    prompt: str
    expected_keywords: List[str]


def _accuracy_from_keywords(text: str, expected_keywords: List[str]) -> float:
    """Simple proxy accuracy: fraction of expected keywords present (case-insensitive).

    If no keywords are provided, returns 1.0.
    """
    if not expected_keywords:
        return 1.0
    t = text.lower() if text else ""
    hits = sum(1 for k in expected_keywords if k.lower() in t)
    return hits / max(1, len(expected_keywords))


def evaluate_single_model(task: ProxyTask, model: ModelClient) -> Dict[str, object]:
    # Skip/flag unsafe prompts
    if not is_safe_text(task.prompt):
        return {
            "variant": "single_model",
            "prompt": "[BLOCKED]",
            "output": "",
            "accuracy": 0.0,
            "success": False,
            "tokens": 0,
        }
    # Simple safe instruction wrapper
    instr = (
        "Provide a brief, safe response. Avoid any sensitive or harmful content.\n"
        f"TASK: {task.prompt}"
    )
    out = model.generate(instr, max_tokens=256, temperature=0.2)
    acc = _accuracy_from_keywords(out, task.expected_keywords)
    return {
        "variant": "single_model",
        "prompt": task.prompt,
        "output": out,
        "accuracy": acc,
        "success": acc >= 1.0,  # exact proxy success criterion
        "tokens": model.last_tokens_used,
    }


def evaluate_composed_model(task: ProxyTask, weak: ModelClient, strong: ModelClient) -> Dict[str, object]:
    if not is_safe_text(task.prompt):
        return {
            "variant": "composed_model",
            "prompt": "[BLOCKED]",
            "output": "",
            "accuracy": 0.0,
            "success": False,
            "tokens": 0,
        }

    res = automated_decompose(task.prompt, weak, strong)
    combined = "\n\n".join(res["solutions"]) if res.get("solutions") else ""
    acc = _accuracy_from_keywords(combined, task.expected_keywords)

    # Token usage proxy: sum estimated tokens of solutions; include subtasks cost lightly
    token_usage = sum(estimate_tokens(s) for s in res.get("solutions", []))
    token_usage += sum(int(0.5 * estimate_tokens(st)) for st in res.get("subtasks", []))

    return {
        "variant": "composed_model",
        "prompt": task.prompt,
        "output": combined,
        "accuracy": acc,
        "success": bool(res.get("success", False) and acc >= 1.0),
        "tokens": token_usage,
    }


def run_evaluation(
    tasks: Iterable[ProxyTask],
    single_model: ModelClient,
    weak_model: ModelClient,
    strong_model: ModelClient,
    trials: int = 3,
    seed: int = 42,
    out_dir: Path | None = None,
) -> Dict[str, object]:
    rng = random.Random(seed)
    tasks_list = list(tasks)

    all_rows: List[Dict[str, object]] = []

    for _ in range(trials):
        rng.shuffle(tasks_list)
        for t in tasks_list:
            single = evaluate_single_model(t, single_model)
            comp = evaluate_composed_model(t, weak_model, strong_model)
            all_rows.extend([single, comp])

    df = pd.DataFrame(all_rows)

    # Aggregate summary metrics by variant
    summary = df.groupby("variant").agg(
        accuracy=("accuracy", "mean"),
        success_rate=("success", "mean"),
        mean_token_usage=("tokens", "mean"),
        count=("prompt", "count"),
    ).reset_index()

    # Save artifacts
    if out_dir is None:
        out_dir = Path("logs")
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "eval_results.csv"
    df.to_csv(csv_path, index=False)

    summary_path = out_dir / "eval_summary.csv"
    summary.to_csv(summary_path, index=False)

    # Plot success rate comparison
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(summary["variant"], summary["success_rate"], color=["#4B8BF4", "#34C759"])  # type: ignore
    ax.set_ylim(0, 1)
    ax.set_ylabel("Success Rate")
    ax.set_title("Success Rate by Variant")
    for i, v in enumerate(summary["success_rate"]):
        ax.text(i, v + 0.02, f"{v:.2f}", ha="center")
    plot_path = out_dir / "eval_success_rate.png"
    fig.tight_layout()
    fig.savefig(plot_path)
    plt.close(fig)

    return {
        "results_df": df,
        "summary_df": summary,
        "artifacts": {
            "results_csv": str(csv_path),
            "summary_csv": str(summary_path),
            "success_plot": str(plot_path),
        },
    }


if __name__ == "__main__":
    # Minimal demo using mock models
    tasks = [
        ProxyTask(prompt="Summarize safe article on productivity", expected_keywords=["productivity", "summarize"]),
        ProxyTask(prompt="Classify safe customer feedback into themes", expected_keywords=["feedback", "themes"]),
        ProxyTask(prompt="Outline safe steps for data cleaning", expected_keywords=["steps", "cleaning"]),
    ]

    sm = ModelClient(name="SingleMock", mock_mode=True)
    wk = ModelClient(name="WeakMock", mock_mode=True)
    st = ModelClient(name="StrongMock", mock_mode=True)

    out = run_evaluation(tasks, sm, wk, st, trials=3, seed=42)
    print("Artifacts:", out["artifacts"])  # Paths to CSV and plot
