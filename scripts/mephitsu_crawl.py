#!/usr/bin/env python3
"""Generic Mephitsu (Wix) action-figure database crawler.

Shelby-authorized source: https://www.mephitsu.co.uk
Collections (cloud-data IDs) cover Marvel Legends, Black Series, Hasbro hub
(GI Joe / Indy / TF Studio Series / …), McFarlane, NECA, Diamond Select,
Doctor Who, Star Trek Universe, Super7, Jazwares.

Emits product records compatible with product-sku-index.json:
  id, shop, tier, company, name, subtitle, line, tags, title, handle,
  sku (GTIN only when known), listingSku, barcode, productId, imageUrl,
  imageUrls, sourceUrl, year, wave, mephitsuId, …

GTIN policy: never invent. Text fields have no EAN; optional --ocr may accept
zbar/tesseract hits that pass EAN-13/UPC-A checksum (figure_identity.is_gtin_strict).
Listing codes from OCR (G####/F####/…) go to listingSku only.

Auth: scrape Authorization instance token from any public item page (cached).
Polite: sleep between pages; disk cache under src/data/figure-archive/mephitsu/.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "src/data/figure-archive/mephitsu"
AUTH_CACHE = OUT_DIR / "auth-token.txt"
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from figure_identity import clean_code, is_gtin_strict, is_listing_code  # noqa: E402

UA = "Mozilla/5.0 (compatible; CollectionBot/1.0; +research; polite)"
API = "https://www.mephitsu.co.uk/_api/cloud-data/v1/items/query"
SITE = "https://www.mephitsu.co.uk"

# Hub lines Shelby authorized. collectionId must match Wix dataBinding schema id.
LINES: dict[str, dict[str, Any]] = {
    "marvel-legends": {
        "collectionId": "MarvelLegends",
        "company": "hasbro",
        "line": "Marvel Legends",
        "authUrl": (
            "https://www.mephitsu.co.uk/marvel-legends/cassandra-nova/2026/"
            "deadpool-%26-wolverine-wave-2/df5ae9a2-7cf6-4156-979f-53a1f7f89b68"
        ),
        "sitemapHint": "dynamic-marvel-legends",
        "franchiseFilter": None,  # all rows
    },
    "black-series": {
        "collectionId": "BlackSeries",
        "company": "hasbro",
        "line": "Star Wars The Black Series",
        "authUrl": None,  # filled from first sitemap item at runtime if needed
        "sitemapHint": "dynamic-black-series",
        "franchiseFilter": None,
    },
    "hasbro": {
        "collectionId": "Hasbro",
        "company": "hasbro",
        "line": None,  # derived from franchise/seriesOrWave
        "authUrl": None,
        "sitemapHint": "dynamic-hasbro",
        "franchiseFilter": None,
        "notes": "Hub: GI Joe, Transformers (Studio Series), Indiana Jones, Plasma, …",
    },
    "gi-joe-classified": {
        "collectionId": "Hasbro",
        "company": "hasbro",
        "line": "G.I. Joe Classified Series",
        "franchiseFilter": ["GI Joe", "G.I. Joe", "G.I Joe"],
        "authUrl": None,
        "sitemapHint": "dynamic-hasbro",
    },
    "indiana-jones": {
        "collectionId": "Hasbro",
        "company": "hasbro",
        "line": "Indiana Jones Adventure Series",
        "franchiseFilter": ["Indiana Jones"],
        "authUrl": None,
        "sitemapHint": "dynamic-hasbro",
    },
    "transformers": {
        "collectionId": "Hasbro",
        "company": "hasbro",
        "line": "Transformers",
        "franchiseFilter": ["Transformers"],
        "authUrl": None,
        "sitemapHint": "dynamic-hasbro",
        "notes": "Includes Studio Series / Plasma / Classified-adjacent TF rows",
    },
    "mcfarlane": {
        "collectionId": "McFarlaneDirectory",
        "company": "mcfarlane",
        "line": "McFarlane",
        "authUrl": None,
        "sitemapHint": "dynamic-mcfarlane-directory",
        "notes": "Multiverse + Spawn + other McFarlane lines via franchise field",
    },
    "neca": {
        "collectionId": "NECADatabase",
        "company": "neca",
        "line": "NECA",
        "authUrl": None,
        "sitemapHint": "dynamic-neca",
    },
    "diamond-select": {
        "collectionId": "DiamondSelect",
        "company": "diamondselect",
        "line": "Diamond Select",
        "authUrl": None,
        "sitemapHint": "dynamic-diamond-select",
    },
    "doctor-who": {
        "collectionId": "DoctorWho",
        "company": "character-options",
        "line": "Doctor Who",
        "authUrl": None,
        "sitemapHint": "dynamic-doctor-who",
    },
    "star-trek": {
        "collectionId": "StarTrekUniverse",
        "company": "exobiology",  # often Playmates/Exo-6/etc — refine per franchise later
        "line": "Star Trek",
        "authUrl": None,
        "sitemapHint": "dynamic-star-trek",
    },
    "super7": {
        "collectionId": "Super7",
        "company": "super7",
        "line": "Super7",
        "authUrl": None,
        "sitemapHint": "dynamic-super7",
    },
    "jazwares": {
        "collectionId": "Jazwares",
        "company": "jazwares",
        "line": "Jazwares",
        "authUrl": None,
        "sitemapHint": "dynamic-jazwares",
    },
}


def _http_get(url: str, timeout: int = 40) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _http_json(url: str, payload: dict, auth: str, timeout: int = 60) -> dict:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", UA)
    req.add_header("Authorization", auth)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def refresh_auth(auth_url: str | None = None) -> str:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    url = auth_url or LINES["marvel-legends"]["authUrl"]
    raw = _http_get(url).decode("utf-8", "ignore")
    m = re.search(r'Authorization["\']?\s*:\s*["\']([^"\']+)["\']', raw)
    if not m:
        raise RuntimeError(f"No Authorization token on {url}")
    token = m.group(1)
    AUTH_CACHE.write_text(token)
    return token


def load_auth(force: bool = False, auth_url: str | None = None) -> str:
    if not force and AUTH_CACHE.exists():
        tok = AUTH_CACHE.read_text().strip()
        if len(tok) > 40:
            return tok
    return refresh_auth(auth_url)


def wix_image_url(raw: Any, width: int = 1200) -> str | None:
    """Normalize wix:image://, https, or slug to a CDN URL."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        src = raw.get("src") or raw.get("slug") or raw.get("url")
        return wix_image_url(src, width)
    s = str(raw).strip()
    if not s:
        return None
    if s.startswith("http://") or s.startswith("https://"):
        return s.split("#")[0]
    if s.startswith("wix:image://"):
        # wix:image://v1/<mediaId>/<filename>#originWidth=…
        mid = s.split("wix:image://v1/")[1].split("/")[0]
        return f"https://static.wixstatic.com/media/{mid}/v1/fill/w_{width},h_{width},al_c,q_90/{mid}"
    if re.match(r"^[a-z0-9]+_[a-f0-9]+~mv2\.(jpg|png|jpeg|webp)$", s, re.I):
        return f"https://static.wixstatic.com/media/{s}/v1/fill/w_{width},h_{width},al_c,q_90/{s}"
    return None


