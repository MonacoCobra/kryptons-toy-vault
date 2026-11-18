"""Curated gap wave52 — AF411 Hasbro Star Wars Legacy Collection 2008-10 + The Clone Wars 2008-13 checklists.
Hand-checked vs whole oneshot.json on 2026-11-18.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave52_data.json")

def build_dc_gap_wave52() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
