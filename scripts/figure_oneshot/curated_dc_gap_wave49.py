"""Curated gap wave49 — AF411 DC MAFEX / Mezco One:12 / Mondo / Hot Toys checklists.
Hand-checked vs whole oneshot.json on 2026-11-18.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave49_data.json")

def build_dc_gap_wave49() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
