"""Curated gap wave58 — AF411 McFarlane DC Multiverse Gold Label checklist.
Hand-checked vs whole oneshot.json on 2026-11-20.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave58_data.json")

def build_dc_gap_wave58() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
