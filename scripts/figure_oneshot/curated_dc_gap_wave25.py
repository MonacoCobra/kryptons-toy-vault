"""DC toys gap wave25 — AF411 Multiverse remaining McFarlane Gold Label / retailer exclusives 2021-2026.

Gold Label section; cross-maker fuzzy hits and UPC collisions skipped.
Hand-checked against oneshot.json on 2026-10-20.

Source: snapshot in _af411_dc_checklists_wave25.json; rows from
_gen_wave25_data.py. No imageUrl; sku = AF411 UPC when valid.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave25_data.json")

def build_dc_gap_wave25() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
