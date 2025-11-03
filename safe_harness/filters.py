from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple


class SafeContentError(ValueError):
    """Raised when text fails the safety policy."""

    def __init__(self, message: str, reasons: Optional[List[str]] = None) -> None:
        super().__init__(message)
        self.reasons = reasons or []


@dataclass
class SafetyConfig:
    blocklist: List[str] = field(default_factory=lambda: [
        # Violence/terrorism
        "kill", "murder", "terror", "bomb", "weapon", "shoot", "suicide",
        # Cybercrime/hacking
        "hack", "hacking", "exploit", "malware", "ransomware", "phishing", "keylogger", "ddos",
        # Illegal activity
        "drug manufacturing", "counterfeit", "forgery",
        # Adult sexual content (broad terms; conservative)
        "porn", "nude", "explicit", "sex",
        # Harm to minors
        "child abuse", "cp", "minor sexual",
        # Self-harm
        "self harm", "self-harm",
        # Graphical gore
        "gore", "torture",
    ])
    # Regex patterns for more nuanced matches
    patterns: List[str] = field(default_factory=lambda: [
        r"\bhow to (build|make|buy) (a )?(weapon|bomb)\b",
        r"\b(bypass|break|crack) (security|password|drm)\b",
        r"\bmanufactur(e|ing) (drugs|narcotics)\b",
    ])
    # Path to JSONL safety log file
    log_path: Path = Path("logs/safety_events.jsonl")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_safety_event(config: SafetyConfig, event: dict) -> None:
    try:
        config.log_path.parent.mkdir(parents=True, exist_ok=True)
        with config.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        # Logging must not crash the app
        pass


def _classifier_placeholder(text: str) -> dict:
    """Mock classifier that returns 'safe' for benign categories.

    A real implementation could integrate a content classifier. Here, we always
    return a benign label unless obvious triggers are present (already handled
    by blocklist/patterns). This function remains a stub for extensibility.
    """
    return {"label": "safe", "category": "benign"}


def is_safe_text(text: str, *, config: Optional[SafetyConfig] = None, context: str = "") -> bool:
    """Check text against safety policy.

    Behavior:
    - Uses case-insensitive blocklist and regex patterns.
    - Consults a placeholder classifier (always 'safe' for benign uses).
    - Logs reasons for any block to JSONL.
    - Returns True if safe; otherwise raises SafeContentError. Does not sanitize.
    """
    if config is None:
        config = SafetyConfig()

    if not text:
        return True

    t = text.lower()
    reasons: List[str] = []

    # Blocklist terms
    for term in config.blocklist:
        if term and term.lower() in t:
            reasons.append(f"blocklist:{term}")

    # Regex patterns
    for pat in config.patterns:
        try:
            if re.search(pat, t):
                reasons.append(f"pattern:{pat}")
        except re.error:
            continue

    # Placeholder classifier: only used if no hard triggers
    if not reasons:
        cls = _classifier_placeholder(text)
        if cls.get("label") not in {"safe", "benign"}:
            reasons.append(f"classifier:{cls}")

    if reasons:
        _log_safety_event(
            config,
            {
                "timestamp": _now_iso(),
                "context": context,
                "reason": reasons,
                "text_preview": text[:120],
            },
        )
        raise SafeContentError("Text failed safety policy", reasons)

    return True


def safe_text_ok(text: str, *, config: Optional[SafetyConfig] = None) -> bool:
    """Boolean convenience wrapper; returns False instead of raising."""
    try:
        is_safe_text(text, config=config)
        return True
    except SafeContentError:
        return False


# Note: redact_if_unsafe is retained for backward-compatibility but is not used
# by the harness to avoid automatic transformation. Prefer blocking instead.
def redact_if_unsafe(text: str) -> Tuple[str, bool]:
    try:
        is_safe_text(text)
        return text, False
    except SafeContentError:
        return "[REDACTED for safety]", True
