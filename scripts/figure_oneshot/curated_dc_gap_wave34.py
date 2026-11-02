"""Curated gap wave34 — AF411 Mattel MOTU Masterverse checklist holes (Origins done in wave33). Hand-checked vs whole oneshot.json on 2026-11-02.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave34_data.json")

def build_dc_gap_wave34() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
