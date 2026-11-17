"""Curated gap wave46 — AF411 Valaverse Action Force + Hasbro D&D checklists.
Hand-checked vs whole oneshot.json on 2026-11-17.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave46_data.json")

def build_dc_gap_wave46() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
