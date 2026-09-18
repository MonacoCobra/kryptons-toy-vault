"""DC toys gap wave5 — Classic TV + Designer Series + CIE Matty + Icons + DCUC leftovers.

Verified against ItsAllTrue Classic TV, DC Collectibles Hunter Designer/Icons,
Cool Toy Review Club Infinite Earths, ActionFigure411 DCUC.
Floor 1980. No imageUrl / no invented GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave5_data.json")

def build_dc_gap_wave5() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
