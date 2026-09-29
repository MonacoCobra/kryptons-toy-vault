"""DC toys gap wave11 — Superman/Batman Series 2/4/5/6/7 checklist holes,
New Teen Titans 2008, JSA 2001/2007 leftovers, JLI Series 1, Mystics/Amazing
Androids leftovers, Green Lantern Corps densify, and Mattel Batman Classic
TV Series remaining villains.

Verified against Wikipedia List of DC Direct action figures. Floor 1980.
No imageUrl / no invented GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave11_data.json")

def build_dc_gap_wave11() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
