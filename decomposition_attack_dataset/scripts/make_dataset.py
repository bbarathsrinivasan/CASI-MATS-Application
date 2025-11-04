#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    # Add decomposition_attack_dataset/src to sys.path for local runs without install
    src = Path(__file__).resolve().parents[1] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _main() -> None:
    _ensure_src_on_path()
    from ds.generate import main  # import after path tweak
    # Default to dataset/ at the project root
    main(["--out", str(Path(__file__).resolve().parents[1] / "dataset")])


if __name__ == "__main__":
    _main()
