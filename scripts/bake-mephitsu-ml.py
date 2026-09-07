#!/usr/bin/env python3
"""Back-compat wrapper → bake-mephitsu.py (Marvel Legends default)."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

# Default --line marvel-legends when no line given
argv = sys.argv[1:]
if not any(a == "--line" or a.startswith("--line=") for a in argv) and "--all-hub" not in argv and "--list-lines" not in argv:
    argv = ["--line", "marvel-legends", *argv]
sys.argv = [str(Path(__file__).with_name("bake-mephitsu.py")), *argv]
runpy.run_path(str(Path(__file__).with_name("bake-mephitsu.py")), run_name="__main__")
