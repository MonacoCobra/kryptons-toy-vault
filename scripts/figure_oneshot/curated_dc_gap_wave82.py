"""Curated gap wave82 — AF411 Mattel Masters of the WWE Universe holes, waves 1-8.
Hand-checked vs whole oneshot.json on 2026-11-27.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave82_data.json")

def build_dc_gap_wave82() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
