"""DC toys gap wave19 — ActionFigure411 McFarlane Collector Edition checklist holes.

One Multiverse subsection (Collector Edition only). Hand-checked against
oneshot.json on 2026-10-12. Catalog CE naming often embeds the figure number
in the name/subtitle — deduped by character + CE number + year; dropped
ambiguous Batman multipacks and figures already present under McFarlane
Collector Edition / overlapping Multiverse rows.

Source: snapshot in _af411_dc_checklists_wave19.json; rows from
_gen_wave19_data.py. No imageUrl / no GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave19_data.json")

def build_dc_gap_wave19() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
