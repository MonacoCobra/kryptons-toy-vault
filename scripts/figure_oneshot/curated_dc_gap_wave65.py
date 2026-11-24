"""Curated gap wave65 — AF411 Kenner Star Wars vintage 1977-85 checklist.
Hand-checked vs whole oneshot.json on 2026-11-24.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave65_data.json")

def build_dc_gap_wave65() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
