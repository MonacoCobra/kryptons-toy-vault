"""Playmates Toys AF densify — TMNT classic + modern + other AF 1980+.

Company playmates. Floor 1980; no imageUrl; skip plush.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("playmates_data.json")


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
        "source": "curated-playmates",
    }


def build_playmates() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []
    for suf, name, sub, date, demand, msrp in raw.get("classicTmnt", []):
        rows.append(
            F(
                f"pm-tmnt-{suf}",
                name,
                sub,
                "Teenage Mutant Ninja Turtles",
                "playmates",
                date,
                msrp,
                '5"',
                demand,
                "tmnt,playmates,classic,curated",
            )
        )
    for suf, name, sub, date, demand, msrp in raw.get("modernTmnt", []):
        line = "Teenage Mutant Ninja Turtles"
        if "Mutant Mayhem" in sub:
            line = "TMNT Mutant Mayhem"
        elif "Tales of the TMNT" in sub:
            line = "Tales of the TMNT"
        elif "Classic Collection" in sub:
            line = "TMNT Classic Collection"
        rows.append(
            F(
                f"pm-tmnt-{suf}",
                name,
                sub,
                line,
                "playmates",
                date,
                msrp,
                '5"',
                demand,
                "tmnt,playmates,modern,curated",
            )
        )
    for row in raw.get("other", []):
        suf, name, sub, date, demand, msrp, scale = row
        line = sub if sub in ("Exo-Squad", "WWF Superstars") else sub
        if "Exo-Squad" in sub or name in ("J.T. Marsh", "Marsala", "Nara Burns", "Kaz Takagi", "Alec DeLeon", "Wolf Bronski", "Phoebe", "Typhonus", "Draconis", "Shiva") or "E-Frame" in name:
            line = "Exo-Squad"
        elif "WWF" in sub:
            line = "WWF Superstars"
        elif "Godzilla" in sub or name in ("Godzilla", "Mechagodzilla", "Rodan", "Mothra"):
            line = "Godzilla"
        elif "Voltron" in name or "Voltron" in sub:
            line = "Voltron"
        else:
            line = sub
        rows.append(
            F(
                f"pm-{suf}",
                name,
                sub,
                line,
                "playmates",
                date,
                msrp,
                scale,
                demand,
                "playmates,curated",
            )
        )
    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out
