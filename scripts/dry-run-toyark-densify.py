#!/usr/bin/env python3
"""Toyark WordPress REST densify: propose (and optionally apply) new figures.

Polls https://www.toyark.com/wp-json/wp/v2/posts (with `_embed`) in a bounded
date window, filters to an allowlisted company set, and writes a JSON report.

Default is dry-run (report only). `--apply` appends accepted candidates that
are not already in oneshot (company+line+name+year+variant). Babysits may
commit figure-archive / alias / image-url deltas to main afterward.

Policy:
  - GTIN preferred but not required; never invent GTINs/UPCs/product codes
  - Manufacturer codes in prose (MMS897, HAS*, labeled UPC) → aliases only
  - Identity = company + line + year + variant (same character ≠ same figure)
  - Allowlist: hasbro, mcfarlane, neca, jazwares, plus Super7 and premium
    1/6 makers that already exist as CompanyIds (hottoys, mondo, threezero,
    enterbay, asmus, starace, exo6). No invented company ids (no sideshow).
  - Filter out sponsor newsletters, sales/deals, customs, photo-of-the-day,
    pure review/in-hand with no new product identity, vehicles/props-only,
    and non-figure entertainment news
  - Prefer new/reveal/pre-order/official-image + recognizable company/line
  - Multi-figure: one candidate per explicitly named figure/variant;
    multipacks stay one set when the source treats them as one product
    (apply skips pack/set rows — low-and-slow singles)
  - Featured/source image URLs on **new** rows only (no rematch)
  - Comics / Build Publish / Mephitsu crawl: untouched
  - Live urllib may be Cloudflare-challenged: use --posts-json; apply
    exits non-zero with a clear blocker if live fetch fails

See docs/toyark-densify.md.
"""
from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from figure_identity import (  # noqa: E402
    clean_code,
    identity_group_key,
    is_gtin,
    is_listing_code,
    norm_text,
    wave_subtitle_core,
)

ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
SKU_MAP = ROOT / "src/data/figure-sku-map.json"
URLS = ROOT / "src/data/figure-image-urls.json"
ONESHOT_STATS = ROOT / "src/data/figure-archive/oneshot-stats.json"
DEFAULT_REPORT = ROOT / "src/data/figure-archive/toyark-densify-dry-run.json"
DEFAULT_APPLY_REPORT = ROOT / "src/data/figure-archive/toyark-densify-apply.json"
DEFAULT_STATS = ROOT / "src/data/figure-archive/toyark-densify-stats.json"

TOYARK_ORIGIN = "https://www.toyark.com"
REST_POSTS = f"{TOYARK_ORIGIN}/wp-json/wp/v2/posts"
ROBOTS_URL = f"{TOYARK_ORIGIN}/robots.txt"

SOURCE = "toyark-densify"
DEFAULT_CAP = 50  # low-and-slow; babysit noon + 11:30pm MT

UA = (
    "KryptonsToyVault-ToyarkDensify/1.1 "
    "(+https://github.com/MonacoCobra/kryptons-toy-vault; "
    "figure-archive densify bot; polite; never invent GTIN)"
)

# Vault CompanyIds only (src/data/companies.ts / src/lib/types.ts). No sideshow id.
ALLOWLIST = (
    "hasbro",
    "mcfarlane",
    "neca",
    "jazwares",
    "super7",
    "hottoys",
    "mondo",
    "threezero",
    "enterbay",
    "asmus",
    "starace",
    "exo6",
)

# Toyark class_list `companies-*` (and a few body-text aliases) → CompanyId.
COMPANY_CLASS: dict[str, str] = {
    "companies-hasbro": "hasbro",
    "companies-mcfarlane": "mcfarlane",
    "companies-mcfarlane-toys": "mcfarlane",
    "companies-neca": "neca",
    "companies-jazwares": "jazwares",
    "companies-wicked-cool": "jazwares",
    "companies-wicked-cool-toys": "jazwares",
    "companies-super-7": "super7",
    "companies-super7": "super7",
    "companies-hot-toys": "hottoys",
    "companies-hottoys": "hottoys",
    "companies-mondo": "mondo",
    "companies-threezero": "threezero",
    "companies-enterbay": "enterbay",
    "companies-asmus": "asmus",
    "companies-asmus-toys": "asmus",
    "companies-star-ace": "starace",
    "companies-starace": "starace",
    "companies-star-ace-toys": "starace",
    "companies-exo-6": "exo6",
    "companies-exo6": "exo6",
    # Detected so we can reject as not-allowlisted instead of "unknown".
    "companies-kaiyodo": "kaiyodo",
    "companies-tamashii": "shfiguarts",
    "companies-hiya-toys": "hiya",
    "companies-sentinel": "sentinel",
    "companies-mezco": "mezco",
    "companies-boss-fight-studio": "bossfight",
    "companies-storm-collectibles": "storm",
    "companies-queen-studios": "other",
    "companies-burger-king": "other",
    "companies-mattel": "mattel",
    "companies-bandai": "bandai",
    "companies-playmates": "playmates",
    "companies-jakks": "jakks",
    "companies-blitzway": "blitzway",
}

SUBLINE_CLASS: dict[str, str] = {
    "subline-dc-multiverse": "DC Multiverse",
    "subline-page-punchers": "Page Punchers",
    "subline-marvel-legends": "Marvel Legends",
    "subline-reaction-figures": "ReAction",
    "subline-one12-collective": "One:12 Collective",
    "subline-sh-figuarts": "S.H. Figuarts",
    "subline-sh-monsterarts": "S.H. MonsterArts",
    "subline-marvel-dlx": "Marvel DLX",
    "subline-epic-h-a-c-k-s": "Epic H.A.C.K.S.",
    "subline-storm-arena": "Storm Arena",
}

LINE_PATTERNS: list[tuple[re.Pattern[str], str, str | None]] = [
    # (pattern, line, company-hint or None)
    (re.compile(r"\bpage\s*punchers\b", re.I), "Page Punchers", "mcfarlane"),
    (re.compile(r"\bdc\s*multiverse\b.*\bgold\s*label\b|\bgold\s*label\b.*\bdc\s*multiverse\b", re.I), "DC Multiverse Gold Label", "mcfarlane"),
    (re.compile(r"\bdc\s*multiverse\b", re.I), "DC Multiverse", "mcfarlane"),
    (re.compile(r"\bdc\s*super\s*powers\b", re.I), "DC Super Powers", "mcfarlane"),
    (re.compile(r"\bspawn\b", re.I), "Spawn", "mcfarlane"),
    (re.compile(r"\bmarvel\s*legends\b", re.I), "Marvel Legends", "hasbro"),
    (re.compile(r"\b(?:star\s*wars\s+)?(?:the\s+)?black\s*series\b", re.I), "Star Wars Black Series", "hasbro"),
    (re.compile(r"\b(?:g\.?\s*i\.?\s*joe\s+)?classified\b", re.I), "GI Joe Classified", "hasbro"),
    (re.compile(r"\bstudio\s*series\b", re.I), "Transformers Studio Series", "hasbro"),
    (re.compile(r"\blightning\s*collection\b|\bpower\s*rangers?\b", re.I), "Lightning Collection", "hasbro"),
    (re.compile(r"\bindiana\s*jones\b", re.I), "Indiana Jones Adventure Series", "hasbro"),
    (re.compile(r"\btransformers\s+masterpiece\b", re.I), "Transformers Masterpiece", "hasbro"),
    (re.compile(r"\baew\s+unrivaled\b|\bunrivaled\b", re.I), "AEW Unrivaled", "jazwares"),
    (re.compile(r"\bworld\s+of\s+halo\b|\bhalo\b", re.I), "World of Halo", "jazwares"),
    (re.compile(r"\bpok[eé]mon\s+select\b|\bpok[eé]mon\b", re.I), "Pokemon Select", "jazwares"),
    (re.compile(r"\bfortnite\b", re.I), "Fortnite", "jazwares"),
    (re.compile(r"\bhorror\s+ultimate\b", re.I), "Horror Ultimate", "neca"),
    (re.compile(r"\bgodzilla\s+ultimate\b", re.I), "Godzilla Ultimate", "neca"),
    (re.compile(r"\btmnt\s+ultimate\b|teenage\s+mutant\s+ninja\s+turtles\s+ultimate", re.I), "TMNT Ultimate", "neca"),
    (re.compile(r"\baliens?\s+ultimate\b", re.I), "Aliens Ultimate", "neca"),
    (re.compile(r"\bpredator\s+ultimate\b", re.I), "Predator Ultimate", "neca"),
    (re.compile(r"\bneca\s+ultimate\b|\bultimate\s+\d", re.I), "NECA Ultimate", "neca"),
    (re.compile(r"\btoony\s+terrors?\b", re.I), "Toony Terrors", "neca"),
    (re.compile(r"\breaction\+|\breaction\b", re.I), "Super7 ReAction", "super7"),
    (re.compile(r"\bultimates?!?\b", re.I), "Super7 ULTIMATES!", "super7"),
    (re.compile(r"\bdeluxe\b", re.I), "Super7 ULTIMATES!", "super7"),
    (re.compile(r"\bmovie\s+masterpiece|\b\bmms\b", re.I), "Hot Toys MMS", "hottoys"),
    (re.compile(r"\bsixth[\s\-]?scale\b|\b1\s*/\s*6\b", re.I), "Hot Toys", "hottoys"),
    (re.compile(r"\b(?:marvel\s+)?dlx\b", re.I), "threezero DLX", "threezero"),
    (re.compile(r"\bfigzero\b", re.I), "threezero FigZero", "threezero"),
    (re.compile(r"\bmdlx\b", re.I), "threezero MDLX", "threezero"),
    (re.compile(r"\bbtas\b|batman\s+the\s+animated", re.I), "Mondo BTAS", "mondo"),
    (re.compile(r"\bmasters?\s+of\s+the\s+universe\b|\bmotu\b", re.I), "Mondo Masters of the Universe 1/6", "mondo"),
    (re.compile(r"\blord\s+of\s+the\s+rings\b|\blotr\b", re.I), "Asmus Lord of the Rings", "asmus"),
    (re.compile(r"\bhobbit\b", re.I), "Asmus The Hobbit", "asmus"),
    (re.compile(r"\bwitcher\b", re.I), "Asmus The Witcher", "asmus"),
]

