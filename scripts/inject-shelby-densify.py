#!/usr/bin/env python3
"""Large densify inject: Dramatic Capture + R.E.D. + Dragon Stars + Gong + Storm Arena + MDLX.

Sources (verified 2026-09):
  - AmiAmi API: Dramatic Capture Series JANs + CDN images
  - TFW2005 / Unicron / iCollectEverything / TRG Toys: R.E.D. EAN-13s
  - CMD Store Shopify: Dragon Stars Bandai UPCs + CDN images
  - BBTS: Gong Evangelion Unit-01 + Storm Arena product images
  - Ages Three and Up / Jap-One: MDLX Toxitron GTIN 4895250821019 + CDN

Policy: real CDN/retailer images; empty sku/image over wrong; primary sku=GTIN/JAN;
retailer codes as aliases; unique ids; kind=figure; dedupe by id / GTIN /
company+line+name+subtitle. Does NOT Build Publish Live.
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
STATS = ROOT / "src/data/figure-archive/shelby-densify-inject-stats.json"
CATALOG = SCRIPTS / "figure_oneshot/densify_shelby_catalog.json"

SOURCE = "inject-shelby-densify"


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


def make_row(
    *,
    rid: str,
    name: str,
    subtitle: str,
    line: str,
    company: str,
    msrp: float,
    scale: str,
    release: str,
    demand: float,
    sku: str | None,
    image: str | None,
    tags: list[str],
    exclusive: str | None = None,
) -> dict:
    out: dict[str, Any] = {
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
        "tags": tags,
        "source": SOURCE,
    }
    if sku:
        out["sku"] = sku
    if image:
        out["imageUrl"] = image
    if exclusive:
        out["exclusive"] = exclusive
    return out


def main() -> None:
    catalog = load_json(CATALOG)
    rows: list[dict] = load_json(ARCHIVE)
    aliases = ensure_alias_doc(load_json(ALIASES) if ALIASES.exists() else {})
    sku_map: dict = load_json(SKU_MAP) if SKU_MAP.exists() else {}
    urls: dict = load_json(URLS) if URLS.exists() else {}
    alias_to = aliases.get("aliasToFigureId") or {}

    ids = {r["id"] for r in rows}
    keys = {row_key(r) for r in rows}
    # also index existing GTINs from sku field
    gtin_owned: dict[str, str] = {}
    for r in rows:
        s = clean_code(r.get("sku"))
        if s and is_gtin(s):
            gtin_owned[s] = r["id"]

    added: list[str] = []
    skipped: list[dict] = []
    counts: dict[str, int] = {
        "dramatic_capture": 0,
        "red": 0,
        "dragon_stars": 0,
        "gong": 0,
        "storm_arena": 0,
        "threezero_mdlx": 0,
    }
    alias_added = 0
    img_baked = 0
    gtin_set: list[str] = []

    def inject(row: dict, alias_codes: list[str], bucket: str) -> bool:
        nonlocal alias_added, img_baked
        rid = row["id"]
        if rid in ids:
            skipped.append({"id": rid, "reason": "id-exists"})
            return False
        k = row_key(row)
        if k in keys:
            skipped.append({"id": rid, "reason": "key-exists", "key": k})
            return False
        sku = clean_code(row.get("sku"))
        if sku and is_gtin(sku) and sku in gtin_owned:
            skipped.append(
                {"id": rid, "reason": "gtin-exists", "sku": sku, "owner": gtin_owned[sku]}
            )
            return False
        for c in alias_codes:
            c2 = clean_code(c) or str(c).strip()
            if c2 and c2 in alias_to and alias_to[c2] != rid:
                # listing alias collision — skip only if mapped to different id
                # allow if same logical; still skip to be safe
                skipped.append({"id": rid, "reason": "alias-collision", "code": c2})
                return False
        if not row.get("sku"):
            row.pop("sku", None)
        if not row.get("imageUrl"):
            row.pop("imageUrl", None)
        rows.append(row)
        ids.add(rid)
        keys.add(k)
        added.append(rid)
        counts[bucket] = counts.get(bucket, 0) + 1
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
        return True

    # ---- A) Dramatic Capture Series (Takara Tomy) ----
    for item in catalog.get("dramatic_capture") or []:
        sku = item.get("sku") or item.get("jan")
        img = item.get("image") or item.get("img")
        inject(
            make_row(
                rid=item["id"],
                name=item["name"],
                subtitle=item.get("subtitle") or "Dramatic Capture Series",
                line="Dramatic Capture Series",
                company="takaratomy",
                msrp=float(item.get("msrp") or 120),
                scale='6"',
                release=item.get("release") or "2024-01-01",
                demand=1.55,
                sku=sku,
                image=img,
                tags=[
                    "takaratomy",
                    "hasbro",
                    "transformers",
                    "dramatic-capture",
                    "premium-finish",
                    "curated",
                    SOURCE,
                ],
            ),
            list(item.get("aliases") or []) + ([item.get("code")] if item.get("code") else []),
            "dramatic_capture",
        )

    # ---- B) Transformers R.E.D. (Hasbro) ----
    for item in catalog.get("red") or []:
        red_aliases = []
        if item.get("code"):
            red_aliases.append(item["code"])
        inject(
            make_row(
                rid=item["id"],
                name=item["name"],
                subtitle=item.get("subtitle") or "Robot Enhanced Design",
                line="Transformers R.E.D.",
                company="hasbro",
                msrp=float(item.get("msrp") or 19.99),
                scale='6"',
                release=item.get("release") or "2020-10-01",
                demand=1.35,
                sku=item.get("sku"),
                image=item.get("image"),
                tags=[
                    "hasbro",
                    "transformers",
                    "red",
                    "robot-enhanced-design",
                    "non-transforming",
                    "walmart-exclusive",
                    "curated",
                    SOURCE,
                ],
            ),
            red_aliases,
            "red",
        )

    # ---- C) Dragon Stars (Bandai) ----
    for item in catalog.get("dragon_stars") or []:
        inject(
            make_row(
                rid=item["id"],
                name=item["name"],
                subtitle=item.get("subtitle") or "Dragon Stars",
                line="Dragon Stars",
                company="bandai",
                msrp=float(item.get("msrp") or 24.99),
                scale='6"',
                release=item.get("release") or "2020-01-01",
                demand=1.25,
                sku=item.get("sku"),
                image=item.get("image"),
                tags=[
                    "bandai",
                    "dragon-ball",
                    "dragon-stars",
                    "curated",
                    SOURCE,
                ],
            ),
            list(item.get("aliases") or []),
            "dragon_stars",
        )

    # ---- D) Gong Studio ----
    for item in catalog.get("gong") or []:
        inject(
            make_row(
                rid=item["id"],
                name=item["name"],
                subtitle=item.get("subtitle") or "Gong Studio",
                line="Gong Studio",
                company="gong",
                msrp=float(item.get("msrp") or 93),
                scale="16.5cm",
                release=item.get("release") or "2026-06-01",
                demand=1.45,
                sku=item.get("sku"),
                image=item.get("image"),
                tags=[
                    "gong",
                    "gongstudio",
                    "evangelion",
                    "diecast",
                    "curated",
                    SOURCE,
                ],
            ),
            list(item.get("aliases") or []),
            "gong",
        )

    # ---- E) Storm Arena densify ----
    for item in catalog.get("storm_arena") or []:
        inject(
            make_row(
                rid=item["id"],
                name=item["name"],
                subtitle=item.get("subtitle") or "Storm Arena",
                line=item.get("line") or "Storm Arena",
                company="storm",
                msrp=float(item.get("msrp") or 99.99),
                scale="1:12",
                release=item.get("release") or "2025-06-01",
                demand=1.4,
                sku=item.get("sku"),
                image=item.get("image"),
                tags=[
                    "storm",
                    "storm-arena",
                    "curated",
                    SOURCE,
                ],
            ),
            list(item.get("aliases") or []),
            "storm_arena",
        )

    # ---- F) threezero MDLX densify (incl. Toxitron) ----
    for item in catalog.get("threezero_mdlx") or []:
        # Skip if product code already aliased to an existing figure
        collision = False
        for a in item.get("aliases") or []:
            c2 = clean_code(a) or str(a).strip()
            if c2 and c2 in alias_to:
                skipped.append(
                    {
                        "id": item["id"],
                        "reason": "product-code-exists",
                        "code": c2,
                        "owner": alias_to[c2],
                    }
                )
                collision = True
                break
        if collision:
            continue
        inject(
            make_row(
                rid=item["id"],
                name=item["name"],
                subtitle=item.get("subtitle") or "MDLX",
                line="threezero MDLX",
                company="threezero",
                msrp=float(item.get("msrp") or 109.99),
                scale='7"',
                release=item.get("release") or "2024-01-01",
                demand=1.6,
                sku=item.get("sku"),
                image=item.get("image"),
                tags=[
                    "threezero",
                    "mdlx",
                    "transformers",
                    "curated",
                    SOURCE,
                ],
                exclusive=item.get("exclusive"),
            ),
            list(item.get("aliases") or []),
            "threezero_mdlx",
        )

    write_json(ARCHIVE, rows)
    write_json(ALIASES, aliases)
    write_json(SKU_MAP, sku_map)
    write_json(URLS, urls)

    stats = {
        "source": SOURCE,
        "finishedAt": now_iso(),
        "added": len(added),
        "skipped": len(skipped),
        "counts": counts,
        "aliasAdded": alias_added,
        "imagesBaked": img_baked,
        "gtins": gtin_set,
        "addedIds": added,
        "skippedSample": skipped[:40],
        "archiveSize": len(rows),
    }
    write_json(STATS, stats)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
