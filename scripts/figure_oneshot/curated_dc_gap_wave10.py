"""DC toys gap wave10 — Justice League of America Series 1/2 (2007–08) and
JLA Series 2 (2004) checklist holes, Kingdom Come Series 3 leftovers, and the
full Mattel Batman Missions 6"/12" evergreen line (2018).

Verified against Wikipedia List of DC Direct action figures, DC Collectibles
Hunter JLA notes, and Figurerealm / comic-cons.xyz Batman Missions checklists.
Floor 1980. No imageUrl / no invented GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave10_data.json")

def build_dc_gap_wave10() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
