#!/usr/bin/env python3
"""Densify real Blokees Fantastics, DaaLaMode, and Astral Rally rows.

Official store listings only. Blind-box pieces are named from the Blokees
product page and ship without invented photos. Does not stamp Transformers
onto Hatsune Miku, Evangelion, or Astral Rally.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
STATS = ROOT / "src/data/figure-archive/blokees-licensed-densify-stats.json"

JURASSIC_WELCOME = "sf-blokees-jurassic-world-terraventure-ts-welcome-to-jurassic-world"
JURASSIC_CAPTURE = "sf-blokees-jurassic-world-terraventure-ts-dinosaur-capture-operation"


def tags(*extra: str) -> list[str]:
    base = ["archive", "shopify", "blokees", "densify-blokees-licensed"]
    for tag in extra:
        if tag not in base:
            base.append(tag)
    return base


def ensure(row: dict, tag: str) -> None:
    row.setdefault("tags", [])
    if tag not in row["tags"]:
        row["tags"].append(tag)


def figure(
    *,
    id: str,
    name: str,
    subtitle: str,
    line: str,
    kind: str,
    release: str,
    msrp: float,
    scale: str,
    sku: str | None,
    image: str | None,
    set_id: str | None = None,
    role: str | None = None,
) -> dict:
    row = {
        "id": id,
        "name": name,
        "subtitle": subtitle,
        "line": line,
        "company": "blokees",
        "kind": kind,
        "releaseDate": release,
        "msrp": msrp,
        "scale": scale,
        "demand": 1.0,
        "tags": tags(kind, *([f"set-{role}"] if role else [])),
        "source": "blokees-store" if image else "blokees-official",
    }
    if image:
        row["imageUrl"] = image
    if sku:
        row["sku"] = sku
    if set_id and role:
        row["setId"] = set_id
        row["setRole"] = role
    return row


def member(parent: dict, wave: str, name: str, subtitle: str) -> dict:
    slug = "".join(ch if ch.isalnum() else "-" for ch in name.lower())
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")[:48]
    child = figure(
        id=f"blk-m-{wave}-{slug}"[:80],
        name=name,
        subtitle=subtitle,
        line=parent["line"],
        kind=parent["kind"],
        release=parent["releaseDate"],
        msrp=parent["msrp"],
        scale=parent["scale"],
        sku=None,
        image=None,
        set_id=parent["id"],
        role="member",
    )
    child["tags"] = tags(parent["kind"], "set-member", wave)
    return child


# House SKUs and images are the official Shopify variant records.
# https://blokees.com/en-us/collections/miku-fantastics-series
# https://blokees.com/en-us/collections/miku-daalamode-series
SINGLES = [
    figure(
        id="sf-blokees-fantastics-series-miku-with-you-2025",
        name="Hatsune Miku · MIKU WITH YOU 2025",
        subtitle="Blokees Fantastics Series",
        line="Blokees Fantastics",
        kind="figure",
        release="2026-02-26",
        msrp=59.99,
        scale='6.50"',
        sku="73533-2",
        image="https://cdn.shopify.com/s/files/1/0679/6538/6990/files/20260318-151726.webp?v=1773818309",
    ),
    figure(
        id="sf-blokees-fantastics-series-hatsune-miku-vivid-echoes",
        name="Hatsune Miku Vivid Echoes",
        subtitle="Blokees Fantastics Series",
        line="Blokees Fantastics",
        kind="figure",
        release="2025-08-14",
        msrp=39.99,
        scale='6.69"',
        sku="73530-2",
        image="https://cdn.shopify.com/s/files/1/0679/6538/6990/files/01621_9cad700f-6dce-4773-bbb7-faa51bfd7859.webp?v=1755167036",
    ),
    figure(
        id="sf-blokees-fantastics-series-hatsune-miku-official-outfit",
        name="Hatsune Miku Official Outfit",
        subtitle="Blokees Fantastics Series",
        line="Blokees Fantastics",
        kind="figure",
        release="2025-06-11",
        msrp=39.99,
        scale="15cm",
        sku="6972984888179",
        image="https://cdn.shopify.com/s/files/1/0679/6538/6990/files/609faa596d7a39a63682c66d27c30e3e.png?v=1751606237",
    ),
    figure(
        id="sf-blokees-fantastics-series-sakura-miku",
        name="Sakura Miku",
        subtitle="Blokees Fantastics Series",
        line="Blokees Fantastics",
        kind="figure",
        release="2025-06-10",
        msrp=39.99,
        scale='5.9"',
        sku="73507-2",
        image="https://cdn.shopify.com/s/files/1/0679/6538/6990/files/18d37aabbad27e737cbaf93ed7c0b083.png?v=1751606217",
    ),
    figure(
        id="sf-blokees-daalamode-series-sakura-miku",
        name="Sakura Miku",
        subtitle="Blokees DaaLaMode Series",
        line="Blokees DaaLaMode",
        kind="figure",
        release="2026-03-06",
        msrp=39.99,
        scale='5.51"',
        sku="73540-2",
        image="https://cdn.shopify.com/s/files/1/0679/6538/6990/files/3Q9A30332.webp?v=1772788985",
    ),
    figure(
        id="sf-blokees-daalamode-series-hatsune-miku-official-outfit",
        name="Hatsune Miku Official Outfit",
        subtitle="Blokees DaaLaMode Series",
        line="Blokees DaaLaMode",
        kind="figure",
        release="2026-01-13",
        msrp=39.99,
        scale='5.51"',
        sku="73536-2",
        image="https://cdn.shopify.com/s/files/1/0679/6538/6990/files/251.webp?v=1770880463",
    ),
]

# Entry Plug Interior is a second official variant of each Evangelion Fantastics
# pilot (distinct SKU, price, and photo), not a case pack of the plug-suit figure.
ENTRY_PLUGS = [
    figure(
        id="sf-blokees-evangelion-fantastics-rei-entry-plug",
        name="Evangelion Fantastics Series - 01 Rei Ayanami With Entry Plug Interior",
        subtitle="Blokees Fantastics · Entry Plug Interior",
        line="Blokees Fantastics",
        kind="figure",
        release="2026-04-01",
        msrp=79.99,
        scale='6"',
        sku="73572-2",
        image="https://cdn.shopify.com/s/files/1/0679/6538/6990/files/img_v3_02vg_081f6c85-824e-46f4-ac5d-41d402783c4g1.webp?v=1775034100",
    ),
    figure(
        id="sf-blokees-evangelion-fantastics-mari-entry-plug",
        name="Evangelion Fantastics Series - 02 Mari Makinami Illustrious With Entry Plug Interior",
        subtitle="Blokees Fantastics · Entry Plug Interior",
        line="Blokees Fantastics",
        kind="figure",
        release="2026-04-01",
        msrp=79.99,
        scale='6"',
        sku="73573-2",
        image="https://cdn.shopify.com/s/files/1/0679/6538/6990/files/img_v3_02vg_5078ade3-5be6-49e2-9644-25cf345f906g1.webp?v=1775113343",
    ),
    figure(
        id="sf-blokees-evangelion-fantastics-asuka-entry-plug",
        name="Evangelion Fantastics Series - 03 Asuka Shikinami Langley With Entry Plug Interior",
        subtitle="Blokees Fantastics · Entry Plug Interior",
        line="Blokees Fantastics",
        kind="figure",
        release="2026-04-02",
        msrp=79.99,
        scale='6"',
        sku="73571-2",
        image="https://cdn.shopify.com/s/files/1/0679/6538/6990/files/img_v3_02vg_2e768586-d89f-4d6d-98a4-4f9e0dfe049g1.webp?v=1775194962",
    ),
]

PLUG_SUIT_UPDATES = {
    "sf-blokees-evangelion-fantastics-series-rei-ayanami": {
        "sku": "73562-2",
        "msrp": 39.99,
        "imageUrl": "https://cdn.shopify.com/s/files/1/0679/6538/6990/files/img_v3_02vg_d3af5306-31ca-4e0b-8040-52e317581f0g_1.webp?v=1775034100",
        "subtitle": "Blokees Fantastics · Plug Suit",
    },
    "sf-blokees-evangelion-fantastics-series-mari-makinami-illustrious": {
        "sku": "73563-2",
        "msrp": 39.99,
        "imageUrl": "https://cdn.shopify.com/s/files/1/0679/6538/6990/files/img_v3_02vg_26cc9540-a4e7-4459-b733-dd2aabeea6cg1.webp?v=1775113343",
        "subtitle": "Blokees Fantastics · Plug Suit",
    },
    "sf-blokees-evangelion-fantastics-series-asuka-shikinami-langley": {
        "sku": "73561-2",
        "msrp": 39.99,
        "imageUrl": "https://cdn.shopify.com/s/files/1/0679/6538/6990/files/img_v3_02vg_834cca1e-ade1-4193-97e2-f6a94396a4dg1.webp?v=1775194962",
        "subtitle": "Blokees Fantastics · Plug Suit",
    },
}


def new_sets() -> list[tuple[dict, str, list[tuple[str, str]]]]:
    sonata = figure(
        id="sf-blokees-daalamode-series-hatsune-miku-sonata-prologue",
        name="Hatsune Miku 01 Sonata Prologue",
        subtitle="Blokees DaaLaMode Series",
        line="Blokees DaaLaMode",
        kind="figure",
        release="2026-03-04",
        msrp=19.99,
        scale='5.51"',
        sku="73538-2",
        image="https://cdn.shopify.com/s/files/1/0679/6538/6990/files/Mask_group_dbd60c15-e589-4a57-a8fa-21eaa00f006e.webp?v=1773977385",
        set_id="sf-blokees-daalamode-series-hatsune-miku-sonata-prologue",
        role="parent",
    )
    mwy = figure(
        id="sf-blokees-hatsune-miku-daalamode-q-series-miku-with-you",
        name="Hatsune Miku DaaLaMode Q Series - MIKU WITH YOU",
        subtitle="Blokees DaaLaMode Q Series",
        line="Blokees DaaLaMode",
        kind="figure",
        release="2026-02-08",
        msrp=14.99,
        scale='3.94"',
        sku="75700-2",
        image="https://cdn.shopify.com/s/files/1/0679/6538/6990/files/Mask_group_-_2026-03-10T143755.599.webp?v=1773125487",
        set_id="sf-blokees-hatsune-miku-daalamode-q-series-miku-with-you",
        role="parent",
    )
    moji = figure(
        id="sf-blokees-daalamode-mojipod-diverse-music-festival",
        name="MOJIPOD Hatsune Miku Diverse Music Festival",
        subtitle="Blokees DaaLaMode Series",
        line="Blokees DaaLaMode",
        kind="figure",
        release="2026-08-27",
        msrp=8.99,
        scale='1.97"',
        sku="75400-2",
        image="https://cdn.shopify.com/s/files/1/0679/6538/6990/files/Maskgroup-7_6f1291b5-ac35-4775-805e-2e88c76238e4.webp?v=1787888968",
        set_id="sf-blokees-daalamode-mojipod-diverse-music-festival",
        role="parent",
    )
    sonata_sub = "DaaLaMode · Sonata Prologue"
    mwy_sub = "DaaLaMode Q · MIKU WITH YOU"
    moji_sub = "DaaLaMode · Diverse Music Festival"
    return [
        (
            sonata,
            "mkson",
            [
                ("Stellar Sonata", f"{sonata_sub} · 1/6"),
                ("Pearl Lullaby", f"{sonata_sub} · 5/36"),
                ("Shimmering Waltz", f"{sonata_sub} · 1/6"),
                ("Diamond Minuet", f"{sonata_sub} · 1/6"),
                ("Velvet Serenade", f"{sonata_sub} · 1/6"),
                ("Heavy Metal", f"{sonata_sub} · 1/6"),
                ("Prelude to the Dance (Chase)", f"{sonata_sub} · 1/36"),
            ],
        ),
        (
            mwy,
            "mkmwy",
            [(f"MIKU WITH YOU {year}", mwy_sub) for year in (2017, 2018, 2019, 2020, 2021, 2024)],
        ),
        (
            moji,
            "mkmoji",
            [
                ("Director", f"{moji_sub} · 5/36"),
                ("Fan", f"{moji_sub} · 1/6"),
                ("Photographer", f"{moji_sub} · 1/6"),
                ("Makeup Artist", f"{moji_sub} · 1/6"),
                ("Security Guard", f"{moji_sub} · 1/6"),
                # Official FAQ names Janitor as the seventh role. The lineup
                # heading for the remaining 1/6 slot did not render a name.
                ("Janitor", f"{moji_sub} · 1/6"),
                ("Pop Star (Chase)", f"{moji_sub} · 1/36"),
            ],
        ),
    ]


EVA_MEMBERS = [
    ("Rei", "Evangelion DaaLaMode Q · Miracle Link · 11/72"),
    ("Asuka", "Evangelion DaaLaMode Q · Miracle Link · 11/72"),
    ("Mari", "Evangelion DaaLaMode Q · Miracle Link · 1/6"),
    ("Kaworu", "Evangelion DaaLaMode Q · Miracle Link · 1/6"),
    ("Shinji", "Evangelion DaaLaMode Q · Miracle Link · 1/6"),
    ("Misato", "Evangelion DaaLaMode Q · Miracle Link · 1/6"),
    ("Rei (Chase)", "Evangelion DaaLaMode Q · Miracle Link · 1/72"),
    ("Asuka (Chase)", "Evangelion DaaLaMode Q · Miracle Link · 1/72"),
]

ASTRAL_MEMBERS = [
    ("KYRR: Fornax", "Astral Rally 01 The First Light · 2/36"),
    ("KYRR: Sagitta", "Astral Rally 01 The First Light · 1/12"),
    ("KYRR: Lyra", "Astral Rally 01 The First Light · 1/12"),
    ("ZORN: Hercules", "Astral Rally 01 The First Light · 2/36"),
    ("ZORN: Perseus", "Astral Rally 01 The First Light · 1/12"),
    ("ZORN: Andromeda", "Astral Rally 01 The First Light · 1/12"),
    ("TARG: Lupus", "Astral Rally 01 The First Light · 2/36"),
    ("TARG: Canes Venatici", "Astral Rally 01 The First Light · 1/12"),
    ("TARG: Vulpecula", "Astral Rally 01 The First Light · 1/12"),
    ("MAV: Astraea", "Astral Rally 01 The First Light"),
    ("MAV: Iris", "Astral Rally 01 The First Light"),
    ("MAV: Hebe", "Astral Rally 01 The First Light"),
    ("KYRR: Fornax (Chase)", "Astral Rally 01 The First Light · glitter translucent · 1/36"),
    ("TARG: Lupus (Chase)", "Astral Rally 01 The First Light · glitter translucent · 1/36"),
    ("ZORN: Hercules (Chase)", "Astral Rally 01 The First Light · faux metal · 3/144"),
    ("ZORN: Hercules (Radiant Chase)", "Astral Rally 01 The First Light · imitation precious metal · 1/144"),
]

# Primary sku plus listing aliases. Official Outfit Fantastics uses the
# Modelverse GTIN-13 (checksum valid, title matches 公式服). House codes stay aliases.
ALIAS_CODES = {
    "sf-blokees-fantastics-series-miku-with-you-2025": ["73533-2"],
    "sf-blokees-fantastics-series-hatsune-miku-vivid-echoes": ["73530-2"],
    "sf-blokees-fantastics-series-hatsune-miku-official-outfit": ["73502-2", "6972984888179"],
    "sf-blokees-fantastics-series-sakura-miku": ["73507-2"],
    "sf-blokees-daalamode-series-sakura-miku": ["73540-2"],
    "sf-blokees-daalamode-series-hatsune-miku-official-outfit": ["73536-2"],
    "sf-blokees-daalamode-series-hatsune-miku-sonata-prologue": ["73538-2", "73538-3"],
    "sf-blokees-hatsune-miku-daalamode-q-series-miku-with-you": ["75700-2", "75700-3"],
    "sf-blokees-daalamode-mojipod-diverse-music-festival": ["75400-2", "75400-3"],
    "sf-blokees-evangelion-daalamode-q-series-miracle-link": ["75630-2", "75630-3"],
    "sf-blokees-astral-rally-defender-version-the-first-light": ["75932-3"],
    "sf-blokees-evangelion-fantastics-series-rei-ayanami": ["73562-2"],
    "sf-blokees-evangelion-fantastics-series-mari-makinami-illustrious": ["73563-2"],
    "sf-blokees-evangelion-fantastics-series-asuka-shikinami-langley": ["73561-2"],
    "sf-blokees-evangelion-fantastics-rei-entry-plug": ["73572-2"],
    "sf-blokees-evangelion-fantastics-mari-entry-plug": ["73573-2"],
    "sf-blokees-evangelion-fantastics-asuka-entry-plug": ["73571-2"],
}

# These house SKUs were filed on Jurassic World sets. Official store variants
# belong to the Miku products above. 73531-2 is DaaVibe Terrace Party, which
# this pass does not add.
DETACH = {
    "73531-2": "DaaVibe 01 Terrace Party is a real Blokees Miku product and was not requested. Removed from the Jurassic World capture alias so it no longer resolves to that set.",
    "73652-3": "Official store SKU for The Powerpuff Girls daadoos Nest Series 01 Operation Snow Fluffy. Removed from the Jurassic World capture alias. The set itself was not added.",
    "75871-3": "Official store SKU for The Powerpuff Girls MOKOO Series 01 Cute Beats. Removed from the Jurassic World capture alias. The set itself was not added.",
}


def upsert(rows: list[dict], by_id: dict[str, dict], row: dict, added: list[str], updated: list[str]) -> dict:
    current = by_id.get(row["id"])
    if current is None:
        rows.append(row)
        by_id[row["id"]] = row
        added.append(row["id"])
        return row
    for key, value in row.items():
        if key == "tags":
            for tag in value:
                ensure(current, tag)
            continue
        current[key] = value
    updated.append(row["id"])
    return current


def attach(doc: dict, figure_id: str, codes: list[str], moved: list[dict]) -> None:
    by = doc.setdefault("aliasesByFigureId", {})
    to = doc.setdefault("aliasToFigureId", {})
    keep = list(by.get(figure_id) or [])
    for code in codes:
        prev = to.get(code)
        if prev and prev != figure_id:
            by[prev] = [item for item in (by.get(prev) or []) if item != code]
            moved.append({"code": code, "from": prev, "to": figure_id})
        if code not in keep:
            keep.append(code)
        to[code] = figure_id
    by[figure_id] = keep


def detach(doc: dict, code: str) -> str | None:
    by = doc.setdefault("aliasesByFigureId", {})
    to = doc.setdefault("aliasToFigureId", {})
    prev = to.pop(code, None)
    if prev:
        by[prev] = [item for item in (by.get(prev) or []) if item != code]
    return prev


def main() -> None:
    rows = json.loads(ONESHOT.read_text())
    by_id = {row["id"]: row for row in rows}
    added: list[str] = []
    updated: list[str] = []

    for row_id, patch in PLUG_SUIT_UPDATES.items():
        row = by_id[row_id]
        row["line"] = "Blokees Fantastics"
        row["kind"] = "figure"
        row["sku"] = patch["sku"]
        row["msrp"] = patch["msrp"]
        row["subtitle"] = patch["subtitle"]
        row["imageUrl"] = patch["imageUrl"]
        ensure(row, "densify-blokees-licensed")
        ensure(row, "figure")
        updated.append(row_id)

    for row in [*SINGLES, *ENTRY_PLUGS]:
        upsert(rows, by_id, row, added, updated)

    for parent, wave, pieces in new_sets():
        parent = upsert(rows, by_id, parent, added, updated)
        for name, subtitle in pieces:
            upsert(rows, by_id, member(parent, wave, name, subtitle), added, updated)

    miracle = by_id["sf-blokees-evangelion-daalamode-q-series-miracle-link"]
    miracle["line"] = "Blokees DaaLaMode"
    miracle["subtitle"] = "Blokees DaaLaMode Q Series"
    miracle["kind"] = "figure"
    miracle["msrp"] = 14.99
    miracle["scale"] = '3.94"'
    miracle["sku"] = "75630-2"
    miracle["setId"] = miracle["id"]
    miracle["setRole"] = "parent"
    ensure(miracle, "densify-blokees-licensed")
    ensure(miracle, "figure")
    ensure(miracle, "set-parent")
    updated.append(miracle["id"])
    for name, subtitle in EVA_MEMBERS:
        upsert(rows, by_id, member(miracle, "evaml", name, subtitle), added, updated)

    astral = by_id["sf-blokees-astral-rally-defender-version-the-first-light"]
    astral["line"] = "Blokees Defender Version"
    astral["subtitle"] = "Astral Rally Defender Version 01 The First Light"
    astral["kind"] = "kit"
    astral["msrp"] = 35.88
    astral["sku"] = "75932-3"
    astral["setId"] = astral["id"]
    astral["setRole"] = "parent"
    ensure(astral, "densify-blokees-licensed")
    ensure(astral, "kit")
    ensure(astral, "set-parent")
    updated.append(astral["id"])
    for name, subtitle in ASTRAL_MEMBERS:
        upsert(rows, by_id, member(astral, "ar01", name, subtitle), added, updated)

    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate figure ids")
    banned = []
    for row in rows:
        if "densify-blokees-licensed" not in (row.get("tags") or []):
            continue
        blob = " ".join(
            [
                row.get("name") or "",
                row.get("subtitle") or "",
                row.get("line") or "",
                " ".join(row.get("tags") or []),
            ]
        ).lower()
        if "transformers" in blob:
            banned.append(row["id"])
    if banned:
        raise SystemExit(f"transformers leaked onto licensed rows: {banned}")

    doc = json.loads(ALIASES.read_text())
    moved: list[dict] = []
    detached: list[dict] = []
    for code, reason in DETACH.items():
        prev = detach(doc, code)
        if prev:
            detached.append({"code": code, "from": prev, "reason": reason})
    for figure_id, codes in ALIAS_CODES.items():
        if figure_id not in by_id:
            raise SystemExit(f"alias target missing: {figure_id}")
        attach(doc, figure_id, codes, moved)

    ONESHOT.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    ALIASES.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

    def sample(prefix_ids: list[str]) -> list[dict]:
        out = []
        for row_id in prefix_ids:
            row = by_id[row_id]
            out.append({"id": row["id"], "name": row["name"], "sku": row.get("sku"), "line": row["line"]})
        return out

    stats = {
        "added": len(added),
        "updatedExisting": sorted(set(updated) - set(added)),
        "addedIds": added,
        "mikuFantastics": sample([row["id"] for row in SINGLES if row["line"] == "Blokees Fantastics"]),
        "evaFantasticsAlreadyPresent": list(PLUG_SUIT_UPDATES),
        "evaFantasticsEntryPlugAdded": [row["id"] for row in ENTRY_PLUGS],
        "daalamodeSingles": ["sf-blokees-daalamode-series-sakura-miku", "sf-blokees-daalamode-series-hatsune-miku-official-outfit"],
        "sets": {
            "sonataPrologue": {"parent": "73538-2", "members": 7},
            "mikuWithYou": {"parent": "75700-2", "members": 6},
            "mojipodDiverseMusicFestival": {"parent": "75400-2", "members": 7},
            "evangelionMiracleLink": {"parent": "75630-2", "members": 8, "alreadyPresentParent": True},
            "astralRally": {"parent": "75932-3", "members": 16, "alreadyPresentParent": True, "line": "Blokees Defender Version"},
        },
        "aliasRetargets": moved,
        "aliasDetached": detached,
        "notAdded": [
            {
                "name": "Hatsune Miku DaaVibe 01 Terrace Party",
                "skus": ["73531-2", "73531-3"],
                "reason": "Real Blokees product, separate from DaaLaMode. Not in this request.",
            }
        ],
        "gtinLeftOff": [
            {
                "product": "Astral Rally 01 The First Light",
                "codes": ["4570164011397", "4570164011380"],
                "reason": "Two different valid JANs are cited for the box. House sku 75932-3 is the only code joined on the official store.",
            },
            {
                "product": "Evangelion DaaLaMode Q Miracle Link",
                "codes": ["4570164011601", "6978165694454"],
                "reason": "Retailer JANs disagree on whether the code is the case or a set of 6. House skus 75630-2 and 75630-3 are stored instead.",
            },
            {
                "product": "Hatsune Miku DaaLaMode Q MIKU WITH YOU",
                "codes": ["0889698883900"],
                "reason": "A retailer URL includes this barcode. It was not confirmed against the official single versus whole-set variant.",
            },
        ],
    }
    STATS.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"added": len(added), "updated": len(set(updated)), "rows": len(rows), "moved": len(moved), "detached": len(detached)}, indent=2))


if __name__ == "__main__":
    main()
