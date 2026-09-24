"""DC toys gap wave9 — History of the DC Universe holes, Watchmen Series
1/2 exclusives, DC Essentials #4–#38 checklist densify, Mattel Total Heroes
Ultra/Wave4 released leftovers, DCUC Green Lantern Classics + SDCC Wonder
Twins, DC Direct Arkham Asylum/City/Origins, DC Icons JSA leftovers.

Verified against DC Collectibles Hunter (Watchmen, History of the DC Universe,
DC Essentials), joeacevedo DC Total Heroes archive, and ItsAllTrue DCUC
sortable checklist. Floor 1980. No imageUrl / no invented GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave9_data.json")

def build_dc_gap_wave9() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
