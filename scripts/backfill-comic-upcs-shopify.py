#!/usr/bin/env python3
"""Backfill comic UPC/ISBN from retailer/publisher Shopify products.json feeds.

Faster than LOCG (no 30s crawl-delay). Never invents codes. Never overwrites a
LOCG (or other existing) UPC. Prefer Cover A / MAIN / unspecified-main rows.

Default source: www.thecomicbookstore.com /collections/comics (real UPC SKUs).
Also supports IDW / Fantagraphics / Austin Books style shops via --shops.

Matching gates:
  - series token overlap
  - issue number equality
  - publisher/vendor family match
  - cover year within ±1 when both known (avoids reboot collisions)
  - skip merch / posters / foil exclusives / incentives for primary catalog rows

Examples:
  python3 scripts/backfill-comic-upcs-shopify.py
  python3 scripts/backfill-comic-upcs-shopify.py --refresh --max-pages 40
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
UPC_MAP = ROOT / "src/data/comic-upc-map.json"
COVER_URLS = ROOT / "src/data/comic-cover-urls.json"
COMICS_TS = ROOT / "src/data/comics.ts"
STATS = ROOT / "scripts/comic-upc-shopify-stats.json"
CACHE_DIR = ROOT / "scripts/shopify-upc-cache"

UA = (
    "KryptonsToyVault/1.0 (personal collection; shopify upc backfill; "
    "+https://github.com/MonacoCobra/kryptons-toy-vault)"
)

# shop_key -> list of products.json bases to try (first that works wins)
SHOPS = {
    "thecomicbookstore": [
        "https://www.thecomicbookstore.com/collections/comics/products.json",
        "https://www.thecomicbookstore.com/products.json",
    ],
    "idw": ["https://www.idwpublishing.com/products.json"],
    "fantagraphics": ["https://www.fantagraphics.com/products.json"],
    "austinbooks": ["https://www.austinbooks.com/products.json"],
    "boom": ["https://shop.boom-studios.com/products.json"],
}

VENDOR_TO_PUB = {
    "marvel": ["marvel comics", "marvel"],
    "dc comics": ["dc comics", "dc", "dc comics / vertigo", "dc comics / black label", "dc comics / wildstorm"],
    "image comics": ["image comics", "image", "skybound / image"],
    "boom entertainment": ["boom! studios", "boom studios", "boom"],
    "boom! studios": ["boom! studios", "boom studios", "boom"],
    "idw publishing": ["idw publishing", "idw"],
    "dark horse comics": ["dark horse", "dark horse comics"],
    "dynamite entertainment": ["dynamite entertainment", "dynamite"],
    "oni press": ["oni press", "oni"],
    "fantagraphics": ["fantagraphics", "fantagraphics books"],
    "valiant": ["valiant", "valiant entertainment"],
    "skybound": ["skybound / image", "image comics"],
    "titan comics": ["titan comics", "titan"],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_upc(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("111111"):
        return None
    if 12 <= len(digits) <= 18:
        return digits
    # some older 11-digit
    if len(digits) == 11:
        return digits
    return None


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s.startswith("the "):
        s = s[4:]
    return s


def pub_norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def publisher_compatible(catalog_pub: str, vendor: str) -> bool:
    cp = pub_norm(catalog_pub)
    vn = pub_norm(vendor)
    if not vn:
        return True  # unknown vendor — allow but score lower
    if cp == vn or cp in vn or vn in cp:
        return True
    aliases = VENDOR_TO_PUB.get(vn) or VENDOR_TO_PUB.get(vendor.lower()) or []
    for a in aliases:
        an = pub_norm(a)
        if an == cp or an in cp or cp in an:
            return True
    # soft: shared token marvel/dc/image/idw/boom
    for token in ("marvel", "dc", "image", "idw", "boom", "dark horse", "dynamite", "oni", "valiant"):
        if token in cp and token in vn:
            return True
    return False


def is_merch(title: str, ptype: str, tags) -> bool:
    tag_s = ",".join(tags) if isinstance(tags, list) else str(tags or "")
    blob = f"{title} {ptype} {tag_s}".lower()
    return bool(
        re.search(
            r"\b(poster|t-?shirt|shirt|hoodie|mug|statue|figure|plush|pin|hat|vinyl|die-?cast|apparel)\b",
            blob,
        )
    )


def is_variantish(title: str, rest: str = "") -> bool:
    blob = f"{title} {rest}".lower()
    if re.search(r"\bcover\s*a\b|\bmain cover\b|\bcover a\s*-?\s*main\b", blob):
        return False
    return bool(
        re.search(
            r"\b(cover\s*[b-z0-9]|variant|exclusive|incentive|foil|virgin|1:\d+|incv|sketch)\b",
            blob,
        )
    )


def parse_title(title: str) -> dict | None:
    t = title.strip()
    m = re.search(r"^(.*?)\s+#\s*([0-9]+(?:\.[0-9]+)?)\b(.*)$", t, re.I)
    if not m:
        m = re.search(r"^(.*?),\s*ISSUE\s*#?\s*([0-9]+)\b(.*)$", t, re.I)
    if not m:
        return None
    series = m.group(1).strip(" -—,")
    issue = m.group(2)
    rest = m.group(3) or ""
    # year in title e.g. (2026)
    ym = re.search(r"\((19|20)\d{2}\)", title)
    year = int(ym.group(0)[1:5]) if ym else None
    return {
        "series": series,
        "issue": issue,
        "rest": rest,
        "year": year,
        "variantish": is_variantish(title, rest),
    }


def extract_code(product: dict) -> str | None:
    for v in product.get("variants") or []:
        for field in ("barcode", "sku"):
            code = normalize_upc(v.get(field))
            if code and not (code.startswith("978") or code.startswith("979")):
                return code
        # ISBN only as last resort for collections — skip here for singles
    return None


def fetch_products(base: str, max_pages: int, delay: float) -> list[dict]:
    out: list[dict] = []
    for page in range(1, max_pages + 1):
        url = f"{base}?limit=250&page={page}" if "?" not in base else f"{base}&limit=250&page={page}"
        # fix double limit
        if base.endswith("products.json"):
            url = f"{base}?limit=250&page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as res:
                data = json.loads(res.read().decode("utf-8", "ignore"))
        except Exception as e:
            print(f"  fetch error {url}: {e}", file=sys.stderr)
            break
        prods = data.get("products") or []
        if not prods:
            break
        out.extend(prods)
        print(f"  {base.split('/')[2]} page {page}: +{len(prods)} (total {len(out)})")
        time.sleep(delay)
    return out


def index_products(products: list[dict], shop: str) -> dict[tuple[str, str], list[dict]]:
    idx: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for p in products:
        title = p.get("title") or ""
        ptype = p.get("product_type") or ""
        tags = p.get("tags") or []
        if is_merch(title, ptype, tags):
            continue
        if ptype and ptype.lower() not in ("", "comics", "comic", "comic books", "single issues"):
            # allow empty; skip graphic novels unless has #
            if ptype.lower() in ("graphic novels", "manga", "books") and not re.search(r"#\s*\d+", title):
                continue
        parsed = parse_title(title)
        if not parsed:
            continue
        if parsed["variantish"]:
            continue  # primary catalog only in this pass
        code = extract_code(p)
        if not code:
            continue
        img = None
        images = p.get("images") or []
        if images:
            img = images[0].get("src")
        iss = parsed["issue"]
        iss_key = str(int(float(iss))) if re.match(r"^\d", iss) else iss
        rec = {
            "upc": code,
            "title": title,
            "series": parsed["series"],
            "issue": iss_key,
            "year": parsed["year"],
            "vendor": p.get("vendor") or "",
            "handle": p.get("handle"),
            "image": img,
            "shop": shop,
            "url": f"https://{shop if '.' in shop else 'www.thecomicbookstore.com'}/products/{p.get('handle')}",
        }
        # fix url host for known shops
        if shop == "thecomicbookstore":
            rec["url"] = f"https://www.thecomicbookstore.com/products/{p.get('handle')}"
        elif shop == "idw":
            rec["url"] = f"https://www.idwpublishing.com/products/{p.get('handle')}"
        elif shop == "fantagraphics":
            rec["url"] = f"https://www.fantagraphics.com/products/{p.get('handle')}"
        elif shop == "austinbooks":
            rec["url"] = f"https://www.austinbooks.com/products/{p.get('handle')}"
        elif shop == "boom":
            rec["url"] = f"https://shop.boom-studios.com/products/{p.get('handle')}"
        key = (series_norm(parsed["series"]), iss_key)
        idx[key].append(rec)
    return idx


def year_ok(catalog_year: int | None, shop_year: int | None) -> bool:
    if not catalog_year or not shop_year:
        return True  # can't verify — allow but we'll prefer year matches in scoring
    return abs(catalog_year - shop_year) <= 1


def score_rec(rec: dict, catalog_pub: str, catalog_year: int | None) -> int:
    s = 0
    if publisher_compatible(catalog_pub, rec.get("vendor") or ""):
        s += 10
    else:
        return -100
    if catalog_year and rec.get("year"):
        if abs(catalog_year - rec["year"]) == 0:
            s += 8
        elif abs(catalog_year - rec["year"]) == 1:
            s += 3
        else:
            return -100
    elif catalog_year and not rec.get("year"):
        # Prefer shop titles that include year when catalog is modern reboot-prone
        if catalog_year >= 2015:
            s -= 2
    # Prefer longer UPC (comic UPC often 17 digits)
    s += min(len(rec.get("upc") or ""), 17) // 3
    return s


def merge_save(upc_map_local: dict, cover_local: dict) -> tuple[dict, dict]:
    disk_upc = load_json(UPC_MAP, {})
    for cid, ent in upc_map_local.items():
        cur = dict(disk_upc.get(cid) or {})
        if cur.get("upc") and "locg" in str(cur.get("source") or ""):
            # keep LOCG upc; may still add shop url note? no — leave alone
            continue
        if cur.get("upc") and not ent.get("upc"):
            continue
        if cur.get("upc") and ent.get("upc") and cur.get("upc") != ent.get("upc"):
            # keep existing non-empty rather than replace blindly
            continue
        disk_upc[cid] = {**cur, **{k: v for k, v in ent.items() if v is not None}}
    disk_covers = load_json(COVER_URLS, {})
    for cid, url in cover_local.items():
        if not url:
            continue
        ex = disk_covers.get(cid)
        if ex and "comicgeeks" in str(ex) and "comicgeeks" not in str(url):
            continue
        if cid not in disk_covers:
            disk_covers[cid] = url
    save_json(UPC_MAP, disk_upc)
    save_json(COVER_URLS, disk_covers)
    return disk_upc, disk_covers


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shops", type=str, default="thecomicbookstore", help="Comma list of shop keys")
    ap.add_argument("--max-pages", type=int, default=40)
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-year", type=int, default=0, help="Only fill catalog rows with cover year >= this")
    args = ap.parse_args()

    meta = parse_comics_meta()
    upc_map = load_json(UPC_MAP, {})
    cover_urls = load_json(COVER_URLS, {})
    before = len([1 for v in upc_map.values() if v.get("upc")])

    shop_keys = [s.strip() for s in args.shops.split(",") if s.strip()]
    combined_idx: dict[tuple[str, str], list[dict]] = defaultdict(list)
    harvested = 0

    for shop in shop_keys:
        bases = SHOPS.get(shop)
        if not bases:
            print(f"unknown shop key {shop}", file=sys.stderr)
            continue
        cache_path = CACHE_DIR / f"{shop}.json"
        products = None
        if cache_path.exists() and not args.refresh:
            cached = json.loads(cache_path.read_text())
            products = cached.get("products") or []
            print(f"{shop}: using cache ({len(products)} products)")
        else:
            products = []
            for base in bases:
                print(f"{shop}: harvesting {base}")
                products = fetch_products(base, args.max_pages, args.delay)
                if products:
                    break
            save_json(cache_path, {"fetchedAt": now_iso(), "products": products, "base": bases[0]})
        harvested += len(products)
        idx = index_products(products, shop)
        print(f"{shop}: indexed keys={len(idx)}")
        for k, recs in idx.items():
            combined_idx[k].extend(recs)

    filled = 0
    matched = 0
    skipped = 0
    rejected_year = 0
    rejected_pub = 0
    details = []
    local_upc: dict = {}
    local_covers: dict = {}

    for cid, m in meta.items():
        if (m.get("format") or "single") not in ("single", "one-shot", "annual", "giant"):
            continue
        if m.get("variant"):
            continue
        if cid.endswith("-fac") or m.get("format") == "facsimile":
            continue
        existing = upc_map.get(cid) or {}
        if existing.get("upc") or m.get("upc"):
            skipped += 1
            continue
        d = m.get("coverDate") or ""
        cy = int(d[:4]) if d[:4].isdigit() else None
        if args.min_year and cy and cy < args.min_year:
            continue

        sn = series_norm(m.get("series") or "")
        iss = str(m.get("issue") or "").lstrip("#")
        iss_key = str(int(float(iss))) if re.match(r"^\d", iss) else iss
        recs = list(combined_idx.get((sn, iss_key)) or [])
        if not recs:
            continue

        scored = []
        for r in recs:
            shop_title = r.get("title") or ""
            if re.search(r"\bfacsimile\b", shop_title, re.I) and not (
                (m.get("format") or "").lower() == "facsimile" or cid.endswith("-fac")
            ):
                continue
            # Require shop series_norm ~= catalog series_norm (already keyed), plus token coverage
            shop_sn = series_norm(r.get("series") or "")
            if shop_sn != sn:
                # allow only if catalog series is exact prefix/suffix with high token overlap
                wt = {x for x in sn.split() if len(x) > 2 and x not in {"the", "and"}}
                gt = set(shop_sn.split())
                if not wt or len(wt & gt) < len(wt):
                    continue
            if not publisher_compatible(m.get("publisher") or "", r.get("vendor") or ""):
                rejected_pub += 1
                continue
            if not year_ok(cy, r.get("year")):
                rejected_year += 1
                continue
            # Modern shop inventory rarely carries correct UPCs for pre-2005 floppies unless year stamped
            if cy and cy < 2005 and not r.get("year"):
                rejected_year += 1
                continue
            sc = score_rec(r, m.get("publisher") or "", cy)
            if sc < 0:
                continue
            scored.append((sc, r))
        if not scored:
            continue
        scored.sort(key=lambda x: -x[0])
        best = scored[0][1]
        # Extra collision guard: if multiple catalog eras share series+# and shop has no year,
        # only accept when catalog year is missing OR score uniquely high with vendor+length
        same_family = [
            x
            for x, mm in meta.items()
            if series_norm(mm.get("series") or "") == sn
            and (
                str(int(float(str(mm.get("issue") or "").lstrip("#")))) 
                if re.match(r"^\d", str(mm.get("issue") or "").lstrip("#") or "x")
                else str(mm.get("issue") or "").lstrip("#")
            )
            == iss_key
        ]
        if len(same_family) > 1 and not best.get("year"):
            # ambiguous reboot / multi-volume — skip rather than assign wrong era UPC
            continue

        matched += 1
        filled += 1
        entry = {
            "upc": best["upc"],
            "source": f"shopify:{best['shop']}",
            "title": best.get("title"),
            "url": best.get("url"),
            "fetchedAt": now_iso(),
        }
        local_upc[cid] = entry
        if best.get("image") and cid not in cover_urls:
            local_covers[cid] = best["image"]
        details.append({"id": cid, "upc": best["upc"], "title": best.get("title"), "shop": best["shop"]})
        print(f"✓ {cid}: upc={best['upc']} [{best['shop']}] {best.get('title')}")

    if not args.dry_run and local_upc:
        upc_map, cover_urls = merge_save(local_upc, local_covers)
    after = len([1 for v in upc_map.values() if v.get("upc")])
    stats = {
        "startedAt": now_iso(),
        "finishedAt": now_iso(),
        "beforeUpc": before,
        "afterUpc": after,
        "upcFilled": filled,
        "matched": matched,
        "skippedExisting": skipped,
        "rejectedYear": rejected_year,
        "rejectedPublisher": rejected_pub,
        "harvestedProducts": harvested,
        "indexKeys": len(combined_idx),
        "shops": shop_keys,
        "details": details[:150],
    }
    save_json(STATS, stats)
    print(json.dumps({k: stats[k] for k in stats if k != "details"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
