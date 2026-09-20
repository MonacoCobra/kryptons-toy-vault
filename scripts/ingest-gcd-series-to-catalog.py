#!/usr/bin/env python3
"""GCD dump → comics.ts catalog importer (OFFLINE first).

Highest-trust growth path alongside scripts/ingest-locg-series-to-catalog.py.
Adds NEW rows to src/data/comics.ts from a local Grand Comics Database dump
that Shelby/Lyra drop on the box (https://www.comics.org/download/ MySQL).
Never invents titles, publishers, issues, barcodes, or ISBNs. No gen-batch.
No Marvel API. No AI art.

HOLD comics.org API traffic. Default path is the dump. `--use-api` is
opt-in leftovers only.

Hard gates (every new comics.ts row) — GCD-only, per Shelby / Lyra:
  * Source is real GCD dump (or opt-in API) series + issue
  * Keep the row if it has ANY of: gcdIssueId OR upc OR isbn
    (barcode/ISBN is NOT required when a real GCD issue id is present)
  * Real series title, issue number, publisher from GCD — never invent
  * Skip duplicates (existing comics.ts id, series|issue|publisher|variant
    key, or existing GCD / LOCG linkage)
  * Variants plug into the live viewer (src/lib/comic-variants.ts):
    sibling comics.ts rows, same series+issue+publisher (comicFamilyKey).
    extra.variant from GCD variant_name (empty = Cover A / primary).
    Own catalog id + gcdIssueId; UPC from the dump when present.
  * Keep a variant only when variant_of_id resolves to a real parent
    gcd_issue in the same series and we can share that parent's
    series+issue+publisher. Skip orphans / no-family.
  * Keep trades / omnibuses / collected editions (default --include-collected).
    Format is the live ComicFormat union: single | annual | tpb | hc |
    omnibus | facsimile — never "hardcover"
  * Skip no parseable GCD date, pre-floor / --min-year. [nn] issue numbers
    are OK for books.

Map: store gcdIssueId (+ comics.org issue url as identity, not a fetch) in
comic-upc-map.json. Never invent UPCs. LOCG / Metron UPCs win on merge.

Dump layouts (--sql-dump / --dump-dir)
--------------------------------------
  * official YYYY-MM-DD.sql / .sql.gz (streamed; only 3 tables)
  * table slices: publishers.sql + series.sql + issues.sql
  * gcd.sqlite (already converted via scripts/load-gcd-sql-dump.py)
  * gcd_publisher.json + gcd_series.json + gcd_issue.json

Glyph box (LIVE — 2026-09-01)
-----------------------------
  zip:    /workspace/gcd-dump/gcd-dump.zip
  sql:    /workspace/gcd-dump/extracted/2026-09-01.sql
  sqlite: /workspace/gcd-dump/gcd.sqlite

  python3 scripts/ingest-gcd-series-to-catalog.py \\
      --sql-dump /workspace/gcd-dump/extracted/2026-09-01.sql \\
      --publisher Image --min-year 2016 --max-issues 8 --dry-run

  python3 scripts/ingest-gcd-series-to-catalog.py \\
      --sql-dump /workspace/gcd-dump/extracted/2026-09-01.sql \\
      --series-ids-file scripts/gcd-series-ids.example.txt --dry-run

  python3 scripts/load-gcd-sql-dump.py \\
      --sql-dump /workspace/gcd-dump/extracted/2026-09-01.sql \\
      --sqlite /workspace/gcd-dump/gcd.sqlite

  python3 scripts/ingest-gcd-series-to-catalog.py \\
      --dump-sqlite /workspace/gcd-dump/gcd.sqlite --publisher Image --max-issues 20 --dry-run

  python3 scripts/ingest-gcd-series-to-catalog.py \\
      --sql-dump /workspace/gcd-dump/extracted/2026-09-01.sql \\
      --list-dump-series --publisher Boom

  # Fixture proof (no live comics.org, no full dump required)
  python3 scripts/ingest-gcd-series-to-catalog.test.py
  python3 scripts/ingest-gcd-series-to-catalog.py \\
      --dump-dir scripts/fixtures/gcd-dump-ingest --series-id 900101 --dry-run

API leftover (OFF by default — do not use during 429 storms)
------------------------------------------------------------
  python3 scripts/ingest-gcd-series-to-catalog.py --use-api --series-id 122674 --dry-run

On 429/403/503: honor Retry-After if present, take ONE long cooldown, raise
session delay, and STOP. Do not retry into a ceiling. Operators: pause this
source on persistent 429 storms rather than looping the importer.

Do not run gen-batch-* from this path.
LOCG importer gates are unchanged (locgId + UPC|cover).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))
import comic_backlog_common as backlog  # noqa: E402
import gcd_dump  # noqa: E402


def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


locg = _load_mod("ingest_locg_series_to_catalog", SCRIPT_DIR / "ingest-locg-series-to-catalog.py")
bf = locg.bf

FLOOR = backlog.FLOOR  # 1980-01-01
API = "https://www.comics.org/api"
UA = (
    "KryptonsToyVault/1.0 (personal collection; gcd series catalog ingest; "
    "+https://github.com/MonacoCobra/kryptons-toy-vault)"
)
LIVE_DELAY_FLOOR = 6.0
DEFAULT_DELAY = 7.0
# Opt-in API only. On 429/403/503: one cooldown, then STOP. No ceiling-retry.
PULLBACK_CODES = {403, 429, 503}
LONG_COOLDOWN_SEC = 300.0
COOLDOWN_CAP_SEC = 900.0
SESSION_DELAY_FLOOR_ON_PULLBACK = 60.0
SESSION_DELAY_CAP = 120.0

MONTHS = locg.MONTHS


class RateLimitAbort(RuntimeError):
    """comics.org 429 pull-back: pause the run instead of retrying into the ceiling."""


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def bind_paths(root: Path) -> None:
    """Point this module + LOCG/backfill/backlog helpers at `root`."""
    global ROOT
    ROOT = root
    locg.bind_paths(root)


def parse_series_ids_file(path: Path) -> list[str]:
    return locg.parse_series_ids_file(path)


def normalize_upc(raw: str | None) -> str | None:
    """Digits-only UPC/EAN/ISBN from GCD. Never invent. Reject placeholder 111111*."""
    if not raw:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if not digits or digits.startswith("111111"):
        return None
    if 11 <= len(digits) <= 18:
        return digits
    return None


def extract_id(url: str | None, kind: str) -> str | None:
    if not url:
        return None
    m = re.search(rf"/{kind}/(\d+)", str(url))
    return m.group(1) if m else None


def gcd_issue_id(issue: dict, url: str = "") -> str | None:
    raw = issue.get("id")
    if raw is not None and str(raw).isdigit():
        return str(raw)
    return extract_id(issue.get("api_url") or url, "issue")


def descriptor_issue_num(desc: str) -> str | None:
    d = (desc or "").strip()
    if not d:
        return None
    if re.fullmatch(r"\d+", d):
        return d
    m = re.match(r"^(\d+)\s*\(", d)
    if m:
        return m.group(1)
    m = re.match(r"^(\d+)\b", d)
    if m and "[" not in d[: m.end() + 1]:
        if re.search(r"variant|cover|edition|virgin|foil", d, re.I):
            return None
        return m.group(1)
    # GCD books often print [nn] / nn (no number). Keep as identity.
    if re.fullmatch(r"\[nnn?\]|nnn?|½|1/2", d, re.I):
        return d
    return None


def catalog_issue_slug(issue: str) -> str:
    """Catalog-id token only — display issue stays as GCD printed it."""
    token = re.sub(r"[^a-z0-9]+", "-", str(issue or "").strip().lower()).strip("-")
    return token or "nn"


def is_nn_issue(number: str | None) -> bool:
    return bool(re.fullmatch(r"\[nnn?\]|nnn?", str(number or "").strip(), re.I))


def main_issue_sort_key(number: str | None, *tiebreak: str) -> tuple:
    """Numbered floppies first so --max-issues does not prefer [nn] books."""
    raw = str(number or "").strip()
    digits = re.sub(r"\D", "", raw)
    if is_nn_issue(raw) or not digits:
        return (1, 0, raw, *tiebreak)
    return (0, int(digits), raw, *tiebreak)


def variant_of_id(issue: dict) -> str | None:
    raw = issue.get("variant_of_id")
    if raw in (None, "", 0, "0"):
        raw = issue.get("variant_of")
    if raw in (None, "", 0, "0"):
        return None
    if isinstance(raw, str) and not raw.strip().isdigit():
        return extract_id(raw, "issue")
    token = str(raw).strip()
    return token if token.isdigit() else None


def is_cover_a_name(name: str | None) -> bool:
    """True when GCD variant_name is empty or Cover A / regular / main (the parent).

    Also treat Direct/Newsstand distribution labels as the main market copy when
    variant_of_id is empty — GCD often stamps these on otherwise-primary issues.
    """
    n = re.sub(r"\s+", " ", (name or "").strip().lower())
    if not n:
        return True
    if n in {
        "a",
        "cover a",
        "regular",
        "main",
        "standard",
        "direct",
        "direct edition",
        "direct market",
        "newsstand",
        "newsstand edition",
    }:
        return True
    # "Cover A - Robert Carey" / "Cover A: Foo"
    return bool(re.match(r"^cover\s*a(\s*[-–:|/].*)?$", n))


def is_variant_issue(issue: dict) -> bool:
    """True IFF variant_of_id resolves. Empty variant_of_id is always a main.

    DC/GCD often stamp artist names ("Jamal Campbell Cover") on primaries with
    empty variant_of_id — those are Cover A / mains, not variants. is_cover_a_name
    remains for Cover A / Direct / Newsstand labels only; it is NOT the
    variant-vs-main discriminator.
    """
    return variant_of_id(issue) is not None


def issue_series_id(issue: dict) -> str:
    sid = issue.get("series_id")
    if sid is not None and str(sid).isdigit():
        return str(sid)
    return extract_id(str(issue.get("series") or ""), "series") or ""


def same_series(issue: dict, series: dict, series_id: str) -> bool:
    iid = issue_series_id(issue)
    if iid and series_id:
        return iid == str(series_id)
    iname = (issue.get("series_name") or "").strip().lower()
    sname = (series.get("name") or "").strip().lower()
    if iname and sname:
        return iname == sname
    return True


def resolve_variant_attachment(
    issue: dict,
    *,
    series: dict,
    series_id: str,
    by_id: dict[str, dict],
    fetch_issue: Callable[[str], dict | None] | None = None,
) -> tuple[dict | None, str | None]:
    """Return (root_parent, skip_reason). (None, None) if this row is a main."""
    if not is_variant_issue(issue):
        return None, None
    name = (issue.get("variant_name") or "").strip()
    vid = variant_of_id(issue)
    if not vid:
        return None, "variant-orphan"
    seen: set[str] = set()
    current = vid
    parent: dict | None = None
    while current and current not in seen:
        seen.add(current)
        parent = by_id.get(current)
        if parent is None and fetch_issue is not None:
            fetched = fetch_issue(current)
            if isinstance(fetched, dict):
                parent = fetched
                by_id[current] = fetched
        if not isinstance(parent, dict):
            return None, "variant-orphan"
        if not same_series(parent, series, str(series_id)):
            return None, "variant-orphan"
        nxt = variant_of_id(parent)
        if not nxt:
            break
        current = nxt
    if not name:
        return None, "variant-orphan"
    return parent, None


def comic_family_key(series: str, issue: str, publisher: str) -> str:
    """Same grouping as src/lib/comic-variants.ts comicFamilyKey (no variant)."""
    def part(raw: str) -> str:
        return re.sub(r"\s+", " ", str(raw or "").strip().lower())

    return f"{part(series)}|{part(issue)}|{part(publisher)}"


def identity_key(series: str, issue: str, publisher: str, variant: str = "") -> str:
    """Ingest dedupe only — viewer grouping is comic_family_key (no variant)."""
    base = comic_family_key(series, issue, publisher)
    v = (variant or "").strip().lower()
    return f"{base}|variant:{v}" if v else base


def _row_family(row: list) -> tuple[str, str, str, str | None, dict]:
    extra = row[13] if len(row) > 13 and isinstance(row[13], dict) else {}
    fmt = str(row[9]) if len(row) > 9 else ""
    return str(row[1]), str(row[2]), str(row[3]), fmt or None, extra


def viewer_family_from_parent(
    parent: dict,
    *,
    series_name: str,
    publisher: str,
    existing_meta: dict[str, dict],
    added_rows: list,
    family_index: dict[str, tuple[str, str, str, str | None]] | None = None,
) -> tuple[str, str, str, str | None] | None:
    """Exact series+issue+publisher the variant must share, or None to skip.

    Live viewer groups siblings by comicFamilyKey (series|issue|publisher).
    Copy those strings from a resolved parent row already in this run or the
    catalog. If we cannot share that family with a real parent sibling, skip.
    Do not invent a parallel variant model.
    """
    gid = str(parent.get("id") or parent.get("gcdIssueId") or "")
    for row in added_rows:
        series_f, issue_f, pub_f, fmt, extra = _row_family(row)
        if gid and str(extra.get("gcdIssueId") or "") == gid:
            if series_f.strip() and issue_f.strip() and pub_f.strip():
                return series_f, issue_f, pub_f, fmt
            return None

    pnum = str(parent.get("number") or "").strip()
    series_c, pub_c = locg.canon_series_publisher(series_name, publisher, existing_meta)
    if not (series_c and pnum and pub_c):
        return None
    want = comic_family_key(series_c, pnum, pub_c)
    for row in added_rows:
        series_f, issue_f, pub_f, fmt, extra = _row_family(row)
        if extra.get("variant"):
            continue
        if comic_family_key(series_f, issue_f, pub_f) == want:
            return series_f, issue_f, pub_f, fmt

    if family_index is not None:
        return family_index.get(want)

    catalog_hit: tuple[str, str, str, str | None] | None = None
    for meta in existing_meta.values():
        if not isinstance(meta, dict):
            continue
        series_f = str(meta.get("series") or "")
        issue_f = str(meta.get("issue") or "")
        pub_f = str(meta.get("publisher") or "")
        if comic_family_key(series_f, issue_f, pub_f) != want:
            continue
        hit = (series_f, issue_f, pub_f, str(meta.get("format") or "") or None)
        if not meta.get("variant"):
            return hit
        if catalog_hit is None:
            catalog_hit = hit
    return catalog_hit


def apply_viewer_family(parsed: dict, parent: dict, *, series_name: str, publisher: str, existing_meta: dict[str, dict], added_rows: list, family_index: dict[str, tuple[str, str, str, str | None]] | None = None) -> str | None:
    """Stamp parent series+issue+publisher onto parsed, or return skip reason."""
    family = viewer_family_from_parent(
        parent,
        series_name=series_name,
        publisher=publisher,
        existing_meta=existing_meta,
        added_rows=added_rows,
        family_index=family_index,
    )
    if family is None:
        return "variant-orphan"
    series_f, issue_f, pub_f, fmt = family
    if not (str(series_f).strip() and str(issue_f).strip() and str(pub_f).strip()):
        return "variant-orphan"
    parsed["series"] = series_f
    parsed["issue"] = issue_f
    parsed["publisher"] = pub_f
    if fmt:
        parsed["format"] = fmt
    return None


def identity_keys_from_meta(existing_meta: dict[str, dict]) -> set[str]:
    keys: set[str] = set()
    for meta in existing_meta.values():
        if not isinstance(meta, dict):
            continue
        keys.add(
            identity_key(
                str(meta.get("series") or ""),
                str(meta.get("issue") or ""),
                str(meta.get("publisher") or ""),
                str(meta.get("variant") or ""),
            )
        )
    return keys


def build_viewer_family_index(
    existing_meta: dict[str, dict],
) -> dict[str, tuple[str, str, str, str | None]]:
    """comic_family_key → (series, issue, publisher, format). Prefer non-variant.

    Same selection rules as the linear scan in viewer_family_from_parent, but O(1)
    per lookup so long-running series (Action Comics, etc.) stay tractable.
    """
    index: dict[str, tuple[str, str, str, str | None]] = {}
    variant_fallback: dict[str, tuple[str, str, str, str | None]] = {}
    for meta in existing_meta.values():
        if not isinstance(meta, dict):
            continue
        series_f = str(meta.get("series") or "")
        issue_f = str(meta.get("issue") or "")
        pub_f = str(meta.get("publisher") or "")
        key = comic_family_key(series_f, issue_f, pub_f)
        if not key or key == "||":
            continue
        hit = (series_f, issue_f, pub_f, str(meta.get("format") or "") or None)
        if meta.get("variant"):
            variant_fallback.setdefault(key, hit)
        else:
            index[key] = hit
    for key, hit in variant_fallback.items():
        index.setdefault(key, hit)
    return index



def build_series_canon_index(
    existing_meta: dict[str, dict],
) -> dict[str, list[tuple[str, str]]]:
    """series_match_key → [(catalog series, catalog publisher), ...] for O(1) canon."""
    index: dict[str, list[tuple[str, str]]] = {}
    for meta in existing_meta.values():
        if not isinstance(meta, dict):
            continue
        series = str(meta.get("series") or "")
        publisher = str(meta.get("publisher") or "")
        key = locg.series_match_key(series)
        if not key:
            continue
        index.setdefault(key, []).append((series, publisher))
    return index


def canon_series_publisher_indexed(
    series: str,
    publisher: str,
    existing_meta: dict[str, dict],
    series_index: dict[str, list[tuple[str, str]]] | None = None,
) -> tuple[str, str]:
    """Same result as locg.canon_series_publisher, with optional match-key index."""
    if series_index is None:
        return locg.canon_series_publisher(series, publisher, existing_meta)
    key = locg.series_match_key(series)
    for cat_series, cat_pub in series_index.get(key, ()):
        if locg.series_names_match(cat_series, series) and bf.publisher_ok(cat_pub, publisher):
            return cat_series, cat_pub
    pub_key = locg.norm_pub_key(publisher)
    return series, locg.PUB_CANON.get(pub_key, publisher)


def make_gcd_catalog_id(
    *,
    series: str,
    issue: str,
    publisher: str,
    cover_date: str,
    existing_ids: set[str],
    existing_meta: dict[str, dict],
    id_prefix_override: str | None,
    variant: str = "",
    gcd_issue_id: str = "",
) -> str | None:
    issue = catalog_issue_slug(issue)
    vslug = locg.slugify_series(variant) if variant else ""
    if not vslug:
        return locg.make_catalog_id(
            series=series,
            issue=issue,
            publisher=publisher,
            cover_date=cover_date,
            existing_ids=existing_ids,
            existing_meta=existing_meta,
            id_prefix_override=id_prefix_override,
        )
    year = cover_date[:4] if re.match(r"^\d{4}", cover_date) else ""
    reused = locg.infer_existing_prefix(existing_meta, series, publisher)
    pub_pref = locg.publisher_prefix(publisher)
    slug = locg.slugify_series(series)
    generated = f"{pub_pref}-{slug}"
    prefix = id_prefix_override or reused or generated
    candidates = [f"{prefix}-{issue}-{vslug}"]
    if year:
        candidates.append(f"{prefix}-{year}-{issue}-{vslug}")
    if gcd_issue_id.isdigit():
        candidates.append(f"{prefix}-{issue}-{vslug}-{gcd_issue_id}")
    for cid in candidates:
        if cid not in existing_ids and re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)+$", cid):
            return cid
    return None


def is_main_descriptor(desc: str) -> bool:
    d = (desc or "").strip()
    if re.search(r"variant|virgin|foil|blank cover|incentive|exclusive", d, re.I):
        return False
    if re.fullmatch(r"\[nnn?\]|nnn?", d, re.I):
        return True
    if "[" in d:
        return False
    return descriptor_issue_num(d) is not None


def parse_gcd_date(*candidates: str | None) -> str | None:
    """Normalize a date GCD printed. YYYY-MM-DD or None. No invention."""
    for raw in candidates:
        if not raw:
            continue
        s = str(raw).strip()
        if not s:
            continue
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
        if m:
            year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if month == 0:
                month = 1
            if day == 0:
                day = 1
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{year:04d}-{month:02d}-{day:02d}"
            continue
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


def parse_gcd_price(raw: str | None) -> float | None:
    if not raw:
        return None
    m = re.search(r"(\d+(?:\.\d{1,2})?)", str(raw).replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def clean_credit(raw: str | None) -> str:
    text = re.sub(r"<[^>]+>", "", str(raw or ""))
    text = re.sub(r"\s+", " ", text).strip(" ;,")
    if not text or text.lower() in {"none", "n/a", "na", "?", "-"}:
        return ""
    return text


def credits_from_stories(issue: dict) -> tuple[str, str]:
    stories = [s for s in (issue.get("story_set") or []) if isinstance(s, dict)]

    def score(s: dict) -> tuple[int, float]:
        t = str(s.get("type") or "").lower()
        pages = s.get("page_count")
        try:
            page_n = -float(pages)
        except (TypeError, ValueError):
            page_n = 0.0
        return (0 if "comic story" in t else 1, page_n)

    writers: list[str] = []
    artists: list[str] = []
    for s in sorted(stories, key=score):
        w = clean_credit(s.get("script"))
        a = clean_credit(s.get("pencils")) or clean_credit(s.get("inks"))
        if w and w not in writers:
            writers.append(w)
        if a and a not in artists:
            artists.append(a)
        if writers and artists:
            break
    return "; ".join(writers), "; ".join(artists)


# Live CatalogComic.format — src/lib/types.ts ComicFormat. Never emit "hardcover".
COMIC_FORMATS = ("single", "annual", "tpb", "hc", "omnibus", "facsimile")
# Collected books only use this subset (Compendium → tpb unless omnibus/hc).
COLLECTED_FORMATS = ("tpb", "hc", "omnibus")


def infer_format(series: str, issue: dict) -> str:
    """Map GCD title/series/publishing_format onto ComicFormat.

    omnibus → omnibus
    hardcover / hardback / HC / absolute edition / deluxe HC → hc
    trade paperback / TP / TPB / compendium / collection → tpb
      unless clearly HC or omnibus
    """
    blob = " ".join(
        str(x or "")
        for x in (
            series,
            issue.get("descriptor"),
            issue.get("title"),
            issue.get("publishing_format"),
            issue.get("publishingFormat"),
            issue.get("series_name"),
            issue.get("series"),
        )
    )
    if re.search(r"\b(?:facsimile)\b", blob, re.I):
        return "facsimile"
    if re.search(r"\b(?:omnibus)\b", blob, re.I):
        return "omnibus"
    if re.search(
        r"\b(?:hardcover|hardback|hc|absolute edition|deluxe\s+(?:hc|hardcover))\b",
        blob,
        re.I,
    ):
        return "hc"
    if re.search(
        r"\b(?:trade paperback|tpb|tp|compendium|collected edition|collection|deluxe edition)\b",
        blob,
        re.I,
    ):
        return "tpb"
    if re.search(r"\b(?:annual)\b", blob, re.I):
        return "annual"
    return "single"


def publisher_from_series(series: dict, client: "GcdClient") -> str:
    pub = series.get("publisher")
    if isinstance(pub, dict):
        return str(pub.get("name") or "").strip()
    if isinstance(pub, str) and pub.strip():
        if "/publisher/" in pub or pub.startswith("http"):
            data = client.get_json(pub)
            if isinstance(data, dict):
                return str(data.get("name") or "").strip()
            return ""
        return pub.strip()
    return ""


def collect_gcd_ids(upc_map: dict) -> set[str]:
    ids: set[str] = set()
    for ent in (upc_map or {}).values():
        if not isinstance(ent, dict):
            continue
        for key in ("gcdIssueId", "sourceId"):
            val = ent.get(key)
            if val is not None and str(val).isdigit() and (
                key == "gcdIssueId" or str(ent.get("source") or "") == "gcd"
            ):
                ids.add(str(val))
        url = str(ent.get("url") or ent.get("api_url") or "")
        gid = extract_id(url, "issue")
        if gid and str(ent.get("source") or "") in {"", "gcd"}:
            ids.add(gid)
    return ids


def collect_locg_ids(upc_map: dict, cover_urls: dict, comics_text: str) -> set[str]:
    return locg.collect_locg_ids(upc_map, cover_urls, comics_text)


def cache_series_entries(cache: dict) -> list[dict]:
    out = []
    for key, ent in (cache or {}).items():
        if not isinstance(ent, dict):
            continue
        sid = extract_id(ent.get("api_url"), "series")
        if not sid:
            continue
        out.append(
            {
                "seriesId": sid,
                "name": ent.get("name") or (key.split("|")[0] if "|" in key else key),
                "year": ent.get("year_began"),
                "country": ent.get("country") or "",
                "issueCount": len(ent.get("active_issues") or []),
            }
        )
    seen: set[str] = set()
    uniq = []
    for e in out:
        if e["seriesId"] in seen:
            continue
        seen.add(e["seriesId"])
        uniq.append(e)
    uniq.sort(key=lambda e: ((e.get("name") or "").lower(), e["seriesId"]))
    return uniq


def parse_retry_after(headers, *, now: datetime | None = None) -> float | None:
    """Seconds from a Retry-After header (delta-seconds or HTTP-date). None if absent/junk."""
    if headers is None:
        return None
    raw = None
    try:
        raw = headers.get("Retry-After") or headers.get("retry-after")
    except Exception:
        raw = None
    if not raw:
        return None
    text = str(raw).strip()
    if re.fullmatch(r"\d+", text):
        return float(text)
    try:
        when = parsedate_to_datetime(text)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        base = now or datetime.now(timezone.utc)
        return max(0.0, (when - base).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None


def pullback_cooldown(headers, *, default: float = LONG_COOLDOWN_SEC) -> float:
    hinted = parse_retry_after(headers)
    wait = hinted if hinted is not None else default
    return min(COOLDOWN_CAP_SEC, max(0.0, wait))


class GcdClient:
    """Opt-in comics.org JSON client. 429/403/503 → cooldown + STOP (no retries)."""

    def __init__(
        self,
        delay: float,
        *,
        sleep: Callable[[float], None] = time.sleep,
        urlopen: Callable[..., Any] | None = None,
        get_json_fn: Callable[[str], dict | list | None] | None = None,
    ):
        self.delay = max(0.0, float(delay))
        self.session_delay = self.delay
        self.sleep = sleep
        self.urlopen = urlopen or urllib.request.urlopen
        self.get_json_fn = get_json_fn
        self.last = 0.0
        self.aborted = False
        self.last_cooldown = 0.0

    def _pace(self) -> None:
        wait_for = self.session_delay
        if self.last and wait_for:
            elapsed = time.monotonic() - self.last
            if elapsed < wait_for:
                self.sleep(wait_for - elapsed)
        self.last = time.monotonic()

    def _raise_session_delay(self) -> None:
        self.session_delay = min(
            SESSION_DELAY_CAP,
            max(self.session_delay * 4.0, SESSION_DELAY_FLOOR_ON_PULLBACK),
        )

    def _pull_back(self, code: int, url: str, headers) -> None:
        """Stop hitting comics.org. One cooldown, then abort — no further requests."""
        self.aborted = True
        self._raise_session_delay()
        cooldown = pullback_cooldown(headers)
        self.last_cooldown = cooldown
        print(
            f"  HTTP {code} — pull-back {cooldown:.0f}s "
            f"(Retry-After honored if present); session delay now "
            f"{self.session_delay:.0f}s. STOP hitting comics.org. "
            f"Pause this source on a 429 storm — do not loop the importer.",
            file=sys.stderr,
        )
        if cooldown:
            self.sleep(cooldown)
        raise RateLimitAbort(
            f"gcd HTTP {code} on {url} — source paused after {cooldown:.0f}s cooldown. "
            f"Do not re-run against comics.org until the storm clears; use --dump-dir."
        )

    def get_json(self, url: str) -> dict | list | None:
        if self.aborted:
            raise RateLimitAbort("gcd pull-back: run already paused — use the dump")
        if self.get_json_fn is not None:
            self._pace()
            return self.get_json_fn(url)
        if "format=" not in url:
            join = "&" if "?" in url else "?"
            url = f"{url}{join}format=json"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": UA, "Accept": "application/json"},
        )
        self._pace()
        try:
            with self.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code in PULLBACK_CODES:
                self._pull_back(e.code, url, e.headers)
            print(f"  HTTP {e.code} {url}", file=sys.stderr)
            return None
        except RateLimitAbort:
            raise
        except Exception as e:
            print(f"  GET error {url}: {e}", file=sys.stderr)
            return None


def fixture_get_json(fixture_dir: Path) -> Callable[[str], dict | list | None]:
    def get_json(url: str) -> dict | list | None:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.rstrip("/")
        m = re.search(r"/api/(series|issue|publisher)/(\d+)", path)
        if not m:
            return None
        kind, ident = m.group(1), m.group(2)
        folder = {"series": "series", "issue": "issues", "publisher": "publishers"}[kind]
        fpath = fixture_dir / folder / f"{ident}.json"
        if not fpath.exists():
            raise FileNotFoundError(f"fixture {kind} {ident} missing: {fpath}")
        return json.loads(fpath.read_text())

    return get_json


def parse_issue(
    issue: dict,
    *,
    url: str,
    series: dict,
    publisher: str,
    descriptor: str,
) -> dict:
    """Lift GCD fields only. Empty stays empty — never invent."""
    series_name = (
        (issue.get("series_name") or "").strip()
        or (series.get("name") or "").strip()
    )
    number = str(issue.get("number") or "").strip() or descriptor_issue_num(descriptor) or ""
    barcode = normalize_upc(issue.get("barcode"))
    isbn = normalize_upc(issue.get("valid_isbn") or issue.get("isbn"))
    cover = str(issue.get("cover") or "").strip()
    if cover and not cover.startswith("http"):
        cover = ""
    writers, artists = credits_from_stories(issue)
    cover_date = parse_gcd_date(
        issue.get("key_date"),
        issue.get("on_sale_date"),
        issue.get("publication_date"),
    )
    street = parse_gcd_date(issue.get("on_sale_date"))
    gid = gcd_issue_id(issue, url)
    api_url = (issue.get("api_url") or url or "").split("?", 1)[0]
    parsed = {
        "gcdIssueId": gid,
        "apiUrl": api_url,
        "series": series_name,
        "issue": number,
        "publisher": publisher,
        "upc": barcode,
        "isbn": isbn,
        "coverUrl": cover or None,
        "coverDate": cover_date,
        "streetDate": street,
        "writers": writers,
        "artists": artists,
        "msrp": parse_gcd_price(issue.get("price")),
        "title": (issue.get("title") or "").strip() or f"{series_name} #{number}".strip(" #"),
        "descriptor": descriptor or str(issue.get("descriptor") or ""),
        "variantName": (
            ""
            if variant_of_id(issue) is None
            else (issue.get("variant_name") or "").strip()
        ),
        "variantOf": issue.get("variant_of"),
        "publishingFormat": issue.get("publishing_format") or series.get("publishing_format"),
    }
    parsed["format"] = infer_format(series_name, parsed)
    return parsed


def gate_reason(
    parsed: dict,
    *,
    existing_ids: set[str],
    existing_keys: set[str],
    existing_gcd: set[str],
    existing_locg: set[str],
    min_year: int,
    catalog_id: str | None,
    include_collected: bool = True,
    max_year: int | None = None,
) -> str | None:
    """Shelby/Lyra: keep if ANY of gcdIssueId OR upc OR isbn + real identity."""
    gid = str(parsed.get("gcdIssueId") or "")
    upc = parsed.get("upc")
    isbn = parsed.get("isbn")
    if not gid.isdigit() and not upc and not isbn:
        return "no-gcdIssueId-or-upc-or-isbn"
    if gid.isdigit() and gid in existing_gcd:
        return "dup-gcdIssueId"
    series = (parsed.get("series") or "").strip()
    issue = str(parsed.get("issue") or "").strip()
    publisher = (parsed.get("publisher") or "").strip()
    if not series or not issue or not publisher:
        return "incomplete-identity"
    if not include_collected and (
        bf.looks_like_collected_edition(parsed.get("title"))
        or bf.looks_like_collected_edition(parsed.get("descriptor"))
        or bf.looks_like_collected_edition(series)
    ):
        return "collected-edition"
    cover_date = parsed.get("coverDate") or ""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", cover_date):
        return "no-cover-date"
    if cover_date < FLOOR:
        return "pre-floor"
    if min_year and int(cover_date[:4]) < min_year:
        return "min-year"
    if max_year is not None and int(cover_date[:4]) > max_year:
        return "max-year"
    if not catalog_id:
        return "id-collision"
    if catalog_id in existing_ids:
        return "dup-id"
    key = identity_key(series, issue, publisher, str(parsed.get("variantName") or ""))
    if key in existing_keys:
        return "dup-series-issue-publisher"
    return None


def build_row(catalog_id: str, parsed: dict, existing_meta: dict[str, dict]) -> list:
    series, publisher = locg.canon_series_publisher(
        parsed["series"], parsed["publisher"], existing_meta
    )
    issue = str(parsed["issue"])
    cover_date = parsed["coverDate"]
    writers = parsed.get("writers") or ""
    artists = parsed.get("artists") or ""
    title = parsed.get("title") or f"{series} #{issue}"
    msrp = float(parsed["msrp"]) if parsed.get("msrp") is not None else 0.0
    fmt = str(parsed.get("format") or "") or infer_format(series, parsed)
    if fmt not in COMIC_FORMATS:
        fmt = infer_format(series, parsed)
    if fmt not in COMIC_FORMATS:
        fmt = "single"
    demand = 0.8 if issue in {"1", "0"} else 0.55
    prefix = catalog_id.rsplit("-", 1)[0].split("-")[0]
    palette = locg.PALETTES.get(
        locg.publisher_prefix(publisher), locg.PALETTES.get(prefix, locg.DEFAULT_PALETTE)
    )
    extra: dict[str, str] = {}
    if parsed.get("variantName"):
        extra["variant"] = str(parsed["variantName"])
    code = parsed.get("upc") or parsed.get("isbn")
    if code:
        extra["upc"] = code
    if parsed.get("streetDate"):
        extra["streetDate"] = parsed["streetDate"]
    if parsed.get("coverUrl"):
        extra["cover"] = parsed["coverUrl"]
    if parsed.get("gcdIssueId"):
        extra["gcdIssueId"] = str(parsed["gcdIssueId"])
    return [
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
        0,
        palette,
        extra,
    ]


def finish_catalog_row(
    parsed: dict,
    *,
    series_id: str,
    desc: str,
    existing_ids: set[str],
    existing_keys: set[str],
    existing_gcd: set[str],
    existing_locg: set[str],
    existing_meta: dict[str, dict],
    min_year: int,
    id_prefix: str | None,
    include_collected: bool = True,
    max_year: int | None = None,
    series_index: dict[str, list[tuple[str, str]]] | None = None,
) -> tuple[list | None, dict | None]:
    # Cheap year/date gates BEFORE O(catalog) canon_series_publisher / id minting.
    # Same skip reasons as gate_reason for these cases; avoids scanning ~100k meta
    # rows for every pre-min_year dump issue on long-running series.
    cover_date = str(parsed.get("coverDate") or "")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", cover_date):
        return None, {
            "seriesId": series_id,
            "issue": parsed.get("issue") or desc,
            "gcdIssueId": parsed.get("gcdIssueId"),
            "variant": parsed.get("variantName") or None,
            "reason": "no-cover-date",
        }
    if cover_date < FLOOR:
        return None, {
            "seriesId": series_id,
            "issue": parsed.get("issue") or desc,
            "gcdIssueId": parsed.get("gcdIssueId"),
            "variant": parsed.get("variantName") or None,
            "reason": "pre-floor",
        }
    if min_year and int(cover_date[:4]) < min_year:
        return None, {
            "seriesId": series_id,
            "issue": parsed.get("issue") or desc,
            "gcdIssueId": parsed.get("gcdIssueId"),
            "variant": parsed.get("variantName") or None,
            "reason": "min-year",
        }
    if max_year is not None and int(cover_date[:4]) > max_year:
        return None, {
            "seriesId": series_id,
            "issue": parsed.get("issue") or desc,
            "gcdIssueId": parsed.get("gcdIssueId"),
            "variant": parsed.get("variantName") or None,
            "reason": "max-year",
        }

    parsed["series"], parsed["publisher"] = canon_series_publisher_indexed(
        parsed.get("series") or "",
        parsed.get("publisher") or "",
        existing_meta,
        series_index,
    )
    catalog_id = make_gcd_catalog_id(
        series=parsed.get("series") or "",
        issue=str(parsed.get("issue") or ""),
        publisher=parsed.get("publisher") or "",
        cover_date=parsed.get("coverDate") or "",
        existing_ids=existing_ids,
        existing_meta=existing_meta,
        id_prefix_override=id_prefix,
        variant=str(parsed.get("variantName") or ""),
        gcd_issue_id=str(parsed.get("gcdIssueId") or ""),
    )
    reason = gate_reason(
        parsed,
        existing_ids=existing_ids,
        existing_keys=existing_keys,
        existing_gcd=existing_gcd,
        existing_locg=existing_locg,
        min_year=min_year,
        max_year=max_year,
        catalog_id=catalog_id,
        include_collected=include_collected,
    )
    if reason:
        return None, {
            "seriesId": series_id,
            "issue": parsed.get("issue") or desc,
            "gcdIssueId": parsed.get("gcdIssueId"),
            "variant": parsed.get("variantName") or None,
            "reason": reason,
        }
    assert catalog_id is not None
    row = build_row(catalog_id, parsed, existing_meta)
    existing_ids.add(catalog_id)
    existing_keys.add(
        identity_key(row[1], row[2], row[3], str(parsed.get("variantName") or ""))
    )
    if parsed.get("gcdIssueId"):
        existing_gcd.add(str(parsed["gcdIssueId"]))
    vlabel = f"  [{parsed['variantName']}]" if parsed.get("variantName") else ""
    print(
        f"  + {catalog_id}  {row[1]} #{row[2]}{vlabel}  gcd={parsed.get('gcdIssueId')}  "
        f"upc={parsed.get('upc') or parsed.get('isbn') or '—'}  {parsed.get('coverDate')}"
    )
    return row, None


def upc_entry(parsed: dict) -> dict:
    gid = str(parsed.get("gcdIssueId") or "")
    api_url = parsed.get("apiUrl") or (f"{API}/issue/{gid}/" if gid else "")
    ent: dict[str, Any] = {
        "fetchedAt": now_iso(),
        "source": "gcd",
        "title": parsed.get("title") or f"{parsed.get('series')} #{parsed.get('issue')}",
    }
    if gid:
        ent["gcdIssueId"] = gid
        ent["sourceId"] = gid
    if api_url:
        ent["url"] = api_url.split("?", 1)[0]
    if parsed.get("upc"):
        ent["upc"] = parsed["upc"]
    if parsed.get("isbn") and parsed.get("isbn") != parsed.get("upc"):
        ent["isbn"] = parsed["isbn"]
    if parsed.get("coverUrl"):
        ent["coverUrl"] = parsed["coverUrl"]
    return ent


def ingest_series(
    series_id: str,
    *,
    client: GcdClient,
    max_issues: int,
    min_year: int,
    max_year: int | None = None,
    mains_only: bool,
    publisher_filter: str,
    existing_ids: set[str],
    existing_keys: set[str],
    existing_gcd: set[str],
    existing_locg: set[str],
    existing_meta: dict[str, dict],
    id_prefix: str | None,
    include_collected: bool = True,
    family_index: dict[str, tuple[str, str, str, str | None]] | None = None,
    series_index: dict[str, list[tuple[str, str]]] | None = None,
) -> tuple[list, list[dict], dict, dict]:
    rows: list = []
    skips: list[dict] = []
    upc_local: dict = {}
    cover_local: dict = {}

    series = client.get_json(f"{API}/series/{series_id}/")
    if not isinstance(series, dict):
        skips.append({"seriesId": series_id, "reason": "no-series"})
        return rows, skips, upc_local, cover_local

    # Do NOT hard-skip the whole series on year_began < min_year.
    # Long-running titles (Action Comics 1938→) still have post-min_year
    # issues; per-issue gate_reason(min_year) filters those. Publisher
    # ingest discovery lists all series (min_year=0); --list-dump-series
    # may still filter year_began for operator listing.

    publisher = publisher_from_series(series, client)
    if publisher_filter:
        pf = publisher_filter.strip()
        pub_url = str(series.get("publisher") or "")
        if pf.isdigit():
            if pf not in pub_url and pf not in publisher:
                skips.append({"seriesId": series_id, "reason": "publisher-filter", "publisher": publisher})
                return rows, skips, upc_local, cover_local
        elif not bf.publisher_ok(publisher, pf):
            skips.append({"seriesId": series_id, "reason": "publisher-filter", "publisher": publisher})
            return rows, skips, upc_local, cover_local

    descs = list(series.get("issue_descriptors") or [])
    urls = list(series.get("active_issues") or [])
    fetched: list[tuple[str, str, dict]] = []
    by_id: dict[str, dict] = {}
    for desc, url in zip(descs, urls):
        url = str(url)
        hinted_id = extract_id(url, "issue") or ""
        try:
            issue = client.get_json(url)
        except RateLimitAbort:
            raise
        if not isinstance(issue, dict):
            skips.append(
                {"seriesId": series_id, "issue": desc, "gcdIssueId": hinted_id, "reason": "no-issue"}
            )
            continue
        gid = gcd_issue_id(issue, url) or hinted_id
        if gid:
            by_id[str(gid)] = issue
        fetched.append((str(desc), url, issue))

    mains: list[tuple[str, str, dict]] = []
    variants: list[tuple[str, str, dict]] = []
    for desc, url, issue in fetched:
        if is_variant_issue(issue):
            variants.append((desc, url, issue))
        else:
            mains.append((desc, url, issue))

    def sort_key(item: tuple[str, str, dict]):
        return main_issue_sort_key(
            descriptor_issue_num(item[0]) or str(item[2].get("number") or ""),
            item[0],
        )

    mains.sort(key=sort_key)
    if max_issues and max_issues > 0:
        mains = mains[:max_issues]
    kept_main_ids = {str(gcd_issue_id(issue, url) or "") for _, url, issue in mains}
    kept_main_ids.discard("")

    print(
        f"series {series_id}: {series.get('name')} ({publisher}) — "
        f"{len(mains)} main / {len(variants)} variant issue(s)"
    )

    def fetch_parent(ident: str) -> dict | None:
        return client.get_json(f"{API}/issue/{ident}/")

    work = list(mains) + list(variants)
    for desc, url, issue in work:
        if mains_only and is_variant_issue(issue):
            skips.append(
                {
                    "seriesId": series_id,
                    "issue": issue.get("number") or desc,
                    "gcdIssueId": gcd_issue_id(issue, url),
                    "reason": "variant",
                }
            )
            continue
        parent, orphan = resolve_variant_attachment(
            issue,
            series=series,
            series_id=series_id,
            by_id=by_id,
            fetch_issue=fetch_parent,
        )
        if orphan:
            skips.append(
                {
                    "seriesId": series_id,
                    "issue": issue.get("number") or desc,
                    "gcdIssueId": gcd_issue_id(issue, url),
                    "reason": orphan,
                }
            )
            continue
        if parent is not None:
            root_id = str(gcd_issue_id(parent, "") or "")
            if max_issues and max_issues > 0 and root_id not in kept_main_ids:
                continue
        parsed = parse_issue(
            issue, url=url, series=series, publisher=publisher, descriptor=desc
        )
        # Skip known gcdIssueIds before expensive viewer-family resolution.
        early_gid = str(parsed.get("gcdIssueId") or "")
        if early_gid.isdigit() and early_gid in existing_gcd:
            skips.append(
                {
                    "seriesId": series_id,
                    "issue": issue.get("number") or desc,
                    "gcdIssueId": early_gid,
                    "reason": "dup-gcdIssueId",
                }
            )
            continue
        if parent is not None:
            parsed["variantName"] = (issue.get("variant_name") or "").strip()
            no_family = apply_viewer_family(
                parsed,
                parent,
                series_name=str(series.get("name") or parsed.get("series") or ""),
                publisher=publisher,
                existing_meta=existing_meta,
                added_rows=rows,
                family_index=family_index,
            )
            if no_family:
                skips.append(
                    {
                        "seriesId": series_id,
                        "issue": issue.get("number") or desc,
                        "gcdIssueId": gcd_issue_id(issue, url),
                        "reason": no_family,
                    }
                )
                continue
        row, skip = finish_catalog_row(
            parsed,
            series_id=series_id,
            desc=desc,
            existing_ids=existing_ids,
            existing_keys=existing_keys,
            existing_gcd=existing_gcd,
            existing_locg=existing_locg,
            existing_meta=existing_meta,
            min_year=min_year,
            max_year=max_year,
            id_prefix=id_prefix,
            include_collected=include_collected,
            series_index=series_index,
        )
        if skip:
            skips.append(skip)
            continue
        assert row is not None
        rows.append(row)
        upc_local[row[0]] = upc_entry(parsed)
        if parsed.get("coverUrl"):
            cover_local[row[0]] = parsed["coverUrl"]
    return rows, skips, upc_local, cover_local



def dump_issue_cover_year(issue: dict) -> int | None:
    """Best-effort year from dump fields for pre-parse year gating."""
    for key in ("key_date", "on_sale_date", "publication_date"):
        raw = str(issue.get(key) or "").strip()
        if not raw:
            continue
        m = re.search(r"(19|20)\d{2}", raw)
        if m:
            return int(m.group(0))
    return None


def preparse_year_skip(issue: dict, *, min_year: int, max_year: int | None) -> str | None:
    """Return min-year / max-year / pre-floor when dump dates are decisive."""
    year = dump_issue_cover_year(issue)
    if year is None:
        return None
    floor_year = int(FLOOR[:4]) if FLOOR else 0
    if floor_year and year < floor_year:
        return "pre-floor"
    if min_year and year < min_year:
        return "min-year"
    if max_year is not None and year > max_year:
        return "max-year"
    return None


def ingest_series_from_dump(
    series_id: str,
    *,
    store: gcd_dump.GcdDumpStore,
    max_issues: int,
    min_year: int,
    max_year: int | None = None,
    mains_only: bool,
    publisher_filter: str,
    existing_ids: set[str],
    existing_keys: set[str],
    existing_gcd: set[str],
    existing_locg: set[str],
    existing_meta: dict[str, dict],
    id_prefix: str | None,
    include_collected: bool = True,
    family_index: dict[str, tuple[str, str, str, str | None]] | None = None,
    series_index: dict[str, list[tuple[str, str]]] | None = None,
) -> tuple[list, list[dict], dict, dict]:
    """Gate dump rows the same way as API rows. No comics.org traffic."""
    rows: list = []
    skips: list[dict] = []
    upc_local: dict = {}
    cover_local: dict = {}

    series = store.get_series(series_id)
    if not series:
        skips.append({"seriesId": series_id, "reason": "no-series"})
        return rows, skips, upc_local, cover_local

    # Do NOT hard-skip the whole series on year_began < min_year.
    # Long-running titles (Action Comics 1938→) still have post-min_year
    # issues; per-issue gate_reason(min_year) filters those. Publisher
    # ingest discovery lists all series (min_year=0); --list-dump-series
    # may still filter year_began for operator listing.

    pub_row = store.get_publisher(series.get("publisher_id")) if series.get("publisher_id") is not None else None
    publisher = str((pub_row or {}).get("name") or "").strip()
    if publisher_filter:
        pf = publisher_filter.strip()
        if pf.isdigit():
            if str(series.get("publisher_id")) != pf:
                skips.append({"seriesId": series_id, "reason": "publisher-filter", "publisher": publisher})
                return rows, skips, upc_local, cover_local
        elif not bf.publisher_ok(publisher, pf):
            skips.append({"seriesId": series_id, "reason": "publisher-filter", "publisher": publisher})
            return rows, skips, upc_local, cover_local

    items = store.issues_for_series(series_id)
    by_id = {str(r.get("id")): r for r in items if r.get("id") is not None}
    mains = [r for r in items if not is_variant_issue(r)]
    variants = [r for r in items if is_variant_issue(r)]
    mains.sort(key=lambda r: main_issue_sort_key(str(r.get("number") or "")))
    if max_issues and max_issues > 0:
        mains = mains[:max_issues]
    kept_main_ids = {str(r.get("id")) for r in mains}

    print(
        f"series {series_id}: {series.get('name')} ({publisher}) — "
        f"{len(mains)} main / {len(variants)} variant dump issue(s)"
    )

    def fetch_parent(ident: str) -> dict | None:
        return store.get_issue(ident)

    for issue in mains + variants:
        desc = gcd_dump.dump_issue_descriptor(issue)
        if mains_only and is_variant_issue(issue):
            skips.append(
                {
                    "seriesId": series_id,
                    "issue": issue.get("number") or desc,
                    "gcdIssueId": issue.get("id"),
                    "reason": "variant",
                }
            )
            continue
        year_skip = preparse_year_skip(issue, min_year=min_year, max_year=max_year)
        if year_skip:
            skips.append(
                {
                    "seriesId": series_id,
                    "issue": issue.get("number") or desc,
                    "gcdIssueId": issue.get("id"),
                    "reason": year_skip,
                }
            )
            continue
        parent, orphan = resolve_variant_attachment(
            issue,
            series=series,
            series_id=series_id,
            by_id=by_id,
            fetch_issue=fetch_parent,
        )
        if orphan:
            skips.append(
                {
                    "seriesId": series_id,
                    "issue": issue.get("number") or desc,
                    "gcdIssueId": issue.get("id"),
                    "reason": orphan,
                }
            )
            continue
        if parent is not None:
            root_id = str(parent.get("id") or "")
            if max_issues and max_issues > 0 and root_id not in kept_main_ids:
                continue
        gid = str(issue.get("id") or "")
        parsed = parse_issue(
            {
                **issue,
                "api_url": f"{API}/issue/{gid}/" if gid.isdigit() else "",
                "series_name": series.get("name"),
                "variant_of": issue.get("variant_of_id"),
            },
            url=f"{API}/issue/{gid}/" if gid.isdigit() else "",
            series=series,
            publisher=publisher,
            descriptor=desc,
        )
        # Skip known gcdIssueIds before expensive viewer-family resolution.
        early_gid = str(parsed.get("gcdIssueId") or "")
        if early_gid.isdigit() and early_gid in existing_gcd:
            skips.append(
                {
                    "seriesId": series_id,
                    "issue": issue.get("number") or desc,
                    "gcdIssueId": early_gid,
                    "reason": "dup-gcdIssueId",
                }
            )
            continue
        if parent is not None:
            parsed["variantName"] = (issue.get("variant_name") or "").strip()
            no_family = apply_viewer_family(
                parsed,
                parent,
                series_name=str(series.get("name") or parsed.get("series") or ""),
                publisher=publisher,
                existing_meta=existing_meta,
                added_rows=rows,
                family_index=family_index,
            )
            if no_family:
                skips.append(
                    {
                        "seriesId": series_id,
                        "issue": issue.get("number") or desc,
                        "gcdIssueId": issue.get("id"),
                        "reason": no_family,
                    }
                )
                continue
        row, skip = finish_catalog_row(
            parsed,
            series_id=series_id,
            desc=desc,
            existing_ids=existing_ids,
            existing_keys=existing_keys,
            existing_gcd=existing_gcd,
            existing_locg=existing_locg,
            existing_meta=existing_meta,
            min_year=min_year,
            max_year=max_year,
            id_prefix=id_prefix,
            include_collected=include_collected,
            series_index=series_index,
        )
        if skip:
            skips.append(skip)
            continue
        assert row is not None
        rows.append(row)
        upc_local[row[0]] = upc_entry(parsed)
        if parsed.get("coverUrl"):
            cover_local[row[0]] = parsed["coverUrl"]
    return rows, skips, upc_local, cover_local


def persist(root: Path, rows: list, series_ids: list[str], upc_local: dict, cover_local: dict) -> None:
    comics_ts = root / "src/data/comics.ts"
    if rows:
        comment = (
            f"GCD series ingest ({', '.join(series_ids[:8])}"
            f"{'…' if len(series_ids) > 8 else ''}; gcd-gated; floor {FLOOR})"
        )
        n = locg.inject_rows(comics_ts, rows, comment)
        print(f"wrote {n} rows → {comics_ts}")
    if upc_local:
        bf.save_upc_map_atomic(upc_local)
    if cover_local:
        bf.save_cover_urls_atomic(cover_local)
    if upc_local or cover_local:
        print(f"merged {len(upc_local)} upc-map / {len(cover_local)} cover-url entries")
    if not rows and not upc_local:
        print("nothing to write")


def _dedupe_ids(ids: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for sid in ids:
        if sid in seen:
            continue
        seen.add(sid)
        out.append(sid)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--series-id", action="append", default=[], help="GCD series id (repeatable)")
    ap.add_argument(
        "--series-ids-file",
        type=str,
        default="",
        help="File of GCD series ids (one per line or JSON list)",
    )
    ap.add_argument(
        "--publisher",
        type=str,
        default="",
        help="GCD publisher name or numeric publisher id (dump filter / discovery)",
    )
    ap.add_argument(
        "--sql-dump",
        type=str,
        default="",
        help="Official YYYY-MM-DD.sql[.gz] (Glyph box: /workspace/gcd-dump/extracted/2026-09-01.sql)",
    )
    ap.add_argument(
        "--dump-dir",
        type=str,
        default="",
        help="Local GCD dump drop: directory, YYYY-MM-DD.sql[.gz], or gcd.sqlite.",
    )
    ap.add_argument(
        "--dump-sqlite",
        type=str,
        default="",
        help="Already-converted gcd.sqlite (Glyph box: /workspace/gcd-dump/gcd.sqlite)",
    )
    ap.add_argument(
        "--cache-sqlite",
        type=str,
        default="",
        help="Where to write/reuse the SQL→sqlite working copy",
    )
    ap.add_argument(
        "--rebuild-dump-cache",
        action="store_true",
        help="Rebuild sqlite from SQL even if a compatible cache exists",
    )
    ap.add_argument(
        "--use-api",
        action="store_true",
        help="OPT-IN comics.org API (off by default). Hold during 429 storms; prefer --dump-dir.",
    )
    ap.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Seconds between opt-in API requests (default {DEFAULT_DELAY:g}; live floor {LIVE_DELAY_FLOOR:g})",
    )
    ap.add_argument("--max-issues", type=int, default=0, help="Cap issues per series (0=no cap)")
    ap.add_argument("--dry-run", action="store_true", help="Parse and gate only; do not write")
    ap.add_argument("--min-year", type=int, default=1980, help="Skip series/issues below this year")
    ap.add_argument(
        "--max-year",
        type=int,
        default=0,
        help="Skip series/issues above this year (0=no ceiling)",
    )
    ap.add_argument("--fixture-dir", type=str, default="", help="API JSON fixtures (only with --use-api)")
    ap.add_argument("--from-cache", action="store_true", help="Use series ids from comic-gcd-series-cache.json")
    ap.add_argument("--list-cache-seeds", action="store_true", help="Print cached GCD series ids and exit")
    ap.add_argument("--list-dump-series", action="store_true", help="Print series from the dump (optional --publisher)")
    ap.add_argument(
        "--include-variants",
        action="store_true",
        help="Keep parent-linked variants (default). Orphans are always skipped.",
    )
    ap.add_argument(
        "--mains-only",
        action="store_true",
        help="Skip all variants, even when variant_of_id resolves to a parent.",
    )
    ap.add_argument(
        "--include-collected",
        dest="include_collected",
        action="store_true",
        default=True,
        help="Keep trades, omnibuses, and collected editions (default ON).",
    )
    ap.add_argument(
        "--skip-collected",
        dest="include_collected",
        action="store_false",
        help="Skip collected editions (omnibus / TP / TPB / HC / deluxe / compendium).",
    )
    ap.add_argument("--id-prefix", type=str, default="", help="Force catalog id prefix (e.g. im-nocterra)")
    ap.add_argument("--root", type=str, default="", help="Workspace root (tests)")
    ap.add_argument("--report", type=str, default="", help="Write JSON report of added/skipped")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve() if args.root else ROOT
    bind_paths(root)

    cache_path = root / "scripts/comic-gcd-series-cache.json"
    cache = bf.load_json(cache_path, {})

    if args.list_cache_seeds:
        seeds = cache_series_entries(cache)
        for e in seeds:
            print(f"{e['seriesId']}\t{e.get('year') or ''}\t{e['name']}")
        print(f"# {len(seeds)} unique GCD series ids", file=sys.stderr)
        return 0

    sql_dump: Path | None = None
    if args.sql_dump:
        sql_dump = gcd_dump.resolve_user_path(args.sql_dump, root)
        if not sql_dump.exists():
            raise SystemExit(f"sql-dump not found: {sql_dump}\n{gcd_dump.MISSING_DUMP_MESSAGE}")
        if not gcd_dump.is_sql_file(sql_dump):
            raise SystemExit(f"--sql-dump must be a .sql / .sql.gz file: {sql_dump}")

    dump_dir = gcd_dump.discover_dump_dir(
        args.dump_dir or None,
        root=root,
    )
    if args.dump_dir:
        dump_dir = gcd_dump.resolve_user_path(args.dump_dir, root)
        if not dump_dir.exists():
            raise SystemExit(f"dump-dir not found: {dump_dir}\n{gcd_dump.MISSING_DUMP_MESSAGE}")
        if dump_dir.is_file() and not (
            gcd_dump.is_sql_file(dump_dir) or gcd_dump.is_sqlite_file(dump_dir)
        ):
            raise SystemExit(f"dump-dir file is not a GCD SQL/sqlite dump: {dump_dir}")

    dump_sqlite = gcd_dump.resolve_user_path(args.dump_sqlite, root) if args.dump_sqlite else None
    cache_sqlite = gcd_dump.resolve_user_path(args.cache_sqlite, root) if args.cache_sqlite else None

    series_ids: list[str] = []
    for sid in args.series_id:
        token = str(sid).strip()
        if token.isdigit():
            series_ids.append(token)
        else:
            raise SystemExit(f"invalid --series-id (must be numeric GCD id): {sid}")
    if args.series_ids_file:
        series_ids.extend(parse_series_ids_file(Path(args.series_ids_file)))
    if args.from_cache:
        series_ids.extend(e["seriesId"] for e in cache_series_entries(cache))
    series_ids = _dedupe_ids(series_ids)

    store: gcd_dump.GcdDumpStore | None = None
    use_dump = not args.use_api
    if args.use_api and (dump_dir or dump_sqlite or sql_dump):
        print("note: --use-api ignores --sql-dump / --dump-dir (API leftover path)", file=sys.stderr)

    if use_dump:
        if not dump_dir and not dump_sqlite and not sql_dump:
            raise SystemExit(gcd_dump.MISSING_DUMP_MESSAGE)
        discover_only = bool(args.list_dump_series or (args.publisher and not series_ids))
        try:
            # Empty filter = publishers + series only (no issue stream) for listing.
            # Explicit series ids stream just those issues. None = all issues.
            filter_ids: list[str] | None
            if discover_only:
                filter_ids = []
            else:
                filter_ids = series_ids or None
            store = gcd_dump.open_dump(
                dump_dir=dump_dir,
                dump_sqlite=dump_sqlite,
                sql_dump=sql_dump,
                cache_sqlite=cache_sqlite,
                series_ids=filter_ids,
                rebuild_cache=args.rebuild_dump_cache,
            )
        except FileNotFoundError as e:
            raise SystemExit(str(e)) from e

        if args.list_dump_series:
            pubs = store.find_publishers(args.publisher) if args.publisher else []
            listed = 0
            if args.publisher and not pubs:
                print(f"# no dump publisher match for {args.publisher!r}", file=sys.stderr)
                return 1
            targets = pubs if pubs else [None]
            for pub in targets:
                rows = (
                    store.series_for_publisher(pub["id"], args.min_year)
                    if pub
                    else []
                )
                if pub is None:
                    # No publisher filter: require series ids already in hand.
                    print("# pass --publisher to list dump series", file=sys.stderr)
                    return 0
                for s in rows:
                    print(f"{s['id']}\t{s.get('year_began') or ''}\t{pub.get('name')}\t{s.get('name')}")
                    listed += 1
            print(f"# {listed} dump series", file=sys.stderr)
            store.close()
            return 0

        if not series_ids and args.publisher:
            pubs = store.find_publishers(args.publisher)
            if not pubs:
                store.close()
                raise SystemExit(f"no dump publisher match for {args.publisher!r}")
            for pub in pubs:
                # Ingest discovery: list ALL non-deleted series for the publisher.
                # Do NOT pass --min-year here — year_began < min_year series
                # (Action Comics 1938, Amazing Spider-Man 1963, …) still carry
                # post-min_year issues; per-issue gate_reason(min_year) filters.
                # --list-dump-series keeps the year filter for operator listing.
                for s in store.series_for_publisher(pub["id"], 0):
                    series_ids.append(str(s["id"]))
            series_ids = _dedupe_ids(series_ids)
            print(f"dump publisher {args.publisher!r} → {len(series_ids)} series", file=sys.stderr)

        if discover_only and series_ids:
            store.close()
            try:
                store = gcd_dump.open_dump(
                    dump_dir=dump_dir,
                    dump_sqlite=dump_sqlite,
                    sql_dump=sql_dump,
                    cache_sqlite=cache_sqlite,
                    series_ids=series_ids,
                    rebuild_cache=args.rebuild_dump_cache,
                )
            except FileNotFoundError as e:
                raise SystemExit(str(e)) from e

        if not series_ids:
            store.close()
            raise SystemExit(
                "no series ids — pass --series-id, --series-ids-file, --from-cache, "
                "or --publisher (dump discovery). Prefer Image / Boom / IDW / Dark Horse. "
                "See scripts/gcd-series-ids.example.txt."
            )
    else:
        if args.list_dump_series:
            raise SystemExit("--list-dump-series needs --sql-dump / --dump-dir (not --use-api)")

    fixture_dir = Path(args.fixture_dir).resolve() if args.fixture_dir else None
    delay = float(args.delay)
    client: GcdClient | None = None
    if args.use_api:
        if fixture_dir:
            if not fixture_dir.is_dir():
                raise SystemExit(f"fixture-dir not found: {fixture_dir}")
            delay = 0.0
        elif delay < LIVE_DELAY_FLOOR:
            print(
                f"comics.org 429s — raising --delay {delay} → {LIVE_DELAY_FLOOR}s (polite floor)",
                file=sys.stderr,
            )
            delay = LIVE_DELAY_FLOOR
        if not series_ids:
            raise SystemExit(
                "no series ids for --use-api — pass --series-id / --series-ids-file / --from-cache. "
                "Prefer --dump-dir instead of the API."
            )
        client = GcdClient(
            delay,
            get_json_fn=fixture_get_json(fixture_dir) if fixture_dir else None,
        )

    comics_ts = root / "src/data/comics.ts"
    existing_ids, existing_keys_plain = backlog.parse_existing_ts()
    existing_meta = bf.parse_comics_meta()
    existing_keys = existing_keys_plain | identity_keys_from_meta(existing_meta)
    family_index = build_viewer_family_index(existing_meta)
    series_index = build_series_canon_index(existing_meta)
    upc_map = bf.load_json(root / "src/data/comic-upc-map.json", {})
    cover_urls = bf.load_json(root / "src/data/comic-cover-urls.json", {})
    existing_gcd = collect_gcd_ids(upc_map)
    existing_locg = collect_locg_ids(upc_map, cover_urls, comics_ts.read_text())

    all_rows: list = []
    all_skips: list[dict] = []
    upc_local: dict = {}
    cover_local: dict = {}
    aborted = False
    source = "dump" if store else "api"

    print(
        f"gcd ingest {len(series_ids)} series  source={source}  "
        f"min_year={args.min_year}  dry_run={args.dry_run}  "
        f"include_collected={args.include_collected}  "
        f"catalog_ids={len(existing_ids)} gcdIds={len(existing_gcd)}"
    )

    try:
        for sid in series_ids:
            try:
                if store is not None:
                    rows, skips, u, c = ingest_series_from_dump(
                        sid,
                        store=store,
                        max_issues=args.max_issues,
                        min_year=args.min_year,
                        max_year=(args.max_year or None),
                        mains_only=args.mains_only,
                        publisher_filter=args.publisher,
                        existing_ids=existing_ids,
                        existing_keys=existing_keys,
                        existing_gcd=existing_gcd,
                        existing_locg=existing_locg,
                        existing_meta=existing_meta,
                        id_prefix=args.id_prefix or None,
                        include_collected=args.include_collected,
                        family_index=family_index,
                        series_index=series_index,
                    )
                else:
                    assert client is not None
                    rows, skips, u, c = ingest_series(
                        sid,
                        client=client,
                        max_issues=args.max_issues,
                        min_year=args.min_year,
                        max_year=(args.max_year or None),
                        mains_only=args.mains_only,
                        publisher_filter=args.publisher,
                        existing_ids=existing_ids,
                        existing_keys=existing_keys,
                        existing_gcd=existing_gcd,
                        existing_locg=existing_locg,
                        existing_meta=existing_meta,
                        id_prefix=args.id_prefix or None,
                        include_collected=args.include_collected,
                        family_index=family_index,
                        series_index=series_index,
                    )
            except RateLimitAbort as e:
                print(str(e), file=sys.stderr)
                aborted = True
                break
            all_rows.extend(rows)
            all_skips.extend(skips)
            upc_local.update(u)
            cover_local.update(c)
    finally:
        if store is not None:
            store.close()

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
                "format": r[9],
                "gcdIssueId": (r[13] or {}).get("gcdIssueId") if len(r) > 13 else None,
                "upc": (r[13] or {}).get("upc") if len(r) > 13 else None,
                "variant": (r[13] or {}).get("variant") if len(r) > 13 else None,
            }
            for r in all_rows
        ],
        "skipped": all_skips,
        "dryRun": bool(args.dry_run),
        "seriesIds": series_ids,
        "source": source,
        "abortedRateLimit": aborted,
        "sessionDelay": client.session_delay if client else 0,
    }
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")

    if args.dry_run:
        print("dry-run: no writes")
        return 2 if aborted else 0

    persist(root, all_rows, series_ids, upc_local, cover_local)
    return 2 if aborted else 0


if __name__ == "__main__":
    raise SystemExit(main())
