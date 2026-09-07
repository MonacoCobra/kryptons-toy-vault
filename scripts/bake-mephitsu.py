#!/usr/bin/env python3
"""Bake Mephitsu hub lines into oneshot (GTIN primary + empty image fills).

Extends the Marvel Legends baker to Black Series, GI Joe Classified,
Transformers (Studio Series when cued), McFarlane, NECA, Super7,
Diamond Select, etc.

Policy:
  - Primary sku = GTIN only (never invent; never overwrite GTIN with listing)
  - Listing codes → aliases
  - Fill empty imageUrl from Mephitsu photos only
  - High-confidence matcher via bake-figure-images.score_pair

  python3 scripts/bake-mephitsu.py --line black-series
  python3 scripts/bake-mephitsu.py --all-hub
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
from typing import Any, Callable

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

RowPred = Callable[[dict], bool]


def _co(r: dict) -> str:
    return str(r.get("company") or "").lower()


def _line(r: dict) -> str:
    return str(r.get("line") or "").lower()


def _rid(r: dict) -> str:
    return str(r.get("id") or "")


def is_hasbro_ml_row(r: dict) -> bool:
    if _co(r) != "hasbro":
        return False
    line, rid = _line(r), _rid(r)
    tags = " ".join(str(t) for t in (r.get("tags") or [])).lower()
    if "marvel legends" in line or "marvel-legends" in line:
        return True
    if rid.startswith(("ml5-", "mlc-", "ml2-", "ml3-", "ml4-", "ml6-", "d14ml-", "ml-")):
        return True
    return "marvel legends" in tags


def is_black_series_row(r: dict) -> bool:
    if _co(r) != "hasbro":
        return False
    line, rid = _line(r), _rid(r)
    if "black series" in line:
        return True
    return rid.startswith(("bsc-", "bs3-", "bs4-", "bs5-", "bs6-", "d14bs-", "swbs-", "tbs-"))


def is_gi_joe_row(r: dict) -> bool:
    if _co(r) != "hasbro":
        return False
    line, rid = _line(r), _rid(r)
    if "gi joe" in line or "g.i. joe" in line or "g.i joe" in line or "classified" in line:
        return True
    return rid.startswith(("joec-", "joe2-", "cls4-", "cls5-", "cls6-", "d14joe-", "gijoe-"))


def is_transformers_row(r: dict) -> bool:
    if _co(r) != "hasbro":
        return False
    line = _line(r)
    return "transformer" in line or "studio series" in line


def is_studio_series_row(r: dict) -> bool:
    return is_transformers_row(r) and "studio series" in _line(r)


def is_mcfarlane_row(r: dict) -> bool:
    return _co(r) == "mcfarlane"


def is_neca_row(r: dict) -> bool:
    return _co(r) == "neca"


def is_super7_row(r: dict) -> bool:
    return _co(r) == "super7"


def is_diamond_row(r: dict) -> bool:
    return _co(r) == "diamondselect"


def is_lightning_row(r: dict) -> bool:
    if _co(r) != "hasbro":
        return False
    line = _line(r)
    return "lightning" in line or "power ranger" in line


def is_indiana_row(r: dict) -> bool:
    if _co(r) != "hasbro":
        return False
    return "indiana" in _line(r)


def is_playmates_row(r: dict) -> bool:
    return _co(r) == "playmates"


LINE_CONFIG: dict[str, dict[str, Any]] = {
    "marvel-legends": {
        "row_pred": is_hasbro_ml_row,
        "enrich_companies": {"hasbro"},
        "default_line": "Marvel Legends",
        "default_company": "hasbro",
    },
    "black-series": {
        "row_pred": is_black_series_row,
        "enrich_companies": {"hasbro"},
        "default_line": "Star Wars The Black Series",
        "default_company": "hasbro",
    },
    "gi-joe-classified": {
        "row_pred": is_gi_joe_row,
        "enrich_companies": {"hasbro"},
        "default_line": "G.I. Joe Classified Series",
        "default_company": "hasbro",
    },
    "transformers": {
        "row_pred": is_transformers_row,
        "enrich_companies": {"hasbro"},
        "default_line": "Transformers",
        "default_company": "hasbro",
    },
    "mcfarlane": {
        "row_pred": is_mcfarlane_row,
        "enrich_companies": {"mcfarlane"},
        "default_line": "McFarlane",
        "default_company": "mcfarlane",
    },
    "neca": {
        "row_pred": is_neca_row,
        "enrich_companies": {"neca"},
        "default_line": "NECA",
        "default_company": "neca",
    },
    "super7": {
        "row_pred": is_super7_row,
        "enrich_companies": {"super7"},
        "default_line": "Super7",
        "default_company": "super7",
    },
    "diamond-select": {
        "row_pred": is_diamond_row,
        "enrich_companies": {"diamondselect"},
        "default_line": "Diamond Select",
        "default_company": "diamondselect",
    },
    "power-rangers": {
        "row_pred": is_lightning_row,
        "enrich_companies": {"hasbro"},
        "default_line": "Lightning Collection",
        "default_company": "hasbro",
    },
    "indiana-jones": {
        "row_pred": is_indiana_row,
        "enrich_companies": {"hasbro"},
        "default_line": "Indiana Jones Adventure Series",
        "default_company": "hasbro",
    },
    "star-trek": {
        "row_pred": is_playmates_row,
        "enrich_companies": {"playmates"},
        "default_line": "Star Trek",
        "default_company": "playmates",
    },
}

HUB_LINES = [
    "black-series",
    "gi-joe-classified",
    "transformers",
    "mcfarlane",
    "neca",
    "super7",
    "diamond-select",
    "power-rangers",
    "indiana-jones",
]


def load_mephitsu(line: str) -> list[dict]:
    path = MEPH_DIR / f"{line}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    doc = json.loads(path.read_text())
    return list(doc.get("products") or [])


def enrich_meph_gtins_from_index(
    meph: list[dict],
    index: list[dict],
    min_score: float,
    *,
    enrich_companies: set[str],
    default_company: str,
    default_line: str,
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
        if (
            sku
            and not is_gtin(sku)
            and clean_code(raw.get("barcode"))
            and is_gtin(raw.get("barcode"))
        ):
            by_listing.setdefault(sku.upper(), clean_code(raw.get("barcode")) or "")
        co = str(raw.get("company") or "").lower()
        if sku and is_gtin(sku) and co in enrich_companies:
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
            "company": p.get("company") or default_company,
            "name": p.get("name") or "",
            "subtitle": p.get("subtitle") or "",
            "line": p.get("line") or default_line,
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


def match_meph_to_rows(
    rows: list[dict],
    meph: list[dict],
    *,
    row_pred: RowPred,
    min_score: float,
    default_company: str,
) -> list[tuple[float, dict, dict]]:
    targets = [r for r in rows if row_pred(r)]
    prods = []
    for p in meph:
        prods.append(
            {
                "id": p["id"],
                "shop": "mephitsu",
                "tier": "specialty",
                "company": p.get("company") or default_company,
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
            # Mild wave/year boost from meph meta
            meph = p.get("_meph") or {}
            if meph.get("year") and str(meph["year"]) in str(fig.get("subtitle") or ""):
                sc += 2
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

        if len(stats["samples"]) < 8:
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


def coverage(rows: list[dict], row_pred: RowPred) -> dict:
    xs = [r for r in rows if row_pred(r)]
    return {
        "total": len(xs),
        "withSku": sum(1 for r in xs if r.get("sku")),
        "withGtin": sum(1 for r in xs if r.get("sku") and is_gtin(r.get("sku"))),
        "withListingPrimary": sum(
            1 for r in xs if r.get("sku") and not is_gtin(r.get("sku"))
        ),
        "withImage": sum(1 for r in xs if r.get("imageUrl")),
        "emptySku": sum(1 for r in xs if not r.get("sku")),
        "emptyImage": sum(1 for r in xs if not r.get("imageUrl")),
    }


def bake_line(
    line: str,
    rows: list[dict],
    index: list[dict],
    *,
    dry_run: bool,
    min_score: float,
    skip_enrich: bool,
) -> dict:
    if line not in LINE_CONFIG:
        raise SystemExit(f"Unknown line {line}. Known: {sorted(LINE_CONFIG)}")
    cfg = LINE_CONFIG[line]
    meph = load_mephitsu(line)
    before = coverage(rows, cfg["row_pred"])

    enrich_stats: dict = {}
    if not skip_enrich:
        enrich_stats = enrich_meph_gtins_from_index(
            meph,
            index,
            min_score,
            enrich_companies=cfg["enrich_companies"],
            default_company=cfg["default_company"],
            default_line=cfg["default_line"],
        )
        path = MEPH_DIR / f"{line}.json"
        doc = json.loads(path.read_text())
        doc["products"] = meph
        doc["withGtin"] = sum(1 for p in meph if p.get("sku") and is_gtin(p["sku"]))
        doc["enrichedAt"] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

    finals = match_meph_to_rows(
        rows,
        meph,
        row_pred=cfg["row_pred"],
        min_score=min_score,
        default_company=cfg["default_company"],
    )
    stats = apply_bake(rows, finals, dry_run=dry_run)
    return {
        "bakedAt": datetime.now(timezone.utc).isoformat(),
        "line": line,
        "dryRun": dry_run,
        "mephitsuCount": len(meph),
        "mephitsuWithGtin": sum(
            1 for p in meph if p.get("sku") and is_gtin(p.get("sku"))
        ),
        "enrichStats": enrich_stats,
        "before": before,
        "after": coverage(rows, cfg["row_pred"]),
        "apply": stats,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--line", action="append", dest="lines")
    ap.add_argument("--all-hub", action="store_true", help="Bake hub lines (excl. ML)")
    ap.add_argument("--include-ml", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE)
    ap.add_argument("--skip-enrich", action="store_true")
    ap.add_argument("--list-lines", action="store_true")
    args = ap.parse_args()

    if args.list_lines:
        for k in LINE_CONFIG:
            print(k)
        return 0

    if args.all_hub:
        keys = list(HUB_LINES)
        if args.include_ml:
            keys = ["marvel-legends"] + keys
    else:
        keys = args.lines or ["marvel-legends"]

    rows = json.loads(ONESHOT.read_text())
    index = json.loads(SKU_INDEX.read_text()) if SKU_INDEX.exists() else []

    reports = []
    for line in keys:
        print(f"=== baking {line} ===", flush=True)
        report = bake_line(
            line,
            rows,
            index,
            dry_run=args.dry_run,
            min_score=args.min_score,
            skip_enrich=args.skip_enrich,
        )
        reports.append(report)
        a = report["apply"]
        print(
            f"[{line}] matched={a['matched']} gtin+={a['gtinAssigned']} "
            f"upgrade={a['gtinUpgraded']} img+={a['imagesFilled']} "
            f"conflict={a['skippedGtinConflict']} "
            f"gtin {report['before']['withGtin']}→{report['after']['withGtin']} "
            f"img {report['before']['withImage']}→{report['after']['withImage']}",
            flush=True,
        )

    out = {
        "bakedAt": datetime.now(timezone.utc).isoformat(),
        "dryRun": args.dry_run,
        "lines": reports,
    }
    STATS.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"summary": [
        {
            "line": r["line"],
            "matched": r["apply"]["matched"],
            "gtinAssigned": r["apply"]["gtinAssigned"],
            "imagesFilled": r["apply"]["imagesFilled"],
            "before": r["before"],
            "after": r["after"],
        }
        for r in reports
    ]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