NEW_SIGNAL_RE = re.compile(
    r"\b(?:announce[ds]?|announcing|reveal(?:ed|s)?|revealing|unveiled|"
    r"pre[\s\-]?orders?|now\s+available\s+to\s+pre[\s\-]?order|"
    r"official\s+images?|official\s+pics?|first\s+look|new\s+assortment|"
    r"new\s+(?:figure|assortment|wave|items?)|coming\s+soon|preview|"
    r"photos?\s+and\s+details|has\s+announced|will\s+go\s+up\s+for\s+pre|"
    r"wave\s+\d+\s+released|(?:now\s+)?released)\b",
    re.I,
)
REVIEW_ONLY_RE = re.compile(
    r"\b(?:in[\s\-]?hand(?:\s+look|\s+review)?|review(?:ed|s)?|gallery|"
    r"package\s+(?:images?|photos?|look)|photo\s+gallery|unboxing)\b",
    re.I,
)
SPONSOR_RE = re.compile(
    r"\b(?:newsletter|sponsor(?:ed)?|the\s+chosen\s+prime|big\s+bad\s+toy\s+store|"
    r"bbts\s+news|tfsource\s+news|customer\s+appreciation)\b",
    re.I,
)
SALES_RE = re.compile(
    r"\b(?:sale|sales|deals?|clearance|discount|save\s+big|%+\s*off)\b",
    re.I,
)
CUSTOM_RE = re.compile(r"\b(?:customs?|custom\s+figure|fan[\s\-]?custom)\b", re.I)
POTD_RE = re.compile(r"\b(?:photo\s+of\s+the\s+day|potd|daily\s+photo)\b", re.I)
ENTERTAINMENT_RE = re.compile(
    r"\b(?:trailer|casting\s+news|box\s+office|release\s+date\s+moved|"
    r"tv\s+spot|movie\s+review|episode\s+recap)\b",
    re.I,
)
PROP_RE = re.compile(
    r"\b(?:1\s*/\s*1|\b1:1\b)?\s*(?:scale\s+)?(?:cowl|helmet|bust|statue|"
    r"replica|prop|diorama|playset|vehicle\s+only|power\s+loader)\b|"
    r"\b(?:cowl|helmet|power\s+loader)\s+(?:replica|statue|set)?\b",
    re.I,
)
VEHICLE_ONLY_RE = re.compile(
    r"\b(?:starfighter|x[\s\-]?wing|tie\s+fighter|tank|warthog|speeder|"
    r"millennium\s+falcon|starship|playset|diorama)\b",
    re.I,
)
MULTI_PACK_RE = re.compile(
    r"\b(?:vs\.?|2[\s\-]?pack|3[\s\-]?pack|4[\s\-]?pack|two[\s\-]?pack|"
    r"three[\s\-]?pack|multipack|multi[\s\-]?pack|battle\s*pack|"
    r"action\s+figure\s+2[\s\-]?pack|figure\s+set)\b",
    re.I,
)
YEAR_RE = re.compile(
    r"\b(?:due(?:\s+out)?|ships?|shipping|available|release[d]?|street|"
    r"estimated|arriving|in\s+hand)\b[^.]{0,40}?\b(20(?:2[4-9]|3[0-5]))\b|"
    r"\b(20(?:2[4-9]|3[0-5]))\b(?=[^.]{0,20}\b(?:release|street|ship))",
    re.I,
)
WINDOW_RE = re.compile(
    r"\b((?:q[1-4]\s*[\-–—]\s*q[1-4]\s+20\d{2})|"
    r"(?:q[1-4]\s+20\d{2})|"
    r"(?:fall|spring|summer|winter|holiday)\s+20\d{2}|"
    r"(?:january|february|march|april|may|june|july|august|september|"
    r"october|november|december)(?:\s*[\-–—]\s*(?:january|february|march|"
    r"april|may|june|july|august|september|october|november|december))?"
    r"\s+20\d{2}|"
    r"(?:sometime|some\s+time)\s+in\s+20\d{2})\b",
    re.I,
)
# Codes we may capture from prose — never invent, never promote unlabeled digit strings.
LABELED_GTIN_RE = re.compile(
    r"\b(?:upc|ean|gtin|barcode)\s*[:#]?\s*(\d{8}|\d{12,14})\b",
    re.I,
)
LISTING_CODE_RE = re.compile(
    r"\b((?:MMS|HT|DX|QS)\d{3,4}[A-Z]?|"
    r"HAS[A-Z0-9]{4,}|"
    r"(?:HSG|HSF|HSE|HSB)\d{3,}|"
    r"(?:item|product)\s*(?:#|no\.?|code|number)\s*[:\s]*[A-Z0-9\-]{4,})\b",
    re.I,
)
BARE_LISTING_RE = re.compile(r"\b((?:MMS|HT|DX|QS)\d{3,4}[A-Z]?)\b", re.I)

