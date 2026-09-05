"""BBTS AF brand expansion wave — starter curated depth for missing makers.

Companies: kaiyodo, jazwares, diamondselect, joytoy, beastkingdom, enterbay,
funko (Legacy/AF only), plus densify storm / shfiguarts / threezero.
Floor 1980; no imageUrl; AF only.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("bbts_wave_data.json")


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
        "source": "curated-bbts-wave",
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


def build_bbts_wave() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []

    rows += _rows(raw.get("kaiyodoAy", []), "ky-ay", "Amazing Yamaguchi", "kaiyodo", '6"', 85.0, "kaiyodo,revoltech,amazing-yamaguchi,curated")
    rows += _rows(raw.get("kaiyodoRevoltech", []), "ky-rev", "Revoltech", "kaiyodo", '6"', 55.0, "kaiyodo,revoltech,curated")

    # Fortnite rows already include msrp
    for suf, name, sub, date, demand, msrp in raw.get("jazwaresFortnite", []):
        rows.append(F(f"jz-{suf}", name, sub, "Fortnite", "jazwares", date, msrp, '4"', demand, "jazwares,fortnite,curated"))
    rows += _rows(raw.get("jazwaresAew", []), "jz", "AEW Unrivaled", "jazwares", '6"', 24.99, "jazwares,aew,curated")

    rows += _rows(raw.get("diamondMarvelSelect", []), "dst", "Marvel Select", "diamondselect", '7"', 30.0, "diamond,marvel-select,curated")
    rows += _rows(raw.get("diamondDst", []), "dst", "Diamond Select", "diamondselect", '7"', 30.0, "diamond,dst,curated")

    for row in raw.get("joytoy", []):
        suf, name, sub, date, demand, msrp = row
        line = sub if sub in ("Warhammer 40K", "Dark Source") else "JoyToy"
        rows.append(F(f"{suf}" if suf.startswith("jt-") else f"jt-{suf}", name, sub, line, "joytoy", date, msrp, '1:18', demand, "joytoy,curated"))

    rows += _rows(raw.get("beastKingdom", []), "bk", "Dynamic Action Heroes", "beastkingdom", '1:9', 120.0, "beast-kingdom,dah,curated")

    for suf, name, sub, date, demand, msrp in raw.get("enterbay", []):
        line = "Enterbay 1/6"
        if any(x in name for x in ("Jordan", "Bryant", "James", "Curry", "Durant", "Antetokounmpo", "Harden", "Westbrook", "Dončić", "Jokić", "Tatum", "Embiid", "Morant", "Edwards")):
            line = "Enterbay NBA"
        rows.append(F(f"{suf}", name, sub, line, "enterbay", date, msrp, '1:6', demand, "enterbay,curated"))

    rows += _rows(raw.get("funko", []), "fk", "Funko Legacy Collection", "funko", '6"', 19.99, "funko,legacy,af,curated")
    # Fix Funko line per subtitle family
    for r in rows:
        if r["company"] != "funko":
            continue
        sub = r["subtitle"]
        if "Star Wars" in sub:
            r["line"] = "Funko Star Wars Legacy"
        elif "Disney" in sub:
            r["line"] = "Funko Disney AF"
        else:
            r["line"] = "Funko Legacy Collection"

    for suf, name, sub, date, demand, msrp in raw.get("storm", []):
        line = "Storm Collectibles"
        if "Street Fighter" in sub:
            line = "Street Fighter"
        elif "Mortal Kombat" in sub:
            line = "Mortal Kombat"
        elif "Tekken" in sub:
            line = "Tekken"
        rows.append(F(f"storm-{suf}", name, sub, line, "storm", date, msrp, '1:12', demand, "storm,curated"))

    for suf, name, sub, date, demand, msrp in raw.get("shfiguarts", []):
        rows.append(F(f"shf-{suf}", name, sub, "S.H.Figuarts", "shfiguarts", date, msrp, '6"', demand, "shfiguarts,tamashii,curated"))

    for suf, name, sub, date, demand, msrp in raw.get("threezero", []):
        line = "threezero DLX"
        if "Overwatch" in sub:
            line = "threezero Overwatch"
        elif "Pacific Rim" in sub:
            line = "threezero Pacific Rim"
        elif "RoboCop" in sub or "Aliens" in sub or "Predator" in sub or "Dark Knight" in sub:
            line = "threezero"
        rows.append(F(f"tz-{suf}", name, sub, line, "threezero", date, msrp, '1:12', demand, "threezero,curated"))

    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out
