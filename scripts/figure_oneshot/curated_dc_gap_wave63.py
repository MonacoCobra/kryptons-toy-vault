"""Curated gap wave63 — AF411 Hasbro Transformers War for Cybertron Siege/Earthrise/Kingdom checklists.
Hand-checked vs whole oneshot.json on 2026-11-23.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave63_data.json")

def build_dc_gap_wave63() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
