"""Curated gap wave86 — AF411 Hasbro Marvel Legends exclusive multipacks and box sets 2007-2019 (TRU/Walmart/Target/Amazon/EE/Disney/SDCC/Fan Channel).
Hand-checked vs whole oneshot.json on 2026-11-27.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave86_data.json")

def build_dc_gap_wave86() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
