#!/usr/bin/env python3
"""Ingest NEW verified comic rows from Shopify products.json (real UPCs).

Unlike backfill-comic-upcs-shopify.py (enrich only), this creates NEW comics.ts rows.

  python3 scripts/ingest-comics-from-shopify.py --dry-run
  python3 scripts/ingest-comics-from-shopify.py --refresh --inject
"""
from __future__ import annotations
import argparse, json, re, sys, time, urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
sys.path.insert(0, str(ROOT / "scripts"))
from comic_backlog_common import FLOOR, BACKLOG, inject_batch, load_live_blocklists  # noqa: E402

UPC_MAP = ROOT / "src/data/comic-upc-map.json"
COVER_URLS = ROOT / "src/data/comic-cover-urls.json"
CACHE_DIR = ROOT / "scripts/shopify-upc-cache"
STATS = ROOT / "scripts/comic-shopify-ingest-stats.json"
STATE = ROOT / "scripts/comic-shopify-ingest-state.json"
UA = "KryptonsToyVault/1.0 (personal collection; shopify catalog ingest; +https://github.com/MonacoCobra/kryptons-toy-vault)"

SHOPS = {
    "thecomicbookstore": ["https://www.thecomicbookstore.com/collections/comics/products.json", "https://www.thecomicbookstore.com/products.json"],
    "idw": ["https://www.idwpublishing.com/products.json"],
    "fantagraphics": ["https://www.fantagraphics.com/products.json"],
    "austinbooks": ["https://www.austinbooks.com/products.json"],
    "boom": ["https://shop.boom-studios.com/products.json"],
    "ignition": ["https://ignitionpress.com/products.json"],
}
VENDOR_PUB = {
    "image comics": ("Image Comics", "im", "f97316,1c1917,fafaf9"),
    "image": ("Image Comics", "im", "f97316,1c1917,fafaf9"),
    "skybound": ("Image Comics", "im", "f97316,1c1917,fafaf9"),
    "boom! studios": ("Boom! Studios", "boom", "7f1d1d,1e293b,f8fafc"),
    "boom studios": ("Boom! Studios", "boom", "7f1d1d,1e293b,f8fafc"),
    "boom entertainment": ("Boom! Studios", "boom", "7f1d1d,1e293b,f8fafc"),
    "idw publishing": ("IDW Publishing", "idw", "0ea5e9,0f172a,f8fafc"),
    "idw": ("IDW Publishing", "idw", "0ea5e9,0f172a,f8fafc"),
    "fantagraphics": ("Fantagraphics", "fan", "171717,f5f5f4,a3a3a3"),
    "fantagraphics books": ("Fantagraphics", "fan", "171717,f5f5f4,a3a3a3"),
    "dark horse comics": ("Dark Horse", "dh", "7c2d12,1c1917,fafaf9"),
    "dark horse": ("Dark Horse", "dh", "7c2d12,1c1917,fafaf9"),
    "dynamite entertainment": ("Dynamite", "dyn", "b91c1c,111827,f8fafc"),
    "dynamite": ("Dynamite", "dyn", "b91c1c,111827,f8fafc"),
    "oni press": ("Oni Press", "oni", "7c3aed,1e1b4b,faf5ff"),
    "valiant": ("Valiant", "val", "1d4ed8,0f172a,eff6ff"),
    "valiant entertainment": ("Valiant", "val", "1d4ed8,0f172a,eff6ff"),
    "archie comics": ("Archie Comics", "arch", "dc2626,fef2f2,1e293b"),
    "archie comics publications": ("Archie Comics", "arch", "dc2626,fef2f2,1e293b"),
    "vault comics": ("Vault Comics", "vault", "312e81,e0e7ff,0f172a"),
    "aftershock comics": ("AfterShock", "as", "334155,f8fafc,0f172a"),
    "ablaze": ("Ablaze", "abl", "9a3412,fff7ed,1c1917"),
    "scout comics": ("Scout", "scout", "065f46,ecfdf5,022c22"),
    "mad cave studios": ("Mad Cave", "mc", "1e3a8a,dbeafe,0f172a"),
    "dstlry": ("DSTLRY", "dst", "4c1d95,f5f3ff,0f172a"),
    "ignition press": ("Ignition Press", "ign", "ea580c,fff7ed,1c1917"),
    "bad idea": ("Bad Idea", "bi", "111827,f8fafc,ef4444"),
    "titan comics": ("Titan Comics", "titan", "0f766e,ccfbf1,042f2e"),
    "alien books": ("Alien Books", "alien", "3f6212,ecfccb,1a2e05"),
    "antarctic press": ("Antarctic Press", "ap", "0369a1,e0f2fe,0c4a6e"),
}
BIG_TWO = {"marvel", "marvel comics", "dc", "dc comics"}

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def load_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default
def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
def normalize_upc(raw):
    if not raw: return None
    digits = re.sub(r"\D", "", str(raw))
    if digits.startswith("111111") or digits.startswith("978") or digits.startswith("979"): return None
    return digits if 11 <= len(digits) <= 18 else None
