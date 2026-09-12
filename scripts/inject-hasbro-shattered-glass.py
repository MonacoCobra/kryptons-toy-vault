#!/usr/bin/env python3
"""Inject Hasbro Generations Shattered Glass Collection (+ Selects 2-pack).

Sources (verified 2026-09):
  - TFW2005 Nevermore UPC/EAN list (product codes + EAN-13)
  - actionfigure411 / icollecteverything barcodes + MSRP
  - Hasbro Pulse / ToyArena / CmdStore Shopify CDN product images
  - Starscream 2026 reissue shares GTIN 5010993897384 with original → one row

Policy: GTIN primary sku; listing codes (F####, WFC-GS17) as aliases;
empty over wrong; company=hasbro; line=Shattered Glass Collection
(or Generations Selects for the 2-pack). Does NOT Build Publish Live.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/workspace/collection-app")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_identity import clean_code, gtin_checksum_ok, is_gtin  # noqa: E402

ARCHIVE = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
SKU_MAP = ROOT / "src/data/figure-sku-map.json"
URLS = ROOT / "src/data/figure-image-urls.json"
STATS = ROOT / "src/data/figure-archive/hasbro-sg-inject-stats.json"

COMPANY = "hasbro"
LINE_SG = "Shattered Glass Collection"
LINE_SEL = "Generations Selects"
SRC = "inject-hasbro-shattered-glass"

# id, name, subtitle, gtin, product_code, aliases, msrp, scale, release, image, demand, line
CATALOG: list[dict[str, Any]] = [
    {
        "id": "hasbro-sg-selects-optimus-ratchet",
        "name": "Optimus Prime & Ratchet",
        "subtitle": "Shattered Glass 2-pack · WFC-GS17",
        "gtin": "5010993800612",
        "code": "WFC-GS17",
        "extra_aliases": ["WFCGS17", "B08R7ZQM1X"],
        "msrp": 49.99,
        "scale": "Voyager + Deluxe",
        "release": "2020-12-01",
        "image": "https://cdn.shopify.com/s/files/1/2637/6278/products/5010993800612a.jpg?v=1611871375",
        "demand": 1.55,
        "line": LINE_SEL,
        "tags_extra": ["selects", "2-pack", "wfc"],
    },
    {
        "id": "hasbro-sg-blurr",
        "name": "Blurr",
        "subtitle": "Deluxe · Pulse exclusive · with IDW comic",
        "gtin": "5010993867042",
        "code": "F2705",
        "extra_aliases": [],
        "msrp": 29.99,
        "scale": "Deluxe",
        "release": "2021-07-01",
        "image": "https://cdn.shopify.com/s/files/1/0169/6995/7440/products/F2705_PROD_RENDER_TRA_GEN_BLURR_BOT_MODE_Online_2000SQ.jpg?v=1617901036",
        "demand": 1.45,
        "line": LINE_SG,
    },
    {
        "id": "hasbro-sg-goldbug",
        "name": "Goldbug",
        "subtitle": "Deluxe · Pulse exclusive · with IDW comic",
        "gtin": "5010993875832",
        "code": "F2704",
        "extra_aliases": ["B09R3LNQ2Q"],
        "msrp": 29.99,
        "scale": "Deluxe",
        "release": "2021-07-01",
        "image": "https://cdn.shopify.com/s/files/1/2637/6278/files/5010993875832f.jpg?v=1696381746",
        "demand": 1.5,
        "line": LINE_SG,
    },
    {
        "id": "hasbro-sg-megatron",
        "name": "Megatron",
        "subtitle": "Voyager · Pulse exclusive · with IDW comic",
        "gtin": "5010993874675",
        "code": "F2912",
        "extra_aliases": [],
        "msrp": 38.99,
        "scale": "Voyager",
        "release": "2021-08-01",
        "image": "https://cdn.shopify.com/s/files/1/0169/6995/7440/products/F2912_PROD_TRA_GEN_MEGATRON_0003_Online_2000SQ.jpg?v=1619533371",
        "demand": 1.65,
        "line": LINE_SG,
    },
    {
        "id": "hasbro-sg-starscream",
        "name": "Starscream",
        "subtitle": "Voyager · Pulse exclusive · with IDW comic",
        "gtin": "5010993897384",
        "code": "F2911",
        # 2026 reissue listing codes — same GTIN, not a second row
        "extra_aliases": ["F29115L01", "F29115L00", "F29115C00"],
        "msrp": 38.99,
        "scale": "Voyager",
        "release": "2021-08-01",
        "image": "https://cdn.shopify.com/s/files/1/0216/0984/0740/files/transformers-generations-voyager-class-shattered-glass-starscream-5010993897384.jpg?v=1788473789",
        "demand": 1.7,
        "line": LINE_SG,
        "notes": "2026 Pulse/EE/BBTS reissue shares this GTIN — no distinct reissue row",
    },
    {
        "id": "hasbro-sg-jetfire",
        "name": "Jetfire",
        "subtitle": "Commander · Pulse exclusive · with IDW comic",
        "gtin": "5010993900657",
        "code": "F3003",
        "extra_aliases": [],
        "msrp": 91.99,
        "scale": "Commander",
        "release": "2022-01-01",
        "image": "https://cdn.shopify.com/s/files/1/2637/6278/products/5010993900657a.jpg?v=1635891188",
        "demand": 1.6,
        "line": LINE_SG,
    },
    {
        "id": "hasbro-sg-blaster-rewind",
        "name": "Blaster & Rewind",
        "subtitle": "Voyager · Pulse exclusive · with IDW comic",
        "gtin": "5010994135690",
        "code": "F3926",
        "extra_aliases": ["B09H1LS1SF"],
        "msrp": 38.99,
        "scale": "Voyager",
        "release": "2022-11-01",
        "image": "https://cdn.shopify.com/s/files/1/0169/6995/7440/products/F3926_PROD_TRA_GEN_SG_VOY_BLASTER_0004_Online_2000SQ.jpg?v=1654000139",
        "demand": 1.55,
        "line": LINE_SG,
        "tags_extra": ["2-pack"],
    },
    {
        "id": "hasbro-sg-ultra-magnus",
        "name": "Ultra Magnus",
        "subtitle": "Leader · Pulse exclusive · Delta Magnus / Magna Convoy heads",
        "gtin": "5010994145729",
        "code": "F4118",
        "extra_aliases": [],
        "msrp": 62.99,
        "scale": "Leader",
        "release": "2022-08-01",
        "image": "https://cdn.shopify.com/s/files/1/2637/6278/products/5010994145729a.webp?v=1662755077",
        "demand": 1.55,
        "line": LINE_SG,
    },
    {
        "id": "hasbro-sg-flamewar-fireglide",
        "name": "Flamewar & Fireglide",
        "subtitle": "Deluxe · Pulse exclusive · with IDW comic",
        "gtin": "5010994183110",
        "code": "F6281",
        "extra_aliases": ["B0BZNC5NML"],
        "msrp": 41.99,
        "scale": "Deluxe",
        "release": "2022-11-01",
        "image": "https://cdn.shopify.com/s/files/1/2637/6278/products/5010994183110a.webp?v=1668132043",
        "demand": 1.5,
        "line": LINE_SG,
        "tags_extra": ["2-pack"],
    },
    {
        "id": "hasbro-sg-slicer-exo-suit",
        "name": "Slicer & Exo-Suit",
        "subtitle": "Deluxe · Pulse exclusive · with IDW comic",
        "gtin": "5010994171780",
        "code": "F6280",
        "extra_aliases": [],
        "msrp": 48.99,
        "scale": "Deluxe",
        "release": "2022-10-01",
        "image": "https://cdn.shopify.com/s/files/1/2637/6278/products/5010994171780a.webp?v=1668129896",
        "demand": 1.5,
        "line": LINE_SG,
        "tags_extra": ["2-pack"],
    },
    {
        "id": "hasbro-sg-soundwave",
        "name": "Soundwave with Ravage & Laserbeak",
        "subtitle": "Voyager · Pulse exclusive · with IDW comic",
        "gtin": "5010994131715",
        "code": "F3921",
        "extra_aliases": [],
        "msrp": 62.99,
        "scale": "Voyager",
        "release": "2022-12-01",
        "image": "https://cdn.shopify.com/s/files/1/2637/6278/products/5010994131715h.webp?v=1670459327",
        "demand": 1.65,
        "line": LINE_SG,
        "tags_extra": ["multipack"],
    },
    {
        "id": "hasbro-sg-grimlock",
        "name": "Grimlock",
        "subtitle": "Leader · Pulse exclusive",
        "gtin": "5010996134653",
        "code": "F7812",
        "extra_aliases": [],
        "msrp": 54.99,
        "scale": "Leader",
        "release": "2023-05-01",
        "image": "https://cdn.shopify.com/s/files/1/2637/6278/files/5010996134653a.webp?v=1689031096",
        "demand": 1.6,
        "line": LINE_SG,
    },
    {
        "id": "hasbro-sg-rodimus-sideswipe-whisper",
        "name": "Rodimus, Sideswipe & Whisper",
        "subtitle": "Voyager + Deluxe · Pulse exclusive",
        "gtin": "5010996138880",
        "code": "F7817",
        "extra_aliases": [],
        "msrp": 54.99,
        "scale": "Voyager + Deluxe",
        "release": "2023-07-01",
        "image": "https://cdn.shopify.com/s/files/1/2637/6278/files/5010996138880a.webp?v=1696460981",
        "demand": 1.55,
        "line": LINE_SG,
        "tags_extra": ["multipack", "3-pack"],
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def ensure_alias_doc(doc: dict) -> dict:
    doc.setdefault("version", 1)
    doc.setdefault("policy", "gtin-canonical")
    doc.setdefault("aliasesByFigureId", {})
    doc.setdefault("aliasToFigureId", {})
    doc.setdefault("collapsed", [])
    doc.setdefault("flagged", [])
    return doc


def add_aliases(doc: dict, figure_id: str, codes: list[str]) -> int:
    doc = ensure_alias_doc(doc)
    by = doc["aliasesByFigureId"]
    to = doc["aliasToFigureId"]
    cur = list(by.get(figure_id) or [])
    added = 0
    for c in codes:
        c2 = clean_code(c)
        if not c2:
            continue
        if c2.upper().startswith("F???") or "skip" in c2.lower():
            continue
        if c2 not in cur:
            cur.append(c2)
            added += 1
        to[c2] = figure_id
        to[c2.upper()] = figure_id
    if cur:
        by[figure_id] = cur
    return added


def make_row(entry: dict[str, Any]) -> dict[str, Any]:
    gtin = entry["gtin"]
    if not is_gtin(gtin) or not gtin_checksum_ok(gtin):
        raise ValueError(f"bad gtin for {entry['id']}: {gtin}")
    tags = [
        "transformers",
        "shattered-glass",
        "hasbro",
        "pulse-exclusive",
        "curated",
        "inject-hasbro-sg",
        "generations",
    ]
    if entry["line"] == LINE_SEL:
        tags = [t for t in tags if t != "pulse-exclusive"]
        tags += ["selects", "retail-exclusive"]
    for t in entry.get("tags_extra") or []:
        if t not in tags:
            tags.append(t)
    return {
        "id": entry["id"],
        "name": entry["name"],
        "subtitle": entry["subtitle"],
        "line": entry["line"],
        "company": COMPANY,
        "kind": "figure",
        "releaseDate": entry["release"],
        "msrp": float(entry["msrp"]),
        "scale": entry["scale"],
        "demand": float(entry["demand"]),
        "tags": tags,
        "source": SRC,
        "sku": gtin,
        "imageUrl": entry["image"],
    }


def main() -> None:
    rows: list[dict] = load_json(ARCHIVE)
    by_id = {r["id"]: i for i, r in enumerate(rows)}
    aliases = ensure_alias_doc(load_json(ALIASES) if ALIASES.exists() else {})
    sku_map: dict[str, str] = load_json(SKU_MAP) if SKU_MAP.exists() else {}
    urls: dict[str, str] = load_json(URLS) if URLS.exists() else {}

    added = updated = 0
    alias_n = 0
    samples: list[dict] = []
    skipped_reissue = {
        "starscream_reissue": "Shares GTIN 5010993897384 with original; aliases F29115L01/L00/C00 only"
    }

    for entry in CATALOG:
        rid = entry["id"]
        row = make_row(entry)
        codes = [entry["code"], *(entry.get("extra_aliases") or [])]
        codes = [c for c in codes if c and "skip" not in str(c).lower()]
        alias_n += add_aliases(aliases, rid, codes)

        if rid in by_id:
            prev = rows[by_id[rid]]
            merged = {**prev, **row}
            # keep stronger existing image/sku if already set and new empty — not needed here
            rows[by_id[rid]] = merged
            updated += 1
        else:
            rows.append(row)
            by_id[rid] = len(rows) - 1
            added += 1

        sku_map[rid] = entry["gtin"]
        urls[rid] = entry["image"]
        samples.append(
            {
                "id": rid,
                "name": entry["name"],
                "sku": entry["gtin"],
                "code": entry["code"],
                "line": entry["line"],
                "msrp": entry["msrp"],
            }
        )

    aliases["updatedAt"] = now_iso()
    write_json(ARCHIVE, rows)
    write_json(ALIASES, aliases)
    write_json(SKU_MAP, sku_map)
    write_json(URLS, urls)

    sg_count = sum(
        1
        for r in rows
        if r.get("company") == "hasbro"
        and (
            (r.get("line") or "") in (LINE_SG, LINE_SEL)
            and "shattered" in (r.get("line") + " " + r.get("name", "") + " " + " ".join(r.get("tags") or [])).lower()
            or str(r.get("id", "")).startswith("hasbro-sg-")
        )
    )
    # Prefer id-prefix count for clarity
    sg_ids = [r["id"] for r in rows if str(r.get("id", "")).startswith("hasbro-sg-")]

    stats = {
        "source": SRC,
        "updatedAt": now_iso(),
        "added": added,
        "updated": updated,
        "aliasesAdded": alias_n,
        "sgIdCount": len(sg_ids),
        "sgIds": sg_ids,
        "samples": samples,
        "notes": skipped_reissue,
        "publish": False,
    }
    write_json(STATS, stats)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
