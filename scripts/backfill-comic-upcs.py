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
  scripts/comic-locg-series-cache.json  (series+publisher → seriesId + issue map)

Examples:
  python3 scripts/backfill-comic-upcs.py --seeds-only --limit 40
  python3 scripts/backfill-comic-upcs.py --from-catalog --limit 200 --max-minutes 90
  python3 scripts/backfill-comic-upcs.py --only dc-abs-batman-1,mv-asm-300 --delay 30
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
SEEDS = ROOT / "src/data/comic-locg-seeds.json"
UPC_MAP = ROOT / "src/data/comic-upc-map.json"
COVER_URLS = ROOT / "src/data/comic-cover-urls.json"
COMICS_TS = ROOT / "src/data/comics.ts"
STATS = ROOT / "scripts/comic-upc-backfill-stats.json"
SERIES_CACHE = ROOT / "scripts/comic-locg-series-cache.json"
SKIP_FILE = ROOT / "scripts/comic-upc-skip.json"
CV_KEY_FILE = Path("/home/box/.config/krypton/comicvine-api-key")

UA = (
    "KryptonsToyVault/1.0 (personal collection; upc backfill; "
    "+https://github.com/MonacoCobra/kryptons-toy-vault)"
)

# Prefer publishers that commonly print barcodes on modern singles.
PRIORITY_PUBS = {
    "Marvel Comics",
    "DC Comics",
    "Image Comics",
    "Boom! Studios",
    "IDW Publishing",
    "Dark Horse",
    "Skybound / Image",
    "Valiant",
    "DC Comics / Vertigo",
    "DC Comics / Black Label",
    "DC Comics / WildStorm",
    "Dynamite Entertainment",
    "Dynamite",
    "Dark Horse Comics",
}


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


def locg_cover(locg_id: str, size: str = "large") -> str:
    return f"https://s3.amazonaws.com/comicgeeks/comics/covers/{size}-{locg_id}.jpg"


