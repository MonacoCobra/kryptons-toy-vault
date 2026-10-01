"""DC toys gap wave13 — DC Collectibles Animated Series holes (Gods and Monsters,
Adventures Continue, Mask of the Phantasm, BTAS/TNBA/JL Animated), Batman Beyond,
and JSA Alex Ross Series 1 individuals.

Verified against Wikipedia List of DC Direct action figures + DC Collectibles Hunter
Animated Series checklists. Floor 1980. No imageUrl / no invented GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave13_data.json")

def build_dc_gap_wave13() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
