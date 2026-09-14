#!/usr/bin/env python3
"""Fill missing catalog covers from Comic Vine, then Metron issue images.

LOCG stays paused (403). GCD is identity only — no comics.org art.
Never writes comics.ts. Never invents UPCs. Never overwrites an existing cover.

Published caps (looked up 2026-09-13), then a notch under:

  Comic Vine (comicvine.gamespot.com/api/): 200 req/resource/hour + velocity
    detection. Polite floor: ≤150/hour on the issue/search resource, ≥2s
    between calls. Interval floor is 24s (3600/150). Cache hits. On 420/429
    pause that hour window and stop — do not keep bumping.

  Metron (docs: burst 20/min, sustained 5000/day): polite floor ≤10 req/min
    and ≤2500/day (half). Always read X-RateLimit-* / Retry-After. On 429
    stop and back off harder — no retry-hammer. Shares daily/rate files
    with scripts/backfill-comic-upcs-metron.py.
"""
from __future__ import annotations

import argparse
import importlib.util
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
SCRIPTS = ROOT / "scripts"
COVER_URLS = ROOT / "src/data/comic-cover-urls.json"
UPC_MAP = ROOT / "src/data/comic-upc-map.json"
STATS = SCRIPTS / "comic-cover-bake-stats.json"
CV_KEY_FILE = Path("/home/box/.config/krypton/comicvine-api-key")
CV_CACHE = SCRIPTS / "comic-cover-cv-cache.json"

# Official 200/resource/hour; polite notch-under.
CV_HOURLY_CAP = 150
CV_MIN_INTERVAL = max(2.0, 3600.0 / CV_HOURLY_CAP)  # 24s
CV_API = "https://comicvine.gamespot.com/api"
CV_UA = (
    "KryptonsToyVault/1.0 (personal collection; cv cover bake; "
    "+https://github.com/MonacoCobra/kryptons-toy-vault)"
)

