"""Curated gap wave38 — AF411 Hasbro Star Wars The Vintage Collection 2010-2025 singles.
Hand-checked vs whole oneshot.json on 2026-11-09.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave38_data.json")

def build_dc_gap_wave38() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
