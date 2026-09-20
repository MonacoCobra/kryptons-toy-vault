#!/usr/bin/env python3
"""LOCG series → comics.ts catalog importer (highest-trust growth path).

Adds NEW rows to src/data/comics.ts from real League of Comic Geeks
series/issue pages. Never invents titles, publishers, issues, or UPCs.
No gen-batch / interpolated ghost ids.

Hard gates (every new comics.ts row):
  * Source is a real LOCG comic page (numeric locgId + parsed page)
  * locgId present
  * UPC and/or cover URL present (prefer both when LOCG has them)
  * Real series title, issue, publisher from LOCG
  * Skip collected editions and anything that fails a gate
  * Do not duplicate existing comics.ts ids or existing locgIds

Also records locgId / UPC / cover into:
  src/data/comic-upc-map.json
  src/data/comic-cover-urls.json
using the same safe merge as scripts/backfill-comic-upcs.py
(does not clobber a stronger existing UPC).

Polite pacing: default --delay 30 (LOCG robots.txt Crawl-delay: 30).
403/429 backoff is reused from backfill-comic-upcs.py (90s → 600s).

Glyph / Lyra — how to feed series id lists
------------------------------------------
LOCG series ids are numeric (see scripts/comic-locg-series-cache.json
`seriesId`, or the series URL /comics/series/<id>/…). Prefer Image /
Boom / IDW / Dark Horse / indie as first seeds (Lyra new-row bias).

  # Repeatable ids
  python3 scripts/ingest-locg-series-to-catalog.py \\
      --series-id 148147 --series-id 139479 --dry-run --max-issues 5

  # File: one id per line; `#` comments ok. Lyra can emit this from the
  # series cache or a publisher crawl. Never invent ids.
  python3 scripts/ingest-locg-series-to-catalog.py \\
      --series-ids-file scripts/locg-series-ids.example.txt --delay 30

  # List preferred cache seeds (no LOCG traffic)
  python3 scripts/ingest-locg-series-to-catalog.py --list-cache-seeds

  # Fixture proof (no live LOCG)
  python3 scripts/ingest-locg-series-to-catalog.py \\
      --fixture-dir scripts/fixtures/locg-series-ingest \\
      --series-id 900001 --dry-run

Do not run gen-batch-* or interpolated inject scripts from this path.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
import urllib.parse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

# Import sibling modules (hyphenated backfill + underscore common).
sys.path.insert(0, str(SCRIPT_DIR))
import comic_backlog_common as backlog  # noqa: E402


def _load_backfill():
    path = SCRIPT_DIR / "backfill-comic-upcs.py"
    spec = importlib.util.spec_from_file_location("backfill_comic_upcs", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bf = _load_backfill()

FLOOR = backlog.FLOOR  # 1980-01-01
INDIE_PUB_HINTS = (
    "image",
    "boom",
    "idw",
    "dark horse",
    "skybound",
    "oni",
    "dynamite",
    "valiant",
    "aftershock",
    "vault",
    "ablaze",
    "mad cave",
    "dstlry",
    "humanoids",
    "drawn and quarterly",
    "fantagraphics",
)

PUB_PREFIX = {
    "marvel comics": "mv",
    "marvel": "mv",
    "dc comics": "dc",
    "dc": "dc",
    "dc entertainment": "dc",
    "dc comics / vertigo": "vert",
    "vertigo": "vert",
    "dc comics / wildstorm": "ws",
    "wildstorm": "ws",
    "image comics": "im",
    "image": "im",
    "image / top cow": "im",
    "skybound / image": "im",
    "skybound": "im",
    "boom! studios": "boom",
    "boom studios": "boom",
    "idw publishing": "idw",
    "dark horse": "dh",
    "dark horse comics": "dh",
    "dynamite": "dyn",
    "dynamite entertainment": "dyn",
    "valiant": "val",
    "valiant entertainment": "val",
    "archie": "arch",
    "archie comics": "arch",
}

PUB_CANON = {
    "boom studios": "Boom! Studios",
    "boom! studios": "Boom! Studios",
    "dark horse comics": "Dark Horse",
    "dark horse": "Dark Horse",
    "image comics": "Image Comics",
    "idw publishing": "IDW Publishing",
    "marvel comics": "Marvel Comics",
    "marvel": "Marvel Comics",
    "dc comics": "DC Comics",
    "dc": "DC Comics",
    "wildstorm": "WildStorm",
    "dc comics / wildstorm": "WildStorm",
    "skybound": "Skybound / Image",
    "skybound image": "Skybound / Image",
}

PALETTES = {
    "im": "111827,7f1d1d,eab308",
    "boom": "1e3a8a,c2410c,f8fafc",
    "idw": "166534,1e3a8a,dc2626",
    "dh": "dc2626,111827,eab308",
    "mv": "dc2626,1e3a8a,f8fafc",
    "dc": "1e3a8a,e30613,f8fafc",
    "dyn": "ea580c,111827,f8fafc",
    "val": "1e3a8a,111827,fbbf24",
    "vert": "111827,7c3aed,fbbf24",
    "arch": "dc2626,1e3a8a,fde047",
}
DEFAULT_PALETTE = "111827,e5e7eb,f8fafc"

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def bind_paths(root: Path) -> None:
    """Point this module + backfill/backlog helpers at `root`."""
    global ROOT
    ROOT = root
    backlog.ROOT = root
    backlog.COMICS_TS = root / "src/data/comics.ts"
    backlog.BACKLOG = root / "src/data/comic-backlog"
    bf.ROOT = root
    bf.SEEDS = root / "src/data/comic-locg-seeds.json"
    bf.UPC_MAP = root / "src/data/comic-upc-map.json"
    bf.COVER_URLS = root / "src/data/comic-cover-urls.json"
    bf.COMICS_TS = root / "src/data/comics.ts"
    bf.STATS = root / "scripts/comic-upc-backfill-stats.json"
    bf.SERIES_CACHE = root / "scripts/comic-locg-series-cache.json"
    bf.SKIP_FILE = root / "scripts/comic-upc-skip.json"


def parse_series_ids_file(path: Path) -> list[str]:
    """One numeric series id per line. `#` comments and blank lines ignored."""
    ids: list[str] = []
    text = path.read_text()
    stripped = text.strip()
    if stripped.startswith("[") or stripped.startswith("{"):
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("seriesIds") or data.get("ids") or data.get("series_ids") or []
        for item in data:
            sid = str(item).strip()
            if sid.isdigit():
                ids.append(sid)
        return ids
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        token = re.split(r"\s+", line, maxsplit=1)[0]
        if token.isdigit():
            ids.append(token)
    return ids


def cache_series_entries(cache: dict) -> list[dict]:
    out = []
    for key, ent in (cache or {}).items():
        if not isinstance(ent, dict):
            continue
        sid = ent.get("seriesId")
        if sid is None or not str(sid).isdigit():
            continue
        name = ent.get("name") or (key.split("||")[0] if "||" in key else key)
        publisher = ent.get("publisher") or (key.split("||")[1] if "||" in key else "")
        out.append(
            {
                "seriesId": str(sid),
                "name": name,
                "publisher": publisher,
                "issueCount": len(ent.get("issues") or {}),
            }
        )
    return out


def is_indie_publisher(publisher: str) -> bool:
    p = (publisher or "").lower()
    return any(h in p for h in INDIE_PUB_HINTS)


def list_cache_seeds(cache: dict, *, prefer_indie: bool = True) -> list[dict]:
    entries = cache_series_entries(cache)
    if prefer_indie:
        entries.sort(key=lambda e: (0 if is_indie_publisher(e["publisher"]) else 1, e["name"].lower()))
    else:
        entries.sort(key=lambda e: e["name"].lower())
    # unique seriesId, first wins
    seen: set[str] = set()
    uniq = []
    for e in entries:
        if e["seriesId"] in seen:
            continue
        seen.add(e["seriesId"])
        uniq.append(e)
    return uniq


def locg_labeled(html: str, label: str) -> str | None:
    """Read a LOCG details `LABEL</div><div>value` block. Never invents."""
    m = re.search(
        rf"{label}\s*</div>\s*<div[^>]*>\s*([\s\S]*?)</div>",
        html,
        re.I,
    )
    if not m:
        return None
    text = re.sub(r"<[^>]+>", ", ", m.group(1))
    text = re.sub(r"(?:\s*,\s*)+", ", ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,")
    return text or None


def parse_locg_date(raw: str | None) -> str | None:
    """Normalize a date LOCG printed. Returns YYYY-MM-DD or None. No invention."""
    if not raw:
        return None
    s = raw.strip()
    if not s:
        return None
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{year:04d}-{month:02d}-{day:02d}"
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})$", s)
    if m:
        month = MONTHS.get(m.group(1).lower())
        if month:
            return f"{int(m.group(3)):04d}-{month:02d}-{int(m.group(2)):02d}"
    m = re.match(r"^([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        month = MONTHS.get(m.group(1).lower())
        if month:
            return f"{int(m.group(2)):04d}-{month:02d}-01"
    m = re.match(r"^(\d{4})$", s)
    if m:
        return f"{m.group(1)}-01-01"
    return None


def parse_locg_price(raw: str | None) -> float | None:
    if not raw:
        return None
    m = re.search(r"(\d+(?:\.\d{1,2})?)", raw.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def infer_format(title: str | None, issue: str | None) -> str:
    blob = f"{title or ''} {issue or ''}"
    if re.search(r"\bfacsimile\b", blob, re.I):
        return "facsimile"
    if re.search(r"\bannual\b", blob, re.I):
        return "annual"
    return "single"


def enrich_issue(parsed: dict, html: str) -> dict:
    """Add cover/street date, credits, price from the same LOCG page. No invention."""
    out = dict(parsed)
    cover = parse_locg_date(locg_labeled(html, r"Cover\s*Date"))
    street = parse_locg_date(
        locg_labeled(html, r"Street\s*Date")
        or locg_labeled(html, r"Release\s*Date")
        or locg_labeled(html, r"Published")
    )
    if cover:
        out["coverDate"] = cover
    if street:
        out["streetDate"] = street
        if not out.get("coverDate"):
            out["coverDate"] = street
    writers = locg_labeled(html, r"Writers?") or locg_labeled(html, r"Written\s*By")
    artists = (
        locg_labeled(html, r"Artists?")
        or locg_labeled(html, r"Pencill?ers?")
        or locg_labeled(html, r"Art(?:work)?")
    )
    if writers:
        out["writers"] = writers
    if artists:
        out["artists"] = artists
    price = parse_locg_price(locg_labeled(html, r"(?:Cover\s*)?Price") or locg_labeled(html, r"MSRP"))
    if price is not None:
        out["msrp"] = price
    return out


def norm_pub_key(p: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (p or "").lower()).strip()


def publisher_prefix(publisher: str) -> str:
    key = norm_pub_key(publisher)
    if key in PUB_PREFIX:
        return PUB_PREFIX[key]
    for canon, pref in PUB_PREFIX.items():
        if canon in key or key in canon:
            return pref
    slug = re.sub(r"[^a-z0-9]+", "", key)[:4] or "ind"
    return slug


def slugify_series(name: str) -> str:
    s = name.strip()
    s = re.sub(r"\(\s*vol\.?\s*\d+\s*\)", " ", s, flags=re.I)
    s = re.sub(r"\(\s*(?:19|20)\d{2}(?:\s*[-–—]\s*(?:present|(?:19|20)\d{2}))?\s*\)\s*$", " ", s, flags=re.I)
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    parts = [p for p in s.split("-") if p and p not in {"the", "a", "an"}]
    if len(parts) > 6:
        parts = parts[:6]
    return "-".join(parts)[:48] or "series"


def series_match_key(name: str) -> str:
    """Strict series identity — no substring / 'die'∈'indie' false friends."""
    s = name or ""
    s = re.sub(r"\(\s*vol\.?\s*\d+\s*\)", " ", s, flags=re.I)
    s = re.sub(r"\(\s*(?:19|20)\d{2}(?:\s*[-–—]\s*(?:present|(?:19|20)\d{2}))?\s*\)\s*$", " ", s, flags=re.I)
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    s = re.sub(r"\b(the|a|an)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def series_names_match(a: str | None, b: str | None) -> bool:
    ka, kb = series_match_key(a or ""), series_match_key(b or "")
    return bool(ka) and ka == kb


def infer_existing_prefix(existing_meta: dict[str, dict], series: str, publisher: str) -> str | None:
    """Reuse an existing comics.ts id prefix for the same series+publisher."""
    counts: Counter[str] = Counter()
    for cid, m in existing_meta.items():
        if not series_names_match(m.get("series"), series):
            continue
        if not bf.publisher_ok(m.get("publisher"), publisher):
            continue
        iss = str(m.get("issue") or "")
        if not iss:
            continue
        if cid.endswith(f"-{iss}-fac"):
            counts[cid[: -(len(iss) + 5)]] += 1
        elif cid.endswith(f"-{iss}"):
            counts[cid[: -(len(iss) + 1)]] += 1
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def canon_series_publisher(
    series: str, publisher: str, existing_meta: dict[str, dict]
) -> tuple[str, str]:
    """Prefer the catalog's existing spelling when the LOCG row matches it."""
    for m in existing_meta.values():
        if series_names_match(m.get("series"), series) and bf.publisher_ok(m.get("publisher"), publisher):
            return m["series"], m["publisher"]
    pub_key = norm_pub_key(publisher)
    return series, PUB_CANON.get(pub_key, publisher)


