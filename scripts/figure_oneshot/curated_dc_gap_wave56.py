"""Curated gap wave56 — AF411 Four Horsemen Mythic Legions + Kenner M.A.S.K. checklists.
Hand-checked vs whole oneshot.json on 2026-11-19.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave56_data.json")

def build_dc_gap_wave56() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
