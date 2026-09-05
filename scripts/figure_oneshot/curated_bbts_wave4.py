"""BBTS AF brand expansion wave 4 — densify + new makers.

New CompanyIds: blokees, robosen, newage, fanstoys, tunshi, damtoys,
easysimple, soldierstory, minutimes, verycool.
Densify: Hasbro ML/BS/Classified/SS, Mattel Masterverse/WWE, Super7, NECA,
Mezco, McFarlane, Hiya, Mondo, SHF, Storm, Four Horsemen, Boss Fight, TLS,
Playmates TMNT, ToyBiz, Kenner Super Powers leftovers, DC Direct gaps,
Takara MPG leftovers.

Skip: Crossovers, Unique Art statues, XM Studios statues.
Floor 1980; no imageUrl; AF only.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("bbts_wave4_data.json")


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
        "source": "curated-bbts-wave4",
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


def build_bbts_wave4() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []

    # NEW: Blokees
    for row in raw.get("blokees", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 25.0
        line = "Blokees Galaxy Version"
        if "Gundam" in sub:
            line = "Blokees Gundam"
        elif "IDW" in sub:
            line = "Blokees Transformers IDW"
        elif "Transformers" in sub:
            line = "Blokees Transformers"
        rows.append(
            F(f"blk-{suf}", name, sub, line, "blokees", date, msrp, '4"', demand,
              "blokees,galaxy-version,curated")
        )

    # NEW: Robosen (sparse)
    for row in raw.get("robosen", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 399.0
        line = "Robosen"
        if "Flagship" in sub:
            line = "Robosen Flagship"
        elif "Elite" in sub:
            line = "Robosen Elite"
        elif "Mini" in sub:
            line = "Robosen Mini"
        elif "One Edition" in sub or "Performance" in sub:
            line = "Robosen Performance"
        rows.append(
            F(f"rob-{suf}", name, sub, line, "robosen", date, msrp, '16"', demand,
              "robosen,transformers,robotic,curated")
        )

    # NEW: Newage
    rows += _rows(raw.get("newage", []), "na", "Newage", "newage", '6"', 55.0,
                  "newage,transformers,3p,curated")

    # NEW: Fans Toys
    rows += _rows(raw.get("fanstoys", []), "ft", "Fans Toys", "fanstoys", '1:24', 120.0,
                  "fans-toys,transformers,3p,curated")

    # NEW: Tunshi
    for row in raw.get("tunshi", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 65.0
        line = "Tunshi Studio"
        if "Street Fighter" in sub:
            line = "Tunshi Street Fighter"
        elif "Mortal Kombat" in sub:
            line = "Tunshi Mortal Kombat"
        rows.append(
            F(f"tun-{suf}", name, sub, line, "tunshi", date, msrp, '1:12', demand,
              "tunshi,1-12,curated")
        )

    # NEW: DamToys 1/12
    for row in raw.get("damtoys", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 55.0
        line = "DamToys 1/12"
        if "Gangsters" in sub:
            line = "Gangsters Kingdom"
        elif "Pocket Elite" in sub:
            line = "Pocket Elite Series"
        elif "Anime" in sub:
            line = "DamToys Anime"
        rows.append(
            F(f"dam-{suf}", name, sub, line, "damtoys", date, msrp, '1:12', demand,
              "damtoys,1-12,curated")
        )

    # NEW: Easy & Simple
    for row in raw.get("easysimple", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 55.0
        line = "Easy & Simple"
        if "PMC" in sub:
            line = "Easy & Simple PMC"
        elif "SOF" in sub:
            line = "Easy & Simple SOF"
        elif "Urban" in sub:
            line = "Easy & Simple Urban"
        elif "Environment" in sub:
            line = "Easy & Simple Environment"
        elif "Contractor" in sub:
            line = "Easy & Simple Contractor"
        rows.append(
            F(f"es-{suf}", name, sub, line, "easysimple", date, msrp, '1:12', demand,
              "easy-simple,1-12,military,curated")
        )

    # NEW: Soldier Story 1/12
    rows += _rows(raw.get("soldierstory", []), "ss12", "Soldier Story 1/12", "soldierstory",
                  '1:12', 55.0, "soldier-story,1-12,military,curated")

    # NEW: Mini Times
    rows += _rows(raw.get("minitimes", []), "mt", "Mini Times 1/12", "minitimes",
                  '1:12', 48.0, "mini-times,1-12,military,curated")

    # NEW: Very Cool
    for row in raw.get("verycool", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 58.0
        line = "Very Cool 1/12"
        if "Agents" in sub:
            line = "Very Cool Agents"
        rows.append(
            F(f"vc-{suf}", name, sub, line, "verycool", date, msrp, '1:12', demand,
              "very-cool,1-12,curated")
        )

    # Hasbro densify
    rows += _rows(raw.get("hasbroMl", []), "ml4", "Marvel Legends", "hasbro", '6"', 24.99,
                  "hasbro,marvel,legends,curated")
    rows += _rows(raw.get("hasbroBs", []), "bs4", "Black Series", "hasbro", '6"', 24.99,
                  "hasbro,star-wars,black-series,curated")
    rows += _rows(raw.get("hasbroClassified", []), "cls4", "GI Joe Classified", "hasbro", '6"', 24.99,
                  "hasbro,gi-joe,classified,curated")
    rows += _rows(raw.get("hasbroSs", []), "ss4", "Transformers Studio Series", "hasbro", '6"', 24.99,
                  "hasbro,transformers,studio-series,curated")

    # Mattel
    rows += _rows(raw.get("masterverse", []), "mv4", "Masterverse", "mattel", '7"', 22.99,
                  "mattel,masterverse,motu,curated")
    for r in rows:
        if not r["id"].startswith("mv4-"):
            continue
        sub = r["subtitle"]
        if "New Eternia" in sub:
            r["line"] = "Masterverse New Eternia"
        elif sub == "Revolution":
            r["line"] = "Masterverse Revolution"
    rows += _rows(raw.get("wwe", []), "wwe4", "WWE Elite", "mattel", '6"', 24.99,
                  "mattel,wwe,curated")
    for r in rows:
        if r["id"].startswith("wwe4-ultimate"):
            r["line"] = "WWE Ultimate Edition"

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
            F(f"s74-{suf}", name, sub, line, "super7", date, msrp, scale, demand,
              "super7,curated")
        )

    # NECA
    for row in raw.get("neca", []):
        suf, name, sub, date, demand = row[:5]
        line = "NECA Ultimate"
        if "Alien" in sub or "Aliens" in sub or "Xenomorph" in name or "Ripley" in name or "Bishop" in name or "Hudson" in name or "Vasquez" in name or "Hicks" in name or "Apone" in name:
            line = "Aliens Ultimate"
        elif "Predator" in sub or "Dutch" in name or "Harrigan" in name or "Jungle Hunter" in name or "City Hunter" in name:
            line = "Predator Ultimate"
        elif "TMNT" in sub or "Mirage" in sub or name in ("Casey Jones", "April O'Neil", "Splinter", "Shredder", "Slash", "Tokka", "Rahzar", "Leatherhead", "Usagi Yojimbo"):
            line = "TMNT Ultimate"
        elif any(x in sub or x in name for x in ("Freddy", "Jason", "Michael", "Chucky", "Tiffany", "Pinhead", "Cenobite", "Butterball", "Chatterer", "Ghostface", "Pennywise", "Ash", "Evil Dead", "Henrietta", "Eligos", "Pugsley")):
            line = "Horror Ultimate"
        elif "Godzilla" in sub or "Godzilla" in name:
            line = "Godzilla Ultimate"
        rows.append(
            F(f"neca4-{suf}", name, sub, line, "neca", date, 34.99, '7"', demand,
              "neca,ultimate,curated")
        )

    # Mezco
    rows += _rows(raw.get("mezco", []), "mez4", "One:12 Collective", "mezco", '1:12', 112.0,
                  "mezco,one12,curated")

    # McFarlane
    for row in raw.get("mcfarlane", []):
        suf, name, sub, date, demand = row[:5]
        line = "DC Multiverse"
        if "Spawn" in sub or "Spawn" in name or "Gunslinger" in name or "Haunt" in name or "Violator" in name or "Cogliostro" in name or "Angela" in name or "Malebolgia" in name or "She-Spawn" in name or "Medieval" in name:
            line = "Spawn"
        elif "Page Punchers" in sub:
            line = "Page Punchers"
        rows.append(
            F(f"mcf4-{suf}", name, sub, line, "mcfarlane", date, 22.99, '7"', demand,
              "mcfarlane,dc,curated")
        )

    # Hiya
    for row in raw.get("hiya", []):
        suf, name, sub, date, demand = row[:5]
        line = "Hiya Exquisite"
        if any(x in sub or x in name for x in ("Godzilla", "Ghidorah", "Rodan", "Mothra", "Mechagodzilla", "Kong", "Shimo", "Scar King", "MonsterVerse", "Minus")):
            line = "Hiya Godzilla"
        elif "G.I. Joe" in sub:
            line = "Hiya G.I. Joe"
        elif "Star Trek" in sub:
            line = "Hiya Star Trek"
        elif "Judge" in sub or "Dredd" in name or "Anderson" in name:
            line = "Hiya Judge Dredd"
        rows.append(
            F(f"hy4-{suf}", name, sub, line, "hiya", date, 45.0, '1:18', demand,
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
        if "BTAS" in sub:
            line = "Mondo BTAS"
        elif "TMNT" in sub:
            line = "Mondo TMNT"
        elif "MotU" in sub:
            line = "Mondo MotU"
        elif any(x in sub for x in ("Horror", "Evil Dead", "Army of Darkness")):
            line = "Mondo Horror"
        elif "ThunderCats" in sub:
            line = "Mondo ThunderCats"
        rows.append(
            F(f"mo4-{suf}", name, sub, line, "mondo", date, msrp, scale, demand,
              "mondo,curated")
        )

    # SHFiguarts
    for row in raw.get("shfiguarts", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 75.0
        rows.append(
            F(f"shf4-{suf}", name, sub, "S.H.Figuarts", "shfiguarts", date, msrp, '6"', demand,
              "shfiguarts,tamashii,bandai,curated")
        )

    # Storm
    for row in raw.get("storm", []):
        suf, name, sub, date, demand = row[:5]
        line = "Street Fighter"
        if "Mortal Kombat" in sub:
            line = "Mortal Kombat"
        rows.append(
            F(f"st4-{suf}", name, sub, line, "storm", date, 90.0, '1:12', demand,
              "storm,curated")
        )

    # Four Horsemen
    for row in raw.get("fourhorsemen", []):
        suf, name, sub, date, demand = row[:5]
        line = "Mythic Legions"
        if "Cosmic" in sub:
            line = "Cosmic Legions"
        elif "Figura Obscura" in sub:
            line = "Figura Obscura"
        rows.append(
            F(f"fh4-{suf}", name, sub, line, "fourhorsemen", date, 45.0, '6"', demand,
              "four-horsemen,curated")
        )

    # Boss Fight
    for row in raw.get("bossfight", []):
        suf, name, sub, date, demand = row[:5]
        line = "Epic H.A.C.K.S."
        if "Vitruvian" in sub or "Blank" in sub or suf.startswith("vit"):
            line = "Vitruvian H.A.C.K.S."
        elif sub == "Accessory":
            line = "H.A.C.K.S. Accessories"
        rows.append(
            F(f"bf4-{suf}", name, sub, line, "bossfight", date, 24.99, '1:12', demand,
              "boss-fight,hacks,curated")
        )

    # Loyal Subjects
    rows += _rows(raw.get("loyalsubjects", []), "tls4", "BST AXN", "loyalsubjects", '5"', 24.99,
                  "loyal-subjects,bst-axn,curated")

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
        rows.append(
            F(f"pm4-{suf}", name, sub, line, "playmates", date, 14.99, '4.5"', demand,
              "playmates,tmnt,curated")
        )

    # ToyBiz
    for row in raw.get("toybiz", []):
        suf, name, sub, date, demand = row[:5]
        line = "Marvel Legends (Toy Biz)"
        if "Icons" in sub:
            line = "Marvel Legends Icons (Toy Biz)"
        elif "BAF" in sub:
            line = "Marvel Legends BAF (Toy Biz)"
        elif "Legendary" in sub:
            line = "Legendary Riders (Toy Biz)"
        elif "Face-Off" in sub:
            line = "Face-Off (Toy Biz)"
        rows.append(
            F(f"tb4-{suf}", name, sub, line, "toybiz", date, 9.99, '6"', demand,
              "toybiz,marvel,legends,curated")
        )

    # Kenner Super Powers leftovers
    rows += _rows(raw.get("kenner", []), "ksp4", "Super Powers", "kenner", '5"', 4.99,
                  "kenner,super-powers,dc,curated")

    # DC Direct densify
    for row in raw.get("dcdirect", []):
        suf, name, sub, date, demand = row[:5]
        line = "DC Direct"
        if "New 52" in sub:
            line = "DC Collectibles New 52"
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
        rows.append(
            F(f"dcd4-{suf}", name, sub, line, "dcdirect", date, 24.99, '6.5"', demand,
              "dc-direct,dc-collectibles,curated")
        )

    # Takara MPG leftovers
    for row in raw.get("takaratomy", []):
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        else:
            suf, name, sub, date, demand = row[:5]
            msrp = 120.0
        line = "Transformers MPG"
        if "Diaclone" in sub:
            line = "Diaclone Reboot"
        rows.append(
            F(f"tt4-{suf}", name, sub, line, "takaratomy", date, msrp, '8"', demand,
              "takara,mpg,transformers,curated")
        )

    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out