def make_catalog_id(
    *,
    series: str,
    issue: str,
    publisher: str,
    cover_date: str,
    existing_ids: set[str],
    existing_meta: dict[str, dict],
    id_prefix_override: str | None = None,
) -> str | None:
    issue = str(issue)
    year = cover_date[:4] if re.match(r"^\d{4}", cover_date) else ""
    reused = infer_existing_prefix(existing_meta, series, publisher)
    pub_pref = publisher_prefix(publisher)
    slug = slugify_series(series)
    generated = f"{pub_pref}-{slug}"
    prefix = id_prefix_override or reused or generated
    candidates = [f"{prefix}-{issue}"]
    if year and f"{prefix}-{year}-{issue}" not in candidates:
        candidates.append(f"{prefix}-{year}-{issue}")
    if reused and generated != reused:
        candidates.append(f"{generated}-{issue}")
        if year:
            candidates.append(f"{generated}-{year}-{issue}")
    for cid in candidates:
        if cid not in existing_ids and re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)+$", cid):
            return cid
    return None


def collect_locg_ids(upc_map: dict, cover_urls: dict, comics_text: str) -> set[str]:
    ids: set[str] = set()
    for ent in (upc_map or {}).values():
        if isinstance(ent, dict) and ent.get("locgId"):
            ids.add(str(ent["locgId"]))
    for url in (cover_urls or {}).values():
        m = re.search(r"(?:medium|large)-(\d+)\.jpg", str(url))
        if m:
            ids.add(m.group(1))
    for m in re.finditer(r"locgId:\s*\"(\d+)\"", comics_text):
        ids.add(m.group(1))
    return ids