def fetch(url: str, accept: str = "text/html") -> tuple[str, str]:
    """Fetch LOCG with polite backoff on 403/429 (Shelby: don't look greedy)."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": accept,
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=45) as res:
                return res.read().decode("utf-8", "ignore"), res.geturl()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and attempt < 4:
                # escalate: 90s, 180s, 360s, 600s
                wait = min(600, 90 * (2 ** attempt))
                print(
                    f"  LOCG HTTP {e.code} — backing off {wait}s (polite throttle)",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue
            raise


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
    cover = og.group(1) if og else locg_cover(locg_id, "large")
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


def score_series_hit(h: dict, series: str, publisher: str) -> int:
    want_s = series.lower().split("(")[0].strip()
    want_p = re.sub(r"[^a-z0-9]+", " ", publisher.lower()).strip()
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
    aliases = (
        ({"dc", "dc comics", "dc entertainment"}, want_p, pub),
        ({"marvel", "marvel comics"}, want_p, pub),
        ({"image", "image comics", "skybound", "skybound image"}, want_p, pub),
        ({"boom", "boom studios"}, want_p, pub),
        ({"vertigo", "dc comics vertigo", "dc vertigo"}, want_p, pub),
        ({"dynamite", "dynamite entertainment"}, want_p, pub),
        ({"idw", "idw publishing"}, want_p, pub),
        ({"dark horse", "dark horse comics"}, want_p, pub),
        ({"valiant", "valiant entertainment"}, want_p, pub),
    )
    for group, w, g in aliases:
        if any(x in w for x in group) and any(x in g for x in group):
            s += 4
    if re.search(r"panini|jbc|fomo|marmara|urban comics|other|traducido|webtoon|boxtree|hoz comics|modern times|simon", h["publisher"], re.I):
        s -= 6
    want_fac = bool(re.search(r"\bfacsimile\b", want_s))
    got_fac = bool(re.search(r"\bfacsimile\b", name))
    if want_fac != got_fac:
        s -= 5
    if re.search(r"\b(omnibus|compendium|absolute edition)\b", name) and not re.search(
        r"\b(omnibus|compendium|absolute edition)\b", want_s
    ):
        s -= 4
    # Soft demote anniversary / treasury / starring one-shots vs flagship title
    if re.search(r"\b(treasury|anniversary|starring|vs\.|versus)\b", name) and not re.search(
        r"\b(treasury|anniversary|starring|vs\.|versus)\b", want_s
    ):
        s -= 3
    return s


def rank_series_hits(hits: list[dict], series: str, publisher: str) -> list[dict]:
    ranked = sorted(((score_series_hit(h, series, publisher), h) for h in hits), key=lambda x: -x[0])
    return [h for sc, h in ranked if sc >= 8]


def pick_series(hits: list[dict], series: str, publisher: str) -> dict | None:
    ranked = rank_series_hits(hits, series, publisher)
    return ranked[0] if ranked else None

def parse_series_issues(html: str) -> dict[str, dict]:
    """Map issue number → {locgId, slug, title, main, coverUrl, variants[]} for covers.

    Main covers (data-parent=0) win the primary locgId. Open-order / other variants are
    retained under variants[] so existing catalog variant rows can be matched later —
    we never invent catalog ids.
    """
    out: dict[str, dict] = {}
    for m in re.finditer(
        r'<li[^>]*id="comic-(\d+)"[^>]*data-comic="(\d+)"[^>]*data-parent="(\d+)"[^>]*>([\s\S]*?)</li>',
        html,
        re.I,
    ):
        locg_id, _comic, parent, body = m.group(1), m.group(2), m.group(3), m.group(4)
        title_m = re.search(
            r'class="title[^"]*"[^>]*data-sorting="([^"]+)"|href="/comic/\d+/[^"]+"\s*>\s*([^<]+)',
            body,
            re.I,
        )
        title = (title_m.group(1) or title_m.group(2) or "").strip() if title_m else ""
        slug_m = re.search(rf'/comic/{locg_id}/([a-z0-9\-]+)', body, re.I)
        slug = slug_m.group(1) if slug_m else "issue"
        im = re.search(r"#\s*([0-9]+[A-Za-z]?)\b", title)
        if not im:
            im = re.search(r"-(\d+)(?:-|$)", slug)
        if not im:
            continue
        issue = im.group(1)
        is_main = parent == "0"
        if re.search(r"-vol-|\btp\b|omnibus|hardcover|-hc$", slug, re.I) or looks_like_collected_edition(title):
            continue
        entry = {
            "locgId": locg_id,
            "slug": slug,
            "title": title,
            "main": is_main,
            "coverUrl": locg_cover(locg_id, "large"),
        }
        prev = out.get(issue)
        if not prev:
            if is_main:
                out[issue] = {**entry, "variants": []}
            else:
                # Variant seen before main — stash as variant, placeholder main empty
                out[issue] = {
                    "locgId": locg_id,
                    "slug": slug,
                    "title": title,
                    "main": False,
                    "coverUrl": locg_cover(locg_id, "large"),
                    "variants": [entry],
                }
            continue
        if is_main:
            variants = list(prev.get("variants") or [])
            # If previous "main" was actually a variant placeholder, keep it in variants
            if not prev.get("main") and prev.get("locgId"):
                variants.insert(
                    0,
                    {
                        "locgId": prev["locgId"],
                        "slug": prev.get("slug") or "issue",
                        "title": prev.get("title") or "",
                        "main": False,
                        "coverUrl": prev.get("coverUrl") or locg_cover(prev["locgId"], "large"),
                    },
                )
            out[issue] = {**entry, "variants": variants}
        else:
            variants = list(prev.get("variants") or [])
            if not any(v.get("locgId") == locg_id for v in variants):
                variants.append(entry)
            prev["variants"] = variants
            out[issue] = prev
    # Fallback looser parse if regex above missed
    if not out:
        for m in re.finditer(r'/comic/(\d+)/([a-z0-9\-]+)', html, re.I):
            locg_id, slug = m.group(1), m.group(2)
            im = re.search(r"-(\d+)$", slug)
            if not im:
                continue
            issue = im.group(1)
            if issue not in out:
                out[issue] = {
                    "locgId": locg_id,
                    "slug": slug,
                    "title": slug,
                    "main": True,
                    "coverUrl": locg_cover(locg_id, "large"),
                    "variants": [],
                }
    return out


def fetch_series_issues(series_id: str, *, delay: float = 0.0, throttle=None) -> dict[str, dict]:
    """Fetch all issue→locgId mappings for a series, paginating via list_mode_offset."""
    merged: dict[str, dict] = {}
    offset = 0
    page_size = 300
    seen_pages = 0
    max_pages = 40  # safety: 40*~140 ≈ 5600 rows
    while seen_pages < max_pages:
        q = urllib.parse.urlencode(
            {
                "list": "series",
                "series_id": series_id,
                "title_id": series_id,
                "format": "json",
                "view": "list",
                "list_mode_offset": offset,
                "list_mode_limit": page_size,
            }
        )
        url = f"https://leagueofcomicgeeks.com/comic/get_comics?{q}"
        try:
            if throttle:
                throttle()
            elif delay and seen_pages:
                time.sleep(delay)
            body, _ = fetch(url, accept="application/json")
            data = json.loads(body)
            html = data.get("list") or ""
        except Exception as e:
            print(f"  series issues error {series_id} offset={offset}: {e}", file=sys.stderr)
            break
        page = parse_series_issues(html)
        if not page:
            # still count raw comics — empty parse may mean only TPs
            raw_n = len(re.findall(r'id="comic-\d+"', html))
            if raw_n == 0:
                break
        # Merge page into merged
        new_ids = 0
        for iss, ent in page.items():
            prev = merged.get(iss)
            if not prev:
                merged[iss] = ent
                new_ids += 1
                continue
            # Prefer true main
            if ent.get("main") and not prev.get("main"):
                variants = list(prev.get("variants") or [])
                if prev.get("locgId") and prev["locgId"] != ent.get("locgId"):
                    variants.append(
                        {
                            "locgId": prev["locgId"],
                            "slug": prev.get("slug") or "issue",
                            "title": prev.get("title") or "",
                            "main": False,
                            "coverUrl": prev.get("coverUrl"),
                        }
                    )
                variants.extend(ent.get("variants") or [])
                # dedupe variants
                seen = set()
                uniq = []
                for v in variants:
                    lid = v.get("locgId")
                    if lid and lid not in seen:
                        seen.add(lid)
                        uniq.append(v)
                merged[iss] = {**ent, "variants": uniq}
                new_ids += 1
            else:
                variants = list(prev.get("variants") or [])
                for v in ent.get("variants") or []:
                    if v.get("locgId") and not any(x.get("locgId") == v["locgId"] for x in variants):
                        variants.append(v)
                        new_ids += 1
                if ent.get("locgId") and ent["locgId"] != prev.get("locgId") and not ent.get("main"):
                    if not any(x.get("locgId") == ent["locgId"] for x in variants):
                        variants.append(
                            {
                                "locgId": ent["locgId"],
                                "slug": ent.get("slug") or "issue",
                                "title": ent.get("title") or "",
                                "main": False,
                                "coverUrl": ent.get("coverUrl"),
                            }
                        )
                        new_ids += 1
                prev["variants"] = variants
                merged[iss] = prev
        raw_n = len(re.findall(r'id="comic-\d+"', html))
        seen_pages += 1
        print(
            f"  series {series_id} page@{offset}: raw={raw_n} parsed_issues={len(page)} "
            f"merged={len(merged)} new={new_ids}"
        )
        # Stop when fewer than a full-ish page of raw comics
        if raw_n < 100:
            break
        # Advance by actual rows returned (LOCG pages ~140 even when limit=300)
        offset += raw_n
    return merged


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
    """Pull id→{series,issue,publisher,variant,upc,coverDate,demand,key,format} from comics.ts."""
    text = COMICS_TS.read_text()
    pat = re.compile(
        r'\["([^"]+)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*'
        r'"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*([0-9.]+),\s*"([^"]+)",\s*'
        r'([0-9.]+),\s*([0-9]+),\s*"([^"]*)"',
        re.M,
    )
    out: dict[str, dict] = {}
    for m in pat.finditer(text):
        cid, series, issue, publisher, cover_date = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        fmt, demand, key = m.group(10), float(m.group(11)), int(m.group(12))
        rest = text[m.end() : m.end() + 400]
        variant = None
        upc = None
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
            "series": series,
            "issue": issue,
            "publisher": publisher,
            "coverDate": cover_date,
            "variant": variant,
            "upc": upc,
            "format": fmt,
            "demand": demand,
            "key": key,
        }
    return out


def candidate_score(m: dict, *, series_batch: bool = False) -> float:
    y = 0
    d = m.get("coverDate") or ""
    if d[:4].isdigit():
        y = int(d[:4])
    score = 0.0
    score += min(float(m.get("demand") or 0), 50) * 2
    score += int(m.get("key") or 0) * 20
    issue = str(m.get("issue") or "")
    if series_batch:
        # Prefer barcode-era depth across a series (pagination unlocks many at once)
        if issue in ("1", "0"):
            score += 8
        if y >= 2005:
            score += 12
    else:
        if issue in ("1", "0"):
            score += 55  # LOCG discovery is reliable for #1 via series cover id
        else:
            score -= 12  # non-#1 needs series-list pagination; deprioritize in timed passes
        if y >= 2005:
            score += 3
    if y >= 2010:
        score += 8
    if y >= 2018:
        score += 6
    if (m.get("publisher") or "") in PRIORITY_PUBS:
        score += 5
    if m.get("format") == "facsimile":
        score += 4
    return score


def build_catalog_candidates(
    meta: dict[str, dict],
    upc_map: dict,
    *,
    min_year: int,
    limit: int,
    include_variants: bool = False,
    series_batch: bool = False,
) -> list[str]:
    scored: list[tuple[float, str]] = []
    for cid, m in meta.items():
        if m.get("upc") or (upc_map.get(cid) or {}).get("upc"):
            continue
        if m.get("variant") and not include_variants:
            continue
        fmt = m.get("format") or "single"
        if fmt not in ("single", "facsimile", "one-shot", "annual", "giant"):
            continue
        d = m.get("coverDate") or ""
        y = int(d[:4]) if d[:4].isdigit() else 0
        if y and y < min_year:
            continue
        scored.append((candidate_score(m, series_batch=series_batch), cid))
    scored.sort(key=lambda x: -x[0])
    return [cid for _, cid in scored[:limit]]


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def merge_upc_maps(disk: dict, local: dict) -> dict:
    """Merge local upc_map onto freshly-read disk map without clobbering foreign sources.

    - Prefer existing non-empty UPC over empty
    - Do not replace locg/publisher UPC with empty
    - Preserve fields from disk entries not touched locally when local value lacks upc but disk has one from another source
    """
    out = dict(disk)
    for cid, ent in local.items():
        cur = dict(out.get(cid) or {})
        new = dict(ent or {})
        # If disk has upc and new doesn't, keep disk upc/source
        if cur.get("upc") and not new.get("upc"):
            new["upc"] = cur["upc"]
            if cur.get("source") and not new.get("source"):
                new["source"] = cur["source"]
        # If both have upc and sources differ, keep locg upc unless local is also locg
        if cur.get("upc") and new.get("upc") and cur.get("upc") != new.get("upc"):
            cur_src = str(cur.get("source") or "")
            new_src = str(new.get("source") or "")
            if "locg" in cur_src and "locg" not in new_src:
                new["upc"] = cur["upc"]
                new["source"] = cur_src
        # Preserve locgId from either
        if cur.get("locgId") and not new.get("locgId"):
            new["locgId"] = cur["locgId"]
        if cur.get("coverUrl") and not new.get("coverUrl"):
            new["coverUrl"] = cur["coverUrl"]
        # Merge: local wins on fetchedAt/title when present
        merged = {**cur, **{k: v for k, v in new.items() if v is not None}}
        out[cid] = merged
    return out


def merge_cover_urls(disk: dict, local: dict) -> dict:
    out = dict(disk)
    for cid, url in local.items():
        if not url:
            continue
        existing = out.get(cid)
        # Prefer LOCG comicgeeks covers
        if existing and "comicgeeks" in str(existing) and "comicgeeks" not in str(url):
            continue
        out[cid] = url
    return out


def _locked_json_update(path: Path, merge_fn, local, default):
    """Exclusive flock around read-merge-write so parallel workers don't clobber."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(default, indent=2, sort_keys=True) + "\n")
    with path.open("r+", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.seek(0)
            raw = f.read()
            disk = json.loads(raw) if raw.strip() else default
            merged = merge_fn(disk, local)
            f.seek(0)
            f.truncate()
            f.write(json.dumps(merged, indent=2, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    return merged


def save_upc_map_atomic(local: dict) -> dict:
    return _locked_json_update(UPC_MAP, merge_upc_maps, local, {})


def save_cover_urls_atomic(local: dict) -> dict:
    return _locked_json_update(COVER_URLS, merge_cover_urls, local, {})


def save_series_cache_atomic(local: dict) -> dict:
    def merge(disk, loc):
        out = dict(disk)
        out.update(loc)
        return out
    return _locked_json_update(SERIES_CACHE, merge, local, {})



def publisher_ok(got: str | None, want: str) -> bool:
    if not got:
        return True
    g = re.sub(r"[^a-z0-9]+", " ", got.lower()).strip()
    w = re.sub(r"[^a-z0-9]+", " ", want.lower()).strip()
    if g == w:
        return True
    if w in g or g in w:
        return True
    aliases = {
        "dc comics": {"dc", "dc comics", "dc entertainment"},
        "marvel comics": {"marvel", "marvel comics"},
        "image comics": {"image", "image comics"},
        "skybound / image": {"skybound", "image", "skybound image", "image comics"},
        "boom! studios": {"boom", "boom studios"},
        "dc comics / vertigo": {"vertigo", "dc vertigo", "dc comics vertigo"},
        "dark horse": {"dark horse", "dark horse comics"},
    }
    for canon, al in aliases.items():
        if w == canon or w in al:
            return g in al or g == canon or any(a in g for a in al)
    return False



def looks_like_collected_edition(title: str | None) -> bool:
    if not title:
        return False
    t = title.lower()
    # Absolute Batman / Absolute Superman series titles are OK (series name).
    if re.search(r"\b(omnibus|absolute edition|deluxe edition|compendium|gallery edition|collector'?s edition)\b", t):
        return True
    if re.search(r"\bvol\.?\s*\d+\b", t) and re.search(r"\b(tp|tpb|hc|hardcover|trade)\b", t):
        return True
    if re.search(r"\bnew edition tp\b", t):
        return True
    if re.search(r"\b(tp|tpb)\b", t) and "#" not in title:
        return True
    # Bare hardcover/HC collected editions (not floppy #N)
    if re.search(r"\b(hc|hardcover)\b", t) and not re.search(r"#\s*\d+", title):
        return True
    return False



def series_ok(got_title: str | None, want_series: str) -> bool:
    if not got_title or not want_series:
        return True
    got = re.sub(r"\s*#\s*[0-9A-Za-z]+.*$", "", got_title)
    g = re.sub(r"[^a-z0-9]+", " ", got.lower()).strip()
    w = re.sub(r"[^a-z0-9]+", " ", want_series.lower().split("(")[0]).strip()
    if not w:
        return True
    if g == w or w in g or g in w:
        return True
    wt, gt = set(w.split()), set(g.split())
    # require most meaningful tokens
    meaningful = {t for t in wt if len(t) > 2 and t not in {"the", "and"}}
    if meaningful and len(meaningful & gt) >= max(1, len(meaningful) - 1):
        return True
    return False


def facsimile_ok(catalog_id: str, catalog_format: str | None, hit_title: str | None, hit_url: str | None = None) -> bool:
    is_fac = (catalog_format or "").lower() == "facsimile" or catalog_id.endswith("-fac")
    if not is_fac:
        return True
    blob = f"{hit_title or ''} {hit_url or ''}".lower()
    return "facsimile" in blob

def format_compatible(catalog_format: str | None, hit_title: str | None) -> bool:
    fmt = (catalog_format or "single").lower()
    if fmt in ("single", "facsimile", "one-shot", "annual", "giant"):
        return not looks_like_collected_edition(hit_title)
    return True


def issue_norm(v: str | None) -> str:
    if not v:
        return ""
    return str(v).lstrip("#").lower().strip()



def publisher_group(publisher: str) -> str:
    """Partition key for parallel workers: marvel | dc | other (disjoint)."""
    p = (publisher or "").lower()
    if "marvel" in p:
        return "marvel"
    if (
        "dc comics" in p
        or p.startswith("dc ")
        or p == "dc"
        or "vertigo" in p
        or "black label" in p
        or "wildstorm" in p
        or "wildstorm" in p
        or "milestone" in p
    ):
        return "dc"
    return "other"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=40, help="Max comics to attempt")
    ap.add_argument("--delay", type=float, default=90.0, help="Seconds between LOCG requests (robots Crawl-delay=30; we use 90+ when 403s appear)")
    ap.add_argument("--only", type=str, default="", help="Comma-separated comic ids")
    ap.add_argument("--seeds-only", action="store_true", help="Only process seeded locgIds")
    ap.add_argument("--from-catalog", action="store_true", help="Prioritize popular modern catalog singles missing UPC")
    ap.add_argument("--ones-only", action="store_true", help="Only attempt issue #1 / nn / 0 (best LOCG hit rate)")
    ap.add_argument("--min-year", type=int, default=1995, help="Min cover year for --from-catalog")
    ap.add_argument("--max-minutes", type=float, default=0, help="Stop starting new LOCG work after N minutes (0=no limit)")
    ap.add_argument("--cv-sweep", action="store_true", help="After LOCG pass, Comic Vine barcode sweep for remaining candidates")
    ap.add_argument("--cv-sweep-limit", type=int, default=400, help="Max extra CV barcode lookups")
    ap.add_argument("--no-cv", action="store_true", help="Skip Comic Vine barcode fallback")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--series-batch",
        action="store_true",
        help="Group catalog candidates by series; paginate full LOCG issue lists; maximize UPC/cover throughput",
    )
    ap.add_argument(
        "--refresh-lists",
        action="store_true",
        help="Force re-fetch of LOCG series issue lists even when cache has entries",
    )
    ap.add_argument(
        "--max-series",
        type=int,
        default=0,
        help="With --series-batch, stop after N series groups (0=no limit)",
    )
    ap.add_argument(
        "--max-per-series",
        type=int,
        default=0,
        help="With --series-batch, cap comics per series (0=no cap; recent issues kept first)",
    )
    ap.add_argument(
        "--publisher-group",
        choices=["marvel", "dc", "other", "all"],
        default="all",
        help="Partition catalog work for parallel LOCG workers (disjoint marvel/dc/other)",
    )
    ap.add_argument(
        "--publishers",
        type=str,
        default="",
        help="Comma-separated publisher substrings to include (optional; applied after --publisher-group)",
    )
    ap.add_argument(
        "--stats-file",
        type=str,
        default="",
        help="Override stats JSON path (per-worker)",
    )
    ap.add_argument(
        "--worker-id",
        type=str,
        default="",
        help="Label printed in logs for parallel workers",
    )
    args = ap.parse_args()

    global STATS
    if args.stats_file:
        STATS = Path(args.stats_file)
    worker = args.worker_id or args.publisher_group or "main"
    seeds = load_json(SEEDS, {})
    upc_map = load_json(UPC_MAP, {})
    cover_urls = load_json(COVER_URLS, {})
    series_cache = load_json(SERIES_CACHE, {})
    skip_ids = load_json(SKIP_FILE, {})
    meta = parse_comics_meta()
    before_upc = len([1 for v in upc_map.values() if v.get("upc")])
    before_covers = len(cover_urls)

    if args.only:
        ids = [x.strip() for x in args.only.split(",") if x.strip()]
    elif args.from_catalog:
        # Pure popularity/modern ranking. Skip rows already confirmed locg_no_upc+cover.
        cat_pool = max(args.limit * (8 if args.series_batch else 4), args.limit)
        catalog_ids = build_catalog_candidates(
            meta,
            upc_map,
            min_year=args.min_year,
            limit=cat_pool,
            series_batch=bool(args.series_batch),
        )
        ids = []
        seen = set()
        for cid in catalog_ids:
            if cid in seen:
                continue
            ent = upc_map.get(cid) or {}
            if ent.get("locgId") and not ent.get("upc") and cid in cover_urls:
                continue
            seen.add(cid)
            ids.append(cid)
        ids = ids[: args.limit]
        print("catalog top sample:", ", ".join(ids[:12]))
    else:
        ids = list(seeds.keys())
        for cid in cover_urls:
            if cid not in ids:
                ids.append(cid)
        ids = ids[: args.limit]

    if args.seeds_only:
        ids = [i for i in ids if seeds.get(i, {}).get("locgId")]

    if args.ones_only:
        ids = [
            i
            for i in ids
            if str((meta.get(i) or {}).get("issue") or "").lstrip("#").lower() in ("1", "0", "nn")
        ]

    # Facsimile discovery needs dedicated LOCG facsimile series ids; skip in timed UPC sweeps.
    if args.from_catalog:
        ids = [
            i
            for i in ids
            if (meta.get(i) or {}).get("format") != "facsimile" and not i.endswith("-fac")
        ]

    if skip_ids:
        ids = [i for i in ids if i not in skip_ids]

    # Publisher partition for parallel workers (disjoint).
    if args.publisher_group and args.publisher_group != "all":
        ids = [
            i
            for i in ids
            if publisher_group((meta.get(i) or {}).get("publisher") or "") == args.publisher_group
        ]
    if args.publishers:
        want = [x.strip().lower() for x in args.publishers.split(",") if x.strip()]
        ids = [
            i
            for i in ids
            if any(w in ((meta.get(i) or {}).get("publisher") or "").lower() for w in want)
        ]
    # Drop ids another worker already filled
    upc_map = load_json(UPC_MAP, {})
    ids = [i for i in ids if not (upc_map.get(i) or {}).get("upc")]


    # Series-batch: prefer deep series so one paginated LOCG list unlocks many UPCs.
    if args.series_batch:
        # Rebuild from a wide modern pool, then keep the largest series groups.
        pool_limit = max(args.limit * 20, 12000)
        pool = build_catalog_candidates(
            meta,
            upc_map,
            min_year=args.min_year,
            limit=pool_limit,
            series_batch=True,
        )
        if args.ones_only:
            pool = [
                i
                for i in pool
                if str((meta.get(i) or {}).get("issue") or "").lstrip("#").lower()
                in ("1", "0", "nn")
            ]
        pool = [
            i
            for i in pool
            if i not in skip_ids
            and (meta.get(i) or {}).get("format") != "facsimile"
            and not i.endswith("-fac")
        ]
        if args.publisher_group and args.publisher_group != "all":
            pool = [
                i
                for i in pool
                if publisher_group((meta.get(i) or {}).get("publisher") or "") == args.publisher_group
            ]
        # Skip ids already LOCG-resolved without UPC (cover baked) — don't re-crawl
        pool = [
            i
            for i in pool
            if not (
                (upc_map.get(i) or {}).get("locgId")
                and not (upc_map.get(i) or {}).get("upc")
                and i in cover_urls
            )
        ]
        if args.publishers:
            want = [x.strip().lower() for x in args.publishers.split(",") if x.strip()]
            pool = [
                i
                for i in pool
                if any(w in ((meta.get(i) or {}).get("publisher") or "").lower() for w in want)
            ]
        # If --only was set, intersect; else replace ids with deep series selection
        if args.only:
            only_set = set(ids)
            pool = [i for i in pool if i in only_set] or ids
        groups: dict[str, list[str]] = {}
        for cid in pool:
            m = meta.get(cid) or {}
            gk = f"{m.get('series') or cid}||{m.get('publisher') or ''}"
            groups.setdefault(gk, []).append(cid)
        # Sort issues within series by numeric issue when possible (recent first)
        def issue_sort_key(cid: str):
            iss = str((meta.get(cid) or {}).get("issue") or "")
            digits = "".join(ch for ch in iss if ch.isdigit())
            return (-int(digits) if digits else 0, iss)

        for gk in groups:
            groups[gk].sort(key=issue_sort_key)

        def series_rank(gk: str) -> tuple:
            ids_g = groups[gk]
            n = len(ids_g)
            pub = gk.split("||", 1)[-1] if "||" in gk else ""
            # Barcode-era US singles first; demote UK/digest/newspaper-heavy pubs
            if any(x in pub for x in ("Marvel", "DC Comics", "Image", "Boom", "IDW", "Dark Horse", "Dynamite", "Valiant", "Skybound")):
                pri = 3.0
            elif pub in PRIORITY_PUBS:
                pri = 2.0
            elif any(x in pub.lower() for x in ("2000 ad", "rebellion", "archie", "panini", "manga")):
                pri = 0.25
            else:
                pri = 0.7
            modern = 0
            for cid in ids_g:
                d = (meta.get(cid) or {}).get("coverDate") or ""
                if d[:4].isdigit() and int(d[:4]) >= 2005:
                    modern += 1
            modern_ratio = modern / max(n, 1)
            score = n * pri * (0.55 + 0.45 * modern_ratio)
            return (-score, -n, gk)

        ordered_keys = sorted(groups.keys(), key=series_rank)
        if args.max_series and args.max_series > 0:
            ordered_keys = ordered_keys[: args.max_series]
        # Fill up to limit preferring largest series wholly, then partial last series
        ids = []
        kept_keys = []
        for k in ordered_keys:
            chunk = groups[k]
            if args.max_per_series and args.max_per_series > 0:
                chunk = chunk[: args.max_per_series]
            if not ids and len(chunk) > args.limit:
                ids.extend(chunk[: args.limit])
                kept_keys.append(k)
                break
            if len(ids) + len(chunk) > args.limit and ids:
                remain = args.limit - len(ids)
                if remain > 0:
                    ids.extend(chunk[:remain])
                    kept_keys.append(k)
                break
            ids.extend(chunk)
            kept_keys.append(k)
            if len(ids) >= args.limit:
                break
        kept_sizes = []
        # Recompute kept chunk sizes for logging
        cursor = 0
        for k in kept_keys:
            chunk = groups[k]
            if args.max_per_series and args.max_per_series > 0:
                chunk = chunk[: args.max_per_series]
            take = min(len(chunk), max(0, len(ids) - cursor))
            # approximate by scanning ids membership count for this series
            n = sum(1 for cid in ids if f"{(meta.get(cid) or {}).get('series')}||{(meta.get(cid) or {}).get('publisher')}" == k)
            kept_sizes.append(n)
            cursor += n
        print(
            f"series-batch: {len(kept_keys)} series groups, {len(ids)} comics "
            f"(kept sizes: {', '.join(str(n) for n in kept_sizes[:8])})"
        )


    # Re-assert publisher partition after series-batch rebuild
    if args.publisher_group and args.publisher_group != "all":
        ids = [
            i
            for i in ids
            if publisher_group((meta.get(i) or {}).get("publisher") or "") == args.publisher_group
        ]
    if args.publishers:
        want = [x.strip().lower() for x in args.publishers.split(",") if x.strip()]
        ids = [
            i
            for i in ids
            if any(w in ((meta.get(i) or {}).get("publisher") or "").lower() for w in want)
        ]
    upc_map = load_json(UPC_MAP, upc_map)
    ids = [i for i in ids if not (upc_map.get(i) or {}).get("upc")]

    print(
        f"backfill[{worker}]: {len(ids)} comics, delay={args.delay}s, publisher_group={args.publisher_group}, "
        f"from_catalog={args.from_catalog}, seeds_only={args.seeds_only}, "
        f"max_minutes={args.max_minutes or '∞'}"
    )
    print(f"before: upc={before_upc} covers={before_covers}")

    stats = {
        "startedAt": now_iso(),
        "attempted": 0,
        "upcFilled": 0,
        "coverUpdated": 0,
        "locgHits": 0,
        "locgNoUpc": 0,
        "cvFallbackUpc": 0,
        "cvSweepUpc": 0,
        "skippedExisting": 0,
        "errors": 0,
        "mismatchPublisher": 0,
        "mismatchIssue": 0,
        "seriesResolved": 0,
        "coversFromSeriesList": 0,
        "seriesBatch": bool(getattr(args, "series_batch", False)),
        "timedOut": False,
        "details": [],
        "beforeUpc": before_upc,
        "beforeCovers": before_covers,
    }

    started = time.time()
    last_locg_at = 0.0
    deadline = started + args.max_minutes * 60 if args.max_minutes and args.max_minutes > 0 else None

    def time_left() -> bool:
        return deadline is None or time.time() < deadline

    def throttle():
        nonlocal last_locg_at
        wait = args.delay - (time.time() - last_locg_at)
        if wait > 0:
            time.sleep(wait)
        last_locg_at = time.time()

    def cache_key(series: str, publisher: str) -> str:
        return f"{series}||{publisher}"

    def resolve_series(series: str, publisher: str, need_issue: str = "1") -> dict | None:
        nonlocal series_cache
        ck = cache_key(series, publisher)
        cached = series_cache.get(ck)
        want = issue_norm(need_issue)
        if cached and cached.get("seriesId"):
            issues = cached.get("issues") or {}
            rich = bool(cached.get("listFetchedAt")) or len(issues) >= 25
            force = bool(getattr(args, "refresh_lists", False)) or (
                bool(getattr(args, "series_batch", False)) and not rich
            )
            if not force:
                if want in ("1", "0", "nn") and (cached.get("coverComicId") or issues.get("1")):
                    return cached
                if want in issues:
                    return cached
                # Rich list already fetched — a missing issue number will not appear by
                # re-paginating (avoids Detective Comics / ASM burning hours per miss).
                if rich:
                    return cached
            # fall through to refresh issue list if we need a missing issue / full list
        if not time_left():
            return cached
        throttle()
        hits = search_locg_series(series)
        candidates = rank_series_hits(hits, series, publisher)
        if not candidates:
            series_cache[ck] = {"seriesId": None, "issues": {}, "failedAt": now_iso()}
            if not args.dry_run:
                series_cache = save_series_cache_atomic(series_cache)
            return None
        rejected = list((cached or {}).get("rejectedSeriesIds") or [])
        # Prefer previously-good seriesId first when present among candidates
        if cached and cached.get("seriesId"):
            sid0 = str(cached.get("seriesId"))
            good = [c for c in candidates if str(c.get("seriesId")) == sid0]
            rest = [c for c in candidates if str(c.get("seriesId")) != sid0]
            candidates = good + rest
        # Skip known-thin / wrong volumes unless nothing else left
        preferred = [c for c in candidates if str(c.get("seriesId")) not in set(rejected)]
        if preferred:
            candidates = preferred
        entry = None
        for picked in candidates[:8]:
            if not time_left():
                break
            stats["seriesResolved"] += 1
            trial = {
                "seriesId": picked["seriesId"],
                "name": picked.get("name"),
                "publisher": picked.get("publisher"),
                "coverComicId": picked.get("coverComicId"),
                "issues": {},
                "resolvedAt": now_iso(),
                "rejectedSeriesIds": rejected,
            }
            # Seed #1 from cover when present
            if picked.get("coverComicId"):
                trial["issues"]["1"] = {
                    "locgId": picked["coverComicId"],
                    "slug": "issue",
                    "title": f"{series} #1",
                    "main": True,
                    "coverUrl": locg_cover(picked["coverComicId"], "large"),
                    "variants": [],
                }
            force_list = bool(getattr(args, "refresh_lists", False) or getattr(args, "series_batch", False))
            need_list = force_list or (want not in ("1", "0", "nn") and want not in trial["issues"])
            if not need_list and len(trial["issues"]) < 3 and want not in ("1", "0", "nn"):
                need_list = True
            if need_list and time_left():
                issues = fetch_series_issues(picked["seriesId"], throttle=throttle)
                for iss, ent in issues.items():
                    trial["issues"][iss] = ent
                if picked.get("coverComicId") and "1" in trial["issues"]:
                    cur = trial["issues"]["1"]
                    # keep fetched main; only fill if missing
                    if not cur.get("locgId"):
                        trial["issues"]["1"] = {
                            "locgId": picked["coverComicId"],
                            "slug": cur.get("slug") or "issue",
                            "title": cur.get("title") or f"{series} #1",
                            "main": True,
                            "coverUrl": locg_cover(picked["coverComicId"], "large"),
                            "variants": list(cur.get("variants") or []),
                        }
                trial["listFetchedAt"] = now_iso()
                trial["listIssueCount"] = len(trial["issues"])
            has_want = want in trial["issues"] or (
                want.isdigit() and str(int(want)) in trial["issues"]
            )
            rich = len(trial["issues"]) >= 25
            thin = len(trial["issues"]) < 5
            if has_want:
                entry = trial
                print(
                    f"  series pick ok id={picked['seriesId']} issues={len(trial['issues'])} has#{want}"
                )
                break
            if thin or (rich and want not in ("1", "0", "nn") and not has_want):
                sid = str(picked["seriesId"])
                if sid not in rejected:
                    rejected.append(sid)
                trial["rejectedSeriesIds"] = rejected
                print(
                    f"  series pick skip id={picked['seriesId']} issues={len(trial['issues'])} missing#{want}"
                )
                # keep best rich entry as fallback even if issue missing (covers still useful)
                if entry is None or len(trial["issues"]) > len(entry.get("issues") or {}):
                    entry = trial
                continue
            # medium-size list without want — keep as fallback, try next
            if entry is None or len(trial["issues"]) > len(entry.get("issues") or {}):
                entry = trial
            print(
                f"  series pick try-next id={picked['seriesId']} issues={len(trial['issues'])} missing#{want}"
            )
        if not entry:
            series_cache[ck] = {"seriesId": None, "issues": {}, "failedAt": now_iso(), "rejectedSeriesIds": rejected}
            if not args.dry_run:
                series_cache = save_series_cache_atomic(series_cache)
            return None
        entry["rejectedSeriesIds"] = rejected
        # If we landed on a volume that has the issue, clear thin rejects staying attached
        series_cache[ck] = entry
        if not args.dry_run:
            series_cache = save_series_cache_atomic(series_cache)
        return entry

    for cid in ids:
        if not time_left():
            stats["timedOut"] = True
            print(f"⏱ time budget reached after {stats['attempted']} attempts")
            break

        # Peer workers may have filled this id — re-read under lock-friendly load
        try:
            upc_map = load_json(UPC_MAP, upc_map)
            cover_urls = load_json(COVER_URLS, cover_urls)
        except Exception:
            pass

        m = meta.get(cid) or {}
        seed = seeds.get(cid) or {}
        existing = upc_map.get(cid) or {}
        if existing.get("upc"):
            stats["skippedExisting"] += 1
            continue
        if existing.get("upc") and existing.get("coverUrl") and cid in cover_urls:
            stats["skippedExisting"] += 1
            continue

        stats["attempted"] += 1
        series = m.get("series") or cid
        issue = m.get("issue") or "1"
        publisher = m.get("publisher") or ""
        detail = {"id": cid, "series": series, "issue": issue}
        want_issue = issue_norm(issue)

        hit = None
        locg_id = seed.get("locgId")
        slug = seed.get("slug") or "issue"
        series_issue_meta = None

        if locg_id:
            if not time_left():
                stats["timedOut"] = True
                break
            throttle()
            hit = fetch_locg(str(locg_id), slug)
        elif not args.seeds_only:
            # Series-aware discovery
            search_series = series
            if (m.get("format") == "facsimile") or cid.endswith("-fac"):
                search_series = f"{series} Facsimile"
            resolved = resolve_series(search_series, publisher, issue)
            if not resolved or not resolved.get("seriesId"):
                resolved = resolve_series(series, publisher, issue)
            detail["seriesPick"] = (resolved or {}).get("seriesId")
            if resolved and resolved.get("issues"):
                series_issue_meta = resolved["issues"].get(want_issue) or resolved["issues"].get(
                    issue_norm(want_issue)
                )
                # Also try bare numeric
                if not series_issue_meta and want_issue.isdigit():
                    series_issue_meta = resolved["issues"].get(str(int(want_issue)))
            if series_issue_meta and series_issue_meta.get("locgId"):
                # Bake cover early from series list main match (solid series+issue)
                if series_issue_meta.get("main", True) and series_issue_meta.get("coverUrl"):
                    if not args.dry_run and cid not in cover_urls:
                        cover_urls[cid] = series_issue_meta["coverUrl"]
                        stats["coverUpdated"] += 1
                        stats["coversFromSeriesList"] += 1
                if not time_left():
                    # Keep cover; skip issue page for UPC this round
                    if not args.dry_run:
                        upc_map[cid] = {
                            **(upc_map.get(cid) or {}),
                            "locgId": series_issue_meta["locgId"],
                            "coverUrl": series_issue_meta.get("coverUrl"),
                            "source": "locg-series-list",
                            "title": series_issue_meta.get("title"),
                            "fetchedAt": now_iso(),
                        }
                    detail["status"] = "series_list_cover_only"
                    stats["details"].append(detail)
                    continue
                throttle()
                hit = fetch_locg(series_issue_meta["locgId"], series_issue_meta.get("slug") or "issue")
            elif resolved and resolved.get("coverComicId") and want_issue in ("1", "nn", "0"):
                if not time_left():
                    break
                throttle()
                hit = fetch_locg(resolved["coverComicId"], slug)

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

            if not format_compatible(m.get("format"), hit.get("title")):
                stats["errors"] += 1
                detail["status"] = "format_mismatch"
                detail["title"] = hit.get("title")
                stats["details"].append(detail)
                print(f"! {cid}: format mismatch title={hit.get('title')} want_format={m.get('format')}")
                skip_ids[cid] = f"format_mismatch:{hit.get('title')}"
                if not args.dry_run:
                    save_json(SKIP_FILE, skip_ids)
                continue

            if not series_ok(hit.get("title"), series):
                stats["mismatchIssue"] += 1
                detail["status"] = "series_mismatch"
                detail["title"] = hit.get("title")
                stats["details"].append(detail)
                print(f"! {cid}: series mismatch title={hit.get('title')} want={series}")
                skip_ids[cid] = f"series_mismatch:{hit.get('title')}"
                if not args.dry_run:
                    save_json(SKIP_FILE, skip_ids)
                continue

            if not facsimile_ok(cid, m.get("format"), hit.get("title"), hit.get("url")):
                stats["errors"] += 1
                detail["status"] = "facsimile_mismatch"
                detail["title"] = hit.get("title")
                stats["details"].append(detail)
                print(f"! {cid}: facsimile mismatch title={hit.get('title')}")
                skip_ids[cid] = f"facsimile_mismatch:{hit.get('title')}"
                if not args.dry_run:
                    save_json(SKIP_FILE, skip_ids)
                continue

            if hit.get("issue") and want_issue not in ("nn", "") and issue_norm(hit["issue"]) != want_issue:
                if not locg_id:
                    stats["mismatchIssue"] += 1
                    detail["status"] = "issue_mismatch"
                    detail["gotIssue"] = hit.get("issue")
                    stats["details"].append(detail)
                    print(f"! {cid}: issue mismatch got=#{hit.get('issue')} want=#{issue}")
                    continue

            entry = {
                "upc": hit.get("upc"),
                "locgId": hit.get("locgId"),
                "coverUrl": hit.get("coverUrl") or locg_cover(hit["locgId"], "large"),
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
            if not args.dry_run:
                upc_map[cid] = {k: v for k, v in entry.items() if v}
                if entry.get("coverUrl") and (hit.get("upc") or locg_id or series_issue_meta):
                    cover_urls[cid] = entry["coverUrl"]
                    stats["coverUpdated"] += 1
            print(f"✓ {cid}: upc={entry.get('upc') or '—'} locg={entry.get('locgId')} {hit.get('title')}")
            stats["details"].append(detail)

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
            if not args.dry_run:
                upc_map = save_upc_map_atomic(upc_map)
                cover_urls = save_cover_urls_atomic(cover_urls)
                save_json(STATS, {**stats, "details": stats["details"][-80:]})
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
                    # Only bake CV cover if we have no LOCG cover yet
                    if cv.get("coverUrl") and cid not in cover_urls:
                        cover_urls[cid] = cv["coverUrl"]
                        stats["coverUpdated"] += 1
                print(f"✓ {cid}: CV-only upc={cv['upc']}")
                stats["details"].append(detail)
                if not args.dry_run:
                    upc_map = save_upc_map_atomic(upc_map)
                    cover_urls = save_cover_urls_atomic(cover_urls)
                continue

        stats["errors"] += 1
        detail["status"] = "missing"
        stats["details"].append(detail)
        print(f"· {cid}: no LOCG/CV upc")
        if not args.dry_run and stats["attempted"] % 10 == 0:
            upc_map = save_upc_map_atomic(upc_map)
            cover_urls = save_cover_urls_atomic(cover_urls)

    # Optional CV sweep for broader UPC fill (still never invents)
    if args.cv_sweep and not args.no_cv:
        print("--- CV barcode sweep ---")
        sweep_ids = build_catalog_candidates(
            meta, upc_map, min_year=args.min_year, limit=args.cv_sweep_limit
        )
        for cid in sweep_ids:
            if (upc_map.get(cid) or {}).get("upc"):
                continue
            m = meta.get(cid) or {}
            series = m.get("series") or cid
            issue = m.get("issue") or "1"
            time.sleep(1.1)  # polite CV pacing
            cv = cv_barcode(series, issue)
            if not cv or not cv.get("upc"):
                continue
            stats["cvSweepUpc"] += 1
            stats["upcFilled"] += 1
            stats["attempted"] += 1
            if not args.dry_run:
                entry = upc_map.get(cid) or {}
                entry.update(
                    {
                        "upc": cv["upc"],
                        "source": ("locg+comicvine-barcode" if entry.get("locgId") else "comicvine-barcode"),
                        "fetchedAt": now_iso(),
                    }
                )
                if cv.get("coverUrl") and not entry.get("coverUrl"):
                    entry["coverUrl"] = cv["coverUrl"]
                upc_map[cid] = entry
                if entry.get("locgId") and entry.get("coverUrl") and "comicgeeks" in str(entry.get("coverUrl")):
                    cover_urls[cid] = entry["coverUrl"]
                    stats["coverUpdated"] += 1
                elif cid not in cover_urls and cv.get("coverUrl"):
                    # Prefer not overwriting LOCG; only set if empty
                    cover_urls[cid] = cv["coverUrl"]
                    stats["coverUpdated"] += 1
            print(f"✓ {cid}: CV-sweep upc={cv['upc']}")
            if stats["cvSweepUpc"] % 25 == 0 and not args.dry_run:
                upc_map = save_upc_map_atomic(upc_map)
                cover_urls = save_cover_urls_atomic(cover_urls)

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
    stats["elapsedMinutes"] = round((time.time() - started) / 60, 2)
    stats["upcMapSize"] = len([1 for v in upc_map.values() if v.get("upc")])
    stats["coverUrlSize"] = len(cover_urls)
    stats["afterUpc"] = stats["upcMapSize"]
    stats["afterCovers"] = stats["coverUrlSize"]
    stats["delay"] = args.delay
    stats["limit"] = args.limit
    stats["fromCatalog"] = args.from_catalog

    if not args.dry_run:
        upc_map = save_upc_map_atomic(upc_map)
        cover_urls = save_cover_urls_atomic(cover_urls)
        series_cache = save_series_cache_atomic(series_cache)
        # Trim details for stats file size but keep summary counts
        save_json(STATS, stats)

    summary = {k: stats[k] for k in stats if k != "details"}
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
