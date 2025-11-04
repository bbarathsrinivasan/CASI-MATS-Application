from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - allow import without openai
    OpenAI = None  # type: ignore


# Conservative blacklist: block credentials, IPs, exploits, and shell/exec patterns
BLACKLIST_TERMS = [
    # Credentials/API keys
    "api_key=", "aws_secret", "gcp_key", "azure_key", "token=", "password=",
    # IPs / sensitive net hints
    "127.0.0.1", "0.0.0.0", "/etc/passwd", "private key",
    # Exploits / malware
    "exploit", "rce", "reverse shell", "payload",
    # Commands (block common dangerous ones)
    "rm -rf", "sudo ", "wget ", "curl ", "ssh ", "nc ", "nmap ", "chmod +x",
]

BLACKLIST_PATTERNS = [
    r"\b[A-Za-z0-9_]{16,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}",  # jwt-like
    r"\b\d{1,3}(?:\.\d{1,3}){3}\b",  # IPv4 address
]


def local_blacklist_ok(text: str) -> Tuple[bool, List[str]]:
    if not text:
        return True, []
    t = text.lower()
    reasons: List[str] = []
    for term in BLACKLIST_TERMS:
        if term.lower() in t:
            reasons.append(f"term:{term}")
    for pat in BLACKLIST_PATTERNS:
        if re.search(pat, text):
            reasons.append(f"pattern:{pat}")
    return len(reasons) == 0, reasons


def have_openai() -> bool:
    return OpenAI is not None and bool(os.environ.get("OPENAI_API_KEY"))


@retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
def moderate_text(text: str) -> Tuple[bool, Dict]:
    """Return (allowed, raw_response). Uses OpenAI Moderation if available, otherwise allows by default."""
    if not have_openai():
        return True, {"mock": True}
    client = OpenAI()
    resp = client.moderations.create(
        model="omni-moderation-latest",
        input=text[:4000],
    )
    # Newer SDK returns a structured object; attempt to read allowed flag
    try:
        result = resp.results[0]  # type: ignore[attr-defined]
        flagged = getattr(result, "flagged", False)
        return not bool(flagged), resp.to_dict() if hasattr(resp, "to_dict") else {"raw": str(resp)}
    except Exception:
        return True, {"raw": str(resp)}


def ensure_safe_text(text: str, *, context: str) -> None:
    ok_local, reasons = local_blacklist_ok(text)
    if not ok_local:
        raise ValueError(f"Text failed local safety checks ({context}): {', '.join(reasons)}")
    ok_mod, _ = moderate_text(text)
    if not ok_mod:
        raise ValueError(f"Text failed moderation ({context})")
