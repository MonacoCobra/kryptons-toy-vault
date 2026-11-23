"""Curated gap wave61 — AF411 Hasbro Transformers Classics 2006-07 + Universe 2003-10 + Generations 2010-13 checklists.
Hand-checked vs whole oneshot.json on 2026-11-23.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave61_data.json")

def build_dc_gap_wave61() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
