#!/usr/bin/env python3
"""Backfill comic UPC/ISBN from Grand Comics Database (comics.org) public API.

Uses Accept: application/json against https://www.comics.org/api/
Never invents codes. Never overwrites an existing UPC in comic-upc-map.json.

Flow:
  catalog series(+year) → /api/series/name/{name}/year/{year}/
  → pick best series → issue descriptors → /api/issue/{id}/ → barcode/isbn

Examples:
  python3 scripts/backfill-comic-upcs-gcd.py --limit 40 --delay 0.5 --dry-run
  python3 scripts/backfill-comic-upcs-gcd.py --limit 200 --min-year 2005
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
UPC_MAP = ROOT / "src/data/comic-upc-map.json"
COVER_URLS = ROOT / "src/data/comic-cover-urls.json"
COMICS_TS = ROOT / "src/data/comics.ts"
STATS = ROOT / "scripts/comic-upc-gcd-stats.json"
SERIES_CACHE = ROOT / "scripts/comic-gcd-series-cache.json"

UA = (
    "KryptonsToyVault/1.0 (personal collection; gcd upc backfill; "
    "+https://github.com/MonacoCobra/kryptons-toy-vault)"
)
API = "https://www.comics.org/api"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_upc(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("111111"):
        return None
    if 11 <= len(digits) <= 18:
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
        series, issue, publisher = m.group(2), m.group(3), m.group(4)
        cover_date = m.group(10)
        out[cid] = {
            "series": series,
            "issue": issue,
            "publisher": publisher,
            "coverDate": cover_date,
        }
    return out


def series_base_and_year(series: str) -> tuple[str, int | None]:
    s = (series or "").strip()
    ym = re.search(r"\((19|20)\d{2}\)\s*$", s)
    year = int(ym.group(0)[1:5]) if ym else None
    base = re.sub(r"\s*\((19|20)\d{2}\)\s*$", "", s).strip()
    return base, year


def cover_year(meta: dict) -> int | None:
    _, sy = series_base_and_year(meta.get("series") or "")
    if sy:
        return sy
    cd = str(meta.get("coverDate") or "")
    m = re.search(r"(19|20)\d{2}", cd)
    return int(m.group(0)) if m else None


def issue_key(issue: str) -> str | None:
    iss = str(issue or "").lstrip("#").strip()
    if not iss:
        return None
    if re.match(r"^\d", iss):
        try:
            return str(int(float(re.split(r"[^\d.]", iss, maxsplit=1)[0])))
        except Exception:
            return iss
    return iss


def http_get_json(url: str, delay: float) -> dict | list | None:
    if delay > 0:
        time.sleep(delay)
    if "format=" not in url:
        join = "&" if "?" in url else "?"
        url = f"{url}{join}format=json"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                wait = min(60, 5 * (2 ** attempt))
                print(f"  HTTP 429 — backing off {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  HTTP {e.code} {url}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"  GET error {url}: {e}", file=sys.stderr)
            return None
    return None


def search_series(name: str, year: int | None, delay: float) -> list[dict]:
    enc = urllib.parse.quote(name)
    if year:
        url = f"{API}/series/name/{enc}/year/{year}/"
    else:
        url = f"{API}/series/name/{enc}/"
    data = http_get_json(url, delay)
    if not isinstance(data, dict):
        return []
    return list(data.get("results") or [])


def pick_series(results: list[dict], name: str, year: int | None) -> dict | None:
    if not results:
        return None
    name_l = name.strip().lower()
    exact = [r for r in results if (r.get("name") or "").strip().lower() == name_l]
    pool = exact or results
    if year is not None:
        yeared = [r for r in pool if r.get("year_began") == year]
        if yeared:
            pool = yeared
        else:
            # allow began within ±1
            near = [r for r in pool if isinstance(r.get("year_began"), int) and abs(r["year_began"] - year) <= 1]
            if near:
                pool = near
    # prefer US english
    us = [r for r in pool if (r.get("country") or "").lower() == "us"]
    pool = us or pool
    # prefer more issues (mainline)
    pool.sort(key=lambda r: (-len(r.get("active_issues") or []), r.get("year_began") or 0))
    return pool[0]


def descriptor_issue_num(desc: str) -> str | None:
    d = (desc or "").strip()
    if not d:
        return None
    # plain number
    if re.fullmatch(r"\d+", d):
        return d
    # "12 (813)" style
    m = re.match(r"^(\d+)\s*\(", d)
    if m:
        return m.group(1)
    # leading number before variant text
    m = re.match(r"^(\d+)\b", d)
    if m and "[" not in d[: m.end() + 1]:
        # still may be variant without bracket; treat as main only if no 'variant' word
        if re.search(r"variant|cover|edition|virgin|foil", d, re.I):
            return None
        return m.group(1)
    return None


def is_main_descriptor(desc: str) -> bool:
    d = (desc or "").strip()
    if re.search(r"variant|virgin|foil|blank cover|incentive|exclusive", d, re.I):
        return False
    if "[" in d:
        return False
    return descriptor_issue_num(d) is not None


def build_issue_index(series: dict) -> dict[str, str]:
    """issue number → first main-ish issue API url."""
    descs = series.get("issue_descriptors") or []
    urls = series.get("active_issues") or []
    idx: dict[str, str] = {}
    # first pass: prefer main descriptors
    for desc, url in zip(descs, urls):
        if not is_main_descriptor(desc):
            continue
        num = descriptor_issue_num(desc)
        if num and num not in idx:
            idx[num] = url
    # second pass: any non-variant-looking if still missing
    for desc, url in zip(descs, urls):
        num = descriptor_issue_num(desc)
        if not num or num in idx:
            continue
        if re.search(r"variant|virgin|foil|exclusive", desc or "", re.I):
            continue
        idx[num] = url
    return idx


def merge_upc(disk: dict, local: dict) -> dict:
    out = dict(disk)
    for cid, new in local.items():
        cur = dict(out.get(cid) or {})
        if cur.get("upc") and not new.get("upc"):
            continue
        if cur.get("upc") and new.get("upc") and cur.get("upc") != new.get("upc"):
            # keep existing (esp. locg)
            continue
        cur.update({k: v for k, v in new.items() if v is not None})
        out[cid] = cur
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--delay", type=float, default=1.5)
    ap.add_argument("--min-year", type=int, default=2005)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", type=str, default="")
    args = ap.parse_args()

    meta = parse_comics_meta()
    upc_map = load_json(UPC_MAP, {})
    cover_urls = load_json(COVER_URLS, {})
    series_cache = load_json(SERIES_CACHE, {})

    if args.only:
        ids = [x.strip() for x in args.only.split(",") if x.strip()]
    else:
        ids = [
            cid
            for cid, m in meta.items()
            if not (upc_map.get(cid) or {}).get("upc")
            and (cover_year(m) is None or cover_year(m) >= args.min_year)
        ]
    ids = ids[: args.limit]
    before = len([1 for v in upc_map.values() if isinstance(v, dict) and v.get("upc")])

    local: dict = {}
    details = []
    filled = 0
    skipped = 0
    no_series = 0
    no_issue = 0
    no_barcode = 0
    errors = 0

    print(f"gcd backfill: {len(ids)} candidates, delay={args.delay}, min_year={args.min_year}")
    print(f"before upc={before}")

    for cid in ids:
        m = meta.get(cid) or {}
        if (upc_map.get(cid) or {}).get("upc") or (local.get(cid) or {}).get("upc"):
            skipped += 1
            continue
        base, sy = series_base_and_year(m.get("series") or "")
        year = sy or cover_year(m)
        iss = issue_key(m.get("issue") or "")
        if not base or not iss:
            no_issue += 1
            continue
        if year is None:
            no_series += 1
            details.append({"id": cid, "status": "no_year", "series": base})
            print(f"· {cid}: skip (no series/cover year for safe GCD search)")
            continue

        cache_key = f"{base.lower()}|{year or ''}"
        series = series_cache.get(cache_key)
        if not series:
            results = search_series(base, year, args.delay)
            series = pick_series(results, base, year)
            if series:
                # store slim
                series_cache[cache_key] = {
                    "api_url": series.get("api_url"),
                    "name": series.get("name"),
                    "year_began": series.get("year_began"),
                    "active_issues": series.get("active_issues"),
                    "issue_descriptors": series.get("issue_descriptors"),
                    "country": series.get("country"),
                }
                # periodic cache flush
                if len(series_cache) % 10 == 0 and not args.dry_run:
                    save_json(SERIES_CACHE, series_cache)
            else:
                no_series += 1
                details.append({"id": cid, "status": "no_series", "series": base, "year": year})
                print(f"· {cid}: no GCD series for {base!r} ({year})")
                continue

        idx = build_issue_index(series)
        url = idx.get(iss)
        if not url:
            no_issue += 1
            details.append({"id": cid, "status": "no_issue", "series": base, "issue": iss})
            print(f"· {cid}: no GCD issue #{iss} in {series.get('name')}")
            continue

        issue = http_get_json(url, args.delay)
        if not isinstance(issue, dict):
            errors += 1
            continue
        # skip variants if variant_name set
        if (issue.get("variant_name") or "").strip():
            # try to find a non-variant sibling already preferred by index; count as no barcode path
            no_barcode += 1
            details.append({"id": cid, "status": "variant_only", "issue": iss})
            print(f"· {cid}: GCD hit is variant ({issue.get('variant_name')})")
            continue

        barcode = normalize_upc(issue.get("barcode"))
        isbn = normalize_upc(issue.get("isbn"))
        code = barcode or isbn
        if not code:
            no_barcode += 1
            details.append({"id": cid, "status": "no_barcode", "gcdIssue": issue.get("api_url")})
            print(f"· {cid}: GCD issue has empty barcode")
            continue

        api_url = (issue.get("api_url") or url or "").split("?", 1)[0].rstrip("/")
        source_id = api_url.rsplit("/", 1)[-1]
        entry = {
            "upc": code,
            "source": "gcd",
            "sourceId": source_id,
            "title": issue.get("series_name") or series.get("name"),
            "fetchedAt": now_iso(),
        }
        if isbn and isbn != code:
            entry["isbn"] = isbn
        local[cid] = entry
        filled += 1
        details.append({"id": cid, "status": "gcd_upc", "upc": code})
        print(f"✓ {cid}: upc={code} gcd={entry['sourceId']} {entry.get('title')} #{iss}")

    if not args.dry_run:
        save_json(SERIES_CACHE, series_cache)
        if local:
            upc_map = merge_upc(load_json(UPC_MAP, {}), local)
            save_json(UPC_MAP, upc_map)

    after = len([1 for v in (upc_map if not args.dry_run else {**upc_map, **local}).values() if isinstance(v, dict) and v.get("upc")])
    stats = {
        "startedAt": now_iso(),
        "finishedAt": now_iso(),
        "beforeUpc": before,
        "afterUpc": after,
        "upcFilled": filled,
        "skippedExisting": skipped,
        "noSeries": no_series,
        "noIssue": no_issue,
        "noBarcode": no_barcode,
        "errors": errors,
        "limit": args.limit,
        "minYear": args.min_year,
        "dryRun": bool(args.dry_run),
        "details": details[:200],
    }
    if not args.dry_run:
        save_json(STATS, stats)
    print(json.dumps({k: stats[k] for k in stats if k != "details"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
