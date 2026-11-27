"""Curated gap wave81 — AF411 Mattel Masters of the Universe Origins holes: core singles, deluxe, Power-Con/SDCC/Target/Creations/Toyplosion/BBTS exclusives and multipacks, beast/vehicle sets with figures, Turtles of Grayskull, ThunderCats crossover.
Hand-checked vs whole oneshot.json on 2026-11-27.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave81_data.json")

def build_dc_gap_wave81() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