def gallery_urls(item: dict) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()

    def add(raw: Any) -> None:
        u = wix_image_url(raw)
        if u and u not in seen:
            seen.add(u)
            out.append(u)

    add(item.get("box"))
    add(item.get("contents"))
    gal = item.get("gallery")
    if isinstance(gal, list):
        for g in gal:
            add(g)
    else:
        add(gal)
    add(item.get("logo"))
    return out


def pick_primary_image(urls: list[str], item: dict) -> str | None:
    """Prefer front card / box over barcode-only or tiny logos."""
    if not urls:
        return None
    # Prefer box field when present
    box = wix_image_url(item.get("box"))
    if box:
        return box
    contents = wix_image_url(item.get("contents"))
    if contents:
        return contents
    # Prefer gallery fileNames that look like Package / front
    gal = item.get("gallery")
    if isinstance(gal, list):
        for g in gal:
            fn = str((g or {}).get("fileName") or (g or {}).get("title") or "")
            if re.search(r"package|packaging|card|front|box", fn, re.I) and not re.search(
                r"bar\s*code|upc|ean", fn, re.I
            ):
                u = wix_image_url(g)
                if u:
                    return u
        if gal:
            return wix_image_url(gal[0])
    return urls[0]


def item_year(item: dict) -> str | None:
    for k in ("year", "yearOfRelease"):
        v = item.get(k)
        if v is None:
            continue
        s = str(v).strip()
        m = re.match(r"(20\d{2}|19\d{2})", s)
        if m:
            return m.group(1)
    return None


