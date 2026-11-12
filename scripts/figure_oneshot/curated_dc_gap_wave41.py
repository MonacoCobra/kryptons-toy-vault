"""Curated gap wave41 — AF411 Ghostbusters Kenner + Hasbro checklists.
Hand-checked vs whole oneshot.json on 2026-11-12.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave41_data.json")

def build_dc_gap_wave41() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
