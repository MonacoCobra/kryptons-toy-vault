"""Curated gap wave77 — AF411 Transformers War for Cybertron Trilogy checklist holes.
Hand-checked vs whole oneshot.json on 2026-11-26.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave77_data.json")

def build_dc_gap_wave77() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
