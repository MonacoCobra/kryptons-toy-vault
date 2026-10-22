"""DC toys gap wave27 — AF411 MAFEX DC, McFarlane DC Super Powers and Page Punchers checklist holes.

Cross-maker fuzzy hits and UPC collisions skipped. Hand-checked against oneshot.json on 2026-10-22.

Source: snapshot in _af411_dc_checklists_wave27.json; rows from
_gen_wave27_data.py. No imageUrl; sku = AF411 UPC when valid.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave27_data.json")

def build_dc_gap_wave27() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