METRON_API = "https://metron.cloud/api"
METRON_UA = (
    "KryptonsToyVault/1.0 (personal collection; metron cover bake; "
    "+https://github.com/MonacoCobra/kryptons-toy-vault)"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


locg = _load("locg_backfill", SCRIPTS / "backfill-comic-upcs.py")
metron = _load("metron_backfill", SCRIPTS / "backfill-comic-upcs-metron.py")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def pub_rank(publisher: str) -> int:
    p = (publisher or "").lower()
    if (
        "dc comics" in p
        or p.startswith("dc ")
        or p == "dc"
        or "vertigo" in p
        or "black label" in p
        or "wildstorm" in p
        or "milestone" in p
    ):
        return 0
    if "marvel" in p:
        return 1
    if "image" in p:
        return 2
    if "dynamite" in p:
        return 3
    if "boom" in p:
        return 4
    if "valiant" in p:
        return 5
    return 6


def row_year(m: dict) -> int:
    y = metron.cover_year(m)
    return y if y is not None else 0


def is_named_variant(variant: str | None) -> bool:
    v = (variant or "").strip().lower()
    if not v:
        return False
    if v in ("a", "cover a", "regular", "main"):
        return False
    return True


def has_cover(cid: str, upc_map: dict, cover_urls: dict, meta_row: dict) -> bool:
    return locg.row_has_cover(cid, upc_map=upc_map, cover_urls=cover_urls, meta_row=meta_row)


def candidates(meta: dict, upc_map: dict, cover_urls: dict, min_year: int) -> list[str]:
    rows = []
    for cid, m in meta.items():
        if has_cover(cid, upc_map, cover_urls, m):
            continue
        y = row_year(m)
        if y and y < min_year:
            continue
        rows.append((cid, y, pub_rank(m.get("publisher") or "")))
    rows.sort(key=lambda t: (-t[1], t[2], t[0]))
    return [t[0] for t in rows]


def cv_key() -> str | None:
    env = os.environ.get("COMICVINE_API_KEY", "").strip()
    if env:
        return env
    try:
        return CV_KEY_FILE.read_text().strip() or None
    except OSError:
        return None


class RatePaused(Exception):
    pass


def cv_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": CV_UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        if e.code in (420, 429):
            retry = e.headers.get("Retry-After") if e.headers else None
            wait = int(retry) if retry and str(retry).isdigit() else 3600
            wait = max(wait, 1800)
            print(f"  CV HTTP {e.code} — pausing {wait}s (hour window)", file=sys.stderr)
            time.sleep(min(wait, 3600))
            raise RatePaused(f"Comic Vine {e.code}")
        raise


def score_cv(hit: dict, series: str, issue: str, variant: str | None) -> int:
    num = (issue or "").lstrip("#").strip()
    if num.lower() == "nn":
        num = ""
    want = num.lower()
    series_core = series.lower().split("(")[0].strip()
    vol = ((hit.get("volume") or {}).get("name") or "").lower()
    iss = str(hit.get("issue_number") or "").lower()
    name = (hit.get("name") or "").lower()
    score = 0
    if want and iss == want:
        score += 5
    if not want:
        score += 2
    if vol == series_core:
        score += 6
    elif series_core and (series_core in vol or vol in series_core):
        score += 3
    img = hit.get("image") or {}
    if img.get("super_url") or img.get("medium_url"):
        score += 1
    if "w.i.p" in vol or "wip" in vol:
        score -= 4
    if is_named_variant(variant):
        vcore = (variant or "").lower()
        if vcore in name or vcore in vol:
            score += 4
        else:
            return -99
    else:
        if re.search(r"\b(variant|cover\s*[b-z]|1:\d+)", name):
            score -= 2
    return score


def cv_pick_cover(series: str, issue: str, variant: str | None, upc: str | None) -> dict | None:
    key = cv_key()
    if not key:
        return None
    queries = []
    if upc:
        queries.append(upc)
    num = (issue or "").lstrip("#").strip()
    if num.lower() == "nn":
        num = ""
    q = f"{series} {num}".strip()
    if q and q not in queries:
        queries.append(q)
    cache = load_json(CV_CACHE, {})
    for q in queries:
        ck = f"search:{q.lower()}"
        if ck in cache:
            results = cache[ck]
        else:
            url = (
                f"{CV_API}/search/?"
                + urllib.parse.urlencode(
                    {
                        "api_key": key,
                        "format": "json",
                        "resources": "issue",
                        "query": q,
                        "limit": "10",
                        "field_list": "id,name,issue_number,barcode,image,volume",
                    }
                )
            )
            data = cv_get(url)
            results = list(data.get("results") or [])
            cache[ck] = [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "issue_number": r.get("issue_number"),
                    "barcode": r.get("barcode"),
                    "image": r.get("image"),
                    "volume": r.get("volume"),
                }
                for r in results
            ]
            if len(cache) % 10 == 0:
                save_json(CV_CACHE, cache)
        best = None
        best_score = -99
        for r in results:
            sc = score_cv(r, series, issue, variant)
            if sc > best_score:
                best_score = sc
                best = r
        if best and best_score >= 5:
            img = best.get("image") or {}
            cover = img.get("super_url") or img.get("medium_url") or img.get("original_url")
            if cover:
                save_json(CV_CACHE, cache)
                return {
                    "coverUrl": cover,
                    "source": "comicvine",
                    "sourceId": str(best.get("id")) if best.get("id") is not None else None,
                }
    save_json(CV_CACHE, cache)
    return None


def metron_image(detail: dict) -> str | None:
    img = detail.get("image")
    if isinstance(img, str) and img.startswith("http"):
        return img
    if isinstance(img, dict):
        for k in ("original", "medium", "small", "thumbnail", "url"):
            v = img.get(k)
            if isinstance(v, str) and v.startswith("http"):
                return v
    return None


