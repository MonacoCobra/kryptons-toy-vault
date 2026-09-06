#!/usr/bin/env python3
"""Backfill UPC/ISBN for catalog comics from League of Comic Geeks (primary).

LOCG-first identity. Never invents codes. Comic Vine barcode is optional fallback
when LOCG has no UPC (and COMICVINE_API_KEY / config file is available).

Politeness:
  LOCG robots.txt Crawl-delay: 30s — default --delay 30.
  Use smaller --delay only for local debugging.

Outputs:
  src/data/comic-upc-map.json     (id → upc, locgId, coverUrl, source)
  src/data/comic-cover-urls.json  (id → cover URL when LOCG cover verified)
  scripts/comic-upc-backfill-stats.json

Examples:
  python3 scripts/backfill-comic-upcs.py --limit 20
  python3 scripts/backfill-comic-upcs.py --only dc-abs-batman-1,mv-asm-300 --delay 30
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
SEEDS = ROOT / "src/data/comic-locg-seeds.json"
UPC_MAP = ROOT / "src/data/comic-upc-map.json"
COVER_URLS = ROOT / "src/data/comic-cover-urls.json"
COMICS_TS = ROOT / "src/data/comics.ts"
STATS = ROOT / "scripts/comic-upc-backfill-stats.json"
CV_KEY_FILE = Path("/home/box/.config/krypton/comicvine-api-key")

UA = (
    "KryptonsToyVault/1.0 (personal collection; upc backfill; "
    "+https://github.com/MonacoCobra/kryptons-toy-vault)"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_upc(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if 11 <= len(digits) <= 18:
        return digits
    cleaned = raw.strip()
    return cleaned or None


def fetch(url: str, accept: str = "text/html") -> tuple[str, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": accept,
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as res:
        return res.read().decode("utf-8", "ignore"), res.geturl()


def parse_locg_html(html: str, url: str) -> dict | None:
    if len(html) < 8000:
        return None
    m = re.search(r"/comic/(\d+)/", url) or re.search(
        r'canonical" href="https://leagueofcomicgeeks\.com/comic/(\d+)/', html
    )
    if not m:
        return None
    locg_id = m.group(1)
    h1 = re.search(r"<h1[^>]*>\s*([\s\S]*?)\s*</h1>", html, re.I)
    title = re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else None
    upc_m = re.search(r"UPC\s*</div>\s*<div[^>]*>\s*([0-9A-Za-z\-]+)", html, re.I) or re.search(
        r"UPC[\s\S]{0,120}?([0-9]{11,18})", html, re.I
    )
    isbn_m = re.search(r"ISBN\s*</div>\s*<div[^>]*>\s*([0-9Xx\-]+)", html, re.I)
    og = re.search(r'property="og:image"\s+content="([^"]+)"', html, re.I)
    pub_m = re.search(
        r'href="/comics/[^"]+"[^>]*>\s*([^<]+)\s*</a>\s*&nbsp;&nbsp;·', html, re.I
    )
    upc = normalize_upc(upc_m.group(1) if upc_m else None)
    isbn = normalize_upc(isbn_m.group(1) if isbn_m else None)
    cover = og.group(1) if og else f"https://s3.amazonaws.com/comicgeeks/comics/covers/large-{locg_id}.jpg"
    issue = None
    series = None
    if title:
        im = re.search(r"#\s*([0-9]+[A-Za-z]?|nn)\b", title, re.I)
        issue = im.group(1) if im else None
        series = re.sub(r"\s*#\s*[0-9A-Za-z]+.*$", "", title).strip()
    return {
        "locgId": locg_id,
        "title": title,
        "upc": upc or isbn,
        "isbn": isbn if isbn and isbn != upc else None,
        "coverUrl": cover,
        "publisher": pub_m.group(1).strip() if pub_m else None,
        "series": series,
        "issue": issue,
        "url": url.split("?")[0],
        "source": "locg",
    }


def fetch_locg(locg_id: str, slug: str = "issue") -> dict | None:
    url = f"https://leagueofcomicgeeks.com/comic/{locg_id}/{slug}"
    try:
        html, final = fetch(url)
        return parse_locg_html(html, final or url)
    except Exception as e:
        print(f"  LOCG fetch error {locg_id}: {e}", file=sys.stderr)
        return None


def search_locg_series(keyword: str) -> list[dict]:
    q = urllib.parse.urlencode(
        {"list": "search", "keyword": keyword, "format": "json", "view": "list"}
    )
    url = f"https://leagueofcomicgeeks.com/comic/get_comics?{q}"
    try:
        body, _ = fetch(url, accept="application/json")
        data = json.loads(body)
        html = data.get("list") or ""
    except Exception as e:
        print(f"  series search error: {e}", file=sys.stderr)
        return []
    hits = []
    for li in re.split(r"<li>", html, flags=re.I)[1:]:
        sid = re.search(r'data-id="(\d+)"', li)
        pub = re.search(r"copy-really-small[^>]*>\s*<span[^>]*>\s*([^<]+)", li, re.I)
        name = re.search(r'class="title[^"]*"[\s\S]*?data-id="\d+"\s*>\s*([^<]+)', li, re.I)
        cover = re.search(r"medium-(\d+)\.jpg", li, re.I)
        if not sid or not name or not pub:
            continue
        hits.append(
            {
                "seriesId": sid.group(1),
                "name": name.group(1).strip(),
                "publisher": pub.group(1).strip(),
                "coverComicId": cover.group(1) if cover else None,
            }
        )
    return hits


def pick_series(hits: list[dict], series: str, publisher: str) -> dict | None:
    want_s = series.lower().split("(")[0].strip()
    want_p = re.sub(r"[^a-z0-9]+", " ", publisher.lower()).strip()

    def score(h: dict) -> int:
        name = h["name"].lower()
        pub = re.sub(r"[^a-z0-9]+", " ", h["publisher"].lower()).strip()
        s = 0
        if name == want_s:
            s += 8
        elif want_s in name or name in want_s:
            s += 4
        if pub == want_p:
            s += 6
        elif want_p in pub or pub in want_p:
            s += 3
        if re.search(r"panini|jbc|fomo|marmara|urban comics|other", h["publisher"], re.I):
            s -= 4
        return s

    ranked = sorted(((score(h), h) for h in hits), key=lambda x: -x[0])
    if ranked and ranked[0][0] >= 8:
        return ranked[0][1]
    return None


def cv_key() -> str | None:
    env = os.environ.get("COMICVINE_API_KEY", "").strip()
    if env:
        return env
    try:
        return CV_KEY_FILE.read_text().strip() or None
    except OSError:
        return None


def cv_barcode(series: str, issue: str) -> dict | None:
    key = cv_key()
    if not key:
        return None
    num = issue.lstrip("#")
    if num.lower() == "nn":
        num = ""
    q = f"{series} {num}".strip()
    url = (
        "https://comicvine.gamespot.com/api/search/?"
        + urllib.parse.urlencode(
            {
                "api_key": key,
                "format": "json",
                "resources": "issue",
                "query": q,
                "limit": "8",
                "field_list": "id,name,issue_number,barcode,image,volume",
            }
        )
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as res:
            data = json.loads(res.read().decode())
    except Exception as e:
        print(f"  CV error: {e}", file=sys.stderr)
        return None
    want = num.lower()
    series_core = series.lower().split("(")[0].strip()
    best = None
    best_score = -99
    for r in data.get("results") or []:
        vol = ((r.get("volume") or {}).get("name") or "").lower()
        iss = str(r.get("issue_number") or "").lower()
        score = 0
        if iss == want:
            score += 5
        if vol == series_core:
            score += 6
        elif series_core in vol or vol in series_core:
            score += 3
        if "w.i.p" in vol or "wip" in vol:
            score -= 4
        barcode = normalize_upc(r.get("barcode"))
        if barcode:
            score += 2
        if score > best_score:
            best_score = score
            best = r
    if not best or best_score < 5:
        return None
    barcode = normalize_upc(best.get("barcode"))
    img = best.get("image") or {}
    cover = img.get("super_url") or img.get("medium_url")
    if not barcode and not cover:
        return None
    return {
        "upc": barcode,
        "coverUrl": cover,
        "source": "comicvine",
        "sourceId": str(best.get("id")) if best.get("id") is not None else None,
    }


def parse_comics_meta() -> dict[str, dict]:
    """Pull id→{series,issue,publisher,variant,upc,coverDate} from comics.ts rows."""
    text = COMICS_TS.read_text()
    # Match tuple rows: ["id", "series", "issue", "publisher", "date", ...]
    pat = re.compile(
        r'\["([^"]+)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)"',
        re.M,
    )
    out: dict[str, dict] = {}
    for m in pat.finditer(text):
        cid, series, issue, publisher, cover_date = m.groups()
        # optional extra object immediately after palette
        rest = text[m.end() : m.end() + 400]
        variant = None
        upc = None
        em = re.search(
            r"\{([^}]*)\}\s*\]",
            rest,
        )
        if em and "upc" in em.group(1):
            um = re.search(r'upc:\s*"([^"]+)"', em.group(1))
            if um:
                upc = um.group(1)
        if em and "variant" in em.group(1):
            vm = re.search(r'variant:\s*"([^"]+)"', em.group(1))
            if vm:
                variant = vm.group(1)
        out[cid] = {
            "series": series,
            "issue": issue,
            "publisher": publisher,
            "coverDate": cover_date,
            "variant": variant,
            "upc": upc,
        }
    return out


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def publisher_ok(got: str | None, want: str) -> bool:
    if not got:
        return True
    g = re.sub(r"[^a-z0-9]+", " ", got.lower()).strip()
    w = re.sub(r"[^a-z0-9]+", " ", want.lower()).strip()
    if g == w:
        return True
    if w in g or g in w:
        return True
    # DC / Marvel short forms
    aliases = {
        "dc comics": {"dc", "dc comics", "dc entertainment"},
        "marvel comics": {"marvel", "marvel comics"},
        "image comics": {"image", "image comics"},
    }
    for canon, al in aliases.items():
        if w in al or w == canon:
            return g in al or g == canon or canon in g
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=40, help="Max comics to attempt")
    ap.add_argument("--delay", type=float, default=30.0, help="Seconds between LOCG requests (robots Crawl-delay=30)")
    ap.add_argument("--only", type=str, default="", help="Comma-separated comic ids")
    ap.add_argument("--seeds-only", action="store_true", help="Only process seeded locgIds")
    ap.add_argument("--no-cv", action="store_true", help="Skip Comic Vine barcode fallback")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    seeds = load_json(SEEDS, {})
    upc_map = load_json(UPC_MAP, {})
    cover_urls = load_json(COVER_URLS, {})
    meta = parse_comics_meta()

    if args.only:
        ids = [x.strip() for x in args.only.split(",") if x.strip()]
    else:
        # Prefer seeded keys, then cover-url keys missing upc
        ids = list(seeds.keys())
        for cid in cover_urls:
            if cid not in ids:
                ids.append(cid)
        # key curated from meta that still lack upc
        for cid, m in meta.items():
            if m.get("upc") or upc_map.get(cid, {}).get("upc"):
                continue
            if cid.startswith(("dc-", "mv-", "im-")) and cid not in ids:
                # only add when we have a seed or will try series#1 discovery
                pass

    if args.seeds_only:
        ids = [i for i in ids if seeds.get(i, {}).get("locgId")]

    ids = ids[: args.limit]
    print(f"backfill: {len(ids)} comics, delay={args.delay}s, seeds_only={args.seeds_only}")

    stats = {
        "startedAt": now_iso(),
        "attempted": 0,
        "upcFilled": 0,
        "coverUpdated": 0,
        "locgHits": 0,
        "locgNoUpc": 0,
        "cvFallbackUpc": 0,
        "skippedExisting": 0,
        "errors": 0,
        "mismatchPublisher": 0,
        "details": [],
    }

    last_locg_at = 0.0

    def throttle():
        nonlocal last_locg_at
        wait = args.delay - (time.time() - last_locg_at)
        if wait > 0:
            time.sleep(wait)
        last_locg_at = time.time()

    for cid in ids:
        m = meta.get(cid) or {}
        seed = seeds.get(cid) or {}
        existing = upc_map.get(cid) or {}
        if existing.get("upc") and not args.dry_run:
            # still allow cover refresh if missing
            if existing.get("coverUrl") and cid in cover_urls:
                stats["skippedExisting"] += 1
                continue

        stats["attempted"] += 1
        series = m.get("series") or cid
        issue = m.get("issue") or "1"
        publisher = m.get("publisher") or ""
        detail = {"id": cid, "series": series, "issue": issue}

        hit = None
        locg_id = seed.get("locgId")
        slug = seed.get("slug") or "issue"

        if locg_id:
            throttle()
            hit = fetch_locg(str(locg_id), slug)
        elif issue in ("1", "nn") and not args.seeds_only:
            # Series search → cover comic id often equals #1
            throttle()
            hits = search_locg_series(series)
            picked = pick_series(hits, series, publisher)
            detail["seriesPick"] = (picked or {}).get("seriesId")
            if picked and picked.get("coverComicId"):
                throttle()
                hit = fetch_locg(picked["coverComicId"], slug)

        if hit:
            stats["locgHits"] += 1
            if not publisher_ok(hit.get("publisher"), publisher):
                stats["mismatchPublisher"] += 1
                detail["status"] = "publisher_mismatch"
                detail["gotPublisher"] = hit.get("publisher")
                detail["title"] = hit.get("title")
                stats["details"].append(detail)
                print(f"! {cid}: publisher mismatch got={hit.get('publisher')} want={publisher}")
                continue

            # Issue sanity when both known
            if hit.get("issue") and issue.lower() not in ("nn",) and str(hit["issue"]).lower() != str(issue).lower():
                # Allow if seed forced this id (explicit), else skip
                if not locg_id:
                    detail["status"] = "issue_mismatch"
                    detail["gotIssue"] = hit.get("issue")
                    stats["details"].append(detail)
                    print(f"! {cid}: issue mismatch got=#{hit.get('issue')} want=#{issue}")
                    continue

            entry = {
                "upc": hit.get("upc"),
                "locgId": hit.get("locgId"),
                "coverUrl": hit.get("coverUrl"),
                "source": "locg",
                "url": hit.get("url"),
                "title": hit.get("title"),
                "fetchedAt": now_iso(),
            }
            if hit.get("upc"):
                stats["upcFilled"] += 1
                detail["upc"] = hit["upc"]
                detail["status"] = "locg_upc"
            else:
                stats["locgNoUpc"] += 1
                detail["status"] = "locg_no_upc"
                # Older pre-barcode issues often have no UPC on LOCG — keep locgId + cover
            if not args.dry_run:
                upc_map[cid] = {k: v for k, v in entry.items() if v}
                if hit.get("coverUrl"):
                    # Prefer LOCG cover when we have identity (UPC or explicit seed)
                    if hit.get("upc") or locg_id:
                        cover_urls[cid] = hit["coverUrl"]
                        stats["coverUpdated"] += 1
            print(f"✓ {cid}: upc={entry.get('upc') or '—'} locg={entry.get('locgId')} {hit.get('title')}")
            stats["details"].append(detail)

            # CV fallback only for missing UPC
            if not entry.get("upc") and not args.no_cv:
                time.sleep(min(1.5, args.delay))
                cv = cv_barcode(series, issue)
                if cv and cv.get("upc"):
                    stats["cvFallbackUpc"] += 1
                    stats["upcFilled"] += 1
                    detail["upc"] = cv["upc"]
                    detail["status"] = "cv_barcode"
                    if not args.dry_run:
                        upc_map[cid]["upc"] = cv["upc"]
                        upc_map[cid]["source"] = "locg+comicvine-barcode"
                        if cv.get("coverUrl") and not upc_map[cid].get("coverUrl"):
                            upc_map[cid]["coverUrl"] = cv["coverUrl"]
                    print(f"  + CV barcode {cv['upc']}")
            continue

        # No LOCG hit — optional CV-only barcode (no invention)
        if not args.no_cv:
            time.sleep(min(1.5, args.delay))
            cv = cv_barcode(series, issue)
            if cv and cv.get("upc"):
                stats["cvFallbackUpc"] += 1
                stats["upcFilled"] += 1
                detail["status"] = "cv_only"
                detail["upc"] = cv["upc"]
                if not args.dry_run:
                    upc_map[cid] = {
                        "upc": cv["upc"],
                        "coverUrl": cv.get("coverUrl"),
                        "source": "comicvine-barcode",
                        "fetchedAt": now_iso(),
                    }
                    if cv.get("coverUrl"):
                        cover_urls[cid] = cv["coverUrl"]
                        stats["coverUpdated"] += 1
                print(f"✓ {cid}: CV-only upc={cv['upc']}")
                stats["details"].append(detail)
                continue

        stats["errors"] += 1
        detail["status"] = "missing"
        stats["details"].append(detail)
        print(f"· {cid}: no LOCG/CV upc")

    # Preserve known FF 550 upc from comics.ts into map if missing
    ff = meta.get("mv-ff-550-3d")
    if ff and ff.get("upc") and "mv-ff-550-3d" not in upc_map:
        upc_map["mv-ff-550-3d"] = {
            "upc": normalize_upc(ff["upc"]),
            "source": "comics.ts",
            "fetchedAt": now_iso(),
        }
        stats["upcFilled"] += 1

    stats["finishedAt"] = now_iso()
    stats["upcMapSize"] = len([1 for v in upc_map.values() if v.get("upc")])
    stats["delay"] = args.delay

    if not args.dry_run:
        save_json(UPC_MAP, upc_map)
        save_json(COVER_URLS, cover_urls)
        save_json(STATS, stats)

    print(json.dumps({k: stats[k] for k in stats if k != "details"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
