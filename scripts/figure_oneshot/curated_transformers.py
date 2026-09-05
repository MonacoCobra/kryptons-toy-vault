"""Hasbro Transformers Masterpiece + Studio Series densify.

Company hasbro; lines Transformers Masterpiece / Transformers Masterpiece Movie /
Transformers Studio Series. Floor 1980; no imageUrl.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("transformers_data.json")


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
        "source": "curated-transformers",
    }


def build_transformers() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []
    for suf, name, sub, date, demand, msrp in raw.get("mp", []):
        rows.append(
            F(
                f"tfmp-{suf}",
                name,
                sub,
                "Transformers Masterpiece",
                "hasbro",
                date,
                msrp,
                '10"',
                demand,
                "transformers,masterpiece,curated",
            )
        )
    for suf, name, sub, date, demand, msrp in raw.get("mpm", []):
        rows.append(
            F(
                f"tfmpm-{suf}",
                name,
                sub,
                "Transformers Masterpiece Movie",
                "hasbro",
                date,
                msrp,
                '10"',
                demand,
                "transformers,masterpiece,mpm,curated",
            )
        )
    for suf, name, sub, date, demand, scale, msrp in raw.get("ss", []):
        rows.append(
            F(
                f"tfss-{suf}",
                name,
                sub,
                "Transformers Studio Series",
                "hasbro",
                date,
                msrp,
                scale,
                demand,
                "transformers,studio-series,curated",
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
