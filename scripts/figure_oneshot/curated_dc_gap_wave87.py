"""Curated gap wave87 — AF411 Hasbro Marvel Legends exclusive multipacks 2020-2026 (Pulse/Fan Channel/Amazon/Target/Disney/GameStop/SDCC).
Hand-checked vs whole oneshot.json on 2026-11-27.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave87_data.json")

def build_dc_gap_wave87() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