def metron_get(url: str, auth: str, delay: float) -> dict | None:
    if metron.daily_remaining() <= 0:
        raise metron.DailyCapReached(
            f"Metron daily cap {metron.METRON_DAILY_CAP} reached for {metron._utc_day()}"
        )
    extra = max(0.0, float(delay or 0.0) - metron.METRON_MIN_INTERVAL)
    metron.wait_for_rate_slot(extra_delay=extra)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": auth,
            "User-Agent": METRON_UA,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            used = metron.bump_daily()
            burst_rem = headers.get("x-ratelimit-burst-remaining")
            sust_rem = headers.get("x-ratelimit-sustained-remaining")
            if used % 50 == 0 or burst_rem in ("0", "1") or sust_rem in ("0", "1"):
                print(
                    f"  metron daily {used}/{metron.METRON_DAILY_CAP} "
                    f"burst_rem={burst_rem} sust_rem={sust_rem}",
                    file=sys.stderr,
                )
            if burst_rem == "0" or sust_rem == "0":
                reset = headers.get("x-ratelimit-burst-reset") if burst_rem == "0" else headers.get(
                    "x-ratelimit-sustained-reset"
                )
                wait = 60
                if reset and str(reset).isdigit():
                    wait = max(1, int(reset) - int(time.time()))
                print(f"  metron header remaining=0 — backing off {wait}s", file=sys.stderr)
                time.sleep(min(wait, 3600))
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        retry = e.headers.get("Retry-After") if e.headers else None
        wait = int(retry) if retry and str(retry).isdigit() else 120
        if e.code == 429:
            print(f"  Metron HTTP 429 Retry-After={retry} — stopping after {wait}s backoff", file=sys.stderr)
            time.sleep(min(max(wait, 120), 1800))
            raise RatePaused("Metron 429")
        print(f"  Metron HTTP {e.code} {url}", file=sys.stderr)
        metron.bump_daily()
        return None


def metron_pick(results: list, series_name: str, year: int, auth: str, delay: float) -> dict | None:
    want = metron.norm_name(series_name)
    scored = []
    for r in results[:3]:
        rid = r.get("id")
        if rid is None:
            continue
        detail = metron_get(f"{METRON_API}/issue/{rid}/", auth, delay)
        if not isinstance(detail, dict):
            continue
        ser = detail.get("series") or {}
        sname = metron.norm_name(str(ser.get("name") or ""))
        yb = ser.get("year_began")
        score = 0
        if sname == want:
            score += 50
        elif want in sname or sname in want:
            score += 15
        else:
            wt = set(want.split())
            st = set(sname.split())
            if not wt or len(wt & st) / max(1, len(wt)) < 0.6:
                continue
            score += 5
        if yb == year:
            score += 20
        elif isinstance(yb, int) and year and abs(yb - year) <= 1:
            score += 8
        if metron_image(detail):
            score += 3
        scored.append((score, detail))
    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    best_score, best = scored[0]
    if best_score < 50:
        return None
    return best


def bake_one_cv(cid: str, m: dict, upc_map: dict) -> dict | None:
    series = m.get("series") or cid
    issue = m.get("issue") or "1"
    variant = m.get("variant")
    upc = locg.normalize_upc(m.get("upc") or (upc_map.get(cid) or {}).get("upc"))
    return cv_pick_cover(series, issue, variant, upc)


