#!/usr/bin/env python3
"""Backfill UPC/ISBN from IDW Publishing Shopify storefront products.json.

Public products.json exposes variant.sku values that are real UPC/ISBN digits for
many singles and collections. Never invents codes. Never overwrites an existing UPC
in comic-upc-map.json (LOCG wins unless --force).

Polite pacing between page fetches (~0.4s). Much faster than LOCG crawl-delay.

Examples:
  python3 scripts/backfill-comic-upcs-idw-shop.py
  python3 scripts/backfill-comic-upcs-idw-shop.py --max-pages 20 --delay 0.4
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
UPC_MAP = ROOT / "src/data/comic-upc-map.json"
COVER_URLS = ROOT / "src/data/comic-cover-urls.json"
COMICS_TS = ROOT / "src/data/comics.ts"
STATS = ROOT / "scripts/comic-upc-idw-shop-stats.json"
CACHE = ROOT / "scripts/comic-idw-shop-cache.json"

UA = (
    "KryptonsToyVault/1.0 (personal collection; idw upc backfill; "
    "+https://github.com/MonacoCobra/kryptons-toy-vault)"
)
SHOP = "https://www.idwpublishing.com/products.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_upc(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if 11 <= len(digits) <= 18:
        return digits
    return None


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def parse_comics_meta() -> dict[str, dict]:
    text = COMICS_TS.read_text()
    pat = re.compile(
        r'\["([^"]+)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*'
        r'"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*([0-9.]+),\s*"([^"]+)",\s*'
        r'([0-9.]+),\s*([0-9]+),\s*"([^"]*)"',
        re.M,
    )
    out: dict[str, dict] = {}
    for m in pat.finditer(text):
        cid = m.group(1)
        rest = text[m.end() : m.end() + 400]
        upc = None
        variant = None
        em = re.search(r"\{([^}]*)\}\s*\]", rest)
        if em and "upc" in em.group(1):
            um = re.search(r'upc:\s*"([^"]+)"', em.group(1))
            if um:
                upc = um.group(1)
        if em and "variant" in em.group(1):
            vm = re.search(r'variant:\s*"([^"]+)"', em.group(1))
            if vm:
                variant = vm.group(1)
        out[cid] = {
            "series": m.group(2),
            "issue": m.group(3),
            "publisher": m.group(4),
            "coverDate": m.group(5),
            "format": m.group(10),
            "upc": upc,
            "variant": variant,
        }
    return out


def series_norm(s: str) -> str:
    s = re.sub(r"\s*\([^)]*\)\s*", " ", s)
    s = s.lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # drop leading the
    if s.startswith("the "):
        s = s[4:]
    return s


def is_exclusive_or_variant(title: str) -> bool:
    t = title.lower()
    return bool(
        re.search(
            r"\b(exclusive|foil|variant|virgin|incentive|convention|sdcc|nycc|cgc)\b",
            t,
        )
    )


def is_collected(title: str) -> bool:
    t = title.lower()
    return bool(
        re.search(
            r"\b(tp|tpb|hardcover|hc|omnibus|compendium|deluxe|art book|poster|collection|vol\.?)\b",
            t,
        )
    ) and not re.search(r"#\s*\d+", title)


def parse_shop_title(title: str) -> dict | None:
    """Extract series + issue from IDW product title."""
    t = title.strip()
    # "Series Name #12 - something"
    m = re.match(r"^(.*?)\s+#\s*([0-9]+[A-Za-z]?)\b(.*)$", t)
    if not m:
        return None
    series = m.group(1).strip()
    issue = m.group(2)
    rest = m.group(3) or ""
    return {
        "series": series,
        "issue": issue,
        "rest": rest,
        "variantish": is_exclusive_or_variant(t),
        "collected": is_collected(t),
    }


def fetch_page(page: int, limit: int = 250) -> list[dict]:
    url = f"{SHOP}?limit={limit}&page={page}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as res:
        data = json.loads(res.read().decode("utf-8", "ignore"))
    return data.get("products") or []


def harvest(max_pages: int, delay: float, use_cache: bool) -> list[dict]:
    if use_cache and CACHE.exists():
        cached = json.loads(CACHE.read_text())
        if cached.get("products") and cached.get("fetchedAt"):
            print(f"using cache {CACHE} ({len(cached['products'])} products)")
            return cached["products"]
    products: list[dict] = []
    for page in range(1, max_pages + 1):
        time.sleep(delay if page > 1 else 0)
        try:
            batch = fetch_page(page)
        except Exception as e:
            print(f"page {page} error: {e}", file=sys.stderr)
            break
        if not batch:
            print(f"page {page}: empty — done")
            break
        products.extend(batch)
        print(f"page {page}: +{len(batch)} (total {len(products)})")
    save_json(CACHE, {"fetchedAt": now_iso(), "products": products})
    return products


def index_products(products: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """Map (series_norm, issue) → list of {upc, title, handle, image, variantish}."""
    idx: dict[tuple[str, str], list[dict]] = {}
    for p in products:
        title = p.get("title") or ""
        parsed = parse_shop_title(title)
        if not parsed or parsed["collected"]:
            # Still try ISBN from sku for collections — skip for singles map
            continue
        code = None
        for v in p.get("variants") or []:
            code = normalize_upc(v.get("sku") or v.get("barcode"))
            if code:
                break
        if not code:
            continue
        img = None
        images = p.get("images") or []
        if images:
            img = images[0].get("src")
        key = (series_norm(parsed["series"]), str(parsed["issue"]).lstrip("0") or "0")
        # also keep raw issue key
        key2 = (series_norm(parsed["series"]), str(parsed["issue"]))
        rec = {
            "upc": code,
            "title": title,
            "handle": p.get("handle"),
            "image": img,
            "variantish": parsed["variantish"],
            "url": f"https://www.idwpublishing.com/products/{p.get('handle')}",
        }
        idx.setdefault(key, []).append(rec)
        if key2 != key:
            idx.setdefault(key2, []).append(rec)
    return idx


def pick_best(recs: list[dict]) -> dict | None:
    if not recs:
        return None
    mains = [r for r in recs if not r.get("variantish")]
    pool = mains or recs
    # Prefer longer UPC (full comic UPC often 17 digits)
    pool = sorted(pool, key=lambda r: (-len(r.get("upc") or ""), r.get("title") or ""))
    return pool[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-pages", type=int, default=30)
    ap.add_argument("--delay", type=float, default=0.4)
    ap.add_argument("--refresh", action="store_true", help="Ignore shop cache and re-harvest")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    upc_map = load_json(UPC_MAP, {})
    cover_urls = load_json(COVER_URLS, {})
    meta = parse_comics_meta()
    before_upc = len([1 for v in upc_map.values() if v.get("upc")])

    products = harvest(args.max_pages, args.delay, use_cache=not args.refresh)
    idx = index_products(products)
    print(f"indexed issue keys: {len(idx)}")

    # IDW catalog candidates
    filled = 0
    matched = 0
    skipped = 0
    details = []
    for cid, m in meta.items():
        pub = m.get("publisher") or ""
        if "IDW" not in pub:
            continue
        if (m.get("format") or "single") not in ("single", "one-shot", "annual", "giant"):
            continue
        if m.get("variant") and not args.force:
            continue
        existing = upc_map.get(cid) or {}
        if existing.get("upc") and not args.force:
            skipped += 1
            continue
        if m.get("upc") and not args.force:
            skipped += 1
            continue

        sn = series_norm(m.get("series") or "")
        iss = str(m.get("issue") or "").lstrip("#")
        iss_alt = iss.lstrip("0") or "0"
        recs = idx.get((sn, iss)) or idx.get((sn, iss_alt)) or []
        # soft: try without subtitle after colon
        if not recs and ":" in (m.get("series") or ""):
            sn2 = series_norm((m.get("series") or "").split(":")[0])
            recs = idx.get((sn2, iss)) or idx.get((sn2, iss_alt)) or []
        # For primary catalog rows (no variant), only accept non-exclusive shop SKUs
        if not m.get("variant"):
            recs = [r for r in recs if not r.get("variantish")]
        best = pick_best(recs)
        if not best:
            continue
        # Singles should not get ISBN-13 book codes from HC/TP exclusives
        code = best.get("upc") or ""
        if (m.get("format") or "single") in ("single", "one-shot", "annual", "giant"):
            if code.startswith("978") or code.startswith("979"):
                continue
            if re.search(r"\b(hardcover|hc|tpb|\btp\b|omnibus)\b", best.get("title") or "", re.I):
                continue
        matched += 1
        # Don't overwrite LOCG UPC
        if existing.get("upc") and not args.force:
            skipped += 1
            continue
        filled += 1
        if args.dry_run:
            print(f"DRY {cid}: {best['upc']} ← {best['title']}")
            continue
        entry = dict(existing)
        src = "idw-shopify"
        if existing.get("locgId"):
            src = "locg+idw-shopify"
        entry.update(
            {
                "upc": best["upc"],
                "source": src,
                "title": best.get("title"),
                "url": best.get("url"),
                "fetchedAt": now_iso(),
            }
        )
        # Prefer LOCG covers; only set shop image if no cover yet
        if best.get("image") and not entry.get("coverUrl") and cid not in cover_urls:
            entry["coverUrl"] = best["image"]
            cover_urls[cid] = best["image"]
        upc_map[cid] = {k: v for k, v in entry.items() if v}
        details.append({"id": cid, "upc": best["upc"], "title": best["title"]})
        print(f"✓ {cid}: upc={best['upc']} {best['title']}")

    if not args.dry_run:
        # Merge-safe: re-read disk maps so a concurrent LOCG run cannot be clobbered
        disk_upc = load_json(UPC_MAP, {})
        for cid, ent in upc_map.items():
            cur = dict(disk_upc.get(cid) or {})
            if cur.get("upc") and ent.get("upc") and cur.get("upc") != ent.get("upc"):
                if "locg" in str(cur.get("source") or ""):
                    continue  # never overwrite LOCG UPC
            if cur.get("upc") and not ent.get("upc"):
                continue
            merged = {**cur, **{k: v for k, v in ent.items() if v is not None}}
            # If disk already had upc from locg, keep it
            if cur.get("upc") and "locg" in str(cur.get("source") or ""):
                merged["upc"] = cur["upc"]
                merged["source"] = cur.get("source")
                if cur.get("locgId"):
                    merged["locgId"] = cur["locgId"]
            disk_upc[cid] = merged
        disk_covers = load_json(COVER_URLS, {})
        for cid, url in cover_urls.items():
            if not url:
                continue
            ex = disk_covers.get(cid)
            if ex and "comicgeeks" in str(ex) and "comicgeeks" not in str(url):
                continue
            disk_covers[cid] = url
        save_json(UPC_MAP, disk_upc)
        save_json(COVER_URLS, disk_covers)
        upc_map = disk_upc
        cover_urls = disk_covers
    after = len([1 for v in upc_map.values() if v.get("upc")])
    stats = {
        "startedAt": now_iso(),
        "finishedAt": now_iso(),
        "beforeUpc": before_upc,
        "afterUpc": after,
        "matched": matched,
        "upcFilled": filled,
        "skippedExisting": skipped,
        "shopProducts": len(products),
        "indexKeys": len(idx),
        "details": details[:100],
    }
    save_json(STATS, stats)
    print(json.dumps({k: stats[k] for k in stats if k != "details"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
