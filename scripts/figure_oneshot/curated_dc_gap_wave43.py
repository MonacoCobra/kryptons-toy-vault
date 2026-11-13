"""Curated gap wave43 — AF411 MOTU New Adventures + 200X checklists.
Hand-checked vs whole oneshot.json on 2026-11-13.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave43_data.json")

def build_dc_gap_wave43() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
