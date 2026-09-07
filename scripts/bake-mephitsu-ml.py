#!/usr/bin/env python3
"""Bake Mephitsu Marvel Legends into oneshot (GTIN primary + photos).

- Primary sku = GTIN only (never invent; never overwrite GTIN with listing)
- Listing codes → aliases
- Fill empty imageUrl from Mephitsu front/box photos
- High-confidence matcher via bake-figure-images.score_pair

  python3 scripts/bake-mephitsu-ml.py --line marvel-legends
  python3 scripts/bake-figure-images.py --sku-first --cache-only
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

_spec = importlib.util.spec_from_file_location(
    "bake_figure_images", SCRIPTS / "bake-figure-images.py"
)
bfi = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(bfi)

from figure_identity import clean_code, is_gtin, is_listing_code, norm_text  # noqa: E402

ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
MEPH_DIR = ROOT / "src/data/figure-archive/mephitsu"
SKU_MAP = ROOT / "src/data/figure-sku-map.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
STATS = ROOT / "src/data/figure-archive/mephitsu-bake-stats.json"
SKU_INDEX = ROOT / "src/data/figure-archive/product-sku-index.json"

DEFAULT_MIN_SCORE = 18.0


def load_mephitsu(line: str) -> list[dict]:
    doc = json.loads((MEPH_DIR / f"{line}.json").read_text())
    return list(doc.get("products") or [])


def enrich_meph_gtins_from_index(
    meph: list[dict], index: list[dict], min_score: float
) -> dict:
    by_listing: dict[str, str] = {}
    gtin_pool: list[dict] = []
    for raw in index:
        if raw.get("shop") == "mephitsu":
            continue
        sku = clean_code(raw.get("sku")) or clean_code(raw.get("barcode"))
        listing = clean_code(raw.get("listingSku"))
        if listing and sku and is_gtin(sku):
            u = listing.upper()
            by_listing.setdefault(u, sku)
            m = re.match(r"^(?:HAS|HSG|HS)([A-Z]?\d{4,})$", u)
            if m:
                by_listing.setdefault(m.group(1), sku)
        if sku and not is_gtin(sku) and clean_code(raw.get("barcode")) and is_gtin(raw.get("barcode")):
            by_listing.setdefault(sku.upper(), clean_code(raw.get("barcode")) or "")
        if sku and is_gtin(sku) and str(raw.get("company") or "").lower() == "hasbro":
            gtin_pool.append(dict(raw))
    bfi.enrich_index(gtin_pool)

    stats = {"listing": 0, "fuzzy": 0, "already": 0}
    used: set[str] = set()
    for p in meph:
        if p.get("sku") and is_gtin(p["sku"]):
            used.add(str(p["sku"]).upper())
            stats["already"] += 1

    for p in meph:
        if p.get("sku") and is_gtin(p["sku"]):
            continue
        listing = clean_code(p.get("listingSku"))
        if listing and listing.upper() in by_listing:
            g = by_listing[listing.upper()]
            if g and g.upper() not in used:
                p["sku"] = g
                p["barcode"] = g
                used.add(g.upper())
                stats["listing"] += 1

    for p in meph:
        if p.get("sku") and is_gtin(p["sku"]):
            continue
        fig = {
            "id": p["id"],
            "company": p.get("company") or "hasbro",
            "name": p.get("name") or "",
            "subtitle": p.get("subtitle") or "",
            "line": p.get("line") or "Marvel Legends",
            "tags": p.get("tags") or [],
        }
        best: tuple[float, dict] | None = None
        for prod in gtin_pool:
            sku = clean_code(prod.get("sku"))
            if not sku or not is_gtin(sku) or sku.upper() in used:
                continue
            sc = bfi.score_pair(fig, prod)
            if sc < min_score:
                continue
            blob = f"{prod.get('title')} {prod.get('subtitle')} {prod.get('name')}".lower()
            if p.get("year") and str(p["year"]) in blob:
                sc += 2
            wave = norm_text(str(p.get("wave") or ""))
            if wave and wave in norm_text(blob):
                sc += 3
            if best is None or sc > best[0]:
                best = (sc, prod)
        if best:
            g = clean_code(best[1].get("sku"))
            if g:
                p["sku"] = g
                p["barcode"] = g
                used.add(g.upper())
                stats["fuzzy"] += 1
    return stats


def is_hasbro_ml_row(r: dict) -> bool:
    if str(r.get("company") or "").lower() != "hasbro":
        return False
    line = str(r.get("line") or "").lower()
    rid = str(r.get("id") or "")
    tags = " ".join(str(t) for t in (r.get("tags") or [])).lower()
    if "marvel legends" in line or "marvel-legends" in line:
        return True
    if rid.startswith(("ml5-", "mlc-", "ml2-", "ml3-", "ml4-", "ml6-", "d14ml-", "ml-")):
        return True
    return "marvel legends" in tags


def match_meph_to_rows(
    rows: list[dict],
    meph: list[dict],
    *,
    min_score: float,
) -> list[tuple[float, dict, dict]]:
    targets = [r for r in rows if is_hasbro_ml_row(r)]
    prods = []
    for p in meph:
        prods.append(
            {
                "id": p["id"],
                "shop": "mephitsu",
                "tier": "specialty",
                "company": p.get("company") or "hasbro",
                "name": p.get("name") or "",
                "subtitle": p.get("subtitle") or "",
                "line": p.get("line") or "",
                "tags": p.get("tags") or [],
                "title": p.get("title") or p.get("name") or "",
                "handle": p.get("handle"),
                "sku": p.get("sku"),
                "listingSku": p.get("listingSku"),
                "imageUrl": p.get("imageUrl"),
                "_meph": p,
            }
        )
    bfi.enrich_index(prods)

    cands: list[tuple[float, dict, dict]] = []
    for fig in targets:
        best: tuple[float, dict] | None = None
        for p in prods:
            sc = bfi.score_pair(fig, p)
            if sc < min_score:
                continue
            fw = set(norm_text(str(fig.get("subtitle") or "")).split())
            pw = set(norm_text(str(p.get("subtitle") or "")).split())
            if fw and pw:
                sc += 2.5 * len(fw & pw)
            if best is None or sc > best[0]:
                best = (sc, p)
        if best:
            cands.append((best[0], fig, best[1]))

    cands.sort(key=lambda x: x[0], reverse=True)
    used_m: set[str] = set()
    used_f: set[str] = set()
    finals: list[tuple[float, dict, dict]] = []
    for sc, fig, p in cands:
        if fig["id"] in used_f or p["id"] in used_m:
            continue
        finals.append((sc, fig, p))
        used_f.add(fig["id"])
        used_m.add(p["id"])
    return finals


def apply_bake(
    rows: list[dict],
    finals: list[tuple[float, dict, dict]],
    *,
    dry_run: bool,
) -> dict:
    by_id = {r["id"]: r for r in rows}
    sku_map: dict[str, str] = {}
    if SKU_MAP.exists():
        try:
            sku_map = {str(k): str(v) for k, v in json.loads(SKU_MAP.read_text()).items()}
        except Exception:
            sku_map = {}

    aliases_by: dict[str, list[str]] = {}
    alias_doc: dict[str, Any] = {}
    if ALIASES.exists():
        try:
            alias_doc = json.loads(ALIASES.read_text())
            body = alias_doc.get("aliasesByFigureId") or {}
            for k, v in body.items():
                if isinstance(v, list):
                    aliases_by[k] = [str(x) for x in v]
        except Exception:
            alias_doc = {}

    used_gtins = {
        str(r.get("sku")).upper()
        for r in rows
        if r.get("sku") and is_gtin(r.get("sku"))
    }

    stats = {
        "matched": len(finals),
        "gtinAssigned": 0,
        "gtinUpgraded": 0,
        "imagesFilled": 0,
        "aliasesAttached": 0,
        "skippedGtinConflict": 0,
        "samples": [],
    }

    for sc, fig, p in finals:
        row = by_id[fig["id"]]
        meph = p.get("_meph") or p
        existing = clean_code(row.get("sku"))
        cand = clean_code(meph.get("sku"))
        listing = clean_code(meph.get("listingSku"))

        if cand and is_gtin(cand):
            if cand.upper() in used_gtins and (
                not existing or existing.upper() != cand.upper()
            ):
                if not existing or not is_gtin(existing):
                    stats["skippedGtinConflict"] += 1
                cand_use = None
            else:
                cand_use = cand
            if cand_use:
                if existing and is_gtin(existing):
                    pass
                elif existing and not is_gtin(existing):
                    if not dry_run:
                        bucket = aliases_by.setdefault(row["id"], [])
                        if existing not in bucket:
                            bucket.append(existing)
                            stats["aliasesAttached"] += 1
                        row["sku"] = cand_use
                        used_gtins.add(cand_use.upper())
                        tags = list(row.get("tags") or [])
                        for t in ("sku-bake", "sku-gtin", "sku:mephitsu"):
                            if t not in tags and len(tags) < 24:
                                tags.append(t)
                        row["tags"] = tags
                        sku_map[row["id"]] = cand_use
                    stats["gtinUpgraded"] += 1
                    stats["gtinAssigned"] += 1
                elif not existing:
                    if not dry_run:
                        row["sku"] = cand_use
                        used_gtins.add(cand_use.upper())
                        tags = list(row.get("tags") or [])
                        for t in ("sku-bake", "sku-gtin", "sku:mephitsu"):
                            if t not in tags and len(tags) < 24:
                                tags.append(t)
                        row["tags"] = tags
                        sku_map[row["id"]] = cand_use
                    stats["gtinAssigned"] += 1

        if listing and is_listing_code(listing):
            if not dry_run:
                bucket = aliases_by.setdefault(row["id"], [])
                if listing not in bucket and listing != row.get("sku"):
                    bucket.append(listing)
                    stats["aliasesAttached"] += 1

        img = meph.get("imageUrl")
        if img and not row.get("imageUrl"):
            if not dry_run:
                row["imageUrl"] = img
                tags = list(row.get("tags") or [])
                for t in ("image-bake", "img:mephitsu"):
                    if t not in tags and len(tags) < 24:
                        tags.append(t)
                row["tags"] = tags
            stats["imagesFilled"] += 1

        if len(stats["samples"]) < 12:
            stats["samples"].append(
                {
                    "score": round(sc, 2),
                    "figureId": row["id"],
                    "name": row.get("name"),
                    "mephitsu": meph.get("name"),
                    "wave": meph.get("wave"),
                    "sku": row.get("sku"),
                    "image": bool(row.get("imageUrl")),
                }
            )

    if not dry_run:
        ONESHOT.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
        SKU_MAP.write_text(json.dumps(sku_map, indent=2, ensure_ascii=False) + "\n")
        if not alias_doc:
            alias_doc = {
                "version": 1,
                "policy": "gtin-canonical",
                "aliasesByFigureId": {},
                "aliasToFigureId": {},
                "collapsed": [],
                "flagged": [],
            }
        alias_doc["policy"] = "gtin-canonical"
        alias_doc["updatedAt"] = datetime.now(timezone.utc).isoformat()
        ab = alias_doc.setdefault("aliasesByFigureId", {})
        at = alias_doc.setdefault("aliasToFigureId", {})
        for fid, codes in aliases_by.items():
            bucket = list(ab.get(fid) or [])
            for c in codes:
                if c not in bucket:
                    bucket.append(c)
                at[c] = fid
            ab[fid] = bucket
        ALIASES.write_text(json.dumps(alias_doc, indent=2, ensure_ascii=False) + "\n")

    return stats


def coverage(rows: list[dict]) -> dict:
    ml = [r for r in rows if is_hasbro_ml_row(r)]
    return {
        "mlTotal": len(ml),
        "withSku": sum(1 for r in ml if r.get("sku")),
        "withGtin": sum(1 for r in ml if r.get("sku") and is_gtin(r.get("sku"))),
        "withListingPrimary": sum(
            1 for r in ml if r.get("sku") and not is_gtin(r.get("sku"))
        ),
        "withImage": sum(1 for r in ml if r.get("imageUrl")),
        "emptySku": sum(1 for r in ml if not r.get("sku")),
        "emptyImage": sum(1 for r in ml if not r.get("imageUrl")),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--line", default="marvel-legends")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE)
    ap.add_argument("--skip-enrich", action="store_true")
    args = ap.parse_args()

    rows = json.loads(ONESHOT.read_text())
    before = coverage(rows)
    meph = load_mephitsu(args.line)
    index = json.loads(SKU_INDEX.read_text()) if SKU_INDEX.exists() else []

    enrich_stats: dict = {}
    if not args.skip_enrich:
        enrich_stats = enrich_meph_gtins_from_index(meph, index, args.min_score)
        path = MEPH_DIR / f"{args.line}.json"
        doc = json.loads(path.read_text())
        doc["products"] = meph
        doc["withGtin"] = sum(1 for p in meph if p.get("sku") and is_gtin(p["sku"]))
        doc["enrichedAt"] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

    finals = match_meph_to_rows(rows, meph, min_score=args.min_score)
    stats = apply_bake(rows, finals, dry_run=args.dry_run)
    report = {
        "bakedAt": datetime.now(timezone.utc).isoformat(),
        "line": args.line,
        "dryRun": args.dry_run,
        "mephitsuCount": len(meph),
        "mephitsuWithGtin": sum(
            1 for p in meph if p.get("sku") and is_gtin(p.get("sku"))
        ),
        "enrichStats": enrich_stats,
        "before": before,
        "after": coverage(rows),
        "apply": stats,
    }
    STATS.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
