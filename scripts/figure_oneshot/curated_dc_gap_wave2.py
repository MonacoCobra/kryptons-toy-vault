"""DC toys gap wave2 — McFarlane Multiverse densify + Mattel older DC + DC Direct Icons/Essentials.

Verified against ActionFigure411 McFarlane/Mattel DC Multiverse checklist and known
Mattel JLU / Total Heroes / Batman Unlimited / Movie Masters retail lists.
Floor 1980. No imageUrl / no invented GTINs. Source tags per section.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave2_data.json")

def build_dc_gap_wave2() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