def item_wave(item: dict) -> str:
    for k in ("wave", "seriesOrWave", "movie", "source", "release"):
        v = item.get(k)
        if v and str(v).strip() and str(v).strip().lower() not in {"n/a", "none", "-"}:
            return html_lib.unescape(str(v).strip())
    return ""


def item_page_url(item: dict, line_key: str) -> str | None:
    for k, v in item.items():
        if k.startswith("link-") and "title" in k and isinstance(v, str) and v.startswith("/"):
            return SITE + v
    # Fallback patterns
    title = urllib.parse.quote(str(item.get("title") or "").lower().replace(" ", "-"))
    year = item_year(item) or ""
    wid = item.get("_id") or ""
    if line_key == "marvel-legends" and title and wid:
        wave = urllib.parse.quote(item_wave(item).lower())
        return f"{SITE}/marvel-legends/{title}/{year}/{wave}/{wid}"
    return None


def hasbro_line_from_item(item: dict, default: str | None) -> str:
    if default:
        return default
    fr = str(item.get("franchise") or "")
    series = str(item.get("seriesOrWave") or item.get("wave") or "")
    blob = f"{fr} {series}".lower()
    if "gi joe" in blob or "g.i. joe" in blob or "classified" in blob:
        return "G.I. Joe Classified Series"
    if "indiana" in blob:
        return "Indiana Jones Adventure Series"
    if "studio series" in blob or (
        "transform" in blob
        and re.search(r"\b(deluxe|voyager|leader|titan|core)\s+class\b", series, re.I)
    ):
        return "Transformers Studio Series"
    if "plasma" in blob:
        return "Transformers Plasma"
    if "masterpiece" in blob and "transform" in blob:
        return "Transformers Masterpiece"
    if "power ranger" in blob or "lightning" in blob:
        return "Lightning Collection"
    if "transformer" in blob:
        return "Transformers"
    if fr:
        return fr
    return "Hasbro"


def company_for_line(line_key: str, item: dict, cfg: dict) -> str:
    co = cfg.get("company") or "unknown"
    if line_key == "mcfarlane":
        fr = str(item.get("franchise") or "").lower()
        if "spawn" in fr:
            return "mcfarlane"
        if "dc" in fr or "multiverse" in fr:
            return "mcfarlane"
    if line_key == "star-trek":
        # Keep generic; bake matcher uses company gate — refine later
        return "playmates"
    return co


def to_product(item: dict, line_key: str, cfg: dict) -> dict:
    title = html_lib.unescape(str(item.get("title") or "").strip())
    year = item_year(item)
    wave = item_wave(item)
    franchise = html_lib.unescape(str(item.get("franchise") or item.get("movie") or "").strip())
    line = hasbro_line_from_item(item, cfg.get("line"))
    urls = gallery_urls(item)
    image = pick_primary_image(urls, item)
    mid = str(item.get("_id") or "")
    handle = mid
    page = item_page_url(item, line_key)
    subtitle_parts = [p for p in [wave, year, franchise] if p]
    subtitle = " · ".join(subtitle_parts)[:180]
    tags = [
        "mephitsu",
        f"mephitsu:{line_key}",
    ]
    if item.get("packaging"):
        tags.append(f"pack:{item['packaging']}")
    if item.get("generalOrExclusive"):
        tags.append(str(item["generalOrExclusive"]))
    if item.get("type"):
        tags.append(str(item["type"])[:40])

    return {
        "id": f"mephitsu:{line_key}:{mid}",
        "shop": "mephitsu",
        "tier": "specialty",
        "company": company_for_line(line_key, item, cfg),
        "name": title,
        "subtitle": subtitle,
        "line": line,
        "tags": tags,
        "title": f"{title} — {subtitle}" if subtitle else title,
        "handle": handle,
        "sku": None,  # GTIN only when OCR / resolved later
        "listingSku": None,
        "barcode": None,
        "productId": mid,
        "imageUrl": image,
        "imageUrls": urls[:24],
        "sourceUrl": page,
        "year": year,
        "wave": wave,
        "franchise": franchise,
        "mephitsuLine": line_key,
        "mephitsuId": mid,
        "packaging": item.get("packaging"),
        "rawGalleryCount": len(urls),
    }


