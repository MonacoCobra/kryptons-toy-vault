"""Curated gap wave68 — AF411 Hot Toys Star Wars 1/6 checklist holes.
Hand-checked vs whole oneshot.json on 2026-11-24.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave68_data.json")

def build_dc_gap_wave68() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
