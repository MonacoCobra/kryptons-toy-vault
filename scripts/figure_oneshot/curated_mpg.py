"""Takara Tomy Transformers MPG (Masterpiece G) densify.

Company takaratomy; line Transformers MPG. Floor 1980; no imageUrl.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("mpg_data.json")


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
        "source": "curated-mpg",
    }


def build_mpg() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []
    for suf, name, sub, date, demand, msrp in raw.get("mpg", []):
        rows.append(
            F(
                f"tt-{suf}",
                name,
                sub,
                "Transformers MPG",
                "takaratomy",
                date,
                msrp,
                '10"',
                demand,
                "transformers,mpg,takaratomy,curated",
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
