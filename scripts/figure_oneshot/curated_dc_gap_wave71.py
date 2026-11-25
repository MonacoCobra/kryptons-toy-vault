"""Curated gap wave71 — AF411 MOTU Eternia Minis/Chronicles/Mondo/Super7 + TMNT Mutant Mayhem checklists.
Hand-checked vs whole oneshot.json on 2026-11-25.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave71_data.json")

def build_dc_gap_wave71() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
