#!/usr/bin/env python3
"""Thin wrapper around dry-run-toyark-densify.py (same fetch/filter/apply).

Babysit: `python3 scripts/toyark-densify.py --apply --days 7`
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_TARGET = Path(__file__).resolve().parent / "dry-run-toyark-densify.py"


def main(argv: list[str] | None = None) -> int:
    spec = importlib.util.spec_from_file_location("dry_run_toyark_densify", _TARGET)
    if spec is None or spec.loader is None:
        print(f"ERROR: cannot load {_TARGET}", file=sys.stderr)
        return 2
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.main(argv if argv is not None else sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