def series_norm(s):
    s = re.sub(r"\s*\([^)]*\)\s*", " ", s or "")
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[4:] if s.startswith("the ") else s
def pub_norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()
def pub_family(a, b):
    if a == b or a in b or b in a: return True
    for t in ("image","boom","idw","dark horse","fantagraphics","dynamite","oni","valiant","archie","vault","mad cave","dstlry","skybound","ignition","titan"):
        if t in a and t in b: return True
    return False
def is_merch(title, ptype, tags):
    tag_s = ",".join(tags) if isinstance(tags, list) else str(tags or "")
    return bool(re.search(r"\b(poster|t-?shirt|shirt|hoodie|mug|statue|figure|plush|pin|hat|vinyl|die-?cast|apparel)\b", f"{title} {ptype} {tag_s}".lower()))
def is_collected(title, ptype):
    if re.search(r"#\s*\d+", title): return False
    return bool(re.search(r"\b(tpb|trade paperback|hardcover|omnibus|compendium|graphic novel|manga|vol\.?\s*\d+)\b", f"{title} {ptype}".lower()))
def is_cover_a_or_main(title):
    t = title.lower()
    if re.search(r"\b(cover\s*a|cvr\s*a|main cover|\ba\s+main\b|\bmain\b)", t):
        if re.search(r"\b(cover\s*[b-z]|cvr\s*[b-z]|1:\d+|incv)\b", t): return False
        return True
    if re.search(r"\b(cover\s*[b-z]|cvr\s*[b-z]|variant|exclusive|incentive|foil|virgin|1:\d+|incv|sketch)\b", t):
        return False
    return True
def parse_title(title):
    t = title.strip()
    m = re.search(r"^(.*?)\s+#\s*([0-9]+(?:\.[0-9]+)?)\b(.*)$", t, re.I)
    if not m: m = re.search(r"^(.*?),\s*ISSUE\s*#?\s*([0-9]+)\b(.*)$", t, re.I)
    if not m: return None
    series = re.sub(r"\s*\((?i:cvr|cover)\s*[a-z0-9].*$", "", m.group(1).strip(" -—,")).strip()
    ym = re.search(r"\((19|20)\d{2}\)", title)
    year = int(ym.group(0)[1:5]) if ym else None
    return {"series": series, "issue": m.group(2), "rest": m.group(3) or "", "year": year}
def extract_code(product):
    for v in product.get("variants") or []:
        for field in ("barcode", "sku"):
            code = normalize_upc(v.get(field))
            if code: return code
    return None
def fetch_products(base, max_pages, delay):
    out = []
    for page in range(1, max_pages + 1):
        url = f"{base}?limit=250&page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as res:
                data = json.loads(res.read().decode("utf-8", "ignore"))
        except Exception as e:
            print(f"  fetch error {url}: {e}", file=sys.stderr); break
        prods = data.get("products") or []
        if not prods: break
        out.extend(prods); print(f"  page {page}: +{len(prods)} (total {len(out)})"); time.sleep(delay)
    return out
def slugify(s):
    return (re.sub(r"[^a-z0-9]+", "-", series_norm(s)).strip("-")[:40] or "series")
def stable_id(prefix, series, issue, used):
    base = f"{prefix}-{slugify(series)}-{issue}"
    if base not in used: return base
    n = 2
    while f"{base}-{n}" in used: n += 1
    return f"{base}-{n}"
def resolve_vendor(vendor):
    vn = pub_norm(vendor)
    if vn in VENDOR_PUB: return VENDOR_PUB[vn]
    for k, v in VENDOR_PUB.items():
        if k in vn or vn in k: return v
    return None