def franchise_ok(item: dict, cfg: dict) -> bool:
    filt = cfg.get("franchiseFilter")
    if not filt:
        return True
    fr = str(item.get("franchise") or "")
    return any(f.lower() in fr.lower() for f in filt)


def crawl_collection(
    line_key: str,
    auth: str,
    *,
    page_size: int = 100,
    sleep_s: float = 0.55,
    max_items: int | None = None,
) -> list[dict]:
    cfg = LINES[line_key]
    cid = cfg["collectionId"]
    items_out: list[dict] = []
    skip = 0
    total = None
    while True:
        payload = {
            "dataCollectionId": cid,
            "query": {
                "filter": {},
                "paging": {"limit": page_size, "offset": skip},
            },
        }
        try:
            data = _http_json(API, payload, auth)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                auth = refresh_auth(cfg.get("authUrl"))
                data = _http_json(API, payload, auth)
            else:
                raise
        if total is None:
            total = data.get("totalCount") or data.get("pagingMetadata", {}).get("total")
            print(f"  [{line_key}] collection={cid} total≈{total}", flush=True)
        batch = data.get("items") or []
        if not batch:
            break
        for it in batch:
            if not franchise_ok(it, cfg):
                continue
            items_out.append(to_product(it, line_key, cfg))
            if max_items and len(items_out) >= max_items:
                return items_out
        skip += len(batch)
        if total is not None and skip >= total:
            break
        if len(batch) < page_size:
            break
        time.sleep(sleep_s)
    return items_out


# --- Optional OCR (listing codes + strict GTINs) ---------------------------------

_LISTING_OCR_RE = re.compile(
    r"\b([FGCEAB]\d{4})\s*/\s*([FGCEAB]?\d{4})\s*ASST\.?\b|"
    r"\b([FGCEAB]\d{4})\b",
    re.I,
)


