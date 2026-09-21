"""DC toys gap wave6 — First Appearance S3, Long Halloween, Secret Files,
Dark Victory, Identity Crisis, Crisis/52/Infinite Crisis leftovers, Last Son,
Batman and Son, Shazam, New Gods, History of DCU, Batman Reborn / ROBW / INC,
Arkham Origins, Outlaws, Earth 2, JL Dark, Teen Titans, Super Villains,
plus Mattel BU Penguin + Total Heroes Catwoman/Mr. Freeze and a few verified
McFarlane Multiverse / Page Punchers densify.

Verified against Wikipedia List of DC Direct action figures, DC Collectibles
Hunter First Appearance/Elseworlds checklists, BatmanYTB Batman Unlimited,
Amazon Total Heroes Catwoman, ActionFigure411 Speeding Bullets / Electric Blue.
Floor 1980. No imageUrl / no invented GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave6_data.json")

def build_dc_gap_wave6() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
