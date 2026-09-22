"""DC toys gap wave7 — Doomsday Clock, Batman Black & White AF, Rainbow Batman,
DC Armory, Showcase gaps, Authority, Planetary, Preacher, Smallville, Trinity,
Classic Heroes, Magic & Mystery, NTT Cyborg/Raven, Crime Syndicate 2002,
Birds of Prey, Flash Rogues, Amazons, Other Worlds, Just-Us-League fills,
Bombshells Wave 2, DC Origins, All Star, Shazam 2002, GL Corps early,
plus Mattel Batman Unlimited holes and McFarlane Multiverse/Super Powers densify.

Verified against Wikipedia List of DC Direct action figures, JoeAcevedo 2018
archive, Toyark Doomsday Clock reveal, DC Collectibles Hunter Rainbow Batman.
Floor 1980. No imageUrl / no invented GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave7_data.json")

def build_dc_gap_wave7() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