def ocr_image_file(path: Path) -> tuple[str | None, str | None]:
    """Return (gtin_strict, listing_code) from a local image via zbar then tesseract."""
    gtin = None
    listing = None
    try:
        r = subprocess.run(
            ["zbarimg", "-q", "--raw", str(path)],
            capture_output=True,
            text=True,
            timeout=20,
        )
        for line in (r.stdout or "").splitlines():
            digits = re.sub(r"\D", "", line)
            if is_gtin_strict(digits):
                gtin = digits
                break
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        r = subprocess.run(
            ["tesseract", str(path), "stdout", "--psm", "11"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        text = r.stdout or ""
        if not gtin:
            for m in re.finditer(r"\b(\d{12,14})\b", re.sub(r"[\s-]", "", text)):
                if is_gtin_strict(m.group(1)):
                    gtin = m.group(1)
                    break
        if not listing:
            m = _LISTING_OCR_RE.search(text)
            if m:
                listing = clean_code(m.group(1) or m.group(3))
                if listing and not is_listing_code(listing):
                    # still accept Hasbro letter+4 digits
                    if not re.match(r"^[FGCEAB]\d{4}$", listing, re.I):
                        listing = None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return gtin, listing


def ocr_enrich_products(
    products: list[dict],
    *,
    limit: int = 40,
    sleep_s: float = 0.4,
) -> dict:
    """OCR a sample of package/front images for listing + GTIN."""
    stats = {"attempted": 0, "gtin": 0, "listing": 0, "errors": 0}
    odir = OUT_DIR / "ocr-cache"
    odir.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in products:
        if n >= limit:
            break
        urls = list(p.get("imageUrls") or [])
        # Prefer images that may be packaging
        ranked = urls[:3]
        for url in ranked:
            if n >= limit:
                break
            slug = url.split("/media/")[-1].split("/")[0] if "/media/" in url else f"img{n}"
            slug = re.sub(r"[^a-zA-Z0-9_.~-]", "_", slug)[:80]
            path = odir / f"{slug}.jpg"
            try:
                if not path.exists() or path.stat().st_size < 1000:
                    # Prefer original media URL without transform when possible
                    if "/media/" in url:
                        mid = url.split("/media/")[1].split("/")[0]
                        dl = f"https://static.wixstatic.com/media/{mid}"
                    else:
                        dl = url
                    path.write_bytes(_http_get(dl))
                    time.sleep(sleep_s)
                gtin, listing = ocr_image_file(path)
                stats["attempted"] += 1
                n += 1
                if gtin and not p.get("sku"):
                    p["sku"] = gtin
                    p["barcode"] = gtin
                    stats["gtin"] += 1
                if listing and not p.get("listingSku"):
                    p["listingSku"] = listing.upper()
                    stats["listing"] += 1
                if gtin or listing:
                    break
            except Exception:
                stats["errors"] += 1
                continue
    return stats


def resolve_gtins_from_sku_index(products: list[dict], sku_index: list[dict]) -> dict:
    """Fill empty GTIN primary via listingSku join, then high-confidence name join.

    Never invents; only copies GTINs already present in product-sku-index.
    """
    by_listing: dict[str, list[dict]] = {}
    gtin_products: list[dict] = []
    for raw in sku_index:
        sku = clean_code(raw.get("sku")) or clean_code(raw.get("barcode"))
        if sku and re.fullmatch(r"\d{8}|\d{12,14}", sku):
            # accept length-shaped GTINs already present in trusted specialty index
            gtin_products.append(raw)
        listing = clean_code(raw.get("listingSku"))
        sku_raw = clean_code(raw.get("sku"))
        if sku_raw and not re.fullmatch(r"\d{8}|\d{12,14}", sku_raw):
            listing = listing or sku_raw
        if listing:
            u = listing.upper()
            by_listing.setdefault(u, []).append(raw)
            # Also index bare Hasbro assort (G2357) when stored as HASG2357 / HSG2357
            m = re.match(r"^(?:HAS|HSG|HS)([A-Z]?\d{4,})$", u)
            if m:
                by_listing.setdefault(m.group(1), []).append(raw)
            m2 = re.match(r"^([FGCEAB]\d{4})$", u)
            if m2:
                by_listing.setdefault("HAS" + m2.group(1), []).append(raw)
                by_listing.setdefault("HSG" + m2.group(1), []).append(raw)

    stats = {"listingJoin": 0, "skippedHasGtin": 0, "noMatch": 0}

    def pick_gtin(cands: list[dict]) -> str | None:
        for c in cands:
            for key in ("sku", "barcode"):
                s = clean_code(c.get(key))
                if s and re.fullmatch(r"\d{8}|\d{12,14}", s):
                    return s
        return None

    for p in products:
        if p.get("sku") and re.fullmatch(r"\d{8}|\d{12,14}", str(p["sku"])):
            stats["skippedHasGtin"] += 1
            continue
        listing = clean_code(p.get("listingSku"))
        if listing and listing.upper() in by_listing:
            g = pick_gtin(by_listing[listing.upper()])
            if g:
                p["sku"] = g
                p["barcode"] = g
                stats["listingJoin"] += 1
                continue
        stats["noMatch"] += 1
    return stats


def write_line_index(line_key: str, products: list[dict]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{line_key}.json"
    doc = {
        "version": 1,
        "source": "mephitsu",
        "line": line_key,
        "collectionId": LINES[line_key]["collectionId"],
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(products),
        "withImage": sum(1 for p in products if p.get("imageUrl")),
        "withGtin": sum(1 for p in products if p.get("sku") and re.fullmatch(r"\d{8}|\d{12,14}", str(p["sku"]))),
        "withListing": sum(1 for p in products if p.get("listingSku")),
        "products": products,
    }
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    return path


def merge_into_product_sku_index(products: list[dict], *, replace_shop: bool = True) -> dict:
    """Append/replace mephitsu shop rows in product-sku-index.json."""
    idx_path = ROOT / "src/data/figure-archive/product-sku-index.json"
    index: list[dict] = json.loads(idx_path.read_text())
    before = len(index)
    if replace_shop:
        index = [p for p in index if p.get("shop") != "mephitsu"]
    # Only merge rows that have image or sku/listing (useful for bake)
    added = 0
    for p in products:
        entry = {
            "id": p["id"],
            "shop": "mephitsu",
            "tier": "specialty",
            "company": p["company"],
            "name": p["name"],
            "subtitle": p.get("subtitle") or "",
            "line": p.get("line") or "",
            "tags": p.get("tags") or [],
            "title": p.get("title") or p["name"],
            "handle": p.get("handle") or p.get("mephitsuId"),
            "sku": p.get("sku"),
            "listingSku": p.get("listingSku"),
            "barcode": p.get("barcode") or p.get("sku"),
            "productId": p.get("productId"),
            "imageUrl": p.get("imageUrl"),
        }
        index.append(entry)
        added += 1
    idx_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    return {"before": before, "after": len(index), "added": added, "removedOldMephitsu": before - (len(index) - added)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--line",
        action="append",
        dest="lines",
        help="Line key(s); default marvel-legends. Use --all for hub list.",
    )
    ap.add_argument("--all", action="store_true", help="Crawl all configured lines")
    ap.add_argument("--list-lines", action="store_true")
    ap.add_argument("--refresh-auth", action="store_true")
    ap.add_argument("--ocr", action="store_true", help="OCR sample images for listing/GTIN")
    ap.add_argument("--ocr-limit", type=int, default=30)
    ap.add_argument("--resolve-gtin", action="store_true", help="Join listing→GTIN via product-sku-index")
    ap.add_argument("--merge-index", action="store_true", help="Merge into product-sku-index.json")
    ap.add_argument("--max-items", type=int, default=None)
    ap.add_argument("--sleep", type=float, default=0.55)
    ap.add_argument("--cache-only", action="store_true", help="Reuse mephitsu/<line>.json")
    args = ap.parse_args()

    if args.list_lines:
        for k, v in LINES.items():
            print(f"{k:22} collection={v['collectionId']:22} company={v.get('company')} line={v.get('line')}")
        return 0

    if args.all:
        keys = [
            "marvel-legends",
            "black-series",
            "hasbro",
            "gi-joe-classified",
            "indiana-jones",
            "transformers",
            "mcfarlane",
            "neca",
            "diamond-select",
            "doctor-who",
            "star-trek",
            "super7",
            "jazwares",
        ]
    else:
        keys = args.lines or ["marvel-legends"]

    for k in keys:
        if k not in LINES:
            print(f"Unknown line {k}. Use --list-lines.", file=sys.stderr)
            return 2

    auth = load_auth(force=args.refresh_auth)

    all_products: list[dict] = []
    for line_key in keys:
        cache_path = OUT_DIR / f"{line_key}.json"
        if args.cache_only and cache_path.exists():
            doc = json.loads(cache_path.read_text())
            products = doc.get("products") or []
            print(f"[{line_key}] cache-only {len(products)} from {cache_path}")
        else:
            print(f"[{line_key}] crawling…", flush=True)
            products = crawl_collection(
                line_key, auth, sleep_s=args.sleep, max_items=args.max_items
            )
            write_line_index(line_key, products)
            print(
                f"[{line_key}] wrote {len(products)} "
                f"(images={sum(1 for p in products if p.get('imageUrl'))})",
                flush=True,
            )
        if args.ocr:
            st = ocr_enrich_products(products, limit=args.ocr_limit)
            print(f"[{line_key}] ocr {st}", flush=True)
            write_line_index(line_key, products)
        all_products.extend(products)

    if args.resolve_gtin:
        idx_path = ROOT / "src/data/figure-archive/product-sku-index.json"
        sku_index = json.loads(idx_path.read_text())
        # Group by line file rewrite
        by_line: dict[str, list[dict]] = {}
        for p in all_products:
            by_line.setdefault(p.get("mephitsuLine") or "unknown", []).append(p)
        for line_key, products in by_line.items():
            st = resolve_gtins_from_sku_index(products, sku_index)
            print(f"[{line_key}] resolve-gtin {st} withGtin="
                  f"{sum(1 for p in products if p.get('sku') and re.fullmatch(r'\\d{8}|\\d{12,14}', str(p.get('sku'))))}")
            write_line_index(line_key, products)

    if args.merge_index:
        # Reload from disk so OCR/resolve mutations are included
        merged_products: list[dict] = []
        for line_key in keys:
            doc = json.loads((OUT_DIR / f"{line_key}.json").read_text())
            merged_products.extend(doc.get("products") or [])
        st = merge_into_product_sku_index(merged_products)
        print(f"merged product-sku-index {st}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
