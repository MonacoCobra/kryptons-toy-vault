"""MAFEX + Mezco One:12 densify from curated/scraped real releases.

Data: mafex_mezco_data.json (MAFEX catalog + One:12 tracker + extras).
No AI art / no imageUrl. Floor 1980.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("mafex_mezco_data.json")


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
        "source": "curated-mafex-mezco",
    }


def build_mafex_mezco() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []
    for r in raw.get("mafex", []):
        rows.append(
            F(r["id"], r["name"], r["subtitle"], "MAFEX", "mafex", r["releaseDate"], 94.99, '6"', r["demand"], "mafex,densify")
        )
    for r in raw.get("mezcoTracker", []):
        rows.append(
            F(r["id"], r["name"], r["subtitle"], "One:12 Collective", "mezco", r["releaseDate"], 112.0, '6"', r["demand"], "mezco,one12,tracker")
        )
    for r in raw.get("mezcoExtra", []):
        rows.append(
            F(r["id"], r["name"], r["subtitle"], "One:12 Collective", "mezco", r["releaseDate"], 115.0, '6"', r["demand"], "mezco,one12,densify")
        )
    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out
