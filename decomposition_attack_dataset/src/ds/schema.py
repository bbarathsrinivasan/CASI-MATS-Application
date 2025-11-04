from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


ALLOWED_CATEGORIES = ["CF", "CFG", "DI", "DOC", "IMS"]


class Category(str, Enum):
    CF = "CF"   # code-refactor
    CFG = "CFG" # config-debug
    DI = "DI"   # data-normalize
    DOC = "DOC" # doc-synthesis
    IMS = "IMS" # incident-summary


class ItemInput(BaseModel):
    # Content the model will receive
    task_prompt: str = Field(..., description="Benign task prompt")
    attachments: Dict[str, str] = Field(default_factory=dict, description="Optional small text attachments keyed by filename")


class ItemExpected(BaseModel):
    # Expected benign output (target) for evaluation
    description: str = Field(..., description="Short human-readable description of expected outcome")
    checks: Dict[str, str] = Field(default_factory=dict, description="Simple keyword checks or CSV schema description")


class ItemMeta(BaseModel):
    id: str
    category: Category
    created_at: str
    blacklist_passed: bool = True
    moderation_passed: bool = True
    notes: Optional[str] = None


class DatasetManifest(BaseModel):
    version: str = "0.1.0"
    count: int
    categories: List[Category]
    items: List[str]


def write_json_schema(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ItemInput.schema.json").write_text(
        json.dumps(ItemInput.model_json_schema(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "ItemExpected.schema.json").write_text(
        json.dumps(ItemExpected.model_json_schema(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "ItemMeta.schema.json").write_text(
        json.dumps(ItemMeta.model_json_schema(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "DatasetManifest.schema.json").write_text(
        json.dumps(DatasetManifest.model_json_schema(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
