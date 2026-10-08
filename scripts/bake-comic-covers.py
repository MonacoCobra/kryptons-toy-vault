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

Run-time controls (2026-10-06, after interrupted Oct 2 / Oct 5 routine runs):

  * Comic Vine spacing is enforced per HTTP request (--cv-interval, floor
    24s, default 36s). Cache hits make no request and never sleep.
  * Persisted miss list (scripts/comic-cover-miss-list.json): a comic that
    misses on a source is skipped on that source for --miss-ttl-days (14).
    Errors and rate pauses are not recorded as misses.
  * Metron backoff is capped at METRON_BACKOFF_CAP (120s); a longer reset
    window or any 429 stops the Metron source for this run.
  * --max-minutes is a per-source wall-clock budget; --max-requests caps
    live HTTP requests per source (handy for tiny tests).
  * Checkout root: --root PATH or KTV_ROOT env (default
    /workspace/collection-app). Metron daily/rate counters stay shared at
    the default checkout (they live in backfill-comic-upcs-metron.py) so the
    polite limits hold across every process on the box.
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

DEFAULT_ROOT = Path("/workspace/collection-app")


def _resolve_root() -> Path:
    """--root PATH / --root=PATH on the command line, else $KTV_ROOT, else default."""
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--root" and i + 1 < len(argv):
            return Path(argv[i + 1]).expanduser().resolve()
        if a.startswith("--root="):
            return Path(a.split("=", 1)[1]).expanduser().resolve()
    env = os.environ.get("KTV_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return DEFAULT_ROOT


ROOT = _resolve_root()
SCRIPTS = ROOT / "scripts"
if not (SCRIPTS / "data_shards.py").is_file():
    raise SystemExit(f"bake-comic-covers: {ROOT} does not look like a collection-app checkout")
# data_shards / helper modules must come from the selected checkout.
sys.path.insert(0, str(SCRIPTS))
COVER_URLS = ROOT / "src/data/comic-cover-urls.json"
UPC_MAP = ROOT / "src/data/comic-upc-map.json"
STATS = SCRIPTS / "comic-cover-bake-stats.json"
CV_KEY_FILE = Path("/home/box/.config/krypton/comicvine-api-key")
CV_CACHE = SCRIPTS / "comic-cover-cv-cache.json"
MISS_LIST = SCRIPTS / "comic-cover-miss-list.json"
MISS_TTL_DAYS_DEFAULT = 14.0
METRON_BACKOFF_CAP = 120  # seconds; longer waits stop the Metron source instead
UPC_RELOAD_SECONDS = 60.0  # upc map is ~64 shards (~1s to load); refresh at most once a minute

# Official 200/resource/hour; polite notch-under.
CV_HOURLY_CAP = 150
CV_MIN_INTERVAL = max(2.0, 3600.0 / CV_HOURLY_CAP)  # 24s
# Per-request spacing (an item can make 2 CV calls: UPC + series query).
# Pulled back to 36s (~100/hr) after repeated 420s 2026-10-01..04.
CV_REQUEST_INTERVAL = 36.0
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
    import data_shards

    if data_shards.dataset_kind(path):
        return data_shards.load_document(path, default)
    if path.exists():
        return json.loads(path.read_text())
    return default
def save_json(path: Path, data) -> None:
    import data_shards

    if data_shards.dataset_kind(path):
        data_shards.save_document(path, data)
        return
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
    """Prefer explicit cover/release date year over series-name year."""
    for key in ("coverDate", "releaseDate", "onSaleDate"):
        raw = (m.get(key) or "")[:10]
        if len(raw) >= 4 and raw[:4].isdigit():
            return int(raw[:4])
    y = metron.cover_year(m)
    return y if y is not None else 0


def cover_date_iso(m: dict) -> str | None:
    for key in ("coverDate", "releaseDate", "onSaleDate"):
        raw = (m.get(key) or "")[:10]
        if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
            return raw
        if len(raw) == 7 and raw[4] == "-":
            return raw + "-01"
        if len(raw) == 4 and raw.isdigit():
            return raw + "-01-01"
    return None


def is_future_dated(m: dict, today: str | None = None) -> bool:
    iso = cover_date_iso(m)
    if not iso:
        return False
    day = today or datetime.now().strftime("%Y-%m-%d")
    return iso > day


def is_low_yield_target(m: dict) -> bool:
    blob = " ".join(str(m.get(k) or "") for k in ("series", "title", "issue", "variant")).lower()
    markers = (
        "facsimile", "ashcan", "batman day", "superman day", "free comic book day",
        "comicspro", "preview", "director's cut", "2025 edition", "2024 edition", "2026 edition",
    )
    if any(x in blob for x in markers):
        return True
    iss = (m.get("issue") or "").strip().lower().lstrip("#")
    return iss in ("nn", "[nn]", "n/a", "")


def is_named_variant(variant: str | None) -> bool:
    v = (variant or "").strip().lower()
    if not v:
        return False
    if v in ("a", "cover a", "regular", "main"):
        return False
    return True


def has_cover(cid: str, upc_map: dict, cover_urls: dict, meta_row: dict) -> bool:
    return locg.row_has_cover(cid, upc_map=upc_map, cover_urls=cover_urls, meta_row=meta_row)


COLLECTED_FORMATS = frozenset({"tpb", "hc", "omnibus"})


def candidates(
    meta: dict,
    upc_map: dict,
    cover_urls: dict,
    min_year: int,
    max_year: int | None = None,
    skip_collected: bool = False,
) -> list[str]:
    """Prefer key-flagged / non-variant comics; skip future-dated and facsimile/nn.

    skip_collected drops tpb / hc / omnibus rows (Comic Vine and Metron rarely
    carry collected editions), leaving single issues and annuals.
    """
    rows = []
    today = datetime.now().strftime("%Y-%m-%d")
    for cid, m in meta.items():
        if skip_collected and str(m.get("format") or "").strip().lower() in COLLECTED_FORMATS:
            continue
        if has_cover(cid, upc_map, cover_urls, m):
            continue
        if is_future_dated(m, today):
            continue
        y = row_year(m)
        if min_year and (not y or y < min_year):
            continue
        if max_year is not None and (not y or y > max_year):
            continue
        named = 1 if is_named_variant(m.get("variant")) else 0
        low = 1 if is_low_yield_target(m) else 0
        key_flag = 0 if (m.get("key") or 0) else 1
        try:
            demand = -float(m.get("demand") or 0.0)
        except (TypeError, ValueError):
            demand = 0.0
        rows.append(
            (cid, y, key_flag, named, low, demand, pub_rank(m.get("publisher") or ""))
        )
    rows.sort(key=lambda t: (t[2], t[3], t[4], -t[1], t[5], t[6], t[0]))
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


class RequestBudgetReached(Exception):
    pass


# Live HTTP request accounting (per source) for --max-requests and stats.
REQUESTS = {"cv": 0, "metron": 0}
MAX_REQUESTS = {"cv": 0, "metron": 0}  # 0 = no cap
_cv_last_request = 0.0
# Set when a Metron call fails with a non-429 HTTP error, so that item is not
# recorded as a genuine miss.
_metron_http_error = False


def _count_request(src: str) -> None:
    cap = MAX_REQUESTS.get(src) or 0
    if cap and REQUESTS[src] >= cap:
        raise RequestBudgetReached(f"{src} max-requests {cap} reached")
    REQUESTS[src] += 1


def cv_get(url: str) -> dict:
    """One Comic Vine HTTP request, spaced >= CV_REQUEST_INTERVAL from the last one."""
    global _cv_last_request
    _count_request("cv")
    gap = max(CV_MIN_INTERVAL, CV_REQUEST_INTERVAL)
    if _cv_last_request:
        wait = gap - (time.time() - _cv_last_request)
        if wait > 0:
            time.sleep(wait)
    _cv_last_request = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": CV_UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        if e.code in (420, 429):
            retry = e.headers.get("Retry-After") if e.headers else None
            print(
                f"  CV HTTP {e.code} Retry-After={retry} — stopping CV for this run (pullback)",
                file=sys.stderr,
            )
            raise RatePaused(f"Comic Vine {e.code}")
        if e.code in (500, 502, 503, 504):
            print(f"  CV HTTP {e.code} — stopping CV for this run (upstream)", file=sys.stderr)
            raise RatePaused(f"Comic Vine {e.code}")
        raise


def issue_numbers(issue: str) -> list[str]:
    raw = (issue or "").lstrip("#").strip().lower()
    if not raw or raw in ("nn", "[nn]", "n/a"):
        return []
    nums = re.findall(r"\d+(?:\.\d+)?", raw)
    if raw and raw not in nums:
        nums = [raw] + [n for n in nums if n != raw]
    out = []
    for n in nums:
        if n not in out:
            out.append(n)
    return out


def series_year_hint(series: str) -> int | None:
    m = re.search(r"\((\d{4})\)\s*$", (series or "").strip())
    return int(m.group(1)) if m else None


def score_cv(
    hit: dict, series: str, issue: str, variant: str | None, catalog_year: int | None = None
) -> int:
    """Strict match: require issue number AND series agreement. Never guess."""
    wants = issue_numbers(issue)
    series_core = series.lower().split("(")[0].strip()
    vol = ((hit.get("volume") or {}).get("name") or "").lower().strip()
    iss = str(hit.get("issue_number") or "").lower().strip()
    name = (hit.get("name") or "").lower()
    score = 0
    if wants:
        iss_nums = re.findall(r"\d+(?:\.\d+)?", iss) or ([iss] if iss else [])
        if not any(w == iss or w in iss_nums for w in wants):
            return -99
        score += 5
    else:
        score += 1
    if not series_core or not vol:
        return -99
    if vol == series_core:
        score += 6
    else:
        sc_tok = set(re.findall(r"[a-z0-9]+", series_core))
        vol_tok = set(re.findall(r"[a-z0-9]+", vol))
        if not sc_tok or not vol_tok:
            return -99
        if sc_tok == vol_tok:
            score += 6
        elif sc_tok <= vol_tok or vol_tok <= sc_tok:
            longer, shorter = (sc_tok, vol_tok) if len(sc_tok) >= len(vol_tok) else (vol_tok, sc_tok)
            if shorter < longer and len(longer) - len(shorter) >= 1:
                return -99
            score += 3
        elif len(sc_tok & vol_tok) / max(len(sc_tok), len(vol_tok)) >= 0.8:
            score += 3
        else:
            return -99
    hit_cd = (hit.get("cover_date") or hit.get("coverDate") or "")[:10]
    hit_year = int(hit_cd[:4]) if len(hit_cd) >= 4 and hit_cd[:4].isdigit() else None
    yhint = series_year_hint(series)
    if catalog_year and hit_year:
        if abs(hit_year - catalog_year) > 1:
            return -99
        score += 3 if hit_year == catalog_year else 1
    elif catalog_year and not hit_year:
        return -99
    elif yhint and hit_year and hit_year < yhint - 1:
        return -99
    vol_obj = hit.get("volume") or {}
    vys = vol_obj.get("start_year") or vol_obj.get("year")
    if yhint and vys:
        try:
            vys_i = int(vys)
        except (TypeError, ValueError):
            vys_i = None
        if vys_i is not None:
            if vys_i == yhint:
                score += 4
            elif abs(vys_i - yhint) > 1:
                return -99
    img = hit.get("image") or {}
    cover = img.get("super_url") or img.get("medium_url") or img.get("original_url") or ""
    if cover and "img_broken" not in cover:
        score += 1
    else:
        return -99
    if "w.i.p" in vol or "wip" in vol:
        return -99
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


def cv_pick_cover(
    series: str, issue: str, variant: str | None, upc: str | None, catalog_year: int | None = None
) -> dict | None:
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
            need_dates = bool(catalog_year or series_year_hint(series))
            if need_dates and results and not any(r.get("cover_date") for r in results):
                results = None
        else:
            results = None
        if results is None:
            url = (
                f"{CV_API}/search/?"
                + urllib.parse.urlencode(
                    {
                        "api_key": key,
                        "format": "json",
                        "resources": "issue",
                        "query": q,
                        "limit": "10",
                        "field_list": "id,name,issue_number,barcode,image,volume,cover_date",
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
                    "cover_date": r.get("cover_date"),
                }
                for r in results
            ]
            if len(cache) % 10 == 0:
                save_json(CV_CACHE, cache)
        best = None
        best_score = -99
        for r in results:
            sc = score_cv(r, series, issue, variant, catalog_year)
            if sc > best_score:
                best_score = sc
                best = r
        need = 11 if issue_numbers(issue) else 7
        if best and best_score >= need:
            img = best.get("image") or {}
            cover = img.get("super_url") or img.get("medium_url") or img.get("original_url")
            if cover and "img_broken" not in cover:
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
    global _metron_http_error
    if metron.daily_remaining() <= 0:
        raise metron.DailyCapReached(
            f"Metron daily cap {metron.METRON_DAILY_CAP} reached for {metron._utc_day()}"
        )
    _count_request("metron")
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
                body = json.loads(resp.read().decode("utf-8", "replace"))
                if wait > METRON_BACKOFF_CAP:
                    print(
                        f"  metron header remaining=0, reset in {wait}s > {METRON_BACKOFF_CAP}s cap — stopping Metron",
                        file=sys.stderr,
                    )
                    raise RatePaused(f"Metron rate window exhausted (reset in {wait}s)")
                print(f"  metron header remaining=0 — backing off {wait}s", file=sys.stderr)
                time.sleep(wait)
                return body
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        retry = e.headers.get("Retry-After") if e.headers else None
        if e.code == 429:
            # No long sleep: stop the source and let the next run (and the
            # shared rate file) take care of spacing.
            print(f"  Metron HTTP 429 Retry-After={retry} — stopping Metron for this run", file=sys.stderr)
            metron.bump_daily()
            raise RatePaused("Metron 429")
        print(f"  Metron HTTP {e.code} {url}", file=sys.stderr)
        metron.bump_daily()
        _metron_http_error = True
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
    return cv_pick_cover(series, issue, variant, upc, catalog_year=row_year(m) or None)


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


def load_miss_list() -> dict:
    data = load_json(MISS_LIST, {})
    if not isinstance(data, dict):
        data = {}
    for src in ("cv", "metron"):
        if not isinstance(data.get(src), dict):
            data[src] = {}
    return data


def _parse_iso(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def recently_missed(misses: dict, src: str, cid: str, ttl_days: float) -> bool:
    if ttl_days <= 0:
        return False
    ent = (misses.get(src) or {}).get(cid)
    if not isinstance(ent, dict):
        return False
    at = _parse_iso(ent.get("lastMissAt"))
    return at is not None and (time.time() - at) < ttl_days * 86400


def record_miss(misses: dict, src: str, cid: str) -> None:
    ent = dict((misses.get(src) or {}).get(cid) or {})
    ent["lastMissAt"] = now_iso()
    ent["count"] = int(ent.get("count") or 0) + 1
    misses.setdefault(src, {})[cid] = ent


def save_miss_list(misses: dict, ttl_days: float) -> None:
    """Persist, dropping entries older than 4x the TTL so the file stays small."""
    horizon = max(ttl_days, MISS_TTL_DAYS_DEFAULT) * 4 * 86400
    now = time.time()
    out = {}
    for src in ("cv", "metron"):
        keep = {}
        for cid, ent in sorted((misses.get(src) or {}).items()):
            at = _parse_iso((ent or {}).get("lastMissAt"))
            if at is not None and now - at < horizon:
                keep[cid] = ent
        out[src] = keep
    save_json(MISS_LIST, out)


def main() -> int:
    global CV_REQUEST_INTERVAL, _metron_http_error
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["cv", "metron", "both"], default="cv")
    ap.add_argument("--limit", type=int, default=0, help="0 = no cap")
    ap.add_argument("--delay", type=float, default=0.0, help="Extra spacing; floors still apply")
    ap.add_argument("--min-year", type=int, default=2020)
    ap.add_argument(
        "--max-year",
        type=int,
        default=2025,
        help="Skip cover years above this (0 = no max). Default 2025 avoids unreleased 2026 facsimiles.",
    )
    ap.add_argument(
        "--skip-collected",
        action="store_true",
        help="Only single issues / annuals: skip tpb, hc and omnibus rows",
    )
    ap.add_argument("--dry-run", action="store_true", help="List candidates (after miss-list filter); no requests")
    ap.add_argument(
        "--max-minutes",
        type=float,
        default=0,
        help="Wall-clock budget PER SOURCE in minutes (0 = none); with --source both each pass gets its own budget",
    )
    ap.add_argument("--max-requests", type=int, default=0, help="Cap live HTTP requests per source (0 = none)")
    ap.add_argument(
        "--cv-interval",
        type=float,
        default=CV_REQUEST_INTERVAL,
        help=f"Seconds between Comic Vine HTTP requests (floor {CV_MIN_INTERVAL:.0f}s; default {CV_REQUEST_INTERVAL:.0f}s)",
    )
    ap.add_argument(
        "--miss-ttl-days",
        type=float,
        default=MISS_TTL_DAYS_DEFAULT,
        help="Skip a comic on a source for this many days after it missed there (0 = retry everything)",
    )
    ap.add_argument(
        "--root",
        default=str(ROOT),
        help="Checkout to read/write (also $KTV_ROOT). Default /workspace/collection-app",
    )
    args = ap.parse_args()
    CV_REQUEST_INTERVAL = max(CV_MIN_INTERVAL, float(args.cv_interval), float(args.delay or 0.0))
    MAX_REQUESTS["cv"] = MAX_REQUESTS["metron"] = max(0, int(args.max_requests or 0))

    meta = locg.parse_comics_meta()
    upc_map = load_json(UPC_MAP, {})
    cover_urls = load_json(COVER_URLS, {})
    max_year = None if args.max_year == 0 else args.max_year
    sources = ["cv", "metron"] if args.source == "both" else [args.source]
    misses = load_miss_list()
    ttl = float(args.miss_ttl_days or 0.0)
    all_ids = candidates(meta, upc_map, cover_urls, args.min_year, max_year, skip_collected=args.skip_collected)
    # --limit applies per source after dropping comics that recently missed on
    # that source, so the daily slots go to comics not yet tried.
    per_source: dict[str, list[str]] = {}
    recent_skips: dict[str, int] = {}
    for src in sources:
        fresh = [cid for cid in all_ids if not recently_missed(misses, src, cid, ttl)]
        recent_skips[src] = len(all_ids) - len(fresh)
        per_source[src] = fresh[: args.limit] if args.limit > 0 else fresh
    before = len(cover_urls)
    year_band = f"{args.min_year}-{max_year if max_year is not None else 'open'}" + (
        " singles" if args.skip_collected else ""
    )
    print(
        f"cover bake root={ROOT} source={args.source} pool={len(all_ids)} "
        + " ".join(f"{s}_candidates={len(per_source[s])} {s}_recent_miss_skips={recent_skips[s]}" for s in sources)
        + f" covers_before={before} year_band={year_band} "
        f"cv_floor={CV_HOURLY_CAP}/hr per-request interval={CV_REQUEST_INTERVAL:.0f}s "
        f"metron_floor={metron.METRON_RPM}/min {metron.METRON_DAILY_CAP}/day "
        f"metron_daily_used={metron.load_daily().get('requests')} "
        f"miss_ttl={ttl:g}d max_minutes_per_source={args.max_minutes:g} max_requests={args.max_requests}",
        flush=True,
    )
    if args.dry_run:
        for src in sources:
            print(f"[{src}] first candidates:")
            for cid in per_source[src][:12]:
                m = meta[cid]
                print(f"  {cid}  {m.get('series')} #{m.get('issue')}  {m.get('publisher')}  {m.get('coverDate')}")
        return 0

    auth = metron.load_auth_header() if "metron" in sources else None
    filled = 0
    filled_cv = 0
    filled_metron = 0
    skipped = 0
    errors = 0
    failures = 0
    details = []
    stopped_reason = None
    source_minutes: dict[str, float] = {}

    def _stats_payload():
        return {
            "updatedAt": now_iso(),
            "source": args.source,
            "yearBand": year_band,
            "coversBefore": before,
            "filled": filled,
            "filledCv": filled_cv,
            "filledMetron": filled_metron,
            "skipped": skipped,
            "misses": errors,
            "errors": failures,
            "recentMissSkips": recent_skips,
            "missTtlDays": ttl,
            "requests": dict(REQUESTS),
            "sourceMinutes": source_minutes,
            "cvRequestInterval": CV_REQUEST_INTERVAL,
            "stoppedReason": stopped_reason,
            "cvHourlyCap": CV_HOURLY_CAP,
            "cvMinInterval": CV_MIN_INTERVAL,
            "metronRpm": metron.METRON_RPM,
            "metronDailyCap": metron.METRON_DAILY_CAP,
            "metronDailyUsed": metron.load_daily().get("requests"),
            "details": details[-80:],
        }

    def _stop(reason: str) -> None:
        nonlocal stopped_reason
        stopped_reason = (stopped_reason + "; " if stopped_reason else "") + reason

    try:
        for src in sources:
            t0 = time.time()
            deadline = t0 + args.max_minutes * 60 if args.max_minutes > 0 else None
            upc_loaded_at = time.time()
            for cid in per_source[src]:
                if deadline and time.time() >= deadline:
                    _stop(f"{src} max-minutes {args.max_minutes:g} reached")
                    print(f"{src}: max-minutes reached", flush=True)
                    break
                cover_urls = load_json(COVER_URLS, cover_urls)
                if time.time() - upc_loaded_at >= UPC_RELOAD_SECONDS:
                    upc_map = load_json(UPC_MAP, upc_map)
                    upc_loaded_at = time.time()
                m = meta.get(cid) or {}
                if has_cover(cid, upc_map, cover_urls, m):
                    skipped += 1
                    continue
                if src == "metron" and is_named_variant(m.get("variant")):
                    skipped += 1
                    continue
                _metron_http_error = False
                try:
                    if src == "cv":
                        hit = bake_one_cv(cid, m, upc_map)
                    else:
                        hit = bake_one_metron(cid, m, auth, max(args.delay, metron.METRON_MIN_INTERVAL))
                except RatePaused as e:
                    reason = f"{e} — pulled back"
                    print(f"stopping {src}: {reason}", flush=True)
                    _stop(reason)
                    break
                except metron.DailyCapReached as e:
                    print(f"stopping {src}: {e}", flush=True)
                    _stop(str(e))
                    break
                except RequestBudgetReached as e:
                    print(f"stopping {src}: {e}", flush=True)
                    _stop(str(e))
                    break
                except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
                    # Network/parse trouble on one item: log, do not record a miss, move on.
                    failures += 1
                    print(f"! {cid}: {src} error {type(e).__name__}: {e}", flush=True)
                    if failures >= 10:
                        _stop(f"{src} too many errors")
                        break
                    continue
                if not hit or not hit.get("coverUrl"):
                    errors += 1
                    if src == "metron" and _metron_http_error:
                        print(f"· {cid}: no {src} cover (HTTP error; not recorded as miss)", flush=True)
                    else:
                        record_miss(misses, src, cid)
                        print(f"· {cid}: no {src} cover", flush=True)
                    if errors % 10 == 0:
                        save_miss_list(misses, ttl)
                    continue
                locg.save_cover_urls_atomic({cid: hit["coverUrl"]})
                ent = dict(upc_map.get(cid) or {})
                if not ent.get("coverUrl"):
                    patch = {"coverUrl": hit["coverUrl"], "coverSource": hit.get("source")}
                    if hit.get("sourceId"):
                        patch["coverSourceId"] = hit["sourceId"]
                    locg.save_upc_map_atomic({cid: {**ent, **patch}}) if cid in upc_map else None
                (misses.get(src) or {}).pop(cid, None)
                filled += 1
                if src == "cv":
                    filled_cv += 1
                else:
                    filled_metron += 1
                details.append({"id": cid, "source": src, "coverUrl": hit["coverUrl"]})
                print(f"✓ {cid}: {src} {hit['coverUrl']}", flush=True)
                if filled % 10 == 0:
                    save_json(STATS, _stats_payload())
            source_minutes[src] = round((time.time() - t0) / 60.0, 2)
    finally:
        save_miss_list(misses, ttl)
        after = len(load_json(COVER_URLS, {}))
        payload = _stats_payload()
        payload["coversAfter"] = after
        save_json(STATS, payload)
        print(
            f"done filled={filled} cv={filled_cv} metron={filled_metron} "
            f"skipped={skipped} misses={errors} errors={failures} covers={before}->{after} "
            f"requests={REQUESTS} minutes={source_minutes} "
            f"stopped={stopped_reason or 'none'}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
