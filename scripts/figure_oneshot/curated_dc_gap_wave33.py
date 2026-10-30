"""Curated gap wave33 — AF411 Mattel MOTU Origins checklist holes (DC AF411 checklists saturated). Hand-checked vs whole oneshot.json on 2026-10-30.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave33_data.json")

def build_dc_gap_wave33() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
