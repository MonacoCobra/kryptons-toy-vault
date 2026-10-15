"""DC toys gap wave22 — AF411 Multiverse BAF subsections + MAFEX DC gaps.

Darkseid (Justice League Task Force), Plastic Man (JLA), Nightmare Bat
(Batman Forever holes), plus 8 MAFEX DC checklist gaps. Hand-checked against
oneshot.json on 2026-10-15.

Source: snapshot in _af411_dc_checklists_wave22.json; rows from
_gen_wave22_data.py. No imageUrl / no GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave22_data.json")

def build_dc_gap_wave22() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
