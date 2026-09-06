#!/usr/bin/env python3
"""Bake accurate Shopify/specialty variant SKUs onto oneshot action figures.

No invented SKUs. Re-fetches first-party + specialty retailer products.json,
extracts variant sku (barcode fallback when SKU empty), and maps onto archive
rows with the same high-confidence matcher as image bake.

Outputs:
  - patches sku on matching rows in src/data/figure-archive/oneshot.json
  - src/data/figure-sku-map.json          (id → sku overlay)
  - src/data/figure-archive/product-sku-index.json
  - src/data/figure-archive/sku-bake-stats.json

Usage:
  python3 scripts/bake-figure-skus.py --fetch          # live pagination + match
  python3 scripts/bake-figure-skus.py --cache-only     # reuse product-sku-index
  python3 scripts/bake-figure-skus.py --dry-run        # report only
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/workspace/collection-app")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_oneshot.shopify_dump import (  # noqa: E402
    STOREFRONTS,
    fetch_all_products,
    is_figure_like,
    tag_list,
)

ARCHIVE_JSON = ROOT / "src/data/figure-archive/oneshot.json"
SKU_MAP_JSON = ROOT / "src/data/figure-sku-map.json"
INDEX_JSON = ROOT / "src/data/figure-archive/product-sku-index.json"
STATS_JSON = ROOT / "src/data/figure-archive/sku-bake-stats.json"
IMAGE_INDEX_JSON = ROOT / "src/data/figure-archive/product-image-index.json"

# Load bake-figure-images helpers (score_pair, RETAILER_FEEDS, etc.) without running main.
_spec = importlib.util.spec_from_file_location("bake_figure_images", SCRIPTS / "bake-figure-images.py")
_bfi = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_bfi)

score_pair = _bfi.score_pair
enrich_index = _bfi.enrich_index
RETAILER_FEEDS = _bfi.RETAILER_FEEDS
infer_retailer_company = _bfi.infer_retailer_company
fetch_retailer_products = _bfi.fetch_retailer_products
product_character_text = _bfi.product_character_text
norm = _bfi.norm
tokens = _bfi.tokens

FAKE_SKU = re.compile(
    r"^(unknown|n/?a|none|null|todo|tbd|-+|\.+|0+|sku|test|placeholder)$",
    re.I,
)
# Prefer first-party storefronts over multi-vendor retailers when scores are close.
FIRST_PARTY_SHOPS = {s["id"] for s in STOREFRONTS}
SHOP_TIER_BONUS = 2.5  # added to score for first-party shops
MIN_SCORE = 18.0  # slightly stricter than image bake (16) — wrong SKU is costly


def clean_sku(raw: Any) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or FAKE_SKU.match(s):
        return None
    # Reject pure whitespace / control
    if not re.search(r"[A-Za-z0-9]", s):
        return None
    # Cap length (Shopify SKUs are usually short)
    if len(s) > 64:
        return None
    return s


def clean_barcode(raw: Any) -> str | None:
    if raw is None:
        return None
    s = re.sub(r"\D", "", str(raw).strip())
    # UPC-A (12), EAN-13 (13), EAN-8 (8), UPC-E (8), GTIN-14 (14)
    if len(s) in {8, 12, 13, 14} and not FAKE_SKU.match(s):
        return s
    return None


def best_variant_identity(p: dict) -> tuple[str | None, str | None]:
    """Return (sku, barcode) from the best variant — prefer non-empty manufacturer SKU."""
    variants = list(p.get("variants") or [])
    if not variants:
        return None, None
    best_sku = None
    best_barcode = None
    for v in variants:
        sku = clean_sku(v.get("sku"))
        barcode = clean_barcode(v.get("barcode"))
        if sku and not best_sku:
            best_sku = sku
        if barcode and not best_barcode:
            best_barcode = barcode
        if best_sku and best_barcode:
            break
    # If no SKU but barcode looks real, use barcode as the identity (honest GTIN)
    if not best_sku and best_barcode:
        best_sku = best_barcode
    return best_sku, best_barcode


def split_title(title: str, p: dict, source_id: str) -> tuple[str, str]:
    if " | " in title:
        segs = [x.strip() for x in title.split(" | ") if x.strip()]
        right = segs[-1]
        left = " | ".join(segs[:-1])
        name = right.split(":")[0].strip() or right
        subtitle = left or str(p.get("product_type") or source_id)
    elif " - " in title:
        left, right = title.rsplit(" - ", 1)
        if len(right) < 80 and not re.search(r"marvel legends|black series|classified", right, re.I):
            name, subtitle = right.strip(), left.strip()
        else:
            name, subtitle = left.strip(), right.strip()
    else:
        parts = re.split(r"\s+[—–]\s+", title)
        if len(parts) >= 2:
            name, subtitle = parts[0].strip(), " - ".join(parts[1:]).strip()
        else:
            colon = title.split(":")
            if len(colon) >= 2 and len(colon[0]) < 48:
                name, subtitle = colon[0].strip(), ":".join(colon[1:]).strip()
            else:
                name, subtitle = title, str(p.get("product_type") or source_id)
    charish = product_character_text(name, subtitle, title)
    lead = (charish.split(title)[0] if title and title in charish else charish).strip()
    if lead and 2 < len(lead) < len(title) and not re.search(
        r"^(amazing yamaguchi|revoltech|mythic legions|cosmic legions|infinite legions)\b",
        lead,
        re.I,
    ):
        if len(lead) <= 80 and lead.lower() != name.lower():
            subtitle = f"{name} {subtitle}".strip()[:160]
            name = lead[:160]
    return name[:160], subtitle[:160]


def entry_from_product(p: dict, source_id: str, company: str, tier: str) -> dict | None:
    sku, barcode = best_variant_identity(p)
    if not sku:
        return None
    title = str(p.get("title") or "").strip()
    if not title:
        return None
    handle = str(p.get("handle") or title)
    name, subtitle = split_title(title, p, source_id)
    return {
        "id": f"{source_id}:{handle}"[:120],
        "shop": source_id,
        "tier": tier,
        "company": company,
        "name": name,
        "subtitle": subtitle,
        "line": str(p.get("product_type") or p.get("vendor") or source_id)[:80],
        "tags": tag_list(p.get("tags"))[:12],
        "title": title[:240],
        "handle": handle[:160],
        "sku": sku,
        "barcode": barcode,
        "productId": str(p.get("id") or "") or None,
        "imageUrl": next(
            (
                str(im.get("src"))
                for im in (p.get("images") or [])
                if (im or {}).get("src") and str(im.get("src")).startswith("http")
            ),
            None,
        ),
    }


def build_sku_index_live() -> list[dict]:
    index: list[dict] = []
    seen: set[str] = set()
    stats_raw: dict[str, int] = {}
    stats_with_sku: dict[str, int] = {}

    for source in STOREFRONTS:
        products = fetch_all_products(source)
        stats_raw[source["id"]] = len(products)
        kept = 0
        for p in products:
            if not is_figure_like(p, source):
                continue
            e = entry_from_product(p, source["id"], source["company"], "first-party")
            if not e or e["id"] in seen:
                continue
            seen.add(e["id"])
            index.append(e)
            kept += 1
        stats_with_sku[source["id"]] = kept
        print(f"sku-index {source['id']}: raw={len(products)} with_sku={kept}")
        time.sleep(0.05)

    for feed in RETAILER_FEEDS:
        products = fetch_retailer_products(feed)
        stats_raw[feed["id"]] = len(products)
        kept = 0
        for p in products:
            company = infer_retailer_company(p)
            if not company:
                continue
            e = entry_from_product(p, feed["id"], company, "retailer")
            if not e or e["id"] in seen:
                continue
            seen.add(e["id"])
            index.append(e)
            kept += 1
        stats_with_sku[feed["id"]] = kept
        print(f"sku-index {feed['id']}: raw={len(products)} with_sku={kept}")
        time.sleep(0.05)

    # Attach build meta on a sentinel? Keep stats separate in caller.
    build_sku_index_live.stats = {"raw": stats_raw, "withSku": stats_with_sku}  # type: ignore[attr-defined]
    return index


def shopify_handle_from_row(row: dict) -> tuple[str | None, str | None]:
    """Parse sf-{shop}-{handle} oneshot ids."""
    rid = str(row.get("id") or "")
    if not rid.startswith("sf-"):
        return None, None
    rest = rid[3:]
    # shop ids may contain hyphens (goodsmile-us, neca-store, shop-dc, store-horsemen, mattel-creations)
    shop_ids = sorted((s["id"] for s in STOREFRONTS), key=len, reverse=True)
    for sid in shop_ids:
        prefix = sid + "-"
        if rest.startswith(prefix):
            return sid, rest[len(prefix) :]
    return None, None


def effective_score(fig: dict, prod: dict) -> float:
    s = score_pair(fig, prod)
    if s < 0:
        return s
    if prod.get("tier") == "first-party" or prod.get("shop") in FIRST_PARTY_SHOPS:
        s += SHOP_TIER_BONUS
    return s


def is_worse_sku(existing: str, candidate: str, cand_prod: dict | None) -> bool:
    """Never overwrite a good SKU with a worse guess.
    Existing shopify/first-party alphanumeric SKUs beat retailer GTIN-as-sku when equal length issues.
    Policy: any existing non-fake SKU is kept (caller shouldn't call overwrite).
    """
    return True  # always treat overwrite as worse — we never replace


def match_skus(rows: list[dict], index: list[dict]) -> tuple[list[tuple[float, dict, dict]], dict]:
    """High-confidence SKU assignment. Returns finals + diagnostics."""
    need = [r for r in rows if not clean_sku(r.get("sku"))]
    # Existing SKUs reserved (one SKU → one figure)
    reserved_skus: set[str] = set()
    for r in rows:
        s = clean_sku(r.get("sku"))
        if s:
            reserved_skus.add(s.upper())

    # Index by shop:handle for exact shopify fills
    by_handle: dict[str, dict] = {}
    by_company: dict[str, list[dict]] = defaultdict(list)
    prepared: list[dict] = []
    for raw in index:
        if not clean_sku(raw.get("sku")):
            continue
        prepared.append(dict(raw))
    enrich_index(prepared)
    for p in prepared:
        by_handle[f"{p['shop']}:{p.get('handle') or ''}"] = p
        by_company[p["company"]].append(p)

    exact_hits: list[tuple[float, dict, dict]] = []
    used_prod_ids: set[str] = set()
    used_skus: set[str] = set(reserved_skus)

    # Pass 1: exact handle match for shopify-sourced archive rows missing SKU
    for fig in need:
        shop, handle = shopify_handle_from_row(fig)
        if not shop or not handle:
            continue
        p = by_handle.get(f"{shop}:{handle}")
        if not p:
            continue
        sku = clean_sku(p.get("sku"))
        if not sku or sku.upper() in used_skus:
            continue
        # Soft score check still — refuse if company mismatch
        if p.get("company") and p["company"] != fig["company"]:
            continue
        exact_hits.append((100.0, fig, p))
        used_prod_ids.add(p["id"])
        used_skus.add(sku.upper())

    exact_ids = {f["id"] for _, f, _ in exact_hits}
    remaining = [r for r in need if r["id"] not in exact_ids]

    # Pass 2: fuzzy high-confidence (same company), prefer best score; 1 SKU → 1 figure
    cands: list[tuple[float, dict, dict]] = []
    for fig in remaining:
        pool = by_company.get(fig["company"]) or []
        best: tuple[float, dict] | None = None
        for p in pool:
            if p["id"] in used_prod_ids:
                continue
            sku = clean_sku(p.get("sku"))
            if not sku or sku.upper() in used_skus:
                continue
            sc = effective_score(fig, p)
            if sc < MIN_SCORE:
                continue
            if best is None or sc > best[0]:
                best = (sc, p)
        if best:
            cands.append((best[0], fig, best[1]))

    # Resolve conflicts: one product / one sku → best figure only
    cands.sort(key=lambda x: x[0], reverse=True)
    finals = list(exact_hits)
    claimed_figs: set[str] = set(exact_ids)
    for sc, fig, p in cands:
        if fig["id"] in claimed_figs:
            continue
        sku = clean_sku(p.get("sku"))
        if not sku or sku.upper() in used_skus:
            continue
        if p["id"] in used_prod_ids:
            continue
        finals.append((sc, fig, p))
        claimed_figs.add(fig["id"])
        used_prod_ids.add(p["id"])
        used_skus.add(sku.upper())

    diag = {
        "need": len(need),
        "exactHandleHits": len(exact_hits),
        "fuzzyCandidates": len(cands),
        "finalAssigned": len(finals),
        "indexWithSku": len(prepared),
    }
    return finals, diag


def apply_assignments(
    rows: list[dict],
    finals: list[tuple[float, dict, dict]],
    dry_run: bool,
) -> tuple[int, dict[str, str]]:
    by_id = {r["id"]: r for r in rows}
    sku_map: dict[str, str] = {}
    # Preserve existing
    for r in rows:
        s = clean_sku(r.get("sku"))
        if s:
            sku_map[r["id"]] = s

    patched = 0
    for sc, fig, p in finals:
        row = by_id.get(fig["id"])
        if not row:
            continue
        existing = clean_sku(row.get("sku"))
        cand = clean_sku(p.get("sku"))
        if not cand:
            continue
        if existing:
            # never overwrite
            continue
        if not dry_run:
            row["sku"] = cand
            barcode = clean_barcode(p.get("barcode")) if p.get("barcode") else clean_barcode(cand)
            # Only set barcode field when it's a real GTIN distinct from display — optional
            if barcode and barcode != cand and not row.get("barcode"):
                # types may not include barcode; skip adding unsupported fields unless already used
                pass
            tags = list(row.get("tags") or [])
            if "sku-bake" not in tags:
                tags.append("sku-bake")
            # provenance shop tag (lightweight)
            shop_tag = f"sku:{p.get('shop')}"
            if shop_tag not in tags and len(tags) < 24:
                tags.append(shop_tag)
            row["tags"] = tags
            # Related product id if supported — store in tags only; don't invent new columns
            if p.get("productId") and not row.get("shopifyProductId"):
                # CatalogFigure may not have shopifyProductId; keep out of row to avoid schema creep
                pass
        sku_map[row["id"]] = cand
        patched += 1
    return patched, sku_map


def main() -> int:
    fetch_live = "--fetch" in sys.argv or "--live" in sys.argv
    use_cache = "--cache-only" in sys.argv
    dry_run = "--dry-run" in sys.argv

    rows = json.loads(ARCHIVE_JSON.read_text())
    before_with = sum(1 for r in rows if clean_sku(r.get("sku")))
    before_total = len(rows)
    before_by_source = Counter(
        (r.get("source") or "none") for r in rows if clean_sku(r.get("sku"))
    )

    index_meta: dict[str, Any] = {}
    if use_cache and INDEX_JSON.exists():
        print(f"=== Using cached SKU index {INDEX_JSON} ===")
        index = json.loads(INDEX_JSON.read_text())
        index_meta["fetchLive"] = False
        index_meta["cache"] = True
    elif fetch_live:
        print("=== Live Shopify + specialty pagination → product SKU index ===")
        index = build_sku_index_live()
        index_meta = getattr(build_sku_index_live, "stats", {})
        index_meta["fetchLive"] = True
        if not dry_run:
            INDEX_JSON.write_text(json.dumps(index, indent=2) + "\n")
            print(f"wrote {INDEX_JSON} ({len(index)} products with sku)")
    else:
        # Prefer dedicated sku index; fall back to rebuilding from image index if it gained skus
        if INDEX_JSON.exists():
            print(f"=== Using existing SKU index (pass --fetch for live) ===")
            index = json.loads(INDEX_JSON.read_text())
        else:
            print("No product-sku-index.json — run with --fetch. Aborting.")
            return 1
        index_meta["fetchLive"] = False

    print(f"index size: {len(index)} | oneshot: {before_total} | with sku before: {before_with}")

    finals, diag = match_skus(rows, index)
    patched, sku_map = apply_assignments(rows, finals, dry_run=dry_run)

    after_with = sum(1 for r in rows if clean_sku(r.get("sku")))
    after_by_source = Counter((r.get("source") or "none") for r in rows if clean_sku(r.get("sku")))
    after_by_shop = Counter()
    for r in rows:
        if not clean_sku(r.get("sku")):
            continue
        for t in r.get("tags") or []:
            if str(t).startswith("sku:"):
                after_by_shop[str(t)[4:]] += 1
                break
        else:
            if r.get("source") == "shopify":
                after_by_shop["shopify-native"] += 1
            else:
                after_by_shop["other"] += 1

    leftovers = [r for r in rows if not clean_sku(r.get("sku"))]
    leftovers_by_co = Counter(r["company"] for r in leftovers)
    leftovers_by_src = Counter(r.get("source") or "none" for r in leftovers)

    stats = {
        "bakedAt": datetime.now(timezone.utc).isoformat(),
        "day": date.today().isoformat(),
        "minScore": MIN_SCORE,
        "indexSize": len(index),
        "indexMeta": index_meta,
        "dryRun": dry_run,
        "before": {
            "total": before_total,
            "withSku": before_with,
            "pct": round(100 * before_with / before_total, 2) if before_total else 0,
            "bySource": dict(before_by_source),
        },
        "after": {
            "total": len(rows),
            "withSku": after_with,
            "pct": round(100 * after_with / len(rows), 2) if rows else 0,
            "bySource": dict(after_by_source),
            "bySkuShopTag": dict(after_by_shop.most_common()),
        },
        "assigned": patched,
        "diagnostics": diag,
        "byCompanyAssigned": dict(Counter(f["company"] for _, f, _ in finals).most_common()),
        "byShopAssigned": dict(Counter(p.get("shop") for _, _, p in finals).most_common()),
        "leftovers": {
            "count": len(leftovers),
            "pct": round(100 * len(leftovers) / len(rows), 2) if rows else 0,
            "byCompany": dict(leftovers_by_co.most_common(25)),
            "bySource": dict(leftovers_by_src.most_common(20)),
            "honestGaps": [
                "Hasbro Pulse / BBTS / Entertainment Earth — no stable public products.json",
                "Mezco official / Hot Toys / Sideshow / Bandai Tamashii US / MAFEX first-party / threezero / Takara Tomy mall — blocked or unverified",
                "Densify / BBTS-wave curated placeholders without a clear specialty-retailer title cue stay SKU-less",
                "JLU / DCUC blocked families (no honest feed line)",
                "Bundle/multipack Shopify rows with null variant.sku stay empty (no invented codes)",
            ],
        },
        "safeguards": [
            "never overwrite an existing non-fake SKU",
            "same-company hard gate via score_pair",
            "minScore 18 (stricter than image bake)",
            "one SKU → at most one figure id",
            "one product index id → at most one figure",
            "exact sf-{shop}-{handle} match preferred for native Shopify rows",
            "first-party shop score bonus over specialty retailers",
            "barcode used as sku only when variant.sku empty and GTIN length valid",
            "no AI art; no catalog row expansion beyond sku (+ sku-bake tags)",
        ],
        "samples": [
            {
                "score": round(s, 2),
                "figureId": f["id"],
                "figure": f"{f['name']} / {f.get('subtitle')} / {f.get('line')}",
                "product": f"{p.get('title') or p.get('name')}",
                "sku": p.get("sku"),
                "shop": p.get("shop"),
                "tier": p.get("tier"),
            }
            for s, f, p in finals[:15]
        ],
    }

    if not dry_run:
        ARCHIVE_JSON.write_text(json.dumps(rows, indent=2) + "\n")
        SKU_MAP_JSON.write_text(json.dumps(sku_map, indent=2, sort_keys=True) + "\n")
        STATS_JSON.write_text(json.dumps(stats, indent=2) + "\n")
        # Refresh oneshot-stats sku coverage hint
        try:
            ost = json.loads((ROOT / "src/data/figure-archive/oneshot-stats.json").read_text())
            ost["withSku"] = after_with
            ost["skuCoveragePct"] = round(100 * after_with / len(rows), 2) if rows else 0
            ost["skuBakedAt"] = stats["bakedAt"]
            (ROOT / "src/data/figure-archive/oneshot-stats.json").write_text(
                json.dumps(ost, indent=2) + "\n"
            )
        except Exception as e:
            print(f"oneshot-stats update skipped: {e}")

    print(
        json.dumps(
            {
                "before": stats["before"],
                "after": stats["after"],
                "assigned": patched,
                "diagnostics": diag,
                "leftovers": stats["leftovers"]["count"],
                "topLeftoverCompanies": stats["leftovers"]["byCompany"],
            },
            indent=2,
        )
    )
    if dry_run:
        print("(dry-run — no files written)")
    else:
        print(f"wrote {SKU_MAP_JSON} ({len(sku_map)} entries)")
        print(f"patched oneshot sku on {patched} rows")
        print(f"wrote {STATS_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
