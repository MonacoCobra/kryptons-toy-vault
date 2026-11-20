"""Curated gap wave57 — AF411 Hasbro Power Rangers Lightning Collection + G.I. Joe Classified checklists.
Hand-checked vs whole oneshot.json on 2026-11-20.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave57_data.json")

def build_dc_gap_wave57() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
