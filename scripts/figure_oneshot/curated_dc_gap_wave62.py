"""Curated gap wave62 — AF411 MAFEX Marvel + Mondo Marvel 1/6 checklists.
Hand-checked vs whole oneshot.json on 2026-11-23.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave62_data.json")

def build_dc_gap_wave62() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
