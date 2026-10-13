"""DC toys gap wave20 — ActionFigure411 McFarlane Multiverse DTE + Vault + Multipacks.

Three Multiverse subsections (Deluxe Theatrical Edition, Vault Collection,
Multipacks). Hand-checked against oneshot.json on 2026-10-13; dropped rows
already present (see snapshot note).

Source: snapshot in _af411_dc_checklists_wave20.json; rows from
_gen_wave20_data.py. No imageUrl / no GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave20_data.json")

def build_dc_gap_wave20() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
