"""BBTS AF brand expansion wave 2 — densify + new makers.

New CompanyIds: fourhorsemen (Mythic Legions / Cosmic / Figura Obscura),
spinmaster (Bakugan AF + MotU Origins SM).

Densify: mcfarlane, neca, storm, shfiguarts, hasbro (PR/Joe/ML), toybiz,
loyalsubjects, bossfight, figma, valaverse, hiya, mondo, jakks, hottoys,
bandai (Robot Spirits / Gundam Universe AF — not Gunpla kits).

Floor 1980; no imageUrl; AF only.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("bbts_wave2_data.json")


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
        "source": "curated-bbts-wave2",
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


def build_bbts_wave2() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []

    # New companies
    for row in raw.get("fourhorsemen", []):
        suf, name, sub, date, demand = row[:5]
        line = "Mythic Legions"
        if "Cosmic Legions" in sub:
            line = "Cosmic Legions"
        elif "Figura Obscura" in sub:
            line = "Figura Obscura"
        elif "All-Stars" in sub:
            line = "Mythic Legions All-Stars"
        rows.append(
            F(f"fh-{suf}", name, sub, line, "fourhorsemen", date, 45.0, '6"', demand,
              "four-horsemen,mythic-legions,curated")
        )

    for row in raw.get("spinmaster", []):
        suf, name, sub, date, demand = row[:5]
        line = "Bakugan"
        scale = '4"'
        msrp = 14.99
        if "MotU" in sub or "Origins" in sub:
            line = "MotU Origins (Spin Master)"
            scale = '5.5"'
            msrp = 19.99
        elif "Legacy" in sub:
            line = "Bakugan Legacy Collection"
            msrp = 19.99
        rows.append(
            F(f"sm-{suf}", name, sub, line, "spinmaster", date, msrp, scale, demand,
              "spin-master,bakugan,curated")
        )

    # Bandai robot AF (not kits)
    for row in raw.get("bandai", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row
            msrp = 55.0
        line = sub if sub in ("Robot Spirits", "Gundam Universe", "G Frame", "MSiA", "Anime Color Edition") else "Robot Spirits"
        scale = '5"' if "G Frame" in line or "MSiA" in line or "Gundam Universe" in line else '6"'
        rows.append(
            F(f"bn-{suf}", name, sub, line, "bandai", date, msrp, scale, demand,
              "bandai,gundam,robot-spirits,af,curated")
        )

    # Densify existing
    for row in raw.get("mcfarlane", []):
        suf, name, sub, date, demand = row[:5]
        line = "DC Multiverse"
        if "Spawn" in sub or suf.startswith("spawn") or "Spawn Artist" in sub:
            line = "Spawn"
        elif sub == "Page Punchers":
            line = "Page Punchers"
        rows.append(
            F(f"mcf2-{suf}", name, sub, line, "mcfarlane", date, 22.99, '7"', demand,
              "mcfarlane,dc,curated")
        )

    for row in raw.get("neca", []):
        suf, name, sub, date, demand = row[:5]
        line = "NECA"
        if "TMNT" in suf or "Mirage" in sub or "Cartoon" in sub or "1990" in sub or sub in ("Movie", "Pirate", "Samurai"):
            line = "TMNT"
        elif "Alien" in sub or sub in ("Aliens", "Aliens 3", "Alien Resurrection", "Deluxe"):
            line = "Aliens"
        elif "Predator" in sub or "Predators" in sub or "The Predator" in sub:
            line = "Predator"
        elif any(x in sub for x in ("Nightmare", "Friday", "Halloween", "Texas", "Child", "Hellraiser", "Scream", "IT", "Saw", "Silent", "Evil Dead", "Candyman", "Trick", "Crypt")):
            line = "Horror"
        elif "Universal" in sub:
            line = "Universal Monsters"
        elif "Godzilla" in sub or sub in ("Godzilla",):
            line = "Godzilla"
        elif "Terminator" in sub:
            line = "Terminator"
        elif "Castlevania" in sub:
            line = "Castlevania"
        elif "Skull Island" in sub:
            line = "King Kong"
        rows.append(
            F(f"neca2-{suf}", name, sub, line, "neca", date, 32.99, '7"', demand,
              "neca,curated")
        )

    for row in raw.get("storm", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row
            msrp = 90.0
        line = "Storm Collectibles"
        if "Street Fighter" in sub:
            line = "Street Fighter"
        elif "Mortal Kombat" in sub:
            line = "Mortal Kombat"
        elif "Tekken" in sub:
            line = "Tekken"
        rows.append(
            F(f"storm2-{suf}", name, sub, line, "storm", date, msrp, '1:12', demand,
              "storm,curated")
        )

    for row in raw.get("shfiguarts", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row
            msrp = 75.0
        rows.append(
            F(f"shf2-{suf}", name, sub, "S.H.Figuarts", "shfiguarts", date, msrp, '6"', demand,
              "shfiguarts,tamashii,curated")
        )

    rows += _rows(raw.get("hasbroPr", []), "pr2", "Lightning Collection", "hasbro", '6"', 22.99,
                  "hasbro,power-rangers,curated")
    # Fix PR line per subtitle family for remastered etc — keep Lightning Collection

    rows += _rows(raw.get("hasbroJoe", []), "joe2", "GI Joe Classified", "hasbro", '6"', 24.99,
                  "hasbro,gi-joe,curated")

    rows += _rows(raw.get("hasbroMl", []), "ml2", "Marvel Legends", "hasbro", '6"', 24.99,
                  "hasbro,marvel,curated")

    rows += _rows(raw.get("toybiz", []), "tb2", "Marvel Legends (Toy Biz)", "toybiz", '6"', 8.99,
                  "toybiz,marvel,vintage,curated")

    for row in raw.get("loyalsubjects", []):
        suf, name, sub, date, demand = row[:5]
        line = "BST AXN"
        rows.append(
            F(f"tls2-{suf}", name, sub, line, "loyalsubjects", date, 24.99, '5"', demand,
              "loyal-subjects,bst-axn,curated")
        )

    for row in raw.get("bossfight", []):
        suf, name, sub, date, demand = row[:5]
        line = "Epic H.A.C.K.S."
        if "Vitruvian" in sub or "Vitruvian" in name:
            line = "Vitruvian H.A.C.K.S."
        elif "Blank" in sub or "Powerhouse" in name:
            line = "Vitruvian H.A.C.K.S."
        elif sub == "Accessory":
            line = "H.A.C.K.S. Accessories"
        rows.append(
            F(f"bf2-{suf}", name, sub, line, "bossfight", date, 24.99, '1:12', demand,
              "boss-fight,hacks,curated")
        )

    for row in raw.get("figma", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row
            msrp = 80.0
        rows.append(
            F(f"fg2-{suf}", name, sub, "figma", "figma", date, msrp, '6"', demand,
              "figma,max-factory,curated")
        )

    rows += _rows(raw.get("valaverse", []), "vv2", "Action Force", "valaverse", '1:12', 24.99,
                  "valaverse,action-force,curated")

    for row in raw.get("hiya", []):
        suf, name, sub, date, demand = row[:5]
        line = "Hiya Exquisite"
        if "Godzilla" in sub or name in ("Godzilla", "King Ghidorah", "Rodan", "Mothra", "Mechagodzilla", "Shimo", "Scar King", "King Kong"):
            line = "Hiya Godzilla"
        elif "G.I. Joe" in sub:
            line = "Hiya G.I. Joe"
        elif "Star Trek" in sub:
            line = "Hiya Star Trek"
        elif "Judge" in sub or "Dredd" in sub:
            line = "Hiya Judge Dredd"
        rows.append(
            F(f"hy2-{suf}", name, sub, line, "hiya", date, 45.0, '1:18', demand,
              "hiya,curated")
        )

    for row in raw.get("mondo", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row
            msrp = 180.0
        scale = '1:6' if '1/6' in sub else '1:12'
        line = "Mondo"
        if "Animated" in sub:
            line = "Mondo BTAS"
        elif "TMNT" in sub:
            line = "Mondo TMNT"
        elif "MotU" in sub:
            line = "Mondo MotU"
        elif "Horror" in sub or "Evil Dead" in sub or "Army of Darkness" in sub:
            line = "Mondo Horror"
        rows.append(
            F(f"mo2-{suf}", name, sub, line, "mondo", date, msrp, scale, demand,
              "mondo,curated")
        )

    for row in raw.get("jakks", []):
        suf, name, sub, date, demand = row[:5]
        line = "JAKKS"
        if sub == "WWE":
            line = "JAKKS WWE"
        elif "Nintendo" in sub:
            line = "Nintendo Super Stars"
        elif "Sonic" in name or "Modern" in sub or "Movie" in sub or name in ("Tails", "Knuckles", "Amy Rose", "Shadow", "Rouge", "Dr. Eggman", "Silver", "Blaze", "Metal Sonic"):
            line = "Sonic the Hedgehog"
        rows.append(
            F(f"jk2-{suf}", name, sub, line, "jakks", date, 14.99, '4"', demand,
              "jakks,curated")
        )

    for row in raw.get("hottoys", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row
            msrp = 350.0
        rows.append(
            F(f"ht2-{suf}", name, sub, "Hot Toys", "hottoys", date, msrp, '1:6', demand,
              "hot-toys,curated")
        )

    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out
