"""DC toys gap wave26 — AF411 non-Multiverse DC checklists (Kenner Super Powers vehicles, Hot Toys DC, Mondo BTAS, McFarlane BTAS, McFarlane DC Direct Digital).

Non-Multiverse checklists; cross-maker fuzzy hits and UPC collisions skipped.
Hand-checked against oneshot.json on 2026-10-21.

Source: snapshot in _af411_dc_checklists_wave26.json; rows from
_gen_wave26_data.py. No imageUrl; sku = AF411 UPC when valid.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave26_data.json")

def build_dc_gap_wave26() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
