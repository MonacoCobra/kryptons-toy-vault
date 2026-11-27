"""Curated gap wave83 — AF411 Four Horsemen Mythic Legions holes left as possible-match skips in wave56, hand-checked: originals vs 2026 Legacies Ver. 2, reissues/2-versions by year, cross-maker false positives.
Hand-checked vs whole oneshot.json on 2026-11-27.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave83_data.json")

def build_dc_gap_wave83() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
