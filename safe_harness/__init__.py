"""Safe experiment harness for model pipelines.

Features:
- Pluggable Model clients (ModelA, ModelB)
- Manual and automated decomposition strategies
- Strict safety filter for sensitive or harmful content
- Structured run logging to JSONL
"""

__all__ = [
    "clients",
    "filters",
    "pipeline",
    "run_logger",
    "report",
    # Common exports
    "ModelClient",
    "ModelClientProtocol",
    "automated_decompose",
    "safe_aggregator",
    "generate_report",
    "SafeContentError",
    "is_safe_text",
    "safe_text_ok",
]

# Re-export key classes for convenience
from .clients import ModelClient, ModelClientProtocol  # noqa: E402,F401
from .decompose import automated_decompose, safe_aggregator  # noqa: E402,F401
from .report import generate_report  # noqa: E402,F401
from .filters import SafeContentError, is_safe_text, safe_text_ok  # noqa: E402,F401
