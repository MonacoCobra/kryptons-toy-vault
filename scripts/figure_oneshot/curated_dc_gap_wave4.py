"""DC toys gap wave4 — Mattel Brave and the Bold + Mattel DC Multiverse 2016-2018 + McFarlane Platinum/Page Punchers + DC Icons leftovers.

Verified against Parry Game Preserve B&B checklist and JoeAcevedo Mattel Multiverse 2016-2018 archives.
Floor 1980. No imageUrl / no invented GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave4_data.json")

def build_dc_gap_wave4() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
