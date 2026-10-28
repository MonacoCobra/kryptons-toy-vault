"""DC toys gap wave31 — AF411 DC Multiverse Gold Label + BAF/CNC leftovers.

Cross-maker fuzzy hits and UPC collisions skipped. Hand-checked against oneshot.json on 2026-10-28.

Source: snapshot in _af411_dc_checklists_wave31.json; rows from
_gen_wave31_data.py. No imageUrl; sku = AF411 UPC when valid.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave31_data.json")

def build_dc_gap_wave31() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