SMALL_WORDS = {"a", "an", "the", "of", "and", "or", "for", "to", "vs", "vs.", "with", "from"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso(raw: str) -> datetime:
    s = (raw or "").strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def html_to_text(raw: str | None) -> str:
    s = raw or ""
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p>", "\n", s)
    s = re.sub(r"(?i)</h[1-6]>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html_lib.unescape(s)
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{2,}", "\n", s)
    return s.strip()


def rendered(field: Any) -> str:
    if isinstance(field, dict):
        return html_lib.unescape(str(field.get("rendered") or ""))
    return html_lib.unescape(str(field or ""))


def class_list(post: dict) -> list[str]:
    raw = post.get("class_list") or []
    return [str(c).lower() for c in raw if isinstance(c, str)]


def title_case_name(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip(" -–—:|"))
    if not s:
        return s
    # Keep mixed-case titles (already prose) as-is after light cleanup.
    letters = re.sub(r"[^A-Za-z]", "", s)
    # Keep mixed-case prose; title-case ALL CAPS or all-lowercase slugs.
    if letters and not letters.isupper() and not letters.islower():
        return s
    parts = s.split()
    out: list[str] = []
    for i, part in enumerate(parts):
        low = part.lower()
        if low in {"marvel's", "marvel’s"}:
            out.append("Marvel's")
            continue
        if i > 0 and low in SMALL_WORDS:
            out.append(low)
            continue
        if "-" in part and not part.startswith("-"):
            out.append("-".join(p[:1].upper() + p[1:].lower() if p else p for p in part.split("-")))
            continue
        out.append(part[:1].upper() + part[1:].lower())
    return " ".join(out)


def slug_to_name(slug: str) -> str:
    return title_case_name(slug.replace("-", " "))


def http_get(
    url: str,
    *,
    timeout: float = 45,
    retries: int = 2,
    retry_sleep: float = 1.5,
) -> tuple[int, bytes, str]:
    """Polite GET with short retries. Cloudflare 403 is retried then returned."""
    last: tuple[int, bytes, str] = (0, b"", "")
    attempts = max(1, retries + 1)
    for attempt in range(attempts):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA,
                "Accept": "application/json, text/plain;q=0.8, */*;q=0.5",
                "Accept-Language": "en-US,en;q=0.8",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                last = (int(resp.status), resp.read(), resp.headers.get("Content-Type") or "")
        except urllib.error.HTTPError as e:
            body = e.read() if e.fp else b""
            ctype = e.headers.get("Content-Type") if e.headers else ""
            last = (int(e.code), body, ctype or "")
        except urllib.error.URLError as e:
            last = (0, str(e.reason if hasattr(e, "reason") else e).encode(), "")
        except TimeoutError as e:
            last = (0, str(e).encode(), "")
        status, body, _ = last
        retryable = status in (0, 429, 502, 503, 504) or looks_like_cloudflare(status, body)
        if retryable and attempt < attempts - 1:
            time.sleep(retry_sleep * (attempt + 1))
            continue
        return last
    return last


def looks_like_cloudflare(status: int, body: bytes) -> bool:
    if status != 403:
        return False
    head = body[:800].decode("utf-8", "ignore").lower()
    return "just a moment" in head or "cf-mitigated" in head or "cloudflare" in head


def check_robots() -> dict[str, Any]:
    """Honor robots.txt. REST `/wp-json/` is allowed; `/feed/` is not."""
    info: dict[str, Any] = {
        "url": ROBOTS_URL,
        "ok": False,
        "wpJsonAllowed": True,
        "feedDisallowed": True,
        "note": "Prefer REST over RSS. /feed/ is disallowed for User-agent: *.",
    }
    status, body, _ = http_get(ROBOTS_URL, timeout=20)
    info["httpStatus"] = status
    if looks_like_cloudflare(status, body):
        info["blocker"] = "cloudflare-challenge"
        info["note"] += " robots.txt fetch challenged; assuming default * rules from last probe."
        return info
    if status != 200:
        info["note"] += f" robots.txt HTTP {status}; assuming /wp-json allowed."
        return info
    text = body.decode("utf-8", "ignore")
    info["ok"] = True
    # Naive * group parse — enough to refuse if /wp-json is newly disallowed.
    star = re.search(r"(?is)user-agent:\s*\*\s*(.*?)(?:\nuser-agent:|\Z)", text)
    block = star.group(1) if star else text
    disallows = [m.group(1).strip() for m in re.finditer(r"(?im)^disallow:\s*(\S+)", block)]
    info["feedDisallowed"] = any(d.rstrip("/") == "/feed" or d.startswith("/feed") for d in disallows)
    if any(d.rstrip("/") in {"/wp-json", "/wp-json/"} or d.startswith("/wp-json/") for d in disallows):
        info["wpJsonAllowed"] = False
    return info


def featured_image(post: dict) -> str | None:
    emb = post.get("_embedded") or {}
    media = emb.get("wp:featuredmedia") or []
    if media and isinstance(media[0], dict):
        url = media[0].get("source_url")
        if isinstance(url, str) and url.startswith("http"):
            return url
        details = (media[0].get("media_details") or {}).get("sizes") or {}
        full = details.get("full") or {}
        if isinstance(full, dict) and str(full.get("source_url") or "").startswith("http"):
            return str(full["source_url"])
    # Last resort: first wp-content image in the body (still source-backed).
    html = rendered(post.get("content"))
    m = re.search(r"https://www\.toyark\.com/wp-content/uploads/[^\"'\s]+", html)
    return m.group(0) if m else None


def map_company(classes: list[str], blob: str) -> tuple[str | None, str]:
    for c in classes:
        if c in COMPANY_CLASS:
            return COMPANY_CLASS[c], f"class:{c}"
    low = blob.lower()
    # Body/title fallback — allowlist makers only, conservative word boundaries.
    pairs = [
        (r"\bmcfarlane(?:\s+toys)?\b", "mcfarlane"),
        (r"\bneca\b", "neca"),
        (r"\bjazwares\b|\bwicked\s+cool\s+toys\b", "jazwares"),
        (r"\bhasbro(?:\s+pulse)?\b", "hasbro"),
        (r"\bhot\s+toys\b", "hottoys"),
        (r"\bsuper\s*7\b", "super7"),
        (r"\bthreezero\b|\b3a\b", "threezero"),
        (r"\bmondo\b", "mondo"),
        (r"\benterbay\b", "enterbay"),
        (r"\basmus(?:\s+toys)?\b", "asmus"),
        (r"\bstar\s*ace\b", "starace"),
        (r"\bexo[\s\-]?6\b", "exo6"),
    ]
    hits = [(name, pat) for pat, name in pairs if re.search(pat, low)]
    if len(hits) == 1:
        return hits[0][0], "body-text"
    return None, "none"


def infer_line(
    company: str | None, classes: list[str], blob: str, *, allow_default: bool = True
) -> str | None:
    # Prefer Toyark subline class when it matches the company.
    sublines = [SUBLINE_CLASS[c] for c in classes if c in SUBLINE_CLASS]
    if company == "mcfarlane":
        if re.search(r"\bgold\s*label\b", blob, re.I) and (
            "DC Multiverse" in sublines or re.search(r"\bdc\s*multiverse\b", blob, re.I)
        ):
            return "DC Multiverse Gold Label"
        for preferred in ("Page Punchers", "DC Multiverse", "DC Super Powers"):
            if preferred in sublines:
                return preferred
        if "DC Super Powers" not in sublines and re.search(r"\bdc\s*super\s*powers\b", blob, re.I):
            return "DC Super Powers"
    if company == "hasbro" and "Marvel Legends" in sublines:
        return "Marvel Legends"
    if company == "neca" and re.search(r"\bultimate\b", blob, re.I):
        if re.search(r"\b(elvira|horror|mistress of the dark|universal)\b", blob, re.I):
            return "Horror Ultimate"
        return "NECA Ultimate"
    if company == "super7":
        if "ReAction" in sublines or re.search(r"\breaction\b", blob, re.I):
            return "Super7 ReAction"
        if "Super7 ULTIMATES!" in sublines or re.search(r"\bultimates?\b|\bdeluxe\b", blob, re.I):
            return "Super7 ULTIMATES!"
    if company == "threezero" and "Marvel DLX" in sublines:
        return "threezero DLX"
    if company == "hottoys" and re.search(r"\bmms\d+", blob, re.I):
        return "Hot Toys MMS"
    for pat, line, hint in LINE_PATTERNS:
        if hint and company and hint != company:
            continue
        if pat.search(blob):
            return line
    if company == "super7" and sublines:
        if sublines[0] == "ReAction":
            return "Super7 ReAction"
    if sublines:
        return sublines[0]
    if not allow_default:
        return None
    return {
        "hottoys": "Hot Toys",
        "mondo": "Mondo",
        "threezero": "threezero",
        "enterbay": "Enterbay",
        "super7": "Super7 ULTIMATES!",
        "starace": "Star Ace",
        "exo6": "EXO-6",
    }.get(company or "")


def content_reject_reason(classes: list[str], title: str, blob: str) -> tuple[str, str] | None:
    joined = " ".join(classes)
    if "category-sales-deals-and-sponsor-updates" in classes or (
        SPONSOR_RE.search(title) and (SPONSOR_RE.search(blob) or "newsletter" in title.lower())
    ):
        return "sponsor-newsletter", "Sponsor newsletter / retailer roundup — not a single-figure identity."
    if "category-sales-deals-and-sponsor-updates" in joined or (
        SALES_RE.search(title) and SPONSOR_RE.search(blob + " " + title)
    ):
        return "sales-deals", "Sales / deals / sponsor update, not a new-figure reveal."
    if POTD_RE.search(title) or POTD_RE.search(blob[:400]):
        return "photo-of-the-day", "Photo-of-the-day / daily photo post."
    if CUSTOM_RE.search(title) or re.search(r"\bcustom\s+figure\b", blob, re.I):
        return "customs", "Customs / fan-custom coverage."
    # Review/in-hand only when there is no new-product signal.
    if REVIEW_ONLY_RE.search(title) and not NEW_SIGNAL_RE.search(title + " " + blob[:500]):
        return "review-in-hand", "In-hand / review / gallery with no new product identity."
    if REVIEW_ONLY_RE.search(blob[:400]) and not NEW_SIGNAL_RE.search(title + " " + blob[:800]):
        return "review-in-hand", "In-hand / review / gallery with no new product identity."
    if ENTERTAINMENT_RE.search(title) and not NEW_SIGNAL_RE.search(title):
        return "entertainment-news", "Entertainment news without a new figure identity."
    # Whole-post vehicle/prop only when the title is a single item (not a list / combo).
    listed = ("," in title and re.search(r"\band\b", title, re.I)) or (
        bool(re.search(r"\band\b", title, re.I)) and bool(re.search(r"\b(?:figure|set|ripley)\b", title, re.I))
    )
    if not listed:
        if PROP_RE.search(title) and not re.search(r"\bfigure\b", title, re.I):
            return "vehicles-props-only", "Title is a prop/vehicle/replica, not a figure."
        if VEHICLE_ONLY_RE.search(title) and not re.search(r"\bfigure\b", title, re.I):
            return "vehicles-props-only", "Title is vehicle/playset-only."
    return None


def split_name_variant(raw: str) -> tuple[str, str]:
    s = re.sub(r"\s+", " ", (raw or "").strip())
    s = re.sub(r"\b(?:action\s+)?figures?\b", "", s, flags=re.I)
    s = re.sub(r"\bpre[\s\-]?orders?\b", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" -–—:,")
    m = re.search(r"^(.*?)[\s]*[\(（](.+?)[\)）]\s*$", s)
    if m:
        return title_case_name(m.group(1)), title_case_name(m.group(2))
    return title_case_name(s), ""


def parse_heading_figure(heading: str, default_line: str | None) -> dict[str, str] | None:
    h = html_to_text(heading)
    h = re.sub(r"\s+", " ", h).strip()
    if len(h) < 4 or len(h) > 140:
        return None
    line = default_line
    rest = h
    m = re.match(r"^(?:hasbro\s+)?marvel\s+legends(?:\s+series)?\s+(?:retro\s+cardback\s+)?(.+)$", h, re.I)
    if m:
        line = "Marvel Legends"
        rest = m.group(1)
        variant_extra = "Retro Cardback" if re.search(r"retro\s+cardback", h, re.I) else ""
        # "AUNT MAY, SPIDER-MAN: THE ANIMATED SERIES" / "MARVEL'S SMYTHE, …"
        if "," in rest:
            name_part, _, tail = rest.partition(",")
            name, var = split_name_variant(name_part)
            var2 = title_case_name(tail) if tail.strip() else ""
            variant = " / ".join(x for x in (variant_extra, var, var2) if x)
            return {"name": name, "line": line, "variant": variant}
        name, var = split_name_variant(rest)
        variant = " / ".join(x for x in (variant_extra, var) if x)
        return {"name": name, "line": line, "variant": variant}
    if re.search(r"\bfigure\b", h, re.I) and len(h.split()) <= 12:
        name, var = split_name_variant(re.sub(r"\b(?:action\s+)?figure\b", "", h, flags=re.I))
        if name:
            return {"name": name, "line": line or "", "variant": var}
    return None


def extract_heading_figures(html: str, default_line: str | None) -> list[dict[str, str]]:
    blocks = re.findall(
        r"<(?:strong|h[1-6]|b)[^>]*>(.*?)</(?:strong|h[1-6]|b)>",
        html or "",
        flags=re.I | re.S,
    )
    # WebFetch / some proxies strip opening tags but leave "HEADING</strong>".
    blocks += re.findall(
        r"(MARVEL\s+LEGENDS[^\n<]{3,120})</(?:strong|b|h[1-6])>",
        html or "",
        flags=re.I,
    )
    # Plain-text ALL CAPS lines (tag-stripped bodies).
    for line in re.split(r"[\n\r]+", html or ""):
        t = html_to_text(line)
        if re.match(r"^marvel\s+legends(?:\s+series|\s+retro\s+cardback)\b", t, re.I):
            blocks.append(t)
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in blocks:
        parsed = parse_heading_figure(raw, default_line)
        if not parsed or not parsed.get("name"):
            continue
        key = norm_text(f"{parsed['name']}|{parsed.get('variant') or ''}")
        if key in seen:
            continue
        seen.add(key)
        out.append(parsed)
    return out


def wave_variant_from_title(title: str, body: str) -> str | None:
    blob = f"{title} {body[:400]}"
    if re.search(r"\bdc\s*classic\b", blob, re.I):
        return "DC Classic"
    if re.search(r"\bfinal\s+wave\b", title, re.I):
        return "Final Wave"
    if re.search(r"\bgamerverse\b", blob, re.I):
        return "Gamerverse"
    mwave = re.search(r"\b(?:deluxe\s+)?wave\s+(\d+[a-z]?)\b", title, re.I)
    if mwave:
        label = f"Wave {mwave.group(1)}"
        if re.search(r"\bdeluxe\b", title, re.I):
            return f"Deluxe {label}"
        return label
    if re.search(r"\breaction\+", blob, re.I):
        return "ReAction+"
    if re.search(r"\barctic\s+suit\b", blob, re.I):
        return "Arctic Suit"
    if re.search(r"\bfinal\s+swing\s+suit\b", blob, re.I):
        return "Final Swing Suit Deluxe"
    return None


def attach_based_on_variants(specs: list[dict[str, str]], body: str) -> list[dict[str, str]]:
    for spec in specs:
        name = spec.get("name") or ""
        if not name or spec.get("variant"):
            continue
        m = re.search(
            rf"{re.escape(name)}\s+based\s+on\s+([^.,;]+)",
            body,
            flags=re.I,
        )
        if m:
            spec["variant"] = title_case_name(m.group(1).strip())
    return specs


def promote_wave_variant(specs: list[dict[str, str]], wave: str | None) -> list[dict[str, str]]:
    if not wave:
        return specs
    for spec in specs:
        cur = spec.get("variant") or ""
        if wave.lower() in cur.lower():
            continue
        spec["variant"] = " / ".join(x for x in (cur, wave) if x)
    return specs


def is_teaser_title(title: str) -> bool:
    return bool(re.search(r"\b(?:preview|teaser|silhouette)s?\b", title, re.I)) and not re.search(
        r"\b(?:pre[\s\-]?order|announced|revealed|official\s+images?)\b",
        title,
        re.I,
    )


def look_like_character_list(title: str) -> list[str]:
    """Split 'Foo, Bar, and Baz' lists after an em-dash / hyphen title cue."""
    t = title.strip()
    t = re.sub(r"\s+", " ", t)
    for sep in (" – ", " — ", " - "):
        if sep in t:
            t = t.split(sep, 1)[1]
            break
    t = re.sub(r"\bpre[\s\-]?orders?\b", "", t, flags=re.I)
    t = re.sub(r"\b(?:preview|revealed|announced)\b", "", t, flags=re.I)
    t = re.sub(
        r"\s+\b(?:reaction\+?|ultimates?!?|deluxe(?:\s+version)?|(?:action\s+)?figures?)\s*$",
        "",
        t,
        flags=re.I,
    )
    t = t.strip(" -–—:,")
    has_and = bool(re.search(r"\band\b", t, re.I))
    if not re.search(r",\s+", t):
        return []
    if not has_and and len(re.findall(r",", t)) < 2:
        return []
    t = re.sub(r",?\s+and\s+", ", ", t, flags=re.I)
    parts = [p.strip(" .") for p in t.split(",") if p.strip(" .")]
    return [p for p in parts if 2 <= len(p) <= 80]


def character_aliases(char_names: list[str]) -> list[str]:
    extra: list[str] = []
    for n in char_names:
        extra.append(n)
        extra.append(n.replace(" ", "-"))
        extra.append(n.replace("-", " "))
        if n.endswith(" 2"):
            extra.append(n[:-2].strip())
        if n.lower().startswith("dr "):
            extra.append("Dr. " + n[3:])
            extra.append(n[3:])
    # unique, longest first
    return sorted({e for e in extra if e}, key=len, reverse=True)


def peel_known_character(text: str, char_names: list[str]) -> tuple[str, str] | None:
    """If prose ends with / contains a known character, use that as the name."""
    if not text or not char_names:
        return None
    ordered = character_aliases(char_names)
    for ch in ordered:
        pat = re.compile(rf"^(.*?)({re.escape(ch)})(.*)$", re.I)
        m = pat.search(text)
        if not m:
            continue
        pre, hit, post = m.group(1).strip(" -–—,:"), m.group(2), m.group(3).strip(" -–—,:")
        flavor = " ".join(x for x in (pre, post) if x)
        flavor = re.sub(
            r"\b(?:dc\s+classic|gold\s+label|collector\s+edition|series|based\s+on|"
            r"hasbro|mcfarlane(?:\s+toys)?|neca|jazwares|super\s*7|hot\s+toys|"
            r"threezero|mondo|enterbay|asmus(?:\s+toys)?|star\s*ace|exo[\s\-]?6|"
            r"ultimate|action\s+figure|figure|figures|pre[\s\-]?orders?|"
            r"deluxe\s+version)\b",
            " ",
            flavor,
            flags=re.I,
        )
        flavor = re.sub(re.escape(ch), " ", flavor, flags=re.I)
        flavor = re.sub(r"\s+", " ", flavor).strip(" -–—,:")
        return title_case_name(hit), title_case_name(flavor)
    return None


def item_line_and_name(
    item: str,
    fallback_line: str | None,
    company: str | None,
    char_names: list[str] | None = None,
) -> dict[str, str]:
    blob = item
    line = infer_line(company, [], blob, allow_default=False) or fallback_line or ""
    name = item
    # Strip known line prefixes from the leftover name.
    for prefix in (
        "DC Multiverse Gold Label",
        "DC Multiverse",
        "Page Punchers",
        "DC Super Powers",
        "Marvel Legends Series",
        "Marvel Legends",
        "NECA Ultimate",
        "Ultimate",
        "DC Classic",
    ):
        name = re.sub(rf"^{re.escape(prefix)}\s+", "", name, flags=re.I)
    name = re.sub(r"\b(?:series|edition)\b", "", name, flags=re.I)
    peeled = peel_known_character(name, char_names or [])
    if peeled:
        name, peeled_var = peeled
        var = peeled_var
    else:
        name, var = split_name_variant(name)
    extra = []
    if re.search(r"gold\s*label", item, re.I) and "gold label" not in (var or "").lower():
        extra.append("Gold Label")
    if re.search(r"arkham\s*city", item, re.I) and "arkham" not in (name + " " + var).lower():
        extra.append("Arkham City")
    if re.search(r"dc\s*classic", item, re.I) and "classic" not in (var or "").lower():
        extra.append("DC Classic")
    if re.search(r"collector edition", item, re.I):
        extra.append("Collector Edition")
    variant = " / ".join(x for x in (var, *extra) if x)
    return {"name": name, "line": line, "variant": variant, "raw": item}


def is_prop_item(name: str, variant: str, raw: str) -> bool:
    # Judge the product name, not accessory flavor on an otherwise named figure.
    blob = f"{name} {raw}"
    if PROP_RE.search(name) and not re.search(r"\bfigure\b", name, re.I):
        return True
    if PROP_RE.search(blob) and not re.search(r"\bfigure\b", blob, re.I):
        return True
    if re.search(r"\bcowl\b|\bbust\b|\bstatue\b|\b1\s*/\s*1\b|\b1:1\b", name, re.I):
        return True
    return False


def extract_year_and_window(blob: str) -> tuple[int | None, str | None]:
    window = None
    mwin = WINDOW_RE.search(blob)
    if mwin:
        window = re.sub(r"\s+", " ", mwin.group(1)).strip()
        if window.isdigit() and not re.search(
            r"(?:due|ship|available|release|fall|spring|summer|winter|q[1-4]|sometime)",
            blob[max(0, mwin.start() - 40) : mwin.end() + 10],
            re.I,
        ):
            # Bare year with no release cue — do not invent a window.
            window = None
    year = None
    my = YEAR_RE.search(blob)
    if my:
        for g in my.groups():
            if g and g.isdigit():
                year = int(g)
                break
    if year is None and window:
        ym = re.search(r"(20\d{2})", window)
        if ym:
            year = int(ym.group(1))
    if year is not None and (year < 2020 or year > 2036):
        year = None
    return year, window


def extract_codes(blob: str) -> tuple[str | None, list[str]]:
    """Return (gtin_or_none, alias codes). Never invent."""
    gtin = None
    aliases: list[str] = []
    seen: set[str] = set()
    for m in LABELED_GTIN_RE.finditer(blob):
        raw = clean_code(m.group(1))
        if raw and is_gtin(raw) and raw not in seen:
            seen.add(raw)
            if gtin is None:
                gtin = raw
            else:
                aliases.append(raw)
    for m in LISTING_CODE_RE.finditer(blob):
        token = m.group(1)
        token = re.sub(
            r"^(?:item|product)\s*(?:#|no\.?|code|number)\s*[:\s]*",
            "",
            token,
            flags=re.I,
        )
        token = clean_code(token)
        if not token:
            continue
        if is_gtin(token):
            if gtin is None:
                gtin = token
            elif token != gtin and token not in seen:
                aliases.append(token)
            seen.add(token)
            continue
        if token.upper() in seen:
            continue
        if is_listing_code(token) or BARE_LISTING_RE.match(token):
            aliases.append(token)
            seen.add(token.upper())
    return gtin, aliases


def characters_from_classes(classes: list[str]) -> list[str]:
    names: list[str] = []
    for c in classes:
        if c.startswith("characters-"):
            names.append(slug_to_name(c[len("characters-") :]))
    return names


def extract_figure_specs(post: dict, company: str | None, line: str | None) -> list[dict[str, str]]:
    title = html_to_text(rendered(post.get("title")))
    html = rendered(post.get("content"))
    excerpt = html_to_text(rendered(post.get("excerpt")))
    body = html_to_text(html)
    classes = class_list(post)

    wave = wave_variant_from_title(title, body)
    headings = extract_heading_figures(html, line)
    if len(headings) >= 2:
        if re.search(r"comic\s+covers?", title, re.I):
            for h in headings:
                v = (h.get("variant") or "").lower()
                if "retro" in v or "holiday" in v or "comic" in v:
                    continue
                h["variant"] = " / ".join(x for x in (h.get("variant"), "Comic Cover") if x)
        return attach_based_on_variants(promote_wave_variant(headings, wave), body)

    # Source-treated multipack / 2-pack → one product.
    if MULTI_PACK_RE.search(title):
        name, var = split_name_variant(title)
        name = re.sub(r"^(?:hasbro|mcfarlane(?:\s+toys)?|neca|jazwares)\s+", "", name, flags=re.I)
        name = re.sub(r"^(?:marvel\s+legends|dc\s+multiverse)\s+[–—-]\s+", "", name, flags=re.I)
        if wave and wave.lower() not in var.lower():
            var = " / ".join(x for x in (var, wave) if x)
        return [{"name": name or title, "line": line or "", "variant": var, "pack": "set"}]

    chars = characters_from_classes(classes)
    listed = look_like_character_list(title)
    if listed:
        specs = [item_line_and_name(item, line, company, chars) for item in listed]
        if len(specs) >= 2:
            return attach_based_on_variants(promote_wave_variant(specs, wave), body)

    # Body "features X, Y, and Z" on a single line/wave.
    feat = re.search(
        r"\b(?:features|includes|featuring|included\s+are)\s+([A-Z][^.]{8,180}?)(?:\.|$)",
        body or excerpt,
    )
    if feat and re.search(r",\s+", feat.group(1)) and re.search(r"\band\b", feat.group(1), re.I):
        chunk = re.sub(r",?\s+and\s+", ", ", feat.group(1), flags=re.I)
        parts = [p.strip() for p in chunk.split(",") if 2 <= len(p.strip()) <= 70]
        if 2 <= len(parts) <= 8:
            specs = [item_line_and_name(p, line, company, chars) for p in parts]
            return attach_based_on_variants(promote_wave_variant(specs, wave), body)

    if len(chars) >= 2 and line:
        prop_chars = [n for n in chars if is_prop_item(n, "", n)]
        fig_chars = [n for n in chars if n not in prop_chars]
        if fig_chars and prop_chars:
            specs = [
                {"name": n, "line": line, "variant": wave or " ".join(prop_chars)}
                for n in fig_chars
            ]
            return attach_based_on_variants(promote_wave_variant(specs, wave), body)
        if re.search(r"\b(?:wave|assortment|previews?|includes|revealed)\b", title, re.I) or listed:
            specs = [{"name": n, "line": line, "variant": ""} for n in chars]
            return attach_based_on_variants(promote_wave_variant(specs, wave), body)

    if is_teaser_title(title) and len(chars) < 2 and not listed:
        return []

    # Single figure: prefer a character tag when it appears in the title.
    name, var = split_name_variant(title)
    name = re.sub(
        r"^(?:hasbro|mcfarlane(?:\s+toys)?|neca|jazwares)\s+",
        "",
        name,
        flags=re.I,
    )
    name = re.sub(
        r"^(?:marvel\s+legends|dc\s+multiverse|dc\s+super\s+powers|neca\s+ultimate)\s+[–—-]\s+",
        "",
        name,
        flags=re.I,
    )
    if chars:
        peeled = peel_known_character(title, chars)
        if peeled:
            name, extra = peeled
            if extra and extra.lower() not in (var or "").lower():
                var = " / ".join(x for x in (var, extra) if x)
    if chars and (not name or name.lower() in {"figure", "preview", "pre-orders"}):
        name = chars[0]
    if wave and wave.lower() not in (var or "").lower():
        var = " / ".join(x for x in (var, wave) if x)
    return attach_based_on_variants(
        [{"name": name or (chars[0] if chars else title), "line": line or "", "variant": var}],
        body,
    )


class OneshotIndex:
    def __init__(self, rows: list[dict[str, Any]], companies: set[str]) -> None:
        self.by_identity: dict[tuple[str, str, str, str], list[str]] = {}
        self.by_core: dict[tuple[str, str, str, str], list[str]] = {}
        self.by_name_line: dict[tuple[str, str, str], list[str]] = {}
        n = 0
        for r in rows:
            company = str(r.get("company") or "").lower()
            if company not in companies:
                continue
            n += 1
            ik = identity_group_key(r)
            self.by_identity.setdefault(ik, []).append(r["id"])
            year = str(r.get("releaseDate") or "")[:4]
            core = (
                company,
                norm_text(str(r.get("name") or "")),
                norm_text(str(r.get("line") or "")),
                year,
            )
            self.by_core.setdefault(core, []).append(r["id"])
            nl = (company, norm_text(str(r.get("name") or "")), norm_text(str(r.get("line") or "")))
            self.by_name_line.setdefault(nl, []).append(r["id"])
        self.row_count = n

    def add(self, row: dict[str, Any]) -> None:
        """Register a newly applied row so the same run cannot double-insert."""
        company = str(row.get("company") or "").lower()
        ik = identity_group_key(row)
        self.by_identity.setdefault(ik, []).append(row["id"])
        year = str(row.get("releaseDate") or "")[:4]
        core = (
            company,
            norm_text(str(row.get("name") or "")),
            norm_text(str(row.get("line") or "")),
            year,
        )
        self.by_core.setdefault(core, []).append(row["id"])
        nl = (company, norm_text(str(row.get("name") or "")), norm_text(str(row.get("line") or "")))
        self.by_name_line.setdefault(nl, []).append(row["id"])
        self.row_count += 1

    def match(
        self, company: str, name: str, line: str, year: int | None, variant: str
    ) -> tuple[str | None, list[str]]:
        row = {
            "company": company,
            "name": name,
            "line": line,
            "subtitle": variant or "",
        }
        ids = self.by_identity.get(identity_group_key(row)) or []
        if ids:
            return "already-in-oneshot", ids[:8]
        if year:
            core = (company, norm_text(name), norm_text(line), str(year))
            ids = self.by_core.get(core) or []
            if ids:
                # Distinct variant (after wave-subtitle normalize) is a new figure.
                if variant and wave_subtitle_core(variant):
                    return None, []
                return "possible-reissue", ids[:8]
        if not variant:
            ids = self.by_name_line.get((company, norm_text(name), norm_text(line))) or []
            if ids:
                return "possible-reissue", ids[:8]
        return None, []


def fetch_posts(
    *,
    after: datetime,
    before: datetime | None,
    per_page: int,
    max_pages: int,
    sleep_s: float,
) -> dict[str, Any]:
    posts: list[dict[str, Any]] = []
    pages = 0
    blocker = None
    last_status = None
    notes: list[str] = []
    per_page = max(1, min(per_page, 100))
    max_pages = max(1, min(max_pages, 20))

    for page in range(1, max_pages + 1):
        q: dict[str, Any] = {
            "per_page": str(per_page),
            "page": str(page),
            "_embed": "1",
            "after": after.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "orderby": "date",
            "order": "desc",
        }
        if before:
            q["before"] = before.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        url = REST_POSTS + "?" + urllib.parse.urlencode(q)
        if page > 1:
            time.sleep(sleep_s)
        status, body, ctype = http_get(url)
        last_status = status
        if looks_like_cloudflare(status, body):
            blocker = "cloudflare-challenge"
            notes.append(f"page {page}: Cloudflare challenge (HTTP {status})")
            break
        if status == 400:
            notes.append(f"page {page}: HTTP 400 (likely past last page)")
            break
        if status != 200:
            notes.append(f"page {page}: HTTP {status}")
            if status >= 400:
                break
        if "json" not in (ctype or "").lower() and not body.lstrip().startswith(b"["):
            notes.append(f"page {page}: non-JSON response ({ctype})")
            blocker = blocker or "non-json-response"
            break
        try:
            chunk = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            notes.append(f"page {page}: JSON decode failed")
            break
        if not isinstance(chunk, list):
            notes.append(f"page {page}: unexpected payload type {type(chunk).__name__}")
            break
        pages += 1
        posts.extend([p for p in chunk if isinstance(p, dict)])
        if len(chunk) < per_page:
            break

    return {
        "posts": posts,
        "pagesFetched": pages,
        "httpStatus": last_status,
        "blocker": blocker,
        "notes": notes,
        "ok": blocker is None and last_status == 200 or (pages > 0 and blocker is None),
    }


def load_replay(path: Path) -> list[dict[str, Any]]:
    doc = json.loads(path.read_text())
    if isinstance(doc, list):
        return [p for p in doc if isinstance(p, dict)]
    if isinstance(doc, dict):
        for key in ("posts", "items", "data"):
            if isinstance(doc.get(key), list):
                return [p for p in doc[key] if isinstance(p, dict)]
    raise ValueError(f"{path} is not a WP REST posts array or {{posts: [...]}} object")


def post_datetime(post: dict) -> datetime | None:
    raw = post.get("date_gmt") or post.get("date")
    if not raw:
        return None
    try:
        return parse_iso(str(raw))
    except ValueError:
        return None


def in_window(post: dict, after: datetime, before: datetime | None) -> bool:
    dt = post_datetime(post)
    if dt is None:
        return True
    if dt < after:
        return False
    if before and dt > before:
        return False
    return True


def evaluate_post(
    post: dict,
    *,
    allow: set[str],
    index: OneshotIndex,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepts: list[dict[str, Any]] = []
    rejects: list[dict[str, Any]] = []
    title = html_to_text(rendered(post.get("title")))
    excerpt = html_to_text(rendered(post.get("excerpt")))
    html = rendered(post.get("content"))
    body = html_to_text(html)
    blob = " ".join(x for x in (title, excerpt, body) if x)
    classes = class_list(post)
    source = post.get("link") or ""
    pid = post.get("id")
    image = featured_image(post)
    dt = post_datetime(post)
    post_year = dt.year if dt else None

    cr = content_reject_reason(classes, title, blob)
    if cr:
        reason, rationale = cr
        rejects.append(
            {
                "decision": "reject",
                "reason": reason,
                "name": None,
                "company": None,
                "line": None,
                "year": None,
                "releaseWindow": None,
                "variant": None,
                "sourceUrl": source,
                "imageUrl": None,
                "aliases": [],
                "codes": [],
                "gtin": None,
                "toyarkPostId": pid,
                "title": title,
                "rationale": rationale,
            }
        )
        return accepts, rejects

    company, company_how = map_company(classes, f"{title} {excerpt}")
    if company is None:
        rejects.append(
            {
                "decision": "reject",
                "reason": "company-unknown",
                "name": None,
                "company": None,
                "line": None,
                "year": None,
                "releaseWindow": None,
                "variant": None,
                "sourceUrl": source,
                "imageUrl": None,
                "aliases": [],
                "codes": [],
                "gtin": None,
                "toyarkPostId": pid,
                "title": title,
                "rationale": "No allowlisted companies-* class or unique body-text company.",
            }
        )
        return accepts, rejects

    if company not in allow:
        rejects.append(
            {
                "decision": "reject",
                "reason": "company-not-allowlisted",
                "name": None,
                "company": company,
                "line": None,
                "year": None,
                "releaseWindow": None,
                "variant": None,
                "sourceUrl": source,
                "imageUrl": None,
                "aliases": [],
                "codes": [],
                "gtin": None,
                "toyarkPostId": pid,
                "title": title,
                "rationale": f"Recognized {company} via {company_how}; allowlist is {', '.join(ALLOWLIST)}.",
            }
        )
        return accepts, rejects

    if not NEW_SIGNAL_RE.search(title + " " + excerpt + " " + body[:900]):
        rejects.append(
            {
                "decision": "reject",
                "reason": "no-new-product-identity",
                "name": None,
                "company": company,
                "line": None,
                "year": None,
                "releaseWindow": None,
                "variant": None,
                "sourceUrl": source,
                "imageUrl": None,
                "aliases": [],
                "codes": [],
                "gtin": None,
                "toyarkPostId": pid,
                "title": title,
                "rationale": "Allowlisted company but no new/reveal/pre-order/official-image signal.",
            }
        )
        return accepts, rejects

    line = infer_line(company, classes, blob)
    year, window = extract_year_and_window(blob)
    gtin, codes = extract_codes(blob)
    specs = extract_figure_specs(post, company, line)

    if not specs:
        rejects.append(
            {
                "decision": "reject",
                "reason": "no-explicit-figure",
                "name": None,
                "company": company,
                "line": line,
                "year": year,
                "releaseWindow": window,
                "variant": None,
                "sourceUrl": source,
                "imageUrl": image,
                "aliases": codes,
                "codes": codes,
                "gtin": gtin,
                "toyarkPostId": pid,
                "title": title,
                "rationale": "Company/signal present but no explicitly named figure/variant.",
            }
        )
        return accepts, rejects

    for spec in specs:
        name = (spec.get("name") or "").strip()
        spec_line = (spec.get("line") or line or "").strip()
        variant = (spec.get("variant") or "").strip()
        raw = spec.get("raw") or name
        if not name:
            rejects.append(
                {
                    "decision": "reject",
                    "reason": "no-explicit-figure",
                    "name": None,
                    "company": company,
                    "line": spec_line or None,
                    "year": year,
                    "releaseWindow": window,
                    "variant": variant or None,
                    "sourceUrl": source,
                    "imageUrl": image,
                    "aliases": codes,
                    "codes": codes,
                    "gtin": gtin,
                    "toyarkPostId": pid,
                    "title": title,
                    "rationale": "Could not extract a figure name.",
                }
            )
            continue
        if is_prop_item(name, variant, raw):
            rejects.append(
                {
                    "decision": "reject",
                    "reason": "vehicles-props-only",
                    "name": name,
                    "company": company,
                    "line": spec_line or None,
                    "year": year,
                    "releaseWindow": window,
                    "variant": variant or None,
                    "sourceUrl": source,
                    "imageUrl": image,
                    "aliases": codes,
                    "codes": codes,
                    "gtin": gtin,
                    "toyarkPostId": pid,
                    "title": title,
                    "rationale": f"{name} reads as a cowl/prop/vehicle, not an articulated figure.",
                }
            )
            continue
        if not spec_line:
            rejects.append(
                {
                    "decision": "reject",
                    "reason": "missing-line",
                    "name": name,
                    "company": company,
                    "line": None,
                    "year": year,
                    "releaseWindow": window,
                    "variant": variant or None,
                    "sourceUrl": source,
                    "imageUrl": image,
                    "aliases": codes,
                    "codes": codes,
                    "gtin": gtin,
                    "toyarkPostId": pid,
                    "title": title,
                    "rationale": "Recognizable company but no line/subline in class_list or prose.",
                }
            )
            continue

        dupe_reason, hit_ids = index.match(company, name, spec_line, year, variant)
        rationale_bits = [
            f"{company} via {company_how}",
            f"line={spec_line}",
        ]
        if variant:
            rationale_bits.append(f"variant={variant}")
        if year:
            rationale_bits.append(f"year={year}")
        elif window:
            rationale_bits.append(f"window={window}")
        else:
            rationale_bits.append("no street year in prose (not invented)")
        if spec.get("pack") == "set":
            rationale_bits.append("source-treated multipack kept as one set")
        if gtin:
            rationale_bits.append(f"gtin-from-source={gtin}")
        if codes:
            rationale_bits.append("aliases-from-source=" + ",".join(codes[:6]))
        rationale_bits.append("new/reveal/pre-order/official-image signal")

        if dupe_reason:
            rejects.append(
                {
                    "decision": "reject",
                    "reason": dupe_reason,
                    "name": name,
                    "company": company,
                    "line": spec_line,
                    "year": year,
                    "releaseWindow": window,
                    "variant": variant or None,
                    "sourceUrl": source,
                    "imageUrl": image,
                    "aliases": codes,
                    "codes": codes,
                    "gtin": gtin,
                    "toyarkPostId": pid,
                    "title": title,
                    "oneshotIds": hit_ids,
                    "rationale": (
                        "Identity key already in oneshot"
                        if dupe_reason == "already-in-oneshot"
                        else "Same company+line+name(+year) exists; variant not distinct enough"
                    )
                    + f" ({', '.join(hit_ids[:4])}).",
                }
            )
            continue

        accepts.append(
            {
                "decision": "accept",
                "name": name,
                "company": company,
                "line": spec_line,
                "year": year,
                "releaseWindow": window,
                "variant": variant or None,
                "sourceUrl": source,
                "imageUrl": image,
                "aliases": codes,
                "codes": codes,
                "gtin": gtin,
                "toyarkPostId": pid,
                "postYear": post_year,
                "pack": spec.get("pack") or None,
                "title": title,
                "rationale": "; ".join(rationale_bits),
            }
        )
    return accepts, rejects


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def ensure_alias_doc(doc: dict) -> dict:
    doc.setdefault("version", 1)
    doc.setdefault("policy", "gtin-canonical")
    doc.setdefault("aliasesByFigureId", {})
    doc.setdefault("aliasToFigureId", {})
    doc.setdefault("collapsed", [])
    doc.setdefault("flagged", [])
    return doc


def add_aliases(doc: dict, figure_id: str, codes: list[str]) -> int:
    """Attach listing codes / short source keys. Never invent. Do not steal."""
    doc = ensure_alias_doc(doc)
    by = doc["aliasesByFigureId"]
    to = doc["aliasToFigureId"]
    cur = list(by.get(figure_id) or [])
    added = 0
    for c in codes:
        raw = str(c or "").strip()
        if not raw:
            continue
        if raw.startswith("http://") or raw.startswith("https://"):
            # Toyark permalinks exceed clean_code's 64-char cap; keep source URL.
            c2 = raw[:240]
        else:
            c2 = clean_code(raw) or raw.strip()
        if not c2:
            continue
        owner = to.get(c2)
        if owner and owner != figure_id:
            continue
        if c2 not in cur:
            cur.append(c2)
            added += 1
        to[c2] = figure_id
    if cur:
        by[figure_id] = cur
    return added


def stable_id(
    post_id: Any,
    name: str,
    company: str,
    line: str,
    variant: str | None,
    existing_ids: set[str],
) -> str:
    """ta-<sha1[:12] of postId+name+company+line[+variant]>; lengthen on clash."""
    raw = "|".join(
        [
            str(post_id or ""),
            (name or "").strip(),
            (company or "").strip().lower(),
            (line or "").strip(),
            (variant or "").strip(),
        ]
    )
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    for n in (12, 16, 20, 40):
        rid = f"ta-{digest[:n]}"
        if rid not in existing_ids:
            return rid
    return f"ta-{digest}-x"


def defaults_for_company_line(company: str, line: str) -> tuple[float, str, float]:
    """Honest catalog defaults (msrp, scale, demand). Not sourced from Toyark."""
    low = (line or "").lower()
    if company in {"hottoys", "enterbay", "asmus", "starace", "exo6"} or "mms" in low:
        return 280.0, "1/6", 1.35
    if company == "threezero":
        if "mdlx" in low:
            return 90.0, "1/12", 1.25
        if "dlx" in low:
            return 180.0, "1/12", 1.3
        return 220.0, "1/6", 1.3
    if company == "mondo":
        return 200.0, "1/6", 1.3
    if company == "super7":
        if "reaction" in low:
            return 22.99, '3.75"', 1.2
        return 55.0, '7"', 1.3
    if company == "neca":
        return 36.99, '7"', 1.3
    if company == "mcfarlane":
        return 24.99, '7"', 1.25
    if company == "jazwares":
        return 24.99, '6"', 1.3
    return 24.99, '6"', 1.25


def build_subtitle(variant: str | None, year: int | None, window: str | None) -> str:
    bits: list[str] = []
    if variant:
        bits.append(variant)
    if window and (not variant or window.lower() not in variant.lower()):
        bits.append(window)
    if year and (not window or str(year) not in window):
        bits.append(str(year))
    return " · ".join(bits) if bits else (str(year) if year else "")


def resolve_release_year(cand: dict[str, Any]) -> int | None:
    """Street year from prose, else announcement year from the post. Never invent."""
    y = cand.get("year")
    if isinstance(y, int) and 2020 <= y <= 2036:
        return y
    if isinstance(y, str) and y.isdigit():
        yi = int(y)
        if 2020 <= yi <= 2036:
            return yi
    py = cand.get("postYear")
    if isinstance(py, int) and 2020 <= py <= 2036:
        return py
    return None


def is_apply_multipack(cand: dict[str, Any]) -> bool:
    if cand.get("pack") == "set":
        return True
    blob = " ".join(
        str(x or "")
        for x in (cand.get("name"), cand.get("title"), cand.get("variant"))
    )
    return bool(MULTI_PACK_RE.search(blob))


def make_oneshot_row(
    *,
    rid: str,
    cand: dict[str, Any],
    year: int,
    sku: str | None,
    image: str | None,
) -> dict[str, Any]:
    company = str(cand.get("company") or "").lower()
    line = str(cand.get("line") or "").strip()
    name = str(cand.get("name") or "").strip()
    variant = cand.get("variant") or None
    window = cand.get("releaseWindow") or None
    msrp, scale, demand = defaults_for_company_line(company, line)
    pid = cand.get("toyarkPostId")
    tags = ["toyark", "toyark-densify", company, SOURCE]
    if pid is not None and str(pid).strip():
        tags.append(f"toyark-{pid}")
    if sku:
        tags.append("sku-gtin")
    seen: set[str] = set()
    tags2: list[str] = []
    for t in tags:
        if t and t not in seen:
            seen.add(t)
            tags2.append(t)
    out: dict[str, Any] = {
        "id": rid,
        "name": name,
        "subtitle": build_subtitle(variant, year, window),
        "line": line,
        "company": company,
        "kind": "figure",
        "releaseDate": f"{year}-01-01",
        "msrp": float(msrp),
        "scale": scale,
        "demand": float(demand),
        "tags": tags2,
        "source": SOURCE,
    }
    if sku:
        out["sku"] = sku
    if image:
        out["imageUrl"] = image
    return out


def apply_candidates(
    accepts: list[dict[str, Any]],
    *,
    rows: list[dict[str, Any]],
    aliases: dict[str, Any],
    sku_map: dict[str, Any],
    urls: dict[str, Any],
    index: OneshotIndex,
    cap: int,
) -> dict[str, Any]:
    """Append accepted singles onto oneshot. Never invent GTINs. No rematch."""
    aliases = ensure_alias_doc(aliases)
    alias_to: dict[str, str] = aliases.get("aliasToFigureId") or {}
    ids = {str(r.get("id")) for r in rows if r.get("id")}
    gtin_owned: dict[str, str] = {}
    for r in rows:
        s = clean_code(r.get("sku"))
        if s and is_gtin(s):
            gtin_owned[s] = str(r["id"])
        mid = sku_map.get(str(r.get("id") or ""))
        if isinstance(mid, str) and is_gtin(mid):
            gtin_owned.setdefault(clean_code(mid) or mid, str(r["id"]))

    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    alias_added = 0
    img_baked = 0
    cap = max(0, min(int(cap), 200))

    for cand in accepts:
        if len(applied) >= cap:
            skipped.append(
                {
                    "name": cand.get("name"),
                    "company": cand.get("company"),
                    "reason": "cap",
                    "toyarkPostId": cand.get("toyarkPostId"),
                }
            )
            continue
        if is_apply_multipack(cand):
            skipped.append(
                {
                    "name": cand.get("name"),
                    "company": cand.get("company"),
                    "reason": "multipack",
                    "toyarkPostId": cand.get("toyarkPostId"),
                }
            )
            continue
        name = str(cand.get("name") or "").strip()
        company = str(cand.get("company") or "").lower()
        line = str(cand.get("line") or "").strip()
        variant = str(cand.get("variant") or "").strip()
        if not name or not company or not line:
            skipped.append({"name": name or None, "reason": "incomplete-identity"})
            continue
        if is_prop_item(name, variant, name):
            skipped.append({"name": name, "reason": "vehicles-props-only"})
            continue

        year = resolve_release_year(cand)
        if year is None:
            skipped.append(
                {
                    "name": name,
                    "company": company,
                    "reason": "no-year",
                    "toyarkPostId": cand.get("toyarkPostId"),
                }
            )
            continue

        dupe_reason, hit_ids = index.match(company, name, line, year, variant)
        if dupe_reason:
            skipped.append(
                {
                    "name": name,
                    "company": company,
                    "reason": dupe_reason,
                    "oneshotIds": hit_ids,
                    "toyarkPostId": cand.get("toyarkPostId"),
                }
            )
            continue

        raw_gtin = cand.get("gtin")
        sku = None
        if raw_gtin:
            g = clean_code(raw_gtin)
            if g and is_gtin(g):
                owner = gtin_owned.get(g)
                if owner:
                    skipped.append(
                        {
                            "name": name,
                            "company": company,
                            "reason": "gtin-exists",
                            "sku": g,
                            "owner": owner,
                        }
                    )
                    continue
                sku = g
            # Non-GTIN "gtin" field is ignored — never promote listing → sku.

        listing_codes = [
            c
            for c in (cand.get("aliases") or cand.get("codes") or [])
            if isinstance(c, str) and c.strip() and not is_gtin(c)
        ]
        stolen = False
        for code in listing_codes:
            c2 = clean_code(code) or code.strip()
            owner = alias_to.get(c2)
            if owner:
                skipped.append(
                    {
                        "name": name,
                        "company": company,
                        "reason": "alias-owned",
                        "alias": c2,
                        "owner": owner,
                    }
                )
                stolen = True
                break
        if stolen:
            continue

        rid = stable_id(cand.get("toyarkPostId"), name, company, line, variant, ids)
        image = cand.get("imageUrl") if isinstance(cand.get("imageUrl"), str) else None
        if image and not image.startswith("http"):
            image = None

        row = make_oneshot_row(rid=rid, cand=cand, year=year, sku=sku, image=image)
        rows.append(row)
        ids.add(rid)
        index.add(row)
        if sku:
            gtin_owned[sku] = rid
            sku_map[rid] = sku
        if image:
            urls[rid] = image
            img_baked += 1

        als: list[str] = [f"id:{rid}", f"toyark:{cand.get('toyarkPostId') or rid}"]
        als.extend(listing_codes)
        if sku:
            als.append(sku)
        src = cand.get("sourceUrl")
        if isinstance(src, str) and src.startswith("http"):
            als.append(src)
        alias_added += add_aliases(aliases, rid, als)

        applied.append(
            {
                "id": rid,
                "name": name,
                "company": company,
                "line": line,
                "year": year,
                "variant": variant or None,
                "sku": sku,
                "image": bool(image),
                "imageUrl": image,
                "aliases": listing_codes,
                "sourceUrl": cand.get("sourceUrl"),
                "toyarkPostId": cand.get("toyarkPostId"),
            }
        )

    return {
        "applied": applied,
        "skipped": skipped,
        "aliasAdded": alias_added,
        "withImage": img_baked,
        "cap": cap,
    }


def summarize(accepts: list[dict], rejects: list[dict], allow: list[str]) -> dict[str, Any]:
    by_company = {
        c: {
            "accepted": sum(1 for a in accepts if a.get("company") == c),
            "rejected": sum(1 for r in rejects if r.get("company") == c),
        }
        for c in allow
    }
    by_reason = Counter(str(r.get("reason") or "unknown") for r in rejects)
    return {
        "fetchedPosts": None,  # filled by caller
        "acceptedCandidates": len(accepts),
        "rejectedRows": len(rejects),
        "byCompany": by_company,
        "byRejectReason": dict(by_reason),
    }


def build_report(
    *,
    posts: list[dict],
    fetch_meta: dict[str, Any],
    after: datetime,
    before: datetime | None,
    days: int | None,
    allow: list[str],
    index: OneshotIndex,
    per_page: int,
    extra: dict[str, Any],
) -> dict[str, Any]:
    accepts: list[dict[str, Any]] = []
    rejects: list[dict[str, Any]] = []
    for post in posts:
        a, r = evaluate_post(post, allow=set(allow), index=index)
        accepts.extend(a)
        rejects.extend(r)
    summary = summarize(accepts, rejects, allow)
    summary["fetchedPosts"] = len(posts)
    apply_mode = bool(extra.get("apply"))
    writes = (
        "oneshot + aliases + image-urls + sku-map (GTIN only) — comics untouched"
        if apply_mode
        else "none — report only"
    )
    oneshot_mode = extra.get("oneshotMode") or ("apply" if apply_mode else "read-only")
    return {
        "generatedAt": now_iso(),
        "mode": "apply" if apply_mode else "dry-run",
        "applyWired": True,
        "source": REST_POSTS,
        "policy": {
            "gtin": "preferred-not-required; never invent",
            "identity": "company + line + year + variant",
            "allowlist": list(allow),
            "writes": writes,
            "cap": extra.get("cap"),
            "idScheme": "ta-<sha1[:12] of postId+name+company+line+variant>",
        },
        "window": {
            "days": days,
            "after": after.astimezone(timezone.utc).isoformat(),
            "before": before.astimezone(timezone.utc).isoformat() if before else None,
        },
        "fetch": {
            **fetch_meta,
            "perPage": per_page,
            "fetchedPostCount": len(posts),
            "userAgent": UA,
        },
        "oneshot": {
            "path": extra.get("oneshotPath")
            or (str(ONESHOT.relative_to(ROOT)) if ONESHOT.exists() else str(ONESHOT)),
            "indexedRows": index.row_count,
            "mode": oneshot_mode,
        },
        "summary": summary,
        "candidates": accepts,
        "rejects": rejects,
        **{k: v for k, v in extra.items() if k not in {"apply", "oneshotMode", "oneshotPath", "cap"}},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--days", type=int, default=7, help="Lookback window in days (default 7)")
    ap.add_argument("--after", help="ISO start (overrides --days), e.g. 2026-09-13 or 2026-09-13T00:00:00Z")
    ap.add_argument("--before", help="Optional ISO end bound")
    ap.add_argument("--per-page", type=int, default=20, help="WP REST per_page (max 100, default 20)")
    ap.add_argument("--max-pages", "--page-cap", dest="max_pages", type=int, default=4, help="Page cap (default 4)")
    ap.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="Report JSON path (default src/data/figure-archive/toyark-densify-dry-run.json)",
    )
    ap.add_argument(
        "--company",
        action="append",
        dest="companies",
        help="Override allowlist (repeatable). Must be an id already in the script allowlist.",
    )
    ap.add_argument("--sleep", type=float, default=0.75, help="Seconds between REST pages (default 0.75)")
    ap.add_argument(
        "--posts-json",
        type=Path,
        help="Replay a saved WP REST posts array (works with dry-run or --apply; skips live fetch)",
    )
    ap.add_argument(
        "--skip-oneshot",
        action="store_true",
        help="Skip oneshot read (dedupe keys empty). Incompatible with --apply.",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Append accepted candidates to oneshot (plus aliases / image URLs). "
        "Never invents GTINs. Comics untouched.",
    )
    ap.add_argument(
        "--cap",
        type=int,
        default=DEFAULT_CAP,
        help=f"Max applied rows per run (default {DEFAULT_CAP}, low-and-slow).",
    )
    ap.add_argument(
        "--oneshot",
        type=Path,
        default=ONESHOT,
        help="Oneshot path (override for tests / copies).",
    )
    ap.add_argument(
        "--aliases",
        type=Path,
        default=ALIASES,
        help="figure-sku-aliases.json path (apply only).",
    )
    ap.add_argument(
        "--image-urls",
        type=Path,
        default=URLS,
        help="figure-image-urls.json path (apply only).",
    )
    ap.add_argument(
        "--sku-map",
        type=Path,
        default=SKU_MAP,
        help="figure-sku-map.json path (apply only; GTIN overlay).",
    )
    ap.add_argument(
        "--stats",
        type=Path,
        default=DEFAULT_STATS,
        help="Apply stats JSON path.",
    )
    args = ap.parse_args(argv)

    allow = list(ALLOWLIST)
    if args.companies:
        allow = []
        for raw in args.companies:
            for part in re.split(r"[,\s]+", raw.strip()):
                if not part:
                    continue
                cid = part.lower()
                if cid not in ALLOWLIST:
                    print(f"ERROR: --company {cid} is not in allowlist {ALLOWLIST}", file=sys.stderr)
                    return 2
                if cid not in allow:
                    allow.append(cid)

    if args.after:
        after = parse_iso(args.after)
        days: int | None = None
    else:
        days = int(args.days)
        after = datetime.now(timezone.utc) - timedelta(days=days)
    before = parse_iso(args.before) if args.before else None

    if args.posts_json:
        robots = {
            "url": ROBOTS_URL,
            "ok": True,
            "wpJsonAllowed": True,
            "feedDisallowed": True,
            "note": "Replay (--posts-json): skipped live robots.txt fetch.",
            "httpStatus": None,
        }
    else:
        robots = check_robots()
        if robots.get("wpJsonAllowed") is False:
            print("ERROR: robots.txt disallows /wp-json; refusing to crawl.", file=sys.stderr)
            return 3

    fetch_meta: dict[str, Any] = {
        "ok": False,
        "robots": robots,
        "source": "live-rest",
    }
    posts: list[dict[str, Any]] = []

    if args.posts_json:
        posts = load_replay(args.posts_json)
        try:
            replay_disp = str(args.posts_json.resolve().relative_to(ROOT))
        except ValueError:
            replay_disp = args.posts_json.name
        fetch_meta.update(
            {
                "ok": True,
                "source": "posts-json-replay",
                "replayPath": replay_disp,
                "pagesFetched": 0,
                "httpStatus": None,
                "blocker": None,
                "notes": [
                    "Replayed saved WP REST payload (same /wp-json/wp/v2/posts?_embed=1 shape). "
                    "Date window still applied.",
                    "Live urllib fetch skipped because --posts-json was set.",
                ],
            }
        )
        posts = [p for p in posts if in_window(p, after, before)]
    else:
        fetched = fetch_posts(
            after=after,
            before=before,
            per_page=args.per_page,
            max_pages=args.max_pages,
            sleep_s=args.sleep,
        )
        posts = fetched.pop("posts")
        fetch_meta.update(fetched)
        if fetched.get("blocker"):
            msg = (
                f"Toyark REST live fetch failed ({fetched.get('blocker')}, "
                f"HTTP {fetched.get('httpStatus')}). "
                "Babysit: report this blocker; do not apply. "
                "Re-run later or pass --posts-json with a saved "
                "/wp-json/wp/v2/posts payload."
            )
            if args.apply:
                print(f"ERROR: {msg}", file=sys.stderr)
            else:
                print(f"WARN: {msg}", file=sys.stderr)

    oneshot_path: Path = args.oneshot
    if args.apply and args.skip_oneshot:
        print("ERROR: --apply requires oneshot identity; --skip-oneshot is refused.", file=sys.stderr)
        return 2
    if args.apply and not oneshot_path.exists():
        print(f"ERROR: --apply requires oneshot at {oneshot_path}", file=sys.stderr)
        return 1

    rows: list[dict[str, Any]] = []
    if args.skip_oneshot or not oneshot_path.exists():
        index = OneshotIndex([], set(allow))
    else:
        rows = load_json(oneshot_path)
        if not isinstance(rows, list):
            print("ERROR: oneshot.json is not a list — refusing (no writes).", file=sys.stderr)
            return 1
        index = OneshotIndex(rows, set(allow))

    live_blocked = (not args.posts_json) and bool(fetch_meta.get("blocker") or not fetch_meta.get("ok"))
    apply_ran = False
    apply_result: dict[str, Any] = {}
    if args.apply and live_blocked:
        apply_result = {
            "applied": [],
            "skipped": [],
            "aliasAdded": 0,
            "withImage": 0,
            "cap": args.cap,
            "blocker": fetch_meta.get("blocker") or "live-fetch-failed",
        }
    elif args.apply:
        raw_aliases = load_json(args.aliases) if args.aliases.exists() else {}
        if not isinstance(raw_aliases, dict):
            print("ERROR: aliases file is not an object — refusing.", file=sys.stderr)
            return 1
        aliases = ensure_alias_doc(raw_aliases)
        sku_map = load_json(args.sku_map) if args.sku_map.exists() else {}
        if not isinstance(sku_map, dict):
            sku_map = {}
        urls = load_json(args.image_urls) if args.image_urls.exists() else {}
        if not isinstance(urls, dict):
            urls = {}
        apply_ran = True

    extra: dict[str, Any] = {
        "apply": bool(args.apply),
        "cap": int(args.cap),
        "oneshotPath": _rel(oneshot_path),
        "oneshotMode": "apply" if args.apply else "read-only",
    }

    report = build_report(
        posts=posts,
        fetch_meta=fetch_meta,
        after=after,
        before=before,
        days=days,
        allow=allow,
        index=index,
        per_page=args.per_page,
        extra=extra,
    )

    if args.apply and apply_ran:
        apply_result = apply_candidates(
            list(report["candidates"]),
            rows=rows,
            aliases=aliases,
            sku_map=sku_map,
            urls=urls,
            index=index,
            cap=args.cap,
        )
        if apply_result["applied"]:
            write_json(oneshot_path, rows)
            write_json(args.aliases, aliases)
            write_json(args.image_urls, urls)
            write_json(args.sku_map, sku_map)
            if ONESHOT_STATS.exists() and oneshot_path.resolve() == ONESHOT.resolve():
                try:
                    os_stats = load_json(ONESHOT_STATS)
                    if isinstance(os_stats, dict):
                        os_stats["archiveTotal"] = len(rows)
                        os_stats["toyarkDensifyAdded"] = len(apply_result["applied"])
                        os_stats["toyarkDensifyAt"] = now_iso()
                        write_json(ONESHOT_STATS, os_stats)
                except (OSError, json.JSONDecodeError, TypeError) as exc:
                    apply_result["oneshotStatsError"] = str(exc)

    if args.apply:
        report["applied"] = apply_result.get("applied") or []
        report["applySkipped"] = apply_result.get("skipped") or []
        report["applyStats"] = {
            "accepted": report["summary"]["acceptedCandidates"],
            "applied": len(apply_result.get("applied") or []),
            "skippedApply": len(apply_result.get("skipped") or []),
            "aliasAdded": apply_result.get("aliasAdded") or 0,
            "withImage": apply_result.get("withImage") or 0,
            "cap": apply_result.get("cap", args.cap),
            "blocker": apply_result.get("blocker"),
        }
        report["policy"]["writes"] = (
            "oneshot + aliases + image-urls + sku-map (GTIN only) — comics untouched"
        )
        report["summary"]["applied"] = report["applyStats"]["applied"]
        report["summary"]["skippedApply"] = report["applyStats"]["skippedApply"]

    report_path: Path = args.report
    if args.apply and report_path == DEFAULT_REPORT:
        report_path = DEFAULT_APPLY_REPORT
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    if args.apply:
        stats_doc = {
            "source": SOURCE,
            "finishedAt": now_iso(),
            "mode": "apply",
            "cap": int(args.cap),
            "acceptedCandidates": report["summary"]["acceptedCandidates"],
            "applied": report["summary"].get("applied", 0),
            "skippedApply": report["summary"].get("skippedApply", 0),
            "rejectedRows": report["summary"]["rejectedRows"],
            "withImage": apply_result.get("withImage") or 0,
            "aliasAdded": apply_result.get("aliasAdded") or 0,
            "byCompany": report["summary"]["byCompany"],
            "byRejectReason": report["summary"]["byRejectReason"],
            "appliedIds": [a.get("id") for a in (apply_result.get("applied") or [])],
            "appliedSample": (apply_result.get("applied") or [])[:25],
            "skippedSample": (apply_result.get("skipped") or [])[:40],
            "archiveSize": len(rows) if apply_ran else None,
            "fetchBlocker": fetch_meta.get("blocker"),
            "wroteOneshot": bool(apply_ran and apply_result.get("applied")),
            "comics": "untouched",
        }
        write_json(args.stats, stats_doc)

    s = report["summary"]
    mode = report["mode"]
    print(
        f"mode={mode} applyWired=true posts={s['fetchedPosts']} "
        f"accepted={s['acceptedCandidates']} rejected={s['rejectedRows']}"
        + (
            f" applied={s.get('applied', 0)} skippedApply={s.get('skippedApply', 0)}"
            if args.apply
            else ""
        )
    )
    print(f"byCompany={s['byCompany']}")
    print(f"byRejectReason={s['byRejectReason']}")
    print(f"report={report_path}")
    if fetch_meta.get("blocker"):
        print(f"fetchBlocker={fetch_meta['blocker']}")
    if args.apply and live_blocked:
        return 1
    return 0 if (fetch_meta.get("ok") or posts) else 1


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
