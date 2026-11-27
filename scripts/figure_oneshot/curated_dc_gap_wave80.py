"""Curated gap wave80 — AF411 M.A.S.K. Kenner 1986–87 waves 2–3 + playsets and The Loyal Subjects 2025–26.
Vehicles/playsets with included figures. Hand-checked vs whole oneshot.json on 2026-11-27.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave80_data.json")

def build_dc_gap_wave80() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
