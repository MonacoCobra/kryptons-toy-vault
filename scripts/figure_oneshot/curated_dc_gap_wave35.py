"""Curated gap wave35 — AF411 NECA Dungeons & Dragons checklist holes (DC AF411 + Super7 ThunderCats Ultimates re-checked saturated). Hand-checked vs whole oneshot.json on 2026-11-04.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave35_data.json")

def build_dc_gap_wave35() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
