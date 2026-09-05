"""BBTS AF brand expansion wave 6 — 3P Transformers + densify + Kotobukiya Frame Arms.

New CompanyIds: drwu, dx9, mastermind, maketoys, planetx, kfc, xtransbots,
flametoys, tfc, gcreation.
Densify: Kotobukiya Frame Arms/Hexa Gear, SHFiguarts, Kaiyodo, Hasbro
Lightning/Classified/ML/BS/SS, Mattel Masterverse/WWE, McFarlane, NECA,
Super7, DC Direct, Playmates, Mezco.

Skipped (not in BBTS universe / statue-primary): APC Toys, Unique Toys,
Unique Art Studio. DNA Design upgrade kits skipped. Flame Toys Furai model
kits / statues skipped (Kuro Kara Kuri AF only).

Floor 1980; no imageUrl; AF only.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("bbts_wave6_data.json")


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
        "source": "curated-bbts-wave6",
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


def build_bbts_wave6() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []

    # NEW: Dr. Wu
    for row in raw.get("drwu", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 50.0
        line = "Dr. Wu EX"
        if "Mini" in sub:
            line = "Dr. Wu Mini"
        elif "Combiner" in sub:
            line = "Dr. Wu Combiner"
        elif sub == "Special":
            line = "Dr. Wu Special"
        rows.append(
            F(f"dw6-{suf}", name, sub, line, "drwu", date, msrp, '6"', demand,
              "dr-wu,transformers,3p,curated")
        )

    # NEW: DX9
    for row in raw.get("dx9", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 90.0
        line = "DX9 War in Pocket"
        if "K-Series" in sub:
            line = "DX9 K-Series"
        elif "Combiner" in sub:
            line = "DX9 Combiner"
        elif "EX Series" in sub:
            line = "DX9 EX"
        elif sub == "Special":
            line = "DX9 Special"
        rows.append(
            F(f"dx96-{suf}", name, sub, line, "dx9", date, msrp, '1:24', demand,
              "dx9,transformers,3p,curated")
        )

    # NEW: Mastermind Creations
    for row in raw.get("mastermind", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 145.0
        line = "MMC Reformatted"
        if "Ocular Max" in sub:
            line = "Ocular Max"
        elif "Combiner" in sub:
            line = "MMC Combiner"
        elif "Lesser" in sub or "Special" in sub:
            line = "MMC Special"
        rows.append(
            F(f"mmc6-{suf}", name, sub, line, "mastermind", date, msrp, '1:24', demand,
              "mastermind,mmc,transformers,3p,curated")
        )

    # NEW: MakeToys
    for row in raw.get("maketoys", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 100.0
        line = "MakeToys MTRM"
        if "MTCM" in sub or "Combiner" in sub:
            line = "MakeToys Combiner"
        elif "City" in sub:
            line = "MakeToys City"
        elif sub == "Special":
            line = "MakeToys Special"
        rows.append(
            F(f"mt6-{suf}", name, sub, line, "maketoys", date, msrp, '1:24', demand,
              "maketoys,transformers,3p,curated")
        )

    # NEW: Planet X
    for row in raw.get("planetx", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 95.0
        line = "Planet X"
        if "Combiner" in sub:
            line = "Planet X Combiner"
        elif sub == "Special":
            line = "Planet X Special"
        rows.append(
            F(f"px6-{suf}", name, sub, line, "planetx", date, msrp, '1:24', demand,
              "planet-x,transformers,3p,curated")
        )

    # NEW: KFC
    for row in raw.get("kfc", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 85.0
        line = "KFC Phase"
        if "Named" in sub:
            line = "KFC Named"
        elif "Combiner" in sub:
            line = "KFC Combiner"
        elif sub == "Special":
            line = "KFC Special"
        rows.append(
            F(f"kfc6-{suf}", name, sub, line, "kfc", date, msrp, '1:24', demand,
              "kfc,keiths-fantasy-club,transformers,3p,curated")
        )

    # NEW: XTransbots
    for row in raw.get("xtransbots", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 110.0
        line = "XTransbots MX"
        if "Combiner" in sub:
            line = "XTransbots Combiner"
        elif sub == "Special":
            line = "XTransbots Special"
        rows.append(
            F(f"xt6-{suf}", name, sub, line, "xtransbots", date, msrp, '1:24', demand,
              "xtransbots,transformers,3p,curated")
        )

    # NEW: Flame Toys (Kuro Kara Kuri AF; Furai kits skipped upstream)
    for row in raw.get("flametoys", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 180.0
        line = "Kuro Kara Kuri"
        if "Flame Toys AF" in sub:
            line = "Flame Toys AF"
        elif sub == "Special":
            line = "Flame Toys Special"
        rows.append(
            F(f"ft6-{suf}", name, sub, line, "flametoys", date, msrp, '6"', demand,
              "flame-toys,kuro-kara-kuri,curated")
        )

    # NEW: TFC Toys
    for row in raw.get("tfc", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 110.0
        line = "TFC Toys"
        if "Hercules" in sub:
            line = "TFC Hercules"
        elif "Uranos" in sub:
            line = "TFC Uranos"
        elif "Prometheus" in sub:
            line = "TFC Prometheus"
        elif "Athena" in sub:
            line = "TFC Athena"
        elif "Saturn" in sub:
            line = "TFC Saturn"
        elif "Combiner" in sub:
            line = "TFC Combiner"
        elif sub == "Special":
            line = "TFC Special"
        elif sub == "Solo":
            line = "TFC Solo"
        rows.append(
            F(f"tfc6-{suf}", name, sub, line, "tfc", date, msrp, '1:24', demand,
              "tfc,transformers,3p,curated")
        )

    # NEW: GCreation
    for row in raw.get("gcreation", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 120.0
        line = "GCreation"
        if "ShuraKing" in sub:
            line = "GCreation ShuraKing"
        elif "Grimlock" in sub:
            line = "GCreation Grimlock King"
        elif "Stinger" in sub:
            line = "GCreation Stinger"
        elif "YX" in sub:
            line = "GCreation YX"
        elif "Combiner" in sub:
            line = "GCreation Combiner"
        elif sub == "Special":
            line = "GCreation Special"
        elif sub == "Solo":
            line = "GCreation Solo"
        rows.append(
            F(f"gc6-{suf}", name, sub, line, "gcreation", date, msrp, '1:24', demand,
              "gcreation,transformers,3p,curated")
        )

    # Kotobukiya Frame Arms / Hexa Gear (robot AF)
    for row in raw.get("kotobukiya", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 55.0
        line = "Frame Arms" if "Frame Arms" in sub else "Hexa Gear"
        rows.append(
            F(f"koto6-{suf}", name, sub, line, "kotobukiya", date, msrp, '6"', demand,
              "kotobukiya,frame-arms,hexa-gear,curated")
        )

    # SHFiguarts densify
    rows += _rows(raw.get("shfiguarts", []), "shf6", "S.H.Figuarts", "shfiguarts", '6"', 85.0,
                  "shfiguarts,tamashii,bandai,curated")

    # Kaiyodo densify
    for row in raw.get("kaiyodo", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 95.0
        line = "Amazing Yamaguchi" if "Yamaguchi" in sub else "Revoltech"
        rows.append(
            F(f"ky6-{suf}", name, sub, line, "kaiyodo", date, msrp, '6"', demand,
              "kaiyodo,revoltech,amazing-yamaguchi,curated")
        )

    # Hasbro densify
    rows += _rows(raw.get("hasbroLightning", []), "lc6", "Lightning Collection", "hasbro", '6"', 22.99,
                  "hasbro,power-rangers,lightning,curated")
    rows += _rows(raw.get("hasbroClassified", []), "cls6", "GI Joe Classified", "hasbro", '6"', 24.99,
                  "hasbro,gi-joe,classified,curated")
    rows += _rows(raw.get("hasbroMl", []), "ml6", "Marvel Legends", "hasbro", '6"', 24.99,
                  "hasbro,marvel,legends,curated")
    rows += _rows(raw.get("hasbroBs", []), "bs6", "Black Series", "hasbro", '6"', 24.99,
                  "hasbro,star-wars,black-series,curated")
    rows += _rows(raw.get("hasbroSs", []), "ss6", "Transformers Studio Series", "hasbro", '6"', 24.99,
                  "hasbro,transformers,studio-series,curated")

    # Mattel densify
    for row in raw.get("mattel", []):
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else 24.99
        line = "Masterverse"
        if "WWE Elite" in sub:
            line = "WWE Elite"
        elif "WWE Ultimate" in sub:
            line = "WWE Ultimate Edition"
        elif "Revolution" in sub:
            line = "Masterverse Revolution"
        elif "New Eternia" in sub:
            line = "Masterverse New Eternia"
        rows.append(
            F(f"mat6-{suf}", name, sub, line, "mattel", date, msrp, '7"', demand,
              "mattel,masterverse,wwe,curated")
        )

    # McFarlane
    for row in raw.get("mcfarlane", []):
        suf, name, sub, date, demand = row[:5]
        line = "DC Multiverse"
        if "Spawn" in sub or "Spawn" in name or any(
            x in name for x in ("Gunslinger", "Haunt", "Violator", "Cogliostro", "Angela", "She-Spawn", "Medieval")
        ):
            line = "Spawn"
        elif "Page Punchers" in sub:
            line = "Page Punchers"
        elif "Gold Label" in sub:
            line = "DC Multiverse Gold Label"
        elif "Collector" in sub or "Megafig" in sub:
            line = "DC Multiverse Collector"
        elif "Platinum" in sub:
            line = "DC Multiverse Platinum"
        rows.append(
            F(f"mcf6-{suf}", name, sub, line, "mcfarlane", date, 22.99, '7"', demand,
              "mcfarlane,dc,curated")
        )

    # NECA
    for row in raw.get("neca", []):
        suf, name, sub, date, demand = row[:5]
        line = "NECA Ultimate"
        alien_keys = ("Alien", "Aliens", "Xenomorph", "Ripley", "Bishop", "Hudson", "Vasquez", "Hicks", "Apone", "Newt", "Big Chap", "Dog Alien", "Alien Queen")
        pred_keys = ("Predator", "Dutch", "Harrigan", "Jungle Hunter", "City Hunter", "Elder Predator", "Scout Predator", "Fugitive", "Assassin Predator")
        horror_keys = ("Freddy", "Jason", "Michael", "Chucky", "Tiffany", "Pinhead", "Ghostface", "Pennywise", "Ash", "Evil Dead", "Henrietta", "Deadite", "Gremlin", "Stripe", "Pumpkinhead", "Chatterer")
        tmnt_names = ("Leonardo", "Raphael", "Michelangelo", "Donatello", "Casey Jones", "April O'Neil", "Splinter", "Shredder", "Slash", "Tokka", "Rahzar", "Leatherhead", "Usagi Yojimbo")
        if any(x in sub or x in name for x in alien_keys):
            line = "Aliens Ultimate"
        elif any(x in sub or x in name for x in pred_keys):
            line = "Predator Ultimate"
        elif name in tmnt_names or "Mirage" in sub or "TMNT" in sub:
            line = "TMNT Ultimate"
        if any(x in sub or x in name for x in horror_keys):
            line = "Horror Ultimate"
        elif "Godzilla" in sub or name in ("Godzilla", "King Ghidorah", "Mothra", "Rodan", "Mechagodzilla", "Kong"):
            line = "Godzilla Ultimate"
        rows.append(
            F(f"neca6-{suf}", name, sub, line, "neca", date, 34.99, '7"', demand,
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
            F(f"s76-{suf}", name, sub, line, "super7", date, msrp, scale, demand,
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
            F(f"dcd6-{suf}", name, sub, line, "dcdirect", date, 24.99, '6.5"', demand,
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
        elif "Storage Shell" in sub:
            line = "TMNT Storage Shell"
        elif "Movie Star" in sub:
            line = "TMNT Movie Star"
        rows.append(
            F(f"pm6-{suf}", name, sub, line, "playmates", date, 14.99, '4.5"', demand,
              "playmates,tmnt,curated")
        )

    # Mezco
    rows += _rows(raw.get("mezco", []), "mez6", "One:12 Collective", "mezco", '1:12', 112.0,
                  "mezco,one12,curated")

    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out
