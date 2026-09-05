"""BBTS AF brand expansion wave 5 — densify + 3P Transformers + Medicom RAH.

New CompanyIds: ironfactory, magicsquare, cangtoys, medicom (RAH only; Kubrick skip).
Densify: SHFiguarts, Kaiyodo Revoltech/AY, Hasbro Lightning/Classified/ML/BS/SS,
McFarlane, NECA, Super7, DC Direct, Playmates, JAKKS, Mezco, Hiya, Storm.

Skip: Unique Art statues, Medicom Kubrick.
Floor 1980; no imageUrl; AF only.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("bbts_wave5_data.json")


def F(rid, name, subtitle, line, company, release, msrp, scale, demand, tags):
    if release < FLOOR:
        release = FLOOR
    return {
        "id": rid,
        "name": name,
        "subtitle": subtitle,
        "line": line,
        "company": company,
        "kind": "figure",
        "releaseDate": release,
        "msrp": float(msrp),
        "scale": scale,
        "demand": float(demand),
        "tags": [t for t in tags.split(",") if t],
        "source": "curated-bbts-wave5",
    }


def _rows(raw_list, prefix, line, company, scale, default_msrp, tags):
    out = []
    for row in raw_list:
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        elif len(row) == 5:
            suf, name, sub, date, demand = row
            msrp = default_msrp
        else:
            continue
        out.append(
            F(f"{prefix}-{suf}", name, sub, line, company, date, msrp, scale, demand, tags)
        )
    return out


def build_bbts_wave5() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []

    # NEW: Iron Factory
    for row in raw.get("ironfactory", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 55.0
        line = "Iron Factory EX"
        if "Combiner" in sub:
            line = "Iron Factory Combiner"
        rows.append(
            F(f"if5-{suf}", name, sub, line, "ironfactory", date, msrp, '6"', demand,
              "iron-factory,transformers,3p,curated")
        )

    # NEW: Magic Square
    for row in raw.get("magicsquare", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 70.0
        line = "Magic Square"
        if "Light of Justice" in sub:
            line = "Magic Square Light of Justice"
        elif "Despoiler" in sub:
            line = "Magic Square Despoiler"
        elif "Combiner" in sub:
            line = "Magic Square Combiner"
        rows.append(
            F(f"ms5-{suf}", name, sub, line, "magicsquare", date, msrp, '1:24', demand,
              "magic-square,transformers,3p,curated")
        )

    # NEW: Cang Toys
    for row in raw.get("cangtoys", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 70.0
        line = "Cang Toys"
        if "Combiner" in sub:
            line = "Cang Toys Combiner"
        elif "Beast Wars" in sub:
            line = "Cang Toys Beast Wars"
        elif "Predacon" in sub:
            line = "Cang Toys Predacon"
        elif "Seacon" in sub:
            line = "Cang Toys Seacon"
        elif "Dinobot" in sub:
            line = "Cang Toys Dinobot"
        rows.append(
            F(f"ct5-{suf}", name, sub, line, "cangtoys", date, msrp, '1:24', demand,
              "cang-toys,transformers,3p,curated")
        )

    # NEW: Medicom RAH (Kubrick intentionally omitted)
    for row in raw.get("medicom", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 280.0
        rows.append(
            F(f"rah5-{suf}", name, sub, "Real Action Heroes", "medicom", date, msrp, '1:6', demand,
              "medicom,rah,1-6,curated")
        )

    # SHFiguarts densify
    rows += _rows(raw.get("shfiguarts", []), "shf5", "S.H.Figuarts", "shfiguarts", '6"', 75.0,
                  "shfiguarts,tamashii,bandai,curated")

    # Kaiyodo Revoltech / Amazing Yamaguchi
    for row in raw.get("kaiyodo", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 95.0
        line = "Amazing Yamaguchi" if "Yamaguchi" in sub else "Revoltech"
        rows.append(
            F(f"ky5-{suf}", name, sub, line, "kaiyodo", date, msrp, '6"', demand,
              "kaiyodo,revoltech,amazing-yamaguchi,curated")
        )

    # Hasbro densify
    rows += _rows(raw.get("hasbroLightning", []), "lc5", "Lightning Collection", "hasbro", '6"', 22.99,
                  "hasbro,power-rangers,lightning,curated")
    rows += _rows(raw.get("hasbroClassified", []), "cls5", "GI Joe Classified", "hasbro", '6"', 24.99,
                  "hasbro,gi-joe,classified,curated")
    rows += _rows(raw.get("hasbroMl", []), "ml5", "Marvel Legends", "hasbro", '6"', 24.99,
                  "hasbro,marvel,legends,curated")
    rows += _rows(raw.get("hasbroBs", []), "bs5", "Black Series", "hasbro", '6"', 24.99,
                  "hasbro,star-wars,black-series,curated")
    rows += _rows(raw.get("hasbroSs", []), "ss5", "Transformers Studio Series", "hasbro", '6"', 24.99,
                  "hasbro,transformers,studio-series,curated")

    # McFarlane
    for row in raw.get("mcfarlane", []):
        suf, name, sub, date, demand = row[:5]
        line = "DC Multiverse"
        if "Spawn" in sub or "Spawn" in name or any(
            x in name for x in ("Gunslinger", "Haunt", "Violator", "Cogliostro", "Angela", "Malebolgia", "She-Spawn", "Medieval")
        ):
            line = "Spawn"
        elif "Page Punchers" in sub:
            line = "Page Punchers"
        elif "Gold Label" in sub:
            line = "DC Multiverse Gold Label"
        elif "Collector" in sub or "Megafig" in sub:
            line = "DC Multiverse Collector"
        rows.append(
            F(f"mcf5-{suf}", name, sub, line, "mcfarlane", date, 22.99, '7"', demand,
              "mcfarlane,dc,curated")
        )

    # NECA
    for row in raw.get("neca", []):
        suf, name, sub, date, demand = row[:5]
        line = "NECA Ultimate"
        alien_keys = ("Alien", "Aliens", "Xenomorph", "Ripley", "Bishop", "Hudson", "Vasquez", "Hicks", "Apone", "Newt", "Burke", "Big Chap", "Dog Alien", "Alien Queen")
        pred_keys = ("Predator", "Dutch", "Harrigan", "Jungle Hunter", "City Hunter", "Elder Predator", "Scout Predator", "Fugitive", "Assassin Predator")
        horror_keys = ("Freddy", "Jason", "Michael", "Chucky", "Tiffany", "Pinhead", "Cenobite", "Butterball", "Chatterer", "Ghostface", "Pennywise", "Ash", "Evil Dead", "Henrietta", "Deadite", "Army of Darkness")
        tmnt_names = ("Leonardo", "Raphael", "Michelangelo", "Donatello", "Casey Jones", "April O'Neil", "Splinter", "Shredder", "Slash", "Tokka", "Rahzar", "Leatherhead", "Usagi Yojimbo")
        if any(x in sub or x in name for x in alien_keys):
            line = "Aliens Ultimate"
        elif any(x in sub or x in name for x in pred_keys):
            line = "Predator Ultimate"
        elif name in tmnt_names or "Mirage" in sub or "TMNT" in sub:
            line = "TMNT Ultimate"
        if any(x in sub or x in name for x in horror_keys):
            line = "Horror Ultimate"
        elif "Godzilla" in sub or name in ("Godzilla", "King Ghidorah", "Mothra", "Rodan", "Mechagodzilla"):
            line = "Godzilla Ultimate"
        rows.append(
            F(f"neca5-{suf}", name, sub, line, "neca", date, 34.99, '7"', demand,
              "neca,ultimate,curated")
        )

    # Super7
    for row in raw.get("super7", []):
        suf, name, sub, date, demand = row[:5]
        line = "Super7 ULTIMATES!"
        msrp = 55.0
        scale = '7"'
        if "ReAction" in sub:
            line = "Super7 ReAction"
            msrp = 18.0
            scale = '3.75"'
        rows.append(
            F(f"s75-{suf}", name, sub, line, "super7", date, msrp, scale, demand,
              "super7,curated")
        )

    # DC Direct
    for row in raw.get("dcdirect", []):
        suf, name, sub, date, demand = row[:5]
        line = "DC Direct"
        if "Icons" in sub:
            line = "DC Icons"
        elif "Essentials" in sub:
            line = "DC Essentials"
        elif "Designer" in sub:
            line = "DC Designer Series"
        elif "Throne" in sub:
            line = "Throne of Atlantis"
        elif "Zero Year" in sub:
            line = "Zero Year"
        elif "Court of Owls" in sub:
            line = "Court of Owls"
        elif "Forever Evil" in sub:
            line = "Forever Evil"
        elif "Classic" in sub:
            line = "DC Direct Classic"
        rows.append(
            F(f"dcd5-{suf}", name, sub, line, "dcdirect", date, 24.99, '6.5"', demand,
              "dc-direct,dc-collectibles,curated")
        )

    # Playmates
    for row in raw.get("playmates", []):
        suf, name, sub, date, demand = row[:5]
        line = "TMNT Classic"
        if "Tales" in sub:
            line = "Tales of the TMNT"
        elif "Mutant Mayhem" in sub:
            line = "Mutant Mayhem"
        elif "Classic Collection" in sub:
            line = "TMNT Classic Collection"
        elif "Soft Head" in sub:
            line = "TMNT Classic Soft Head"
        elif "Exo-Squad" in sub:
            line = "Exo-Squad"
        elif "Astro" in sub or "Biker" in sub:
            line = "Playmates AF"
        rows.append(
            F(f"pm5-{suf}", name, sub, line, "playmates", date, 14.99, '4.5"', demand,
              "playmates,tmnt,curated")
        )

    # JAKKS
    for row in raw.get("jakks", []):
        suf, name, sub, date, demand = row[:5]
        line = "JAKKS Pacific"
        msrp = 14.99
        scale = '4"'
        if "Sonic" in sub or (sub == "Movie" and "sonic" in suf):
            line = "Sonic the Hedgehog"
        elif sub == "WWE":
            line = "JAKKS WWE"
            scale = '6"'
        elif sub == "Nintendo":
            line = "JAKKS Nintendo"
        elif "Primal Age" in sub:
            line = "MotU Primal Age"
            scale = '5.5"'
            msrp = 19.99
        elif sub == "Movie":
            line = "Sonic the Hedgehog"
        rows.append(
            F(f"jak5-{suf}", name, sub, line, "jakks", date, msrp, scale, demand,
              "jakks,curated")
        )

    # Mezco
    rows += _rows(raw.get("mezco", []), "mez5", "One:12 Collective", "mezco", '1:12', 112.0,
                  "mezco,one12,curated")

    # Hiya
    for row in raw.get("hiya", []):
        suf, name, sub, date, demand = row[:5]
        line = "Hiya Exquisite"
        if any(x in sub or x in name for x in ("Godzilla", "Ghidorah", "Rodan", "Mothra", "Mechagodzilla", "Kong", "Shimo", "Scar King", "Minus", "Evolved", "New Empire")):
            line = "Hiya Godzilla"
        elif "G.I. Joe" in sub:
            line = "Hiya G.I. Joe"
        elif "Star Trek" in sub:
            line = "Hiya Star Trek"
        elif "Judge" in sub or "Dredd" in name or "Anderson" in name or "2000 AD" in sub:
            line = "Hiya Judge Dredd"
        elif any(x in sub or x in name for x in ("Alien", "Aliens", "Predator", "RoboCop", "Terminator", "Ripley", "Dutch", "Ash", "Evil Dead")):
            line = "Hiya Exquisite Mini"
        rows.append(
            F(f"hy5-{suf}", name, sub, line, "hiya", date, 45.0, '1:18', demand,
              "hiya,curated")
        )

    # Storm
    for row in raw.get("storm", []):
        suf, name, sub, date, demand = row[:5]
        line = "Street Fighter"
        if "Mortal Kombat" in sub:
            line = "Mortal Kombat"
        rows.append(
            F(f"st5-{suf}", name, sub, line, "storm", date, 90.0, '1:12', demand,
              "storm,curated")
        )

    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out
