"""DC toys gap wave28 — AF411 Retro 66 (McFarlane DC Retro Super Friends + Batman 66 playsets) and Kenner BTAS playset holes.

Cross-maker fuzzy hits and UPC collisions skipped. Hand-checked against oneshot.json on 2026-10-23.

Source: snapshot in _af411_dc_checklists_wave28.json; rows from
_gen_wave28_data.py. No imageUrl; sku = AF411 UPC when valid.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave28_data.json")

def build_dc_gap_wave28() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
