#!/usr/bin/env python3
"""Canonical figure identity helpers (GTIN primary, listing codes as aliases).

Policy (Shelby 2026-09-07):
  - Durable `sku` on a figure row is the universal EAN/UPC/GTIN when known.
  - Hasbro Pulse / retailer listing codes (HAS*, F/G assort, MLDEADM3, BBTS ids,
    shop handles, etc.) are **aliases**, never a second figure row.
  - Never invent codes. When two rows share company+character+wave but carry
    listing vs GTIN labels, collapse into one row (GTIN wins as sku).
  - When two distinct GTINs disagree, leave both and flag.
"""
from __future__ import annotations

import re
from typing import Any

# UPC-A / EAN-8 / EAN-13 / GTIN-14
_GTIN_RE = re.compile(r"^\d{8}$|^\d{12,14}$")

# Retailer / manufacturer *listing* styles (not universal barcodes)
_LISTING_RE = re.compile(
    r"^(?:"
    r"HAS|HSF?|HSG|ASST|ASSORT|"  # Hasbro Pulse / specialty listing
    r"ML|BS|TF|GI|PR|WC|MEZ|BAN|BKD?MEA|PMF|MCF|MF|"  # line/house prefixes
    r"F|G|E|C|B|A"  # Hasbro assort letter+digits (F9115, G2370, …)
    r")[A-Z0-9]*\d[A-Z0-9]*$",
    re.I,
)

_STOP = set(
    "the a an of and or for to with from series wave deluxe exclusive edition "
    "figure figures action ver version vol volume pack set new legends".split()
)


def norm_text(s: str) -> str:
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens(s: str) -> list[str]:
    return [t for t in norm_text(s).split() if t and t not in _STOP and len(t) > 1]


def clean_code(raw: Any) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or not re.search(r"[A-Za-z0-9]", s):
        return None
    if len(s) > 64:
        return None
    if re.match(r"^(unknown|n/?a|none|null|todo|tbd|-+|\.+|0+|sku|test|placeholder)$", s, re.I):
        return None
    return s


def is_gtin(raw: Any) -> bool:
    s = clean_code(raw)
    return bool(s and _GTIN_RE.match(s))


def gtin_checksum_ok(raw: Any) -> bool:
    """Validate UPC-A / EAN-8 / EAN-13 / GTIN-14 check digit (mod-10)."""
    s = clean_code(raw)
    if not s or not _GTIN_RE.match(s):
        return False
    digits = [int(c) for c in s]
    check = digits[-1]
    body = digits[:-1]
    total = 0
    for i, d in enumerate(reversed(body)):
        total += d * 3 if (i % 2 == 0) else d
    return (10 - (total % 10)) % 10 == check


def is_gtin_strict(raw: Any) -> bool:
    """Length-shaped GTIN that also passes check digit — required for OCR accepts."""
    return gtin_checksum_ok(raw)


def is_listing_code(raw: Any) -> bool:
    """Hasbro/retailer listing / assort code — alias material, not canonical sku."""
    s = clean_code(raw)
    if not s or is_gtin(s):
        return False
    if _LISTING_RE.match(s):
        return True
    # Alphanumeric house SKUs without being pure GTIN (e.g. MLDEADM3, DE-INVN-12601)
    if re.search(r"[A-Za-z]", s) and re.search(r"\d", s):
        return True
    return False


def sku_kind(raw: Any) -> str:
    if is_gtin(raw):
        return "gtin"
    if is_listing_code(raw):
        return "listing"
    if clean_code(raw):
        return "other"
    return "none"


def prefer_canonical_sku(a: Any, b: Any) -> str | None:
    """Pick durable sku: GTIN beats listing/other. Never invent."""
    ca, cb = clean_code(a), clean_code(b)
    if is_gtin(ca) and not is_gtin(cb):
        return ca
    if is_gtin(cb) and not is_gtin(ca):
        return cb
    if is_gtin(ca) and is_gtin(cb):
        # Distinct GTINs — caller must not merge; return None to signal conflict
        if ca != cb:
            return None
        return ca
    return ca or cb


def wave_subtitle_core(s: str) -> str:
    """Normalize subtitle for dupe grouping: strip wave nums + trailing 'Legends' filler."""
    t = norm_text(s)
    t = re.sub(r"\b(?:w|wave)\s*\d+[a-z]?\b", " ", t)
    t = re.sub(r"\blegends\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def identity_group_key(row: dict) -> tuple[str, str, str, str]:
    return (
        str(row.get("company") or "").lower(),
        norm_text(str(row.get("name") or "")),
        norm_text(str(row.get("line") or "")),
        wave_subtitle_core(str(row.get("subtitle") or "")),
    )


def listing_digit_tail(code: str) -> str | None:
    m = re.search(r"(\d{5,})$", code.strip())
    return m.group(1) if m else None


def listing_embeds_in_gtin(listing: str, gtin: str) -> bool:
    dig = listing_digit_tail(listing)
    return bool(dig and dig in gtin)


def image_score(url: str | None) -> float:
    if not url or not str(url).startswith("http"):
        return 0.0
    u = str(url)
    sc = 50.0
    # Prefer URLs that embed a GTIN / clear product shot over generic placeholders
    if re.search(r"\d{12,14}", u):
        sc += 30
    if "cdn.shopify.com" in u:
        sc += 10
    if re.search(r"placeholder|coming.?soon|no.?image", u, re.I):
        sc -= 40
    return sc


def keep_rank(row: dict) -> float:
    """Higher = better survivor. GTIN sku + real image preferred."""
    sc = 0.0
    kind = sku_kind(row.get("sku"))
    if kind == "gtin":
        sc += 200
    elif kind == "listing":
        sc += 40
    elif kind == "other":
        sc += 20
    sc += image_score(row.get("imageUrl"))
    src = str(row.get("source") or "")
    if src == "curated":
        sc += 25
    elif src == "shopify":
        sc += 35
    elif "densify" in src:
        sc -= 30
    elif "bbts-wave" in src:
        sc += 5
    # Prefer plausible release years over placeholder far-future densify dates
    rd = str(row.get("releaseDate") or "9999")[:4]
    try:
        y = int(rd)
        if 1980 <= y <= 2030:
            sc += 15
        elif y > 2030:
            sc -= 10
    except ValueError:
        pass
    sc -= min(8, len(str(row.get("id") or "")) / 25)
    return sc


def collect_alias_codes(*rows: dict, canonical: str | None) -> list[str]:
    """Gather listing/other codes from rows that are not the canonical GTIN."""
    out: list[str] = []
    seen: set[str] = set()
    can_u = (canonical or "").upper()
    if can_u:
        seen.add(can_u)
    for r in rows:
        s = clean_code(r.get("sku"))
        if not s:
            continue
        if s.upper() in seen:
            continue
        if is_gtin(s) and canonical and s != canonical:
            # Conflicting GTIN — do not silently alias
            continue
        if is_gtin(s) and s == canonical:
            continue
        seen.add(s.upper())
        out.append(s)
    return out
