"""DC toys gap wave8 — Alex Ross Justice Series 1/2/5/8 holes, JLI Martian
Manhunter S2, 52 Batwoman/Booster Gold, Flash Rogues Gallery, Secret Files
S2/S3, Silver Age 2-packs, Shazam 2007 Sivana, JSA Villains, ABC Promethea,
Metamorpho Deluxe, Return of Superman Life Suit, GL Corps Classic Hal,
Re-Activated S1/S4, Classic Heroes, Birds of Prey Deluxe, Hard-Traveling
Heroes, Other Worlds, Amazons & Adversaries, Impulse/Max Mercury, plus
Mattel Metal Men Tin/Platinum and McFarlane Multiverse/Super Powers densify
(Atrocitus, Star Sapphire, World's Finest, Krypto Megafig, New Gods SP).

Verified against DC Collectibles Hunter checklists (Justice League
International, Alex Ross Justice League, 52, Flash Rogues Gallery, Secret
Files, Silver Age, Shazam 2007, JSA Villains, America's Best Comics,
Metamorpho, Return of Superman, Green Lantern Corps, Re-Activated, Classic
Heroes, Birds of Prey, Hard-Traveling Heroes, Other Worlds, Wonder Woman
Amazons and Adversaries, Impulse) and joeacevedo DC Direct year archives.
Floor 1980. No imageUrl / no invented GTINs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = Path(__file__).with_name("_dc_gap_wave8_data.json")

def build_dc_gap_wave8() -> list[dict]:
    if not _DATA.is_file():
        return []
    return json.loads(_DATA.read_text())
