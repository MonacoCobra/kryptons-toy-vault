"""Curated gap wave44 — AF411 ThunderCats LJN + Matty + AD&D LJN checklists.
Hand-checked vs whole oneshot.json on 2026-11-16.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave44_data.json")

def build_dc_gap_wave44() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
