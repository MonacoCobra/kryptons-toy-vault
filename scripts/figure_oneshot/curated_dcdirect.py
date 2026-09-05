"""DC Direct Icons + classic DC Direct AF densify (1998–2012 + Icons).

Company dcdirect. Icons use line "DC Direct Icons". Classic AF use collector
series line names or "DC Direct". Floor 1980; no imageUrl.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("dcdirect_data.json")


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
        "source": "curated-dcdirect",
    }


def _line_for_series(series: str) -> str:
    s = series.lower()
    mapping = [
        ("hush", "DC Direct Hush"),
        ("kingdom come", "DC Direct Kingdom Come"),
        ("dark knight returns", "DC Direct Dark Knight Returns"),
        ("blackest night", "DC Direct Blackest Night"),
        ("brightest day", "DC Direct Brightest Day"),
        ("elseworld", "DC Direct Elseworlds"),
        ("red son", "DC Direct Elseworlds"),
        ("identity crisis", "DC Direct Identity Crisis"),
        ("public enemies", "DC Direct Superman/Batman"),
        ("superman/batman", "DC Direct Superman/Batman"),
        ("superman batman", "DC Direct Superman/Batman"),
        ("with a vengeance", "DC Direct Superman/Batman"),
        ("alex ross justice", "DC Direct Justice"),
        ("justice series", "DC Direct Justice"),
        ("new frontier", "DC Direct New Frontier"),
        ("crisis", "DC Direct Crisis"),
        ("infinite crisis", "DC Direct Infinite Crisis"),
        ("teen titans", "DC Direct Teen Titans"),
        ("first appearance", "DC Direct First Appearance"),
        ("arkham", "DC Direct Arkham"),
        ("flashpoint", "DC Direct Flashpoint"),
        ("watchmen", "DC Direct Watchmen"),
        ("new 52", "DC Direct New 52"),
        ("return of superman", "DC Direct Superman"),
        ("silver age", "DC Direct Silver Age"),
        ("super friends", "DC Direct Super Friends"),
        ("jla ", "DC Direct JLA"),
        ("jli ", "DC Direct JLI"),
        ("jsa ", "DC Direct JSA"),
        ("green lantern", "DC Direct Green Lantern"),
        ("wonder woman series", "DC Direct Wonder Woman"),
        ("batman reborn", "DC Direct Batman"),
        ("batman inc", "DC Direct Batman"),
        ("return of bruce", "DC Direct Batman"),
        ("sandman", "DC Direct Vertigo"),
        ("preacher", "DC Direct Vertigo"),
        ("transmetropolitan", "DC Direct Vertigo"),
        ("legion", "DC Direct Legion"),
        ("japanese import", "DC Direct"),
        ("kia asamiya", "DC Direct"),
        ("hard traveling", "DC Direct"),
        ("new teen titans", "DC Direct Teen Titans"),
        ("shazam", "DC Direct Shazam"),
        ("52 series", "DC Direct 52"),
        ("re-activated", "DC Direct Re-Activated"),
        ("all star", "DC Direct All Star"),
        ("classic icons", "DC Direct"),
        ("new krypton", "DC Direct Superman"),
        ("secret files", "DC Direct"),
        ("history of the dc", "DC Direct"),
        ("killing joke", "DC Direct Batman"),
        ("long halloween", "DC Direct Batman"),
        ("origins", "DC Direct"),
        ("showcase", "DC Direct"),
        ("boxed set", "DC Direct"),
        ("box set", "DC Direct"),
        ("collector set", "DC Direct"),
    ]
    for key, line in mapping:
        if key in s:
            return line
    return "DC Direct"


def build_dcdirect() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []
    for suf, name, sub, date, demand in raw.get("icons", []):
        msrp = (
            44.99
            if ("2-Pack" in sub or "7-Pack" in sub or "Darkseid" in name)
            else (14.99 if "Accessory" in name else 29.99)
        )
        scale = (
            '6.75"'
            if ("Rebirth" in sub and ("#27" in sub or "#28" in sub or "7-Pack" in sub))
            else '6"'
        )
        rows.append(
            F(
                f"dcdicons-{suf}",
                name,
                sub,
                "DC Direct Icons",
                "dcdirect",
                date,
                msrp,
                scale,
                demand,
                "dc,dcdirect,icons,curated",
            )
        )
    for suf, name, series, date, demand in raw.get("dcd", []):
        line = _line_for_series(series)
        msrp = (
            34.99
            if (
                "Boxed" in series
                or "Box Set" in series
                or "Collector Set" in series
                or "&" in name
            )
            else 19.99
        )
        if "Deluxe" in series:
            msrp = 29.99
        scale = (
            '7"'
            if (
                "Deluxe" in series
                or "Nekron" in name
                or "Anti-Monitor" in name
                or "Doomsday" in name
                or "Darkseid" in name
            )
            else '6.5"'
        )
        rows.append(
            F(
                f"dcdclassic-{suf}",
                name,
                series,
                line,
                "dcdirect",
                date,
                msrp,
                scale,
                demand,
                "dc,dcdirect,classic,curated",
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
