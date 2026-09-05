"""BBTS AF brand expansion wave 3 — densify + new makers.

New CompanyIds: sentinel, thousandtoys, acidrain, freshmonkey, jada.
Densify: super7, premiumdna, hiya, mondo, beastkingdom, hottoys, threezero,
mattel (Creations/WWE/Masterverse), hasbro (Black Series/Legends BAFs),
neca Ultimate, mezco One:12, fourhorsemen Cosmic Legions, bossfight,
loyalsubjects, mcfarlane, bandai robot AF, shfiguarts (Tamashii).

Skip: ACBA-adjacent, Fresh (brand), Nano Metalfigs diecast-only.
Floor 1980; no imageUrl; AF only.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("bbts_wave3_data.json")


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
        "source": "curated-bbts-wave3",
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


def build_bbts_wave3() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []

    # Super7 densify
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
            F(f"s73-{suf}", name, sub, line, "super7", date, msrp, scale, demand,
              "super7,curated")
        )

    # Premium DNA
    for row in raw.get("premiumdna", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 55.0
        rows.append(
            F(f"pd3-{suf}", name, sub, "Premium DNA Signature", "premiumdna", date, msrp, '1:12', demand,
              "premium-dna,curated")
        )

    # Hiya
    for row in raw.get("hiya", []):
        suf, name, sub, date, demand = row[:5]
        line = "Hiya Exquisite"
        if "Godzilla" in sub or name in (
            "Godzilla", "King Ghidorah", "Rodan", "Mothra", "Mechagodzilla",
            "Shimo", "Scar King", "King Kong",
        ):
            line = "Hiya Godzilla"
        elif "G.I. Joe" in sub:
            line = "Hiya G.I. Joe"
        elif "Star Trek" in sub:
            line = "Hiya Star Trek"
        elif "Judge" in sub or "Dredd" in name or "Anderson" in name:
            line = "Hiya Judge Dredd"
        rows.append(
            F(f"hy3-{suf}", name, sub, line, "hiya", date, 45.0, '1:18', demand,
              "hiya,curated")
        )

    # Mondo
    for row in raw.get("mondo", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 180.0
        scale = '1:6' if '1/6' in sub else '1:12'
        line = "Mondo"
        if "Animated" in sub:
            line = "Mondo BTAS"
        elif "TMNT" in sub:
            line = "Mondo TMNT"
        elif "MotU" in sub:
            line = "Mondo MotU"
        elif any(x in sub for x in ("Horror", "Evil Dead", "Army of Darkness", "Hellraiser")):
            line = "Mondo Horror"
        elif "ThunderCats" in sub:
            line = "Mondo ThunderCats"
        rows.append(
            F(f"mo3-{suf}", name, sub, line, "mondo", date, msrp, scale, demand,
              "mondo,curated")
        )

    # Beast Kingdom
    rows += _rows(raw.get("beastKingdom", []), "bk3", "Dynamic Action Heroes", "beastkingdom", '1:9', 120.0,
                  "beast-kingdom,dah,curated")

    # Hot Toys
    for row in raw.get("hottoys", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 350.0
        rows.append(
            F(f"ht3-{suf}", name, sub, "Hot Toys", "hottoys", date, msrp, '1:6', demand,
              "hot-toys,curated")
        )

    # threezero
    for row in raw.get("threezero", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 180.0
        line = "threezero DLX"
        if "Overwatch" in sub:
            line = "threezero Overwatch"
        elif "Pacific Rim" in sub:
            line = "threezero Pacific Rim"
        elif any(x in sub for x in ("RoboCop", "Aliens", "Predator", "Dark Knight", "G.I. Joe", "DC", "Arkham")):
            line = "threezero"
        rows.append(
            F(f"tz3-{suf}", name, sub, line, "threezero", date, msrp, '1:12', demand,
              "threezero,curated")
        )

    # NEW: Sentinel
    for row in raw.get("sentinel", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 90.0
        line = "Sentinel"
        if "Fighting Armor" in sub:
            line = "Fighting Armor"
        elif "Riobot" in sub:
            line = "Riobot"
        elif "Wonderful Acts" in sub:
            line = "Wonderful Acts"
        rows.append(
            F(f"sen-{suf}", name, sub, line, "sentinel", date, msrp, '6"', demand,
              "sentinel,curated")
        )

    # NEW: 1000Toys
    for row in raw.get("thousandtoys", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 80.0
        line = "Tough Guys" if "Tough" in sub or "Tough Guys" in sub else "Synthetic Human"
        if "Synthetic" in sub or suf.startswith("synth"):
            line = "Synthetic Human"
        rows.append(
            F(f"tt-{suf}", name, sub, line, "thousandtoys", date, msrp, '6"', demand,
              "1000toys,thousandtoys,curated")
        )

    # NEW: Acid Rain
    rows += _rows(raw.get("acidrain", []), "ar", "Acid Rain World", "acidrain", '1:18', 35.0,
                  "acid-rain,toys-alliance,curated")
    for r in rows:
        if r["company"] != "acidrain":
            continue
        sub = r["subtitle"]
        if "FAV" in sub:
            r["line"] = "Acid Rain FAV"
        elif " AG" in sub or sub.endswith("AG"):
            r["line"] = "Acid Rain AG"
        elif "B2Five" in sub:
            r["line"] = "Acid Rain B2Five"

    # NEW: Fresh Monkey / Fresh Retro
    for row in raw.get("freshmonkey", []):
        suf, name, sub, date, demand = row[:5]
        line = "Fresh Monkey Fiction"
        if "Fresh Retro" in sub:
            line = "Fresh Retro"
        rows.append(
            F(f"fm-{suf}", name, sub, line, "freshmonkey", date, 24.99, '6"', demand,
              "fresh-monkey,fresh-retro,curated")
        )

    # NEW: Jada
    for row in raw.get("jada", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 24.99
        line = "Jada Toys"
        if "Street Fighter" in sub:
            line = "Street Fighter"
        elif "Universal" in sub:
            line = "Universal Monsters"
        elif sub in ("DC Comics",):
            line = "Jada DC"
        elif sub in ("Marvel",):
            line = "Jada Marvel"
        rows.append(
            F(f"jada-{suf}", name, sub, line, "jada", date, msrp, '6"', demand,
              "jada,curated")
        )

    # Mattel Creations / WWE / Masterverse
    rows += _rows(raw.get("mattelCreations", []), "mc3", "Mattel Creations", "mattel", '7"', 50.0,
                  "mattel,creations,motu,curated")
    rows += _rows(raw.get("wwe", []), "wwe3", "WWE Elite", "mattel", '6"', 24.99,
                  "mattel,wwe,curated")
    for r in rows:
        if r["id"].startswith("wwe3-ultimate"):
            r["line"] = "WWE Ultimate Edition"
    rows += _rows(raw.get("masterverse", []), "mv3", "Masterverse", "mattel", '7"', 22.99,
                  "mattel,masterverse,motu,curated")
    for r in rows:
        if not r["id"].startswith("mv3-"):
            continue
        sub = r["subtitle"]
        if "New Eternia" in sub:
            r["line"] = "Masterverse New Eternia"
        elif sub == "Revolution":
            r["line"] = "Masterverse Revolution"
        elif "Movie" in sub:
            r["line"] = "Masterverse Movie"
        elif sub == "Revelation":
            r["line"] = "Masterverse Revelation"

    # Hasbro Black Series / Legends BAFs
    rows += _rows(raw.get("hasbroBs", []), "bs3", "Black Series", "hasbro", '6"', 24.99,
                  "hasbro,star-wars,black-series,curated")
    rows += _rows(raw.get("hasbroMl", []), "ml3", "Marvel Legends", "hasbro", '6"', 24.99,
                  "hasbro,marvel,legends,baf,curated")

    # NECA Ultimate
    for row in raw.get("neca", []):
        suf, name, sub, date, demand = row[:5]
        line = "NECA Ultimate"
        if "Alien" in sub or "Aliens" in sub:
            line = "Aliens Ultimate"
        elif "Predator" in sub or "Predators" in sub:
            line = "Predator Ultimate"
        elif "TMNT" in sub or "Mirage" in sub:
            line = "TMNT Ultimate"
        elif any(x in sub for x in ("Freddy", "Jason", "Michael", "Leatherface", "Chucky", "Pinhead", "Pennywise", "Ash", "Candy", "Ghostface", "Jigsaw", "Pyramid", "Nemesis")) or name in (
            "Freddy Krueger", "Jason Voorhees", "Michael Myers", "Leatherface", "Chucky", "Pinhead",
            "Pennywise", "Ash Williams", "Candyman", "Ghostface", "Jigsaw", "Pyramid Head", "Nemesis",
        ):
            line = "Horror Ultimate"
        elif "Castlevania" in sub:
            line = "Castlevania Ultimate"
        elif "Universal" in sub:
            line = "Universal Monsters Ultimate"
        elif "Godzilla" in sub or "Kong" in name:
            line = "Godzilla Ultimate"
        rows.append(
            F(f"neca3-{suf}", name, sub, line, "neca", date, 34.99, '7"', demand,
              "neca,ultimate,curated")
        )

    # Mezco One:12
    rows += _rows(raw.get("mezco", []), "mez3", "One:12 Collective", "mezco", '1:12', 112.0,
                  "mezco,one12,curated")

    # Cosmic Legions (fourhorsemen)
    rows += _rows(raw.get("cosmicLegions", []), "cl3", "Cosmic Legions", "fourhorsemen", '6"', 45.0,
                  "four-horsemen,cosmic-legions,curated")

    # Boss Fight
    for row in raw.get("bossfight", []):
        suf, name, sub, date, demand = row[:5]
        line = "Epic H.A.C.K.S."
        if "Vitruvian" in sub or "Blank" in sub or suf.startswith("vit"):
            line = "Vitruvian H.A.C.K.S."
        elif sub == "Accessory":
            line = "H.A.C.K.S. Accessories"
        rows.append(
            F(f"bf3-{suf}", name, sub, line, "bossfight", date, 24.99, '1:12', demand,
              "boss-fight,hacks,curated")
        )

    # Loyal Subjects
    rows += _rows(raw.get("loyalsubjects", []), "tls3", "BST AXN", "loyalsubjects", '5"', 24.99,
                  "loyal-subjects,bst-axn,curated")

    # McFarlane
    for row in raw.get("mcfarlane", []):
        suf, name, sub, date, demand = row[:5]
        line = "DC Multiverse"
        if "Spawn" in sub or "Spawn" in name or "Gunslinger" in name or "Haunt" in name or "Violator" in name or "Cogliostro" in name:
            line = "Spawn"
        elif "Page Punchers" in sub:
            line = "Page Punchers"
        rows.append(
            F(f"mcf3-{suf}", name, sub, line, "mcfarlane", date, 22.99, '7"', demand,
              "mcfarlane,dc,curated")
        )

    # Bandai robot AF
    for row in raw.get("bandai", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 55.0
        line = sub if sub in ("Robot Spirits", "Gundam Universe", "G Frame", "MSiA") else "Robot Spirits"
        scale = '5"' if line in ("G Frame", "MSiA", "Gundam Universe") else '6"'
        rows.append(
            F(f"bn3-{suf}", name, sub, line, "bandai", date, msrp, scale, demand,
              "bandai,gundam,robot-spirits,af,curated")
        )

    # SHFiguarts / Tamashii
    for row in raw.get("shfiguarts", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 75.0
        rows.append(
            F(f"shf3-{suf}", name, sub, "S.H.Figuarts", "shfiguarts", date, msrp, '6"', demand,
              "shfiguarts,tamashii,bandai,curated")
        )

    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out
