"""Curated gap wave40 — AF411 Hasbro Star Wars 3.75in Retro Collection checklist.
Hand-checked vs whole oneshot.json on 2026-11-11.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave40_data.json")

def build_dc_gap_wave40() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
