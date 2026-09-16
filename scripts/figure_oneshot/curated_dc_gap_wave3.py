"""DC toys gap wave3 — McFarlane Super Powers (AF411) + Designer Capullo + DCUC exclusives + DC Essentials.

Verified against ActionFigure411 McFarlane Super Powers checklist and known
Mattel DCUC exclusive / CnC retail lists + DC Collectibles Designer/Essentials.
Floor 1980. No imageUrl / no invented GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave3_data.json")

def build_dc_gap_wave3() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
