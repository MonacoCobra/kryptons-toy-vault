"""Curated gap wave59 — AF411 Hasbro Transformers Generation 1 (1984-86) checklist.
Hand-checked vs whole oneshot.json on 2026-11-23.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave59_data.json")

def build_dc_gap_wave59() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
