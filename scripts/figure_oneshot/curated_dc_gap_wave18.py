"""DC toys gap wave18 — ActionFigure411 MAFEX DC Comics checklist holes.

Hand-checked against oneshot.json on 2026-10-09. Catalog MAFEX naming/No.
labels are messy — deduped by character + variant + year (not No. alone).
Skipped figures already present under alternate titles, 2026+ waves, and
fuzzy same-character matches (e.g. Selina Kyle 2015 ≈ Catwoman TDKR,
Batman ZSJL already in catalog, Robin Hush already in catalog).

Source: snapshot in _af411_dc_checklists_wave18.json; rows from
_gen_wave18_data.py. No imageUrl / no GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave18_data.json")

def build_dc_gap_wave18() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
