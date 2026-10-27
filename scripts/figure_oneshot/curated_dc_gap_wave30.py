"""DC toys gap wave30 — AF411 McFarlane DC Multiverse Bane BAF waves + Black Adam holes.

Cross-maker fuzzy hits and UPC collisions skipped. Hand-checked against oneshot.json on 2026-10-27.

Source: snapshot in _af411_dc_checklists_wave30.json; rows from
_gen_wave30_data.py. No imageUrl; sku = AF411 UPC when valid.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave30_data.json")

def build_dc_gap_wave30() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
