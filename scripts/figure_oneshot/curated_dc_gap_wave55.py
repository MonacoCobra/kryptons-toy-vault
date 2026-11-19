"""Curated gap wave55 — AF411 Playmates Teenage Mutant Ninja Turtles 1988-97 checklist.
Hand-checked vs whole oneshot.json on 2026-11-19.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave55_data.json")

def build_dc_gap_wave55() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
