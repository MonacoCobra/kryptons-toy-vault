"""DC toys gap wave12 — Blackest Night Series 1/8 + exclusives, Legion Mon-El/Star Boy,
JLA Identity Crisis Classics, New 52 Pandora/Simon Baz/Stargirl/Hawkman/Orion,
Watchmen movie variants, Mattel DCUC leftovers, Movie Masters leftovers, and
McFarlane Multiverse Doom Patrol / Katana / Creeper commons.

Verified against Wikipedia List of DC Direct action figures (+ known Mattel DCUC /
McFarlane Multiverse releases). Floor 1980. No imageUrl / no invented GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave12_data.json")

def build_dc_gap_wave12() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
