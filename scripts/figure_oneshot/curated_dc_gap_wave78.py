"""Curated gap wave78 — official Transformers Masterpiece releases
Shelby approved (t530s3208) after wave73 KO-only skips.
Hand-checked vs whole oneshot.json on 2026-11-27.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave78_data.json")

def build_dc_gap_wave78() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
