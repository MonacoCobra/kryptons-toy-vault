"""Curated gap wave60 — AF411 Hasbro Transformers Titans Return 2016-17 + Combiner Wars 2014-16 checklists.
Hand-checked vs whole oneshot.json on 2026-11-23.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave60_data.json")

def build_dc_gap_wave60() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