def bake_one_metron(cid: str, m: dict, auth: str, delay: float) -> dict | None:
    # Metron list/detail image is the issue's A cover. Never stamp it on named variants.
    if is_named_variant(m.get("variant")):
        return None
    base, sy = metron.series_base_and_year(m.get("series") or "")
    year = sy or metron.cover_year(m)
    iss = metron.issue_key(m.get("issue") or "")
    if not base or not iss or year is None:
        return None
    q = urllib.parse.urlencode(
        {"series_name": base, "number": iss, "series_year_began": year}
    )
    data = metron_get(f"{METRON_API}/issue/?{q}", auth, delay)
    if not isinstance(data, dict):
        return None
    results = list(data.get("results") or [])
    if not results:
        q2 = urllib.parse.urlencode({"series_name": base, "number": iss})
        data = metron_get(f"{METRON_API}/issue/?{q2}", auth, delay)
        results = list((data or {}).get("results") or []) if isinstance(data, dict) else []
    if not results:
        return None
    hit = metron_pick(results, base, year, auth, delay)
    if not hit:
        return None
    cover = metron_image(hit)
    if not cover:
        return None
    return {
        "coverUrl": cover,
        "source": "metron",
        "sourceId": str(hit.get("id")) if hit.get("id") is not None else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", choices=["cv", "metron", "both"], default="cv")
    ap.add_argument("--limit", type=int, default=0, help="0 = no cap")
    ap.add_argument("--delay", type=float, default=0.0, help="Extra spacing; floors still apply")
    ap.add_argument("--min-year", type=int, default=2020)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-minutes", type=float, default=0)
    args = ap.parse_args()

    meta = locg.parse_comics_meta()
    upc_map = load_json(UPC_MAP, {})
    cover_urls = load_json(COVER_URLS, {})
    ids = candidates(meta, upc_map, cover_urls, args.min_year)
    if args.limit > 0:
        ids = ids[: args.limit]
    before = len(cover_urls)
    print(
        f"cover bake source={args.source} candidates={len(ids)} "
        f"covers_before={before} min_year={args.min_year} "
        f"cv_floor={CV_HOURLY_CAP}/hr interval>={CV_MIN_INTERVAL:.0f}s "
        f"metron_floor={metron.METRON_RPM}/min {metron.METRON_DAILY_CAP}/day "
        f"metron_daily_used={metron.load_daily().get('requests')}"
    )
    if args.dry_run:
        for cid in ids[:12]:
            m = meta[cid]
            print(f"  {cid}  {m.get('series')} #{m.get('issue')}  {m.get('publisher')}  {m.get('coverDate')}")
        return 0

    sources = ["cv", "metron"] if args.source == "both" else [args.source]
    auth = metron.load_auth_header() if "metron" in sources else None
    deadline = time.time() + args.max_minutes * 60 if args.max_minutes > 0 else None
    filled = 0
    skipped = 0
    errors = 0
    last_cv = 0.0
    details = []

    try:
        for src in sources:
            for cid in ids:
                if deadline and time.time() >= deadline:
                    print("max-minutes reached")
                    return 0
                cover_urls = load_json(COVER_URLS, cover_urls)
                upc_map = load_json(UPC_MAP, upc_map)
                m = meta.get(cid) or {}
                if has_cover(cid, upc_map, cover_urls, m):
                    skipped += 1
                    continue
                if src == "metron" and is_named_variant(m.get("variant")):
                    skipped += 1
                    continue
                try:
                    if src == "cv":
                        wait = max(CV_MIN_INTERVAL, float(args.delay or 0.0)) - (
                            time.time() - last_cv
                        )
                        if last_cv and wait > 0:
                            time.sleep(wait)
                        hit = bake_one_cv(cid, m, upc_map)
                        last_cv = time.time()
                    else:
                        hit = bake_one_metron(cid, m, auth, max(args.delay, metron.METRON_MIN_INTERVAL))
                except RatePaused as e:
                    print(f"stopping: {e}")
                    break
                except metron.DailyCapReached as e:
                    print(f"stopping: {e}")
                    break
                if not hit or not hit.get("coverUrl"):
                    errors += 1
                    print(f"· {cid}: no {src} cover")
                    continue
                locg.save_cover_urls_atomic({cid: hit["coverUrl"]})
                # Optional coverUrl on existing map row only — never invent upc
                ent = dict(upc_map.get(cid) or {})
                if not ent.get("coverUrl"):
                    patch = {"coverUrl": hit["coverUrl"], "coverSource": hit.get("source")}
                    if hit.get("sourceId"):
                        patch["coverSourceId"] = hit["sourceId"]
                    locg.save_upc_map_atomic({cid: {**ent, **patch}}) if cid in upc_map else None
                filled += 1
                details.append({"id": cid, "source": src, "coverUrl": hit["coverUrl"]})
                print(f"✓ {cid}: {src} {hit['coverUrl'][:80]}")
                if filled % 10 == 0:
                    save_json(
                        STATS,
                        {
                            "updatedAt": now_iso(),
                            "source": args.source,
                            "coversBefore": before,
                            "filled": filled,
                            "skipped": skipped,
                            "misses": errors,
                            "cvHourlyCap": CV_HOURLY_CAP,
                            "cvMinInterval": CV_MIN_INTERVAL,
                            "metronRpm": metron.METRON_RPM,
                            "metronDailyCap": metron.METRON_DAILY_CAP,
                            "metronDailyUsed": metron.load_daily().get("requests"),
                            "details": details[-40:],
                        },
                    )
    finally:
        save_json(
            STATS,
            {
                "updatedAt": now_iso(),
                "source": args.source,
                "coversBefore": before,
                "filled": filled,
                "skipped": skipped,
                "misses": errors,
                "cvHourlyCap": CV_HOURLY_CAP,
                "cvMinInterval": CV_MIN_INTERVAL,
                "metronRpm": metron.METRON_RPM,
                "metronDailyCap": metron.METRON_DAILY_CAP,
                "metronDailyUsed": metron.load_daily().get("requests"),
                "details": details[-80:],
            },
        )
        print(f"done filled={filled} skipped={skipped} misses={errors} covers_before={before}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
