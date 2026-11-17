"""Curated gap wave47 — AF411 Hasbro Power Rangers Lightning Collection checklist.
Hand-checked vs whole oneshot.json on 2026-11-17.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave47_data.json")

def build_dc_gap_wave47() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
