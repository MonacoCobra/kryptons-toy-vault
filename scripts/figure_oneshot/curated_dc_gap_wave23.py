"""DC toys gap wave23 — AF411 Multiverse remaining Mattel CNC 2017-2019 + McFarlane BAF holes.

Mattel Collect & Connect: Steppenwolf retailer exclusives, Batman Ninja, Killer Croc 80th.
McFarlane Build-A: Joker Bot, The Monitor, Starro, Darkest Knight, Atrocitus holes.
Hand-checked against oneshot.json on 2026-10-16.

Source: snapshot in _af411_dc_checklists_wave23.json; rows from
_gen_wave23_data.py. No imageUrl / no GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave23_data.json")

def build_dc_gap_wave23() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
