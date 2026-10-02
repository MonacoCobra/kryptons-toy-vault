"""DC toys gap wave14 — DC Collectibles Batman Arkham Knight (Hunter checklist),
Arkham City Series 3/4 leftovers (Wikipedia), and Mattel Young Justice 6"/4.25"
(Young Justice fandom wiki / Mattel DC Universe Young Justice).

Verified checklists only. Floor 1980. No imageUrl / no invented GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave14_data.json")

def build_dc_gap_wave14() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
