"""Curated gap wave51 — AF411 Hasbro Star Wars Saga Collection 2006-07 + Original Trilogy Collection 2004 + 30th Anniversary Collection 2007-08 checklists.
Hand-checked vs whole oneshot.json on 2026-11-18.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave51_data.json")

def build_dc_gap_wave51() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
