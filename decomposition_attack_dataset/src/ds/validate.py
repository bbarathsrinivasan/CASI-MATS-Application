from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from pydantic import BaseModel, ValidationError

from .schema import DatasetManifest, ItemExpected, ItemInput, ItemMeta


def _read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_item_dir(item_dir: Path) -> Tuple[bool, List[str]]:
    errs: List[str] = []

    inputs = item_dir / "inputs"
    expected = item_dir / "expected"
    meta_path = item_dir / "meta.json"

    if not inputs.exists() or not expected.exists() or not meta_path.exists():
        errs.append("missing required files/directories")
        return False, errs

    try:
        ItemMeta.model_validate_json(meta_path.read_text(encoding="utf-8"))
    except ValidationError as e:
        errs.append(f"meta invalid: {e}")

    if not (inputs / "prompt.txt").exists():
        errs.append("inputs/prompt.txt missing")

    checks_path = expected / "checks.json"
    if not checks_path.exists():
        errs.append("expected/checks.json missing")
    else:
        try:
            _ = json.loads(checks_path.read_text(encoding="utf-8"))
        except Exception as e:
            errs.append(f"checks.json invalid: {e}")

    return len(errs) == 0, errs


def validate_dataset(root: Path) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        errs.append("manifest.json missing")
        return False, errs
    try:
        manifest = DatasetManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    except ValidationError as e:
        errs.append(f"manifest invalid: {e}")
        return False, errs

    for item_id in manifest.items:
        ok, sub_errs = validate_item_dir(root / "items" / item_id)
        if not ok:
            errs.extend([f"{item_id}: {e}" for e in sub_errs])

    return len(errs) == 0, errs
