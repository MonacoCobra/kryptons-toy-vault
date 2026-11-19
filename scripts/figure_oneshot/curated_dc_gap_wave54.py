"""Curated gap wave54 — AF411 Hasbro G.I. Joe A Real American Hero 3.75in 1982-91 checklist.
Hand-checked vs whole oneshot.json on 2026-11-19.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave54_data.json")

def build_dc_gap_wave54() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
