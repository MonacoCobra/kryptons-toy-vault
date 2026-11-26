"""Curated gap wave76 — AF411 Transformers Generations checklist holes.
Hand-checked vs whole oneshot.json on 2026-11-26.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave76_data.json")

def build_dc_gap_wave76() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
