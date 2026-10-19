"""DC toys gap wave24 — AF411 Multiverse remaining McFarlane Vehicles and Playsets 2020-2026.

Vehicles & Playsets section; cross-maker fuzzy hits and UPC collisions skipped.
Hand-checked against oneshot.json on 2026-10-19.

Source: snapshot in _af411_dc_checklists_wave24.json; rows from
_gen_wave24_data.py. No imageUrl; sku = AF411 UPC when valid.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave24_data.json")

def build_dc_gap_wave24() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
