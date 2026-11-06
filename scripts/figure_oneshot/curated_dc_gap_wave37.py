"""Curated gap wave37 — AF411 McFarlane DC Multiverse main-line 2025-26 holes (+ Poison Ivy Gold Label).
Hand-checked vs whole oneshot.json on 2026-11-06.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave37_data.json")

def build_dc_gap_wave37() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
