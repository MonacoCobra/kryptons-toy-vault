"""DC toys gap wave17 — ActionFigure411 checklist holes:
DC Collectibles Batman: The Animated Series / The New Batman Adventures
(2014-2019 numbered figures, multi-packs, vehicles), McFarlane Page Punchers
(3" and 7", 2022-2025), McFarlane Super Powers (Gold Label packs, vehicles,
2024-2025) and Mattel DC Universe Classics variants (Mary Batson, Blade Hand
Martian Manhunter, MattyCollector Super Powers Kalibak wave).

Source: snapshot in _af411_dc_checklists_wave17.json; rows from
_gen_wave17_data.py after hand-checking each pick against oneshot.json
(company + line + character + year/variant). 2026+ waves skipped. No imageUrl
/ no GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave17_data.json")

def build_dc_gap_wave17() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