def pad_html(html: str, minimum: int = 8000) -> str:
    """Fixture helper — live pages are already long; parse_locg_html requires ≥8000."""
    if len(html) >= minimum:
        return html
    pad = "<!-- locg-fixture-pad -->\n"
    need = minimum - len(html)
    html = html + pad * (need // len(pad) + 1)
    return html


def install_fixture_fetch(fixture_dir: Path) -> None:
    """Serve series JSON + comic HTML from disk. No live LOCG."""
    orig = bf.fetch

    def fetch(url: str, accept: str = "text/html") -> tuple[str, str]:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        if "series_id" in qs or qs.get("list", [""])[0] == "series":
            sid = (qs.get("series_id") or qs.get("title_id") or [""])[0]
            path = fixture_dir / "series" / f"{sid}.json"
            if not path.exists():
                raise FileNotFoundError(f"fixture series {sid} missing: {path}")
            data = json.loads(path.read_text())
            body = json.dumps({"list": data.get("list") or ""})
            return body, url
        m = re.search(r"/comic/(\d+)/", url)
        if m:
            locg_id = m.group(1)
            path = fixture_dir / "comics" / f"{locg_id}.html"
            if not path.exists():
                raise FileNotFoundError(f"fixture comic {locg_id} missing: {path}")
            return pad_html(path.read_text()), url
        return orig(url, accept)

    bf.fetch = fetch


class Pace:
    def __init__(self, delay: float):
        self.delay = max(0.0, delay)
        self.last = 0.0

    def wait(self) -> None:
        if self.last and self.delay:
            elapsed = time.monotonic() - self.last
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        self.last = time.monotonic()


def gate_reason(
    parsed: dict,
    *,
    existing_ids: set[str],
    existing_keys: set[str],
    existing_locg: set[str],
    min_year: int,
    catalog_id: str | None,
) -> str | None:
    locg_id = str(parsed.get("locgId") or "")
    if not locg_id.isdigit():
        return "no-locgId"
    if locg_id in existing_locg:
        return "dup-locgId"
    if not parsed.get("upc") and not parsed.get("coverUrl"):
        return "no-upc-or-cover"
    series = (parsed.get("series") or "").strip()
    issue = str(parsed.get("issue") or "").strip()
    publisher = (parsed.get("publisher") or "").strip()
    if not series or not issue or not publisher:
        return "incomplete-identity"
    if bf.looks_like_collected_edition(parsed.get("title")):
        return "collected-edition"
    cover_date = parsed.get("coverDate") or ""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", cover_date):
        return "no-cover-date"
    if cover_date < FLOOR:
        return "pre-floor"
    if min_year and int(cover_date[:4]) < min_year:
        return "min-year"
    if not catalog_id:
        return "id-collision"
    if catalog_id in existing_ids:
        return "dup-id"
    key = f"{series}|{issue}|{publisher}".lower()
    if key in existing_keys:
        return "dup-series-issue-publisher"
    url = parsed.get("url") or ""
    if locg_id not in url and "/comic/" not in url:
        return "not-locg-page"
    return None


def build_row(catalog_id: str, parsed: dict, existing_meta: dict[str, dict]) -> list:
    series, publisher = canon_series_publisher(
        parsed["series"], parsed["publisher"], existing_meta
    )
    issue = str(parsed["issue"])
    cover_date = parsed["coverDate"]
    writers = parsed.get("writers") or ""
    artists = parsed.get("artists") or ""
    title = parsed.get("title") or f"{series} #{issue}"
    msrp = float(parsed["msrp"]) if parsed.get("msrp") is not None else 0.0
    fmt = infer_format(parsed.get("title"), issue)
    demand = 0.8 if issue in {"1", "0"} else 0.55
    key = 0
    prefix = catalog_id.rsplit("-", 1)[0].split("-")[0]
    palette = PALETTES.get(publisher_prefix(publisher), PALETTES.get(prefix, DEFAULT_PALETTE))
    extra = {}
    if parsed.get("upc"):
        extra["upc"] = parsed["upc"]
    if parsed.get("streetDate"):
        extra["streetDate"] = parsed["streetDate"]
    if parsed.get("coverUrl"):
        extra["cover"] = parsed["coverUrl"]
    extra["locgId"] = str(parsed["locgId"])
    row = [
        catalog_id,
        series,
        issue,
        publisher,
        cover_date,
        writers,
        artists,
        title,
        msrp,
        fmt,
        demand,
        key,
        palette,
        extra,
    ]
    return row


def series_meta_from_cache_or_fixture(
    series_id: str, cache: dict, fixture_dir: Path | None
) -> dict:
    if fixture_dir:
        path = fixture_dir / "series" / f"{series_id}.json"
        if path.exists():
            data = json.loads(path.read_text())
            return {
                "seriesId": series_id,
                "name": data.get("name") or "",
                "publisher": data.get("publisher") or "",
            }
    for key, ent in (cache or {}).items():
        if not isinstance(ent, dict):
            continue
        if str(ent.get("seriesId") or "") == str(series_id):
            name = ent.get("name") or (key.split("||")[0] if "||" in key else "")
            publisher = ent.get("publisher") or (key.split("||")[1] if "||" in key else "")
            return {"seriesId": str(series_id), "name": name, "publisher": publisher}
    return {"seriesId": str(series_id), "name": "", "publisher": ""}


def inject_rows(comics_ts: Path, rows: list, comment: str) -> int:
    if not rows:
        return 0
    src = comics_ts.read_text()
    marker = "];\n\nfunction pal"
    if marker not in src:
        raise SystemExit("comics.ts marker not found")
    lines = [backlog.ts_literal(row) for row in rows]
    block = f"\n  // {comment}\n" + "\n".join(lines) + "\n"
    comics_ts.write_text(src.replace(marker, block + marker, 1))
    return len(rows)


def upc_entry(catalog_id: str, parsed: dict) -> dict:
    ent = {
        "fetchedAt": now_iso(),
        "source": "locg",
        "locgId": str(parsed["locgId"]),
        "title": parsed.get("title") or f"{parsed.get('series')} #{parsed.get('issue')}",
        "url": parsed.get("url")
        or f"https://leagueofcomicgeeks.com/comic/{parsed['locgId']}/",
    }
    if parsed.get("upc"):
        ent["upc"] = parsed["upc"]
    if parsed.get("coverUrl"):
        ent["coverUrl"] = parsed["coverUrl"]
    return ent


def ingest_series(
    series_id: str,
    *,
    delay: float,
    max_issues: int,
    min_year: int,
    mains_only: bool,
    use_cache_lists: bool,
    pace: Pace,
    existing_ids: set[str],
    existing_keys: set[str],
    existing_locg: set[str],
    existing_meta: dict[str, dict],
    cache: dict,
    fixture_dir: Path | None,
    id_prefix: str | None,
) -> tuple[list, list[dict], dict, dict]:
    """Return (rows, skips, upc_local, cover_local)."""
    rows: list = []
    skips: list[dict] = []
    upc_local: dict = {}
    cover_local: dict = {}

    meta = series_meta_from_cache_or_fixture(series_id, cache, fixture_dir)
    cache_key = f"{meta.get('name') or series_id}||{meta.get('publisher') or ''}"
    cached = cache.get(cache_key) if isinstance(cache.get(cache_key), dict) else None
    issues: dict[str, dict] = {}
    if use_cache_lists and cached and cached.get("issues"):
        issues = dict(cached["issues"])
        print(f"series {series_id}: using cached issue list ({len(issues)} issues)")
    else:
        pace.wait()
        issues = bf.fetch_series_issues(series_id, delay=0.0, throttle=pace.wait)
        print(f"series {series_id}: fetched {len(issues)} issues from LOCG list")

    items = []
    for iss, ent in issues.items():
        if mains_only and ent.get("main") is False:
            skips.append({"seriesId": series_id, "issue": iss, "locgId": ent.get("locgId"), "reason": "variant"})
            continue
        items.append((iss, ent))

    def issue_sort_key(pair):
        iss = str(pair[0])
        num = int(re.sub(r"\D", "", iss) or 0)
        return (num, iss)

    items.sort(key=issue_sort_key)
    if max_issues and max_issues > 0:
        items = items[:max_issues]

    for iss, ent in items:
        locg_id = str(ent.get("locgId") or "")
        slug = ent.get("slug") or "issue"
        if not locg_id.isdigit():
            skips.append({"seriesId": series_id, "issue": iss, "reason": "no-locgId"})
            continue
        if locg_id in existing_locg:
            skips.append({"seriesId": series_id, "issue": iss, "locgId": locg_id, "reason": "dup-locgId"})
            continue
        try:
            pace.wait()
            html, final_url = bf.fetch(
                f"https://leagueofcomicgeeks.com/comic/{locg_id}/{slug}"
            )
        except Exception as e:
            skips.append({"seriesId": series_id, "issue": iss, "locgId": locg_id, "reason": f"fetch-error:{e}"})
            continue
        parsed = bf.parse_locg_html(html, final_url or f"https://leagueofcomicgeeks.com/comic/{locg_id}/{slug}")
        if not parsed:
            skips.append({"seriesId": series_id, "issue": iss, "locgId": locg_id, "reason": "unparsed-page"})
            continue
        parsed = enrich_issue(parsed, html)
        # Fill identity from the series list / cache when the page omits a field.
        # Still LOCG-sourced — never invented.
        if not parsed.get("issue"):
            parsed["issue"] = str(iss)
        if not parsed.get("series") and meta.get("name"):
            parsed["series"] = meta["name"]
        if not parsed.get("publisher") and meta.get("publisher"):
            parsed["publisher"] = meta["publisher"]
        if not parsed.get("coverUrl") and ent.get("coverUrl"):
            parsed["coverUrl"] = ent["coverUrl"]
        parsed["series"], parsed["publisher"] = canon_series_publisher(
            parsed.get("series") or "", parsed.get("publisher") or "", existing_meta
        )
        catalog_id = make_catalog_id(
            series=parsed.get("series") or "",
            issue=str(parsed.get("issue") or iss),
            publisher=parsed.get("publisher") or "",
            cover_date=parsed.get("coverDate") or "",
            existing_ids=existing_ids,
            existing_meta=existing_meta,
            id_prefix_override=id_prefix,
        )
        reason = gate_reason(
            parsed,
            existing_ids=existing_ids,
            existing_keys=existing_keys,
            existing_locg=existing_locg,
            min_year=min_year,
            catalog_id=catalog_id,
        )
        if reason:
            skips.append(
                {
                    "seriesId": series_id,
                    "issue": parsed.get("issue") or iss,
                    "locgId": parsed.get("locgId"),
                    "reason": reason,
                }
            )
            continue
        assert catalog_id is not None
        row = build_row(catalog_id, parsed, existing_meta)
        rows.append(row)
        existing_ids.add(catalog_id)
        existing_keys.add(f"{row[1]}|{row[2]}|{row[3]}".lower())
        existing_locg.add(str(parsed["locgId"]))
        upc_local[catalog_id] = upc_entry(catalog_id, parsed)
        if parsed.get("coverUrl"):
            cover_local[catalog_id] = parsed["coverUrl"]
        print(
            f"  + {catalog_id}  {row[1]} #{row[2]}  locg={parsed['locgId']}  "
            f"upc={parsed.get('upc') or '—'}  {parsed.get('coverDate')}"
        )
    return rows, skips, upc_local, cover_local


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--series-id", action="append", default=[], help="LOCG series id (repeatable)")
    ap.add_argument("--series-ids-file", type=str, default="", help="File of series ids (one per line or JSON list)")
    ap.add_argument("--delay", type=float, default=30.0, help="Seconds between LOCG requests (robots Crawl-delay=30)")
    ap.add_argument("--max-issues", type=int, default=0, help="Cap issues per series (0=no cap; lowest numbers first)")
    ap.add_argument("--dry-run", action="store_true", help="Parse and gate only; do not write comics.ts / maps")
    ap.add_argument("--min-year", type=int, default=1980, help="Skip issues with cover year below this (default 1980 floor)")
    ap.add_argument("--fixture-dir", type=str, default="", help="Local series/comic fixtures; skips live LOCG")
    ap.add_argument("--from-cache", action="store_true", help="Use series ids from comic-locg-series-cache.json")
    ap.add_argument("--list-cache-seeds", action="store_true", help="Print preferred cache series ids and exit")
    ap.add_argument("--use-cache-lists", action="store_true", help="Reuse cached issue lists instead of re-fetching")
    ap.add_argument("--include-variants", action="store_true", help="Also ingest data-parent!=0 covers (default: mains only)")
    ap.add_argument("--id-prefix", type=str, default="", help="Force catalog id prefix for this run (e.g. im-nocterra)")
    ap.add_argument(
        "--prefer-indie",
        dest="prefer_indie",
        action="store_true",
        default=True,
        help="Sort --from-cache Image/Boom/IDW/DH first (default)",
    )
    ap.add_argument("--no-prefer-indie", dest="prefer_indie", action="store_false")
    ap.add_argument("--root", type=str, default="", help="Workspace root (tests)")
    ap.add_argument("--report", type=str, default="", help="Write JSON report of added/skipped")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve() if args.root else ROOT
    bind_paths(root)

    cache_path = root / "scripts/comic-locg-series-cache.json"
    cache = bf.load_json(cache_path, {})

    if args.list_cache_seeds:
        seeds = list_cache_seeds(cache, prefer_indie=args.prefer_indie)
        for e in seeds:
            tag = "indie" if is_indie_publisher(e["publisher"]) else "other"
            print(f"{e['seriesId']}\t{e['publisher']}\t{e['name']}\t{tag}")
        print(f"# {len(seeds)} unique series ids", file=sys.stderr)
        return 0

    fixture_dir = Path(args.fixture_dir).resolve() if args.fixture_dir else None
    if fixture_dir:
        if not fixture_dir.is_dir():
            raise SystemExit(f"fixture-dir not found: {fixture_dir}")
        install_fixture_fetch(fixture_dir)
        args.delay = 0.0

    series_ids: list[str] = []
    for sid in args.series_id:
        token = str(sid).strip()
        if token.isdigit():
            series_ids.append(token)
        else:
            raise SystemExit(f"invalid --series-id (must be numeric LOCG id): {sid}")
    if args.series_ids_file:
        series_ids.extend(parse_series_ids_file(Path(args.series_ids_file)))
    if args.from_cache:
        series_ids.extend(e["seriesId"] for e in list_cache_seeds(cache, prefer_indie=args.prefer_indie))

    # de-dupe, preserve order
    seen_s: set[str] = set()
    ordered: list[str] = []
    for sid in series_ids:
        if sid in seen_s:
            continue
        seen_s.add(sid)
        ordered.append(sid)
    series_ids = ordered

    if not series_ids:
        raise SystemExit("no series ids — pass --series-id, --series-ids-file, or --from-cache")

    comics_ts = root / "src/data/comics.ts"
    existing_ids, existing_keys = backlog.parse_existing_ts()
    existing_meta = bf.parse_comics_meta()
    upc_map = bf.load_json(root / "src/data/comic-upc-map.json", {})
    cover_urls = bf.load_json(root / "src/data/comic-cover-urls.json", {})
    existing_locg = collect_locg_ids(upc_map, cover_urls, comics_ts.read_text())

    pace = Pace(0.0 if fixture_dir else args.delay)
    all_rows: list = []
    all_skips: list[dict] = []
    upc_local: dict = {}
    cover_local: dict = {}

    print(
        f"ingest {len(series_ids)} series  delay={args.delay}s  "
        f"min_year={args.min_year}  dry_run={args.dry_run}  "
        f"catalog_ids={len(existing_ids)} locgIds={len(existing_locg)}"
    )

    for sid in series_ids:
        rows, skips, u, c = ingest_series(
            sid,
            delay=args.delay,
            max_issues=args.max_issues,
            min_year=args.min_year,
            mains_only=not args.include_variants,
            use_cache_lists=args.use_cache_lists,
            pace=pace,
            existing_ids=existing_ids,
            existing_keys=existing_keys,
            existing_locg=existing_locg,
            existing_meta=existing_meta,
            cache=cache,
            fixture_dir=fixture_dir,
            id_prefix=args.id_prefix or None,
        )
        all_rows.extend(rows)
        all_skips.extend(skips)
        upc_local.update(u)
        cover_local.update(c)

    reasons = Counter(s["reason"] for s in all_skips)
    print(f"added={len(all_rows)} skipped={len(all_skips)} {dict(reasons)}")

    report = {
        "added": [
            {
                "id": r[0],
                "series": r[1],
                "issue": r[2],
                "publisher": r[3],
                "coverDate": r[4],
                "locgId": (r[13] or {}).get("locgId") if len(r) > 13 else None,
                "upc": (r[13] or {}).get("upc") if len(r) > 13 else None,
            }
            for r in all_rows
        ],
        "skipped": all_skips,
        "dryRun": bool(args.dry_run),
        "seriesIds": series_ids,
    }
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")

    if args.dry_run:
        print("dry-run: no writes")
        return 0

    if all_rows:
        comment = (
            f"LOCG series ingest ({', '.join(series_ids[:8])}"
            f"{'…' if len(series_ids) > 8 else ''}; locg-gated; floor {FLOOR})"
        )
        n = inject_rows(comics_ts, all_rows, comment)
        print(f"wrote {n} rows → {comics_ts}")
        bf.save_upc_map_atomic(upc_local)
        bf.save_cover_urls_atomic(cover_local)
        print(f"merged {len(upc_local)} upc-map / {len(cover_local)} cover-url entries")
    else:
        print("nothing to write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
