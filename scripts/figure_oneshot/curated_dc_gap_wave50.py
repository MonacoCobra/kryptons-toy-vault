"""Curated gap wave50 — AF411 Kenner Star Wars The Power of the Force 1995-99 checklist.
Hand-checked vs whole oneshot.json on 2026-11-18.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave50_data.json")

def build_dc_gap_wave50() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
