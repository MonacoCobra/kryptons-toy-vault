"""Curated gap wave79 — AF411 Hasbro G.I. Joe Classified Series holes
(Target/Walmart/Pulse/HasLab/SDCC exclusives, Retro cardbacks, multipacks
not yet in catalog). Hand-checked vs whole oneshot.json on 2026-11-27;
naming-variant dupes and cross-maker fuzzy hits skipped.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave79_data.json")

def build_dc_gap_wave79() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
