"""Curated gap wave36 — AF411 McFarlane DC Multiverse Gold Label 2025-26 holes (Vault/DTE/vehicles re-checked: mostly saturated or fuzzy cross-maker skips). Hand-checked vs whole oneshot.json on 2026-11-05.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave36_data.json")

def build_dc_gap_wave36() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