def build_key_index(existing_keys):
    idx = defaultdict(set)
    for k in existing_keys:
        parts = k.split("|")
        if len(parts) != 3: continue
        sn, iss, pub = parts
        ik = str(int(float(iss))) if re.match(r"^\d", iss) else iss
        idx[(series_norm(sn), ik)].add(pub_norm(pub))
    return idx
def shop_url(shop, handle):
    hosts = {"thecomicbookstore":"https://www.thecomicbookstore.com","idw":"https://www.idwpublishing.com",
             "fantagraphics":"https://www.fantagraphics.com","austinbooks":"https://www.austinbooks.com",
             "boom":"https://shop.boom-studios.com","ignition":"https://ignitionpress.com"}
    return f"{hosts.get(shop,'https://example.com')}/products/{handle}"

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shops", type=str, default="thecomicbookstore,boom,idw,fantagraphics,ignition,austinbooks")
    ap.add_argument("--max-pages", type=int, default=50)
    ap.add_argument("--delay", type=float, default=0.25)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--limit-add", type=int, default=400)
    ap.add_argument("--batch-id", type=str, default="batch-018-shopify-real")
    ap.add_argument("--inject", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--include-big-two", action="store_true")
    ap.add_argument("--min-year", type=int, default=1980)
    args = ap.parse_args()

    existing_ids, existing_keys = load_live_blocklists()
    key_index = build_key_index(existing_keys)
    used_ids = set(existing_ids); used_keys = set(existing_keys)
    shop_keys = [s.strip() for s in args.shops.split(",") if s.strip()]
    candidates = []; skipped = Counter(); harvested = 0

    for shop in shop_keys:
        bases = SHOPS.get(shop)
        if not bases: print(f"unknown shop {shop}", file=sys.stderr); continue
        cache_path = CACHE_DIR / f"{shop}.json"
        if cache_path.exists() and not args.refresh:
            products = (json.loads(cache_path.read_text()).get("products")) or []
            print(f"{shop}: cache {len(products)}")
        else:
            products = []
            for base in bases:
                print(f"{shop}: harvest {base}")
                products = fetch_products(base, args.max_pages, args.delay)
                if products: break
            save_json(cache_path, {"fetchedAt": now_iso(), "products": products, "base": bases[0]})
        harvested += len(products)
        for p in products:
            title = p.get("title") or ""; ptype = p.get("product_type") or ""; tags = p.get("tags") or []
            if is_merch(title, ptype, tags): skipped["merch"] += 1; continue
            if is_collected(title, ptype): skipped["collected"] += 1; continue
            if not is_cover_a_or_main(title): skipped["variant"] += 1; continue
            parsed = parse_title(title)
            if not parsed: skipped["no_parse"] += 1; continue
            code = extract_code(p)
            if not code: skipped["no_upc"] += 1; continue
            vendor = (p.get("vendor") or "").strip(); vn = pub_norm(vendor)
            if not args.include_big_two and (vn in BIG_TWO or vn.startswith("marvel") or vn == "dc comics"):
                skipped["big_two"] += 1; continue
            resolved = resolve_vendor(vendor)
            if not resolved: skipped["vendor_skip"] += 1; continue
            publisher, prefix, palette = resolved
            iss = parsed["issue"]; iss_key = str(int(float(iss))) if re.match(r"^\d", iss) else iss
            sn = series_norm(parsed["series"]); pn = pub_norm(publisher)
            pubs = key_index.get((sn, iss_key), set())
            if any(pub_family(pn, x) for x in pubs): skipped["in_catalog"] += 1; continue
            published = (p.get("published_at") or p.get("created_at") or "")[:10]
            year = parsed["year"]
            if year and year < args.min_year: skipped["pre_floor"] += 1; continue
            if published and published < FLOOR: skipped["pre_floor"] += 1; continue
            if year: cover_date = f"{year:04d}-01-01"
            elif published and re.match(r"^\d{4}-\d{2}-\d{2}$", published): cover_date = published
            else: skipped["no_date"] += 1; continue
            if cover_date < FLOOR: skipped["pre_floor"] += 1; continue
            img = (p.get("images") or [{}])[0].get("src") if p.get("images") else None
            price = None
            for v in p.get("variants") or []:
                if v.get("price"):
                    try: price = float(v["price"])
                    except Exception: pass
                    break
            candidates.append(dict(shop=shop, title=title, series=parsed["series"], issue=iss_key,
                publisher=publisher, prefix=prefix, palette=palette, upc=code, cover_date=cover_date,
                street=published if published and published >= FLOOR else None, image=img,
                handle=p.get("handle"), price=price, vendor=vendor))

    candidates.sort(key=lambda c: (0 if c["shop"] == "thecomicbookstore" else 1, -len(c["upc"]), c["cover_date"]))
    rows = []; upc_local = {}; cover_local = {}; by_pub = Counter(); by_series = Counter(); seen = set()
    for c in candidates:
        if len(rows) >= args.limit_add: break
        skey = f"{c['series']}|{c['issue']}|{c['publisher']}".lower()
        if skey in used_keys or skey in seen: skipped["dup"] += 1; continue
        rid = stable_id(c["prefix"], c["series"], c["issue"], used_ids)
        msrp = c["price"] if c["price"] and 1.0 <= c["price"] <= 12.0 else 3.99
        extra = {"upc": c["upc"]}
        if c.get("street"): extra["streetDate"] = c["street"]
        row = [rid, c["series"], c["issue"], c["publisher"], c["cover_date"], "Various", "Various",
               f"{c['series']} #{c['issue']}.", float(msrp), "single", 0.55, 0, c["palette"], extra]
        rows.append(row); used_ids.add(rid); used_keys.add(skey); seen.add(skey)
        key_index[(series_norm(c["series"]), c["issue"])].add(pub_norm(c["publisher"]))
        by_pub[c["publisher"]] += 1; by_series[c["series"]] += 1
        upc_local[rid] = {"upc": c["upc"], "source": f"shopify:{c['shop']}", "title": c["title"],
                          "url": shop_url(c["shop"], c["handle"]), "fetchedAt": now_iso()}
        if c.get("image"):
            upc_local[rid]["coverUrl"] = c["image"]; cover_local[rid] = c["image"]

    print(f"harvested={harvested} candidates={len(candidates)} addable={len(rows)}")
    print("SKIP", dict(skipped)); print("BY_PUB", dict(by_pub))
    print("BY_SERIES", by_series.most_common(20)); print("sample", [r[0] for r in rows[:12]])
    save_json(STATE, {"lastRunAt": now_iso(), "shops": shop_keys, "addable": len(rows), "skipped": dict(skipped)})

    if args.dry_run or not rows:
        save_json(STATS, {"finishedAt": now_iso(), "dryRun": args.dry_run, "wouldAdd": len(rows),
            "harvested": harvested, "skipped": dict(skipped), "byPublisher": dict(by_pub), "sampleIds": [r[0] for r in rows[:20]]})
        return 0

    batch = {"id": args.batch_id, "title": "Shopify UPC-verified new comics",
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "status": "queued",
        "focus": "Thin pubs from Shopify products.json with real UPCs", "rows": rows,
        "conventions": {"floor": FLOOR, "dates": "Title year or published_at", "identity": "Shopify UPC",
            "covers": "Shopify product image when present"}, "source": "shopify",
        "stats": {"harvested": harvested, "skipped": dict(skipped), "byPublisher": dict(by_pub)}}
    out = BACKLOG / f"{args.batch_id}.json"
    out.write_text(json.dumps(batch, indent=2) + "\n"); print(f"wrote {out} rows={len(rows)}")

    disk_upc = load_json(UPC_MAP, {})
    for cid, ent in upc_local.items():
        cur = dict(disk_upc.get(cid) or {}); cur.update({k: v for k, v in ent.items() if v is not None}); disk_upc[cid] = cur
    save_json(UPC_MAP, disk_upc)
    disk_covers = load_json(COVER_URLS, {})
    for cid, url in cover_local.items():
        if url and cid not in disk_covers: disk_covers[cid] = url
    save_json(COVER_URLS, disk_covers)

    injected = 0
    if args.inject:
        injected = inject_batch(args.batch_id, comment=f"Injected Shopify-UPC comics ({args.batch_id}; floor {FLOOR})")
        print(f"injected {injected}")
    save_json(STATS, {"finishedAt": now_iso(), "added": len(rows), "injected": injected, "batchId": args.batch_id,
        "harvested": harvested, "skipped": dict(skipped), "byPublisher": dict(by_pub),
        "bySeries": by_series.most_common(), "sampleIds": [r[0] for r in rows[:20]]})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
