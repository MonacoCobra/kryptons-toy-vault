#!/usr/bin/env python3
"""Inject Pop Mart × Gong Studio DC 1/12 AFs (Kingdom Come + Hush).

Sources (verified 2026-09):
  - INS Hobby Shopify product JSON: KC Superman / Shazam Regular+Special SKUs,
    Hush Batman (GNG-0014) / Hush Superman (GNG-0016), CDN images; KC Superman
    Regular barcode/GTIN 6941848276711
  - Pop Mart US PDPs: Hush Batman (#4039) + Hush Superman (#5618) official CDN
  - Toyark / BigFan / Dragon's Chest for line identity (GONG-003 / GONG-004)
  - No Wonder Woman / other Gong DC 1/12 AFs found on honest feeds

Policy: real CDN images; empty sku over wrong; primary sku=GTIN when known;
listing codes as aliases; unique ids; kind=figure. Does NOT Build Publish Live.
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

from figure_identity import clean_code, is_gtin  # noqa: E402

ARCHIVE = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
SKU_MAP = ROOT / "src/data/figure-sku-map.json"
URLS = ROOT / "src/data/figure-image-urls.json"
STATS = ROOT / "src/data/figure-archive/gong-dc-inject-stats.json"
CATALOG = SCRIPTS / "figure_oneshot/gong_dc_catalog.json"

SOURCE = "inject-gong-dc"
COMPANY = "gong"


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
        c2 = clean_code(c) or str(c).strip()
        if not c2:
            continue
        if c2 not in cur:
            cur.append(c2)
            added += 1
        to[c2] = figure_id
    if cur:
        by[figure_id] = cur
    return added


def row_key(r: dict) -> str:
    return "|".join(
        [
            (r.get("company") or "").lower(),
            (r.get("line") or "").lower(),
            (r.get("name") or "").lower(),
            (r.get("subtitle") or "").lower(),
        ]
    )


def make_row(item: dict) -> dict:
    tags = [
        "gong",
        "gongstudio",
        "curated",
        SOURCE,
        *(item.get("tags") or []),
    ]
    # dedupe tags preserving order
    seen: set[str] = set()
    tags2: list[str] = []
    for t in tags:
        if t and t not in seen:
            seen.add(t)
            tags2.append(t)
    out: dict[str, Any] = {
        "id": item["id"],
        "name": item["name"],
        "subtitle": item.get("subtitle") or "",
        "line": item.get("line") or "Gong Studio",
        "company": COMPANY,
        "kind": "figure",
        "releaseDate": item.get("release") or "2024-01-01",
        "msrp": float(item.get("msrp") or 99.99),
        "scale": item.get("scale") or "1:12",
        "demand": float(item.get("demand") or 1.5),
        "tags": tags2,
        "source": SOURCE,
    }
    sku = item.get("sku")
    if sku:
        out["sku"] = str(sku).strip()
    img = item.get("image")
    if img:
        out["imageUrl"] = img
    if item.get("exclusive"):
        out["exclusive"] = item["exclusive"]
    return out


def main() -> None:
    catalog = load_json(CATALOG)
    items = list(catalog.get("items") or [])
    rows: list[dict] = load_json(ARCHIVE)
    aliases = ensure_alias_doc(load_json(ALIASES) if ALIASES.exists() else {})
    sku_map: dict = load_json(SKU_MAP) if SKU_MAP.exists() else {}
    urls: dict = load_json(URLS) if URLS.exists() else {}
    alias_to = aliases.get("aliasToFigureId") or {}

    ids = {r["id"] for r in rows}
    keys = {row_key(r) for r in rows}
    gtin_owned: dict[str, str] = {}
    for r in rows:
        s = clean_code(r.get("sku"))
        if s and is_gtin(s):
            gtin_owned[s] = r["id"]

    added: list[str] = []
    skipped: list[dict] = []
    alias_added = 0
    img_baked = 0
    gtin_set: list[str] = []

    for item in items:
        row = make_row(item)
        rid = row["id"]
        alias_codes = list(item.get("aliases") or [])

        if rid in ids:
            skipped.append({"id": rid, "reason": "id-exists"})
            continue
        k = row_key(row)
        if k in keys:
            skipped.append({"id": rid, "reason": "key-exists", "key": k})
            continue
        sku = clean_code(row.get("sku"))
        if sku and is_gtin(sku) and sku in gtin_owned:
            skipped.append(
                {"id": rid, "reason": "gtin-exists", "sku": sku, "owner": gtin_owned[sku]}
            )
            continue
        collision = False
        for c in alias_codes:
            c2 = clean_code(c) or str(c).strip()
            if c2 and c2 in alias_to and alias_to[c2] != rid:
                skipped.append({"id": rid, "reason": "alias-collision", "code": c2})
                collision = True
                break
        if collision:
            continue

        if not row.get("sku"):
            row.pop("sku", None)
        if not row.get("imageUrl"):
            row.pop("imageUrl", None)

        rows.append(row)
        ids.add(rid)
        keys.add(k)
        added.append(rid)

        als = [a for a in alias_codes if a]
        als.append(f"id:{rid}")
        if sku:
            als.append(sku)
        alias_added += add_aliases(aliases, rid, als)
        for a in als:
            a2 = clean_code(a) or str(a).strip()
            if a2:
                alias_to[a2] = rid

        if sku and is_gtin(sku):
            sku_map[rid] = sku
            gtin_owned[sku] = rid
            gtin_set.append(sku)
            tags = list(row.get("tags") or [])
            for t in ("sku-gtin", "sku-bake"):
                if t not in tags:
                    tags.append(t)
            row["tags"] = tags

        if row.get("imageUrl"):
            urls[rid] = row["imageUrl"]
            img_baked += 1
            tags = list(row.get("tags") or [])
            if "image-bake" not in tags:
                tags.append("image-bake")
            row["tags"] = tags

    aliases["updatedAt"] = now_iso()
    write_json(ARCHIVE, rows)
    write_json(ALIASES, aliases)
    write_json(SKU_MAP, sku_map)
    write_json(URLS, urls)

    # Character tallies for report
    supers = [i for i in added if "superman" in i]
    bats = [i for i in added if "batman" in i]
    shaz = [i for i in added if "shazam" in i]

    stats = {
        "updatedAt": now_iso(),
        "source": SOURCE,
        "added": added,
        "addedCount": len(added),
        "skipped": skipped,
        "aliasAdded": alias_added,
        "imagesBaked": img_baked,
        "gtinsSet": gtin_set,
        "supermanCount": len(supers),
        "batmanCount": len(bats),
        "shazamCount": len(shaz),
        "names": [
            next((x["name"] + " — " + (x.get("subtitle") or "") for x in items if x["id"] == i), i)
            for i in added
        ],
        "honestGaps": [
            "No Gong Studio Wonder Woman / other DC 1/12 AFs found on Pop Mart, INS Hobby, Toyark, BigFan feeds beyond KC Superman/Shazam + Hush Batman/Superman.",
            "Exclusive KC variants + Hush figures lack verified GTIN/barcode (empty sku).",
            "INS Hobby labels Hush as 1:10; catalog uses official 1:12 / ~17.5 cm.",
        ],
    }
    write_json(STATS, stats)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
