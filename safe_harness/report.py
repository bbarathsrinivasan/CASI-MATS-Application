from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import matplotlib.pyplot as plt
import pandas as pd


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _df_to_markdown(df: pd.DataFrame, max_rows: int = 50) -> str:
    """Convert a small DataFrame to a GitHub-flavored Markdown table.

    Avoids requiring 'tabulate' by building the table manually.
    Truncates to max_rows to keep reports readable.
    """
    if df is None or df.empty:
        return "(no data)"
    df_disp = df.head(max_rows)
    cols = list(df_disp.columns)
    # Header
    lines = ["| " + " | ".join(map(str, cols)) + " |"]
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    # Rows
    for _, row in df_disp.iterrows():
        vals = [str(row[c]) for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    if len(df) > max_rows:
        lines.append(f"\n> Note: showing first {max_rows} of {len(df)} rows.")
    return "\n".join(lines)


def _plot_success_rate(summary_df: pd.DataFrame, out_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6, 4))
    variants = summary_df["variant"].tolist()
    values = summary_df["success_rate"].tolist() if "success_rate" in summary_df else []
    ax.bar(variants, values, color=["#4B8BF4", "#34C759"])  # type: ignore
    ax.set_ylim(0, 1)
    ax.set_ylabel("Success Rate")
    ax.set_title("Success Rate by Variant")
    for i, v in enumerate(values):
        ax.text(i, min(0.98, v + 0.02), f"{v:.2f}", ha="center")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def _plot_mean_tokens(summary_df: pd.DataFrame, out_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6, 4))
    variants = summary_df["variant"].tolist()
    values = summary_df["mean_token_usage"].tolist() if "mean_token_usage" in summary_df else []
    ax.bar(variants, values, color=["#8E8E93", "#FF9F0A"])  # type: ignore
    ax.set_ylabel("Mean Token Usage (proxy)")
    ax.set_title("Mean Token Usage by Variant")
    for i, v in enumerate(values):
        ax.text(i, v * 1.01 if v else 0.02, f"{v:.1f}", ha="center")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def generate_report(results_df: pd.DataFrame, config: Dict[str, object], output_path: Path | str) -> Dict[str, object]:
    """Generate a Markdown report and optional PDF, with attached artifacts.

    Parameters
    - results_df: pandas DataFrame from evaluation (rows per (task, variant))
    - config: dict with metadata, e.g., {"trials": int, "seed": int, "models": {...}}
    - output_path: directory where report.md and artifacts/ are written

    Returns
    - dict with paths to report, pdf (if created), and artifacts folder
    """
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts = out_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    # Derive summary
    summary = (
        results_df.groupby("variant").agg(
            accuracy=("accuracy", "mean"),
            success_rate=("success", "mean"),
            mean_token_usage=("tokens", "mean"),
            count=("prompt", "count"),
        ).reset_index()
        if not results_df.empty
        else pd.DataFrame()
    )

    # Plots
    success_plot = _plot_success_rate(summary, artifacts / "success_rate.png") if not summary.empty else None
    tokens_plot = _plot_mean_tokens(summary, artifacts / "mean_token_usage.png") if not summary.empty else None

    # Tables
    summary_md = _df_to_markdown(summary) if not summary.empty else "(no summary)"
    sample_rows = results_df.head(10) if not results_df.empty else pd.DataFrame()
    sample_md = _df_to_markdown(sample_rows) if not sample_rows.empty else "(no samples)"

    # Attach raw logs (best-effort)
    attached: List[str] = []
    for candidate in [
        Path("logs/experiment_runs.jsonl"),
        Path("logs/eval_results.csv"),
        Path("logs/eval_summary.csv"),
    ]:
        if candidate.exists():
            dst = artifacts / candidate.name
            try:
                shutil.copyfile(candidate, dst)
                attached.append(str(dst))
            except Exception:
                pass

    # Write config and metadata
    meta = {
        "generated_at": _now_iso(),
        "config": config or {},
        "attached": attached,
    }
    with (artifacts / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    with (artifacts / "config.json").open("w", encoding="utf-8") as f:
        json.dump(config or {}, f, ensure_ascii=False, indent=2)

    # Build report markdown
    intro = config.get("introduction") if isinstance(config, dict) else None
    models_desc = config.get("models") if isinstance(config, dict) else None

    md_lines: List[str] = []
    md_lines.append(f"# Experiment Report\n")
    md_lines.append(f"_Generated: {meta['generated_at']}_\n")

    # Introduction
    md_lines.append("## Introduction\n")
    md_lines.append((intro or "This report summarizes evaluation results for model pipelines.") + "\n")

    # Methods
    md_lines.append("## Methods\n")
    md_lines.append("We evaluate two variants: a single-model baseline and a composed pipeline using automated decomposition. "
                    "Accuracy is approximated by keyword matches; success is 1.0 accuracy; token usage is a proxy estimate.\n")

    # Models
    md_lines.append("## Models\n")
    if isinstance(models_desc, dict):
        md_lines.append("- Single model: " + str(models_desc.get("single", "(unspecified)")))
        md_lines.append("- Weak model:   " + str(models_desc.get("weak", "(unspecified)")))
        md_lines.append("- Strong model: " + str(models_desc.get("strong", "(unspecified)")))
    else:
        md_lines.append("Models are described in the experiment configuration.")
    md_lines.append("")

    # Safety
    md_lines.append("## Safety\n")
    md_lines.append("All prompts and outputs pass a conservative safety filter. Unsafe content is blocked or redacted. "
                    "No instructions for harmful activities or explicit imagery are produced.\n")

    # Results
    md_lines.append("## Results\n")
    if success_plot:
        md_lines.append("![Success Rate](artifacts/success_rate.png)\n")
    if tokens_plot:
        md_lines.append("![Mean Token Usage](artifacts/mean_token_usage.png)\n")

    md_lines.append("### Summary Table\n")
    md_lines.append(summary_md + "\n")

    md_lines.append("### Sample Rows\n")
    md_lines.append(sample_md + "\n")

    # Discussion
    md_lines.append("## Discussion\n")
    md_lines.append("Briefly interpret the results, noting where composition helps or harms performance and cost.\n")

    # Limitations
    md_lines.append("## Limitations\n")
    md_lines.append("Keyword-based accuracy is a coarse proxy; token estimates are approximate; mock models are deterministic.\n")

    # Ethics
    md_lines.append("## Ethics\n")
    md_lines.append("All experiments prioritize safety. We avoid generating harmful, illicit, or explicit content and apply defense-in-depth filtering.\n")

    report_md = "\n".join(md_lines)
    report_md_path = out_dir / "report.md"
    report_md_path.write_text(report_md, encoding="utf-8")

    # Optional: convert to PDF via pandoc if available
    pdf_path: Optional[Path] = None
    if shutil.which("pandoc"):
        try:
            pdf_path = out_dir / "report.pdf"
            # Run pandoc from the report directory so relative image paths resolve
            subprocess.run(["pandoc", str(report_md_path.name), "-o", str(pdf_path.name)], check=True, cwd=str(out_dir))
        except Exception:
            pdf_path = None

    return {
        "report_md": str(report_md_path),
        "report_pdf": str(pdf_path) if pdf_path else None,
        "artifacts_dir": str(artifacts),
        "attached": attached,
    }
