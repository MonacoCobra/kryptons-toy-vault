"""Curated gap wave84 — AF411 Valaverse Action Force holes: new 2024-25 checklist rows plus wave46 cross-maker skips hand-checked as unrelated.
Hand-checked vs whole oneshot.json on 2026-11-27.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave84_data.json")

def build_dc_gap_wave84() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
