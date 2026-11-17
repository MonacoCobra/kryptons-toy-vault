"""Curated gap wave48 — AF411 Hasbro G.I. Joe Classified Series checklist.
Hand-checked vs whole oneshot.json on 2026-11-17.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave48_data.json")

def build_dc_gap_wave48() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
