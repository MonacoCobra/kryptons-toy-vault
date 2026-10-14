"""DC toys gap wave21 — ActionFigure411 McFarlane Multiverse CNC (Collect-and-Connect).

Seven Multiverse CNC subsections (Justice Buster, New 52 Doomsday, Grapnel Blaster,
Killer Croc Suicide Squad, King Shark, Ares, Rookie). Hand-checked against
oneshot.json on 2026-10-14; catalog has almost no McFarlane 2016-2019 Multiverse
so later Megafig/reissue rows were not treated as dups (different year/variant).

Source: snapshot in _af411_dc_checklists_wave21.json; rows from
_gen_wave21_data.py. No imageUrl / no GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave21_data.json")

def build_dc_gap_wave21() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
