"""Curated gap wave45 — AF411 G.I. Joe 25th Anniversary + Retro Collection checklists.
Hand-checked vs whole oneshot.json on 2026-11-16.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave45_data.json")

def build_dc_gap_wave45() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
