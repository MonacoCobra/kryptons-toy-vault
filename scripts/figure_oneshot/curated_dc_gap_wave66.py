"""Curated gap wave66 — AF411 Hasbro Star Wars The Vintage Collection holes.
Hand-checked vs whole oneshot.json on 2026-11-24.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave66_data.json")

def build_dc_gap_wave66() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
