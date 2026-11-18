"""Curated gap wave53 — AF411 Mattel Masters of the Universe Classics 2008-16 checklist.
Hand-checked vs whole oneshot.json on 2026-11-18.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave53_data.json")

def build_dc_gap_wave53() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
