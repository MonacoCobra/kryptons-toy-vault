"""DC toys gap wave15 — Mattel DC Superheroes S3 "Select Sculpt" 6" line
(2006-2007, Series 1-8 + Target 2-packs + SDCC 2007 / NYCC 2008 exclusives;
Wikipedia "DC Superheroes" + Fwoosh DCSH release guides for quarters) and
Mattel DC Universe Classics exclusive multipacks missing from the catalog
(TRU / MattyCollector / Walmart two-packs, DCUC vs MOTUC TRU two-packs,
SDCC 2014 Containment Suit Doomsday) plus Mattel Watchmen Club Black
Freighter 2013 (Wikipedia "DC Universe Classics").

Verified checklists only. Floor 1980. No imageUrl / no invented GTINs.
MSRP left 0 (unknown) except DCSH Series 3 ($8.99, Cool Toy Review).
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave15_data.json")

def build_dc_gap_wave15() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
