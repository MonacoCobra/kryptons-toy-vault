"""Curated gap wave42 — AF411 Indiana Jones + MOTU Original checklists.
Hand-checked vs whole oneshot.json on 2026-11-13.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave42_data.json")

def build_dc_gap_wave42() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
