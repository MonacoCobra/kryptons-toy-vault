#!/usr/bin/env python3
"""Bake real Shopify CDN product images onto curated/placeholder figures.

No generative AI. Builds a searchable product→image index from AF Shopify
storefronts (same shops as figure-storefronts / oneshot), fuzzy-matches
catalog rows that lack imageUrl, and persists high-confidence hits only.

Outputs:
  - src/data/figure-image-urls.json  (id → CDN URL, comic-cover-urls style)
  - patches imageUrl on matching rows in src/data/figure-archive/oneshot.json
  - src/data/figure-archive/image-bake-stats.json

SKU-first rematch (--sku-first):
  Exact-join oneshot.sku → product-sku-index.sku → product imageUrl.
  Overwrites fuzzy mismatches when the SKU proves a different CDN URL.
  Fuzzy fill never overwrites a SKU-proven image.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_oneshot.shopify_dump import STOREFRONTS, fetch_all_products, is_figure_like, tag_list  # noqa: E402

ARCHIVE_JSON = ROOT / "src/data/figure-archive/oneshot.json"
URLS_JSON = ROOT / "src/data/figure-image-urls.json"
STATS_JSON = ROOT / "src/data/figure-archive/image-bake-stats.json"
INDEX_JSON = ROOT / "src/data/figure-archive/product-image-index.json"
SKU_INDEX_JSON = ROOT / "src/data/figure-archive/product-sku-index.json"
SKU_REMATCH_STATS_JSON = ROOT / "src/data/figure-archive/sku-image-rematch-stats.json"
FIGURES_TS = ROOT / "src/data/figures.ts"

STOP = set(
    "the a an of and or for to with from series wave deluxe exclusive edition "
    "figure figures action ver version vol volume pack set new toys toy scale "
    "ultimate ultimates reaction collectibles collection comic comics movie "
    "multipack boxed bundle pack".split()
)
WEAK = set("man men boy girl king queen lord lady black white red blue green glow robot pack".split())
SUBTITLE_NOISE = set(
    "wave waves exclusive deluxe special edition classic remaster remastered battle "
    "movie numbered boxed set pack multipack variant ver version vol volume series "
    "collective one12 one mmpr sdcc comic comics animated".split()
)
COLOR_WORDS = {
    "red", "blue", "green", "black", "white", "pink", "yellow", "purple", "orange",
    "crimson", "scarlet", "azure", "gold", "silver", "bronze", "grey", "gray",
}

LINE_AS_NAME = re.compile(
    r"ultimates?!?|reaction|masters of the universe|dc multiverse|mcfarlane|"
    r"teenage mutant|g\.?i\.?\s*joe|thundercats|silverhawks|universal monsters|"
    r"toho|spongebob|wwe elite|ben cooper|h\.?a\.?c\.?k\.?s|epic h\.?a\.?c\.?k|"
    r"vitruvian|court of the dead|hiya exquisite|exquisite (?:basic|mini)|"
    r"blokees|champion class|galaxy version|defostyle|carbote?x?|"
    r"marvel legends|black series|classified|studio series|lightning collection|"
    r"s\.?h\.?\s*figuarts|mafex|one:?12|robot spirits",
    re.I,
)

FAMILY_REQUIRE = {
    "masterverse": re.compile(r"masterverse", re.I),
    "origins": re.compile(r"origins", re.I),
    "ultimates": re.compile(r"ultimates?", re.I),
    "reaction": re.compile(r"reaction", re.I),
    "bst": re.compile(r"bst|axn|loyal", re.I),
    "wwe": re.compile(r"\bwwe\b", re.I),
    "jurassic": re.compile(r"jurassic|hammond", re.I),
    "multiverse": re.compile(r"multiverse", re.I),
    "spawn": re.compile(r"\bspawn\b", re.I),
    "tmnt": re.compile(r"tmnt|turtle|ronin", re.I),
    "universal": re.compile(r"universal monster", re.I),
    "jlu": re.compile(r"justice league unlimited|\bjlu\b", re.I),
    "dcuc": re.compile(r"dc universe classics|universe classics", re.I),
    "dcd": re.compile(r"dc direct|dc collectibles", re.I),
    "motu-generic": re.compile(r"masters of the universe|masterverse|origins", re.I),
    "hacks": re.compile(r"h\.?a\.?c\.?k|hacks|boss fight|vitruvian|epic", re.I),
    "hiya-godzilla": re.compile(r"godzilla|kong|ghidorah|mechagodzilla|shimo|mothra|rodan", re.I),
    "hiya-exquisite": re.compile(r"exquisite|hiya", re.I),
    # Hasbro lines (retailer Shopify titles must carry the line cue)
    "marvel-legends": re.compile(r"marvel legends", re.I),
    "black-series": re.compile(r"black series", re.I),
    "classified": re.compile(r"classified|g\.?i\.?\s*joe", re.I),
    "studio-series": re.compile(r"studio series", re.I),
    "lightning": re.compile(r"lightning collection|power rangers", re.I),
    "tf-masterpiece": re.compile(r"masterpiece", re.I),
    # Premium / Tamashii / Medicom / Mezco
    "one12": re.compile(r"one:?12|mezco", re.I),
    "mafex": re.compile(r"\bmafex\b", re.I),
    "shfiguarts": re.compile(r"figuarts", re.I),
    "storm": re.compile(r"storm|street fighter|mortal kombat|tekken|king of fighters|baki|arena", re.I),
    # Specialty brands newly indexed from retailers / Store Horsemen
    "fourhorsemen": re.compile(
        r"mythic legions|cosmic legions|figura obscura|infinite legions|four horsemen", re.I
    ),
    "kaiyodo": re.compile(r"kaiyodo|revoltech|yamaguchi", re.I),
    "playmates": re.compile(r"playmates|tmnt|turtle|exo.?squad|ninja turtle", re.I),
    "jakks": re.compile(r"jakks|sonic|nintendo|primal age|\bwwe\b|super mario", re.I),
    "toybiz": re.compile(r"toy\s*biz|toybiz|marvel legends", re.I),
    "kenner": re.compile(r"kenner|super powers", re.I),
    "dcdirect": re.compile(r"dc direct|dc collectibles", re.I),
}

# Curated lines with no honest Shopify counterpart on our feeds — never match.
# DC Direct/Collectibles unblocked when retailer vendor/title is classic DCD (not McFarlane Page Punchers).
BLOCKED_FAMILIES = {"jlu", "dcuc"}


def norm(s: str) -> str:
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens(s: str) -> list[str]:
    return [t for t in norm(s).split() if t and t not in STOP and len(t) > 1]


def significant_name_tokens(name: str) -> list[str]:
    toks = tokens(name)
    return [t for t in toks if t not in WEAK or len(toks) == 1]

NAME_PREFIX_STRIP = re.compile(
    r"^(superb scale|figure complex|carbotix|hiya|blokees|defostyle|vitruvian|"
    r"mafex(?:\s+no\.?\s*\d+)?|s\.?h\.?\s*figuarts|one:?12(?:\s+collective)?|"
    r"mezco(?:\s+toyz)?)\s+",
    re.I,
)


def figure_match_name(name: str) -> str:
    """Strip line-style prefixes so 'Figure Complex Boss Borot' → 'Boss Borot'."""
    n = (name or "").strip()
    prev = None
    while prev != n:
        prev = n
        n = NAME_PREFIX_STRIP.sub("", n).strip()
    return n




def line_family(line: str, company: str) -> str:
    l = norm(line)
    if "masterverse" in l:
        return "masterverse"
    if "origins" in l:
        return "origins"
    if "ultimates" in l:
        return "ultimates"
    if "reaction" in l:
        return "reaction"
    if "bst" in l or "axn" in l:
        return "bst"
    if "wwe" in l or (company == "mattel" and "elite" in l):
        return "wwe"
    if "jurassic" in l or "hammond" in l:
        return "jurassic"
    if "multiverse" in l:
        return "multiverse"
    if "spawn" in l:
        return "spawn"
    if "tmnt" in l or "turtle" in l or "ronin" in l:
        return "tmnt"
    if "universal monster" in l:
        return "universal"
    if "universe classics" in l:
        return "dcuc"
    if "justice league unlimited" in l or re.search(r"\bjlu\b", l):
        return "jlu"
    if "dc direct" in l or "dc collectibles" in l:
        return "dcd"
    if "h.a.c.k" in l or "hacks" in l or "vitruvian" in l:
        return "hacks"
    if company == "mattel" and "masters of the universe" in l:
        return "motu-generic"
    if company == "hiya" and ("godzilla" in l or "kong" in l):
        return "hiya-godzilla"
    if company == "hiya":
        return "hiya-exquisite"
    if company == "neca":
        return "neca"
    if company == "super7":
        return "super7"
    if company == "hasbro":
        if "marvel legends" in l or ("legends" in l and "marvel" in l):
            return "marvel-legends"
        if "black series" in l:
            return "black-series"
        if "classified" in l or "g.i. joe" in l or "gi joe" in l:
            return "classified"
        if "studio series" in l:
            return "studio-series"
        if "lightning" in l or "power rangers" in l:
            return "lightning"
        if "masterpiece" in l:
            return "tf-masterpiece"
        return "hasbro"
    if company == "mezco":
        return "one12"
    if company == "mafex":
        return "mafex"
    if company == "shfiguarts":
        return "shfiguarts"
    if company == "storm":
        return "storm"
    if company == "fourhorsemen":
        return "fourhorsemen"
    if company == "kaiyodo":
        return "kaiyodo"
    if company == "playmates":
        if "tmnt" in l or "turtle" in l or "ronin" in l:
            return "tmnt"
        return "playmates"
    if company == "jakks":
        return "jakks"
    if company == "toybiz":
        return "toybiz"
    if company == "kenner":
        return "kenner"
    if company == "dcdirect":
        return "dcd"
    if company == "loyalsubjects":
        return "bst"
    return company


# ALL-CAPS character runs common on AFAC / used-market specialty titles
# e.g. "marvel legends BARON ZEMO series", "dc direct SUPERMAN 6.5 inch"
_AFAC_CAPS_SKIP = {
    "MARVEL", "LEGENDS", "SERIES", "ACTION", "FIGURE", "FIGURES", "MASTERS", "UNIVERSE",
    "MASTERVERSE", "ORIGINS", "CLASSIFIED", "DIRECT", "COLLECTIBLES", "BLACK", "STUDIO",
    "LIGHTNING", "COLLECTION", "TEENAGE", "MUTANT", "NINJA", "TURTLES", "STAR", "WARS",
    "ANIMATED", "COMIC", "COMICS", "LOYAL", "SUBJECTS", "REACTION", "SUPER7", "MEZCO",
    "HASBRO", "MATTEL", "TOY", "BIZ", "TOYBIZ", "INCH", "MOC", "MIB", "COMPLETE",
    "VINTAGE", "RETRO", "MOVIE", "DC", "GI", "JOE", "COBRA", "BATMAN", "ONE", "COLLECTIVE",
    "POWER", "RANGERS", "EXCLUSIVE", "DELUXE", "EDITION", "WAVE", "PRE", "ORDER",
    "SHIPPING", "NEW", "MIB", "MOC", "LOOSE", "COMPLETE", "CARD", "BACK", "PACKAGING",
    "TEENAGE", "MUTANT", "NINJA", "TURTLE", "TMNT", "EXOSQUAD", "EXO", "SQUAD",
}


def caps_character_run(title: str) -> str:
    """Pull ALL-CAPS character name from specialty used-market titles.

    Only fires on AFAC-style mixed titles (lowercase franchise words + CAPS name),
    so Super7/ULTIMATES headers and normal Title Case Shopify titles are untouched.
    """
    if not title or not re.search(r"[A-Z]{3,}", title):
        return ""
    # Need lowercase content (franchise words) — pure CAPS / Title Case skip
    if not re.search(r"[a-z]{3,}", title):
        return ""
    hits = re.findall(
        r"\b([A-Z][A-Z0-9][A-Z0-9\'\.\-]*(?:\s+[A-Z][A-Z0-9][A-Z0-9\'\.\-]*){0,4})\b",
        title,
    )
    extra_skip = _AFAC_CAPS_SKIP | {
        "ULTIMATES", "ULTIMATE", "REACTION", "MULTIVERSE", "FIGUARTS", "MAFEX",
        "REVOLTECH", "YAMAGUCHI", "AMAZING", "COMPLEX", "EXQUISITE", "BASIC",
        "MINI", "HIYA", "STORM", "ARENA", "COLLECTIVE", "ONE12", "SDCC", "NYCC",
    }
    for h in hits:
        words = h.split()
        if not words:
            continue
        if all(w in extra_skip for w in words):
            continue
        if any(w not in extra_skip for w in words):
            return h.title() if h.isupper() else h
    return ""


def product_character_text(name: str, subtitle: str, title: str = "") -> str:
    """Where the character usually lives for noisy Shopify titles."""
    n, s, t = name or "", subtitle or "", title or ""
    full = t or f"{n} {s}"
    # AFAC / specialty CAPS character mid-title (mixed-case only)
    caps = caps_character_run(full)
    if caps:
        return f"{caps} {full}"
    # Pipe titles: last segment is usually the character
    if " | " in full:
        segs = [x.strip() for x in full.split(" | ") if x.strip()]
        if segs:
            char = segs[-1].split(":")[0].strip()
            return f"{char} {full}"
    # Kaiyodo / Amazing Yamaguchi / Revoltech — character after line prefix
    if re.search(r"amazing yamaguchi|revoltech|\bkaiyodo\b", full, re.I):
        stripped = re.sub(
            r"^(?:Pre-?[Oo]rder:\s*)?(?:Kaiyodo\s+)?(?:Amazing Yamaguchi\s+)?(?:Revoltech\s+)?(?:Figure Complex\s+)?",
            "",
            full,
            flags=re.I,
        )
        stripped = re.sub(r"\s*Action Figures?\s*", " ", stripped, flags=re.I)
        stripped = re.sub(r"\s+", " ", stripped).strip(" -:")
        if stripped:
            return f"{stripped} {full}"
    # Four Horsemen / Mythic / Cosmic / Figura Obscura
    if re.search(r"(?:mythic|cosmic|infinite)\s+legions|figura obscura|four horsemen", full, re.I):
        char = ""
        m = re.search(r"action figures?\s+(.+)$", full, re.I)
        if m:
            char = m.group(1).strip()
        elif ":" in full:
            char = full.split(":", 1)[-1].strip()
        elif " - " in full:
            char = full.rsplit(" - ", 1)[-1].strip()
        char = re.sub(r"\s*\(.*?\)\s*", " ", char)
        char = re.sub(r"\s+", " ", char).strip(" -:")
        if char:
            return f"{char} {full}"
    # Hiya long prefixes
    if re.search(r"\bhiya\b|exquisite (?:basic|mini)", full, re.I):
        stripped = re.sub(
            r"^HIYA\s+Exquisite\s+(?:Basic|Mini)\s+Series\s*(?:None\s+Scale\s*)?(?:\d+(?:\.\d+)?\s*Inch\s+)?",
            "",
            full,
            flags=re.I,
        )
        stripped = re.sub(r"\s*Action Figures?\s*$", "", stripped, flags=re.I)
        return f"{stripped} {full}"
    # McFarlane / shop.dc character-leading titles
    if re.search(r"mcfarlane|dc multiverse", full, re.I):
        m = re.match(r"^([A-Z0-9][A-Za-z0-9\'\.\- ]+?)\s*(?:\(|McFarlane|DC Multiverse)", full)
        if m:
            return f"{m.group(1)} {full}"
    cleaned = re.sub(
        r"\s*[-–—]?\s*(pre-?order(?:\s+deposit|\s+ended)?|ships?\s+q\d.*)$",
        "",
        full,
        flags=re.I,
    )
    # Solaris / JP import: "Series - Character - S.H.Figuarts (Bandai Spirits)"
    if re.search(r"s\.?h\.?\s*figuarts|\bmafex\b", full, re.I) and " - " in full:
        segs = [x.strip() for x in re.split(r"\s+-\s+", full) if x.strip()]
        for seg in reversed(segs):
            if re.search(r"figuarts|mafex|bandai|kaiyodo|revoltech|yamaguchi|spirits", seg, re.I):
                continue
            if len(seg) >= 2:
                return f"{seg} {full}"
    # Retailer / Hasbro / Tamashii / Medicom / Mezco long titles
    if re.search(
        r"marvel legends|black series|classified|studio series|lightning collection|"
        r"s\.?h\.?\s*figuarts|\bmafex\b|one:?12|storm (?:arena|collect)",
        full,
        re.I,
    ):
        char = ""
        if " - " in cleaned:
            char = cleaned.rsplit(" - ", 1)[-1].strip()
        elif " | " in cleaned:
            char = cleaned.split(" | ")[-1].strip()
        if not char:
            char = re.sub(
                r"^(?:Pre-?[Oo]rder:\s*)?(?:Marvel Legends(?:\s+Series)?|"
                r"Star Wars(?: The)? Black Series(?: Archives)?|"
                r"G\.?I\.?\s*Joe Classified|"
                r"Transformers Studio Series|"
                r"Power Rangers Lightning Collection|"
                r"S\.?H\.?\s*Figuarts|"
                r"Mafex(?:\s+No\.?\s*\d+)?|"
                r"Mezco Toyz ONE:12 Collective|"
                r"ONE:12 Collective)\s*",
                "",
                cleaned,
                flags=re.I,
            )
        char = re.sub(r"\s*\d+(?:\.\d+)?\s*Inch(?:\s+Scale)?\s*", " ", char, flags=re.I)
        char = re.sub(r"\s*Action Figures?\s*", " ", char, flags=re.I)
        char = re.sub(r"\s*\(.*?\)\s*", " ", char)
        char = re.sub(r"\s+", " ", char).strip(" -:")
        if char:
            return f"{char} {cleaned}"
    # Masters of the Universe / Masterverse / Origins — character usually trails the line name
    if re.search(r"masters of the universe|masterverse|\borigins\b", full, re.I):
        # Prefer explicit " - Character" tail when present (avoid peeling to "7 Inch")
        if " - " in cleaned:
            tail = cleaned.rsplit(" - ", 1)[-1].strip()
            tail = re.sub(r"\s*Action Figures?\s*.*$", "", tail, flags=re.I)
            tail = re.sub(r"\s+", " ", tail).strip(" -:")
            if tail and not re.match(r"^\d+(?:\.\d+)?\s*inch\b", tail, re.I):
                return f"{tail} {cleaned}"
        stripped = re.sub(
            r"^(?:Pre-?[Oo]rder:\s*)?(?:Figurine\s+)?(?:Mattel(?:\s+Creations)?\s+)?"
            r"Masters of the Universe(?:\s+(?:Masterverse|Origins|Chronicles|Revelation|"
            r"New Eternia|Vintage Collection|200X Cartoon Collection|2026 Movie|"
            r"Cartoon Collection))*\s*",
            "",
            cleaned,
            flags=re.I,
        )
        stripped = re.sub(
            r"^(?:Masterverse|Origins|Revelation|New Eternia)\s+",
            "",
            stripped,
            flags=re.I,
        )
        stripped = re.sub(r"\s*Action Figures?\s*.*$", "", stripped, flags=re.I)
        stripped = re.sub(r"\s*\(.*?\)\s*", " ", stripped)
        stripped = re.sub(r"\s+", " ", stripped).strip(" -:")
        if stripped and 1 < len(stripped) < len(cleaned):
            return f"{stripped} {cleaned}"
    if LINE_AS_NAME.search(n) and s.strip():
        return f"{s} {n} {cleaned}"
    if re.match(r"^masters of the universe\b", n, re.I):
        return f"{n} {s} {cleaned}"
    return f"{n} {s} {cleaned}"


def image_from_product(p: dict) -> str | None:
    for im in p.get("images") or []:
        src = (im or {}).get("src")
        if src and str(src).startswith("http"):
            return str(src)
    return None



# Specialty retailers with open products.json — image-index only (not oneshot dump).
# Vendor/title → CompanyId so Hasbro/Mezco/MAFEX/SHF curated rows can match.
RETAILER_FEEDS = [
    # maxPages bumped to Shopify products.json ceiling (~100) where catalogs were truncated
    {"id": "toyarena", "baseUrl": "https://www.toyarena.com", "pageLimit": 250, "maxPages": 75},
    {"id": "cmdstore", "baseUrl": "https://www.cmdstore.ca", "pageLimit": 250, "maxPages": 80},
    {"id": "planet-af", "baseUrl": "https://www.planetactionfigures.co.uk", "pageLimit": 250, "maxPages": 35},
    # Verified open specialty AF catalogs (2026-09) — Hasbro/Playmates/JAKKS/DCD/ToyBiz/BST
    {"id": "cooltoyden", "baseUrl": "https://cooltoyden.com", "pageLimit": 250, "maxPages": 30},
    {"id": "afcollector", "baseUrl": "https://afcollector.com", "pageLimit": 250, "maxPages": 15},
    {"id": "legendztoys", "baseUrl": "https://legendztoys.com", "pageLimit": 250, "maxPages": 10},
    # New open specialty / first-party (verified 2026-09-06) — Mattel retail + JP import SHF/AY
    {"id": "shop-mattel", "baseUrl": "https://shop.mattel.com", "pageLimit": 250, "maxPages": 40},
    {"id": "solarisjapan", "baseUrl": "https://www.solarisjapan.com", "pageLimit": 250, "maxPages": 100},
    {"id": "jbhifi", "baseUrl": "https://www.jbhifi.com.au", "pageLimit": 250, "maxPages": 12},
    # Large used/new specialty AF catalog (CAPS character titles) — Hasbro/Mattel/DCD/Playmates/TLS
    {"id": "afac", "baseUrl": "https://www.actionfiguresandcomics.com", "pageLimit": 250, "maxPages": 100},
    # JP import specialty — SHFiguarts / MAFEX / Kaiyodo (filter via infer + RETAILER_SKIP)
    {"id": "japan-figure", "baseUrl": "https://www.japan-figure.com", "pageLimit": 250, "maxPages": 100},
    # Verified open specialty (2026-09-06 evening) — real variant.sku; AF via infer+RETAILER_SKIP
    # staractionfigures: UK specialty, strong Hasbro ML/BS/Classified + McFarlane Multiverse
    {"id": "staractionfigures", "baseUrl": "https://www.staractionfigures.co.uk", "pageLimit": 250, "maxPages": 30},
    # toydojo: US specialty import — SHFiguarts / Bandai / Hasbro / MAFEX / Mezco
    {"id": "toydojo", "baseUrl": "https://www.toydojo.com", "pageLimit": 250, "maxPages": 20},
    # toynk: large US specialty (noisy merch; RETAILER_SKIP drops bag clips/costumes)
    {"id": "toynk", "baseUrl": "https://www.toynk.com", "pageLimit": 250, "maxPages": 100},
    # Verified open specialty (2026-09-06 late) — real variant.sku; AF via infer+RETAILER_SKIP
    # indemandtoys: UK AF specialist (~3.5k catalog) — Hasbro ML/BS/Classified/TF + Mattel/NECA/McFarlane
    {"id": "indemandtoys", "baseUrl": "https://www.indemandtoys.co.uk", "pageLimit": 250, "maxPages": 20},
    # hobbyfigures: UK specialty import — Hasbro/McFarlane/SHF/MAFEX/Hot Toys (nendoroid/scale skipped)
    {"id": "hobbyfigures", "baseUrl": "https://www.hobbyfigures.co.uk", "pageLimit": 250, "maxPages": 100},
    # Verified open specialty (2026-09-06 night) — real variant.sku; AF via infer+RETAILER_SKIP
    # collecticon: US specialty (~4.3k) — strong Hasbro TF/ML/BS + McFarlane/NECA/Mattel Origins
    {"id": "collecticon", "baseUrl": "https://www.collecticontoys.com", "pageLimit": 250, "maxPages": 25},
    # nerdzoic: US specialty AF (~1k) — Hasbro/Mattel/McFarlane/NECA/Four Horsemen + Mezco One:12
    {"id": "nerdzoic", "baseUrl": "https://nerdzoic.com", "pageLimit": 250, "maxPages": 10},
    # Verified open specialty (2026-09-06 plateau pass) — real variant.sku; AF via infer+RETAILER_SKIP
    # kitsap: comics/games shop with strong AF aisle — Hasbro ML/BS/Classified/TF + McFarlane/NECA/Mattel
    # (Games/Comics product_types skipped in infer; prior 429 deferred — recovered with cool-down)
    {"id": "kitsap", "baseUrl": "https://www.kitsapcomics.com", "pageLimit": 250, "maxPages": 20},
    # sifitoys: specialty AF — Mezco One:12 + Four Horsemen/McFarlane/Hasbro (thin but honest SKUs)
    {"id": "sifitoys", "baseUrl": "https://www.sifitoys.com", "pageLimit": 250, "maxPages": 12},
    # Hasbro Pulse (2026-09-07): myshopify products.json is open with real variant.sku.
    # Almost all are listing codes (F/G/H*); barcode empty. Bake treats listing→aliases;
    # rare GTIN-shaped sku values may fill primary. Public hasbropulse.com PWA is Mobify HTML.
    {"id": "hasbro-pulse", "baseUrl": "https://hasbropulse.myshopify.com", "pageLimit": 250, "maxPages": 25},
]

RETAILER_SKIP = re.compile(
    r"\b(roleplay|life size|prop replica|die cast|diecast|static figure|model kit|gunpla|"
    r"figuarts zero|statue|plush|funko|\bpop\b|trading card|pokemon|soft goods|"
    r"empty box|backdrop|t-?shirt|hoodie|mug|poster|apparel|enamel|pin set|"
    r"blind box flat|gift card|nendoroid|pop up parade|scale figure|"
    r"non-scale figure|vibration stars|\blego\b|steiff|loungefly|ornament|"
    r"living dead dolls?|mds mega scale|barbie|hot wheels|little people|fisher.?price|"
    r"monster high|kpop demon|tonies|deck box|beach towel|cozy set|"
    r"wall calendar|calendar|tcg|booster|sleeves|playmat|diecast car|"
    r"trading card set|magnet only|poster.?stand|poster & stand|"
    r"imaginext|spin master|mini blind bag|2 inch mini|"
    r"bag clip|foam bag|keychain|cosbi|bobble.?head|q-fig|minico|"
    r"costume|jumpsuit|hockey jersey|inspirit|"
    r"vinyl art|dunny|kidrobot|"
    r"comic book|graphic novel|\btpb\b|trade paperback|"
    r"warhammer|games workshop|age of sigmar|citadel paint|"
    r"\bunmatched\b|hero deck|game master screen|rpg:|"
    r"dice set)\b",
    re.I,
)

def infer_retailer_company(p: dict) -> str | None:
    """Map multi-vendor retailer product → vault CompanyId (high confidence only)."""
    vendor = str(p.get("vendor") or "")
    title = str(p.get("title") or "")
    ptype = str(p.get("product_type") or "")
    tags = " ".join(tag_list(p.get("tags")))
    blob = f"{vendor} {title} {ptype} {tags}"
    bl = blob.lower()
    # Comic-shop / board-game product_types (kitsap etc.) — never AF SKU sources
    pt = ptype.strip().lower()
    if pt.startswith("games") or pt.startswith("comics") or pt in {
        "book", "graphic novels", "novels", "sports cards", "posters and prints",
        "supplies - game", "supplies - comic", "retailers sales tools",
        "game", "games", "apparel", "clothing", "soft goods", "accessories",
    }:
        return None
    if RETAILER_SKIP.search(blob):
        return None
    # Specific lines first
    if re.search(r"\bmafex\b", bl):
        return "mafex"
    if re.search(r"figuarts", bl) and not re.search(r"figuarts zero", bl):
        return "shfiguarts"
    if re.search(r"one:?12", bl) or re.search(r"\bmezco\b", bl):
        # Reject Mezco soft goods / pins if tagged
        if re.search(r"\b(poster|apparel|pin set|enamel)\b", bl):
            return None
        return "mezco"
    if re.search(r"storm collect", bl) or re.match(r"storm\b", vendor, re.I):
        return "storm"
    # Toy Biz ML before Hasbro ML
    if re.search(r"toy\s*biz|toybiz", bl) and re.search(r"marvel legends|marvel", bl):
        return "toybiz"
    if re.search(r"marvel legends", bl):
        return "hasbro"
    if re.search(r"black series", bl):
        return "hasbro"
    if re.search(r"classified|g\.?i\.?\s*joe", bl) and re.search(r"hasbro|classified|g\.?i\.?\s*joe", bl):
        return "hasbro"
    if re.search(r"studio series", bl):
        return "hasbro"
    if re.search(r"lightning collection|power rangers lightning", bl):
        return "hasbro"
    if re.search(r"transformers masterpiece", bl):
        return "hasbro"
    if re.search(r"\bhasbro\b", bl) and re.search(
        r"legends|black series|classified|transformers|lightning|star wars|g\.?i\.?\s*joe",
        bl,
    ):
        return "hasbro"
    # McFarlane "DC Direct" Page Punchers ≠ classic DC Direct/Collectibles
    if re.search(r"page punchers|mcfarlane\s+dc\s+direct", bl):
        return "mcfarlane"
    if re.search(r"mcfarlane|dc multiverse", bl) and not re.search(r"marvel legends", bl):
        return "mcfarlane"
    # Classic DC Direct / DC Collectibles (vendor or title; not McFarlane)
    if re.match(r"dc\s*(direct|collectibles)\b", vendor, re.I) or (
        re.search(r"dc\s*direct|dc\s*collectibles", bl)
        and not re.search(r"mcfarlane|page punchers|dc multiverse", bl)
    ):
        return "dcdirect"
    if re.search(r"robot spirits", bl):
        return "bandai"
    if re.search(r"\bhiya\b", bl):
        return "hiya"
    if re.search(r"threezero|three zero", bl):
        return "threezero"
    if re.search(r"\bneca\b", bl):
        return "neca"
    if re.search(r"\bsuper7\b", bl):
        return "super7"
    if re.search(
        r"four horsemen|mythic legions|cosmic legions|figura obscura|infinite legions",
        bl,
    ):
        return "fourhorsemen"
    if re.search(r"joytoy|joy toy", bl):
        return "joytoy"
    if re.search(r"hot toys", bl):
        return "hottoys"
    if re.search(r"\bkaiyodo\b|revoltech|amazing yamaguchi|\bkayodo\b", bl):
        return "kaiyodo"
    # Loyal Subjects — require explicit cue (bare "bst" false-hits Clawful/Webstor)
    if re.search(r"loyal subjects|bst axn|the loyal subjects", bl):
        return "loyalsubjects"
    if re.search(r"\bplaymates\b", bl):
        return "playmates"
    # TMNT / Exo-Squad without NECA/Super7/TLS/Mattel MotU cues → Playmates
    if re.search(r"teenage mutant|\btmnt\b|ninja turtle|exo.?squad", bl) and not re.search(
        r"\bneca\b|\bsuper7\b|loyal subjects|bst axn|mcfarlane|mondo|"
        r"\bmattel\b|masters of the universe|motu|turtles of grayskull",
        bl,
    ):
        return "playmates"
    if re.search(r"\bjakks\b", bl):
        return "jakks"
    # Kenner Super Powers / vintage Kenner AF (not Hasbro "Kenner Classics" Ghostbusters)
    if re.search(r"\bkenner\b", bl) and not re.search(r"kenner classics|hasbro", bl):
        if re.search(r"super powers|batman|action figure|figure", bl):
            return "kenner"
    if re.search(r"\bfigma\b", bl) or re.search(r"good smile", bl) and re.search(r"\bfigma\b", bl):
        return "figma"
    if re.search(r"beast kingdom", bl):
        return "beastkingdom"
    if re.search(r"diamond select", bl):
        return "diamondselect"
    if re.search(r"\bjada\b", bl):
        return "jada"
    if re.search(r"\bblokees\b", bl):
        return "blokees"
    if re.search(r"yolo\s*park|\byolopark\b", bl) or (
        re.search(r"\bamk\b", bl) and re.search(r"transformers|beast wars|voltes|shurato", bl)
    ):
        return "yolopark"
    if re.search(r"\bsoskill\b|so\s*skill", bl):
        return "soskill"
    # Mattel AF lines (shop.mattel / retailers) — dolls skipped via RETAILER_SKIP
    if re.search(
        r"masterverse|motu origins|masters of the universe|\bwwe\b|hammond collection|"
        r"jurassic world.*(?:action )?figure|dc (?:universe|comics) unlimited|"
        r"dc premier",
        bl,
    ):
        if re.search(
            r"mattel|masters of the universe|\bwwe\b|jurassic|hammond|dc universe|dc premier",
            bl,
        ):
            return "mattel"
    return None


def fetch_retailer_products(feed: dict) -> list[dict]:
    """Paginate a retailer with larger page size (image-index only)."""
    from figure_oneshot.shopify_dump import fetch_page

    path = feed.get("productsPath") or "/products.json"
    limit = int(feed.get("pageLimit") or 250)
    max_pages = int(feed.get("maxPages") or 40)
    out: list[dict] = []
    for page in range(1, max_pages + 1):
        products = fetch_page(feed["baseUrl"], path, page, limit=limit)
        if products is None or not products:
            break
        out.extend(products)
        if len(products) < limit:
            break
        time.sleep(0.85)
    return out


def index_entries_from_products(products: list[dict], source_id: str, company_for) -> list[dict]:
    """Build index rows; company_for(p) -> company or None."""
    index: list[dict] = []
    seen: set[str] = set()
    for p in products:
        company = company_for(p)
        if not company:
            continue
        img = image_from_product(p)
        if not img:
            continue
        title = str(p.get("title") or "").strip()
        if not title:
            continue
        handle = str(p.get("handle") or title)
        pid = f"{source_id}:{handle}"[:120]
        if pid in seen:
            continue
        seen.add(pid)
        if " | " in title:
            segs = [x.strip() for x in title.split(" | ") if x.strip()]
            right = segs[-1]
            left = " | ".join(segs[:-1])
            name = (right.split(":")[0].strip() or right)
            subtitle = left or str(p.get("product_type") or source_id)
        elif " - " in title:
            left, right = title.rsplit(" - ", 1)
            # Prefer character on the right for retailer "Line - Character" titles
            if len(right) < 80 and not re.search(r"marvel legends|black series|classified", right, re.I):
                name, subtitle = right.strip(), left.strip()
            else:
                name, subtitle = left.strip(), right.strip()
        else:
            parts = re.split(r"\s+[—–]\s+", title)
            if len(parts) >= 2:
                name, subtitle = parts[0].strip(), " - ".join(parts[1:]).strip()
            else:
                colon = title.split(":")
                if len(colon) >= 2 and len(colon[0]) < 48:
                    name, subtitle = colon[0].strip(), ":".join(colon[1:]).strip()
                else:
                    name, subtitle = title, str(p.get("product_type") or source_id)
        # Prefer character-forward name for noisy retailer titles
        charish = product_character_text(name, subtitle, title)
        # If character helper returned a useful lead token sequence shorter than full title, use it
        lead = (charish.split(title)[0] if title and title in charish else charish).strip()
        if lead and 2 < len(lead) < len(title) and not re.search(
            r"^(amazing yamaguchi|revoltech|mythic legions|cosmic legions|infinite legions)\b",
            lead,
            re.I,
        ):
            # Keep original title as subtitle context when we peel a character
            if len(lead) <= 80 and lead.lower() != name.lower():
                subtitle = f"{name} {subtitle}".strip()[:160]
                name = lead[:160]
        index.append(
            {
                "id": pid,
                "shop": source_id,
                "company": company,
                "name": name[:160],
                "subtitle": subtitle[:160],
                "line": str(p.get("product_type") or p.get("vendor") or source_id)[:80],
                "tags": tag_list(p.get("tags"))[:12],
                "title": title[:240],
                "imageUrl": img,
            }
        )
    return index


def build_index_from_live() -> list[dict]:
    """Paginate Shopify products into a searchable image index."""
    index: list[dict] = []
    seen: set[str] = set()
    for source in STOREFRONTS:
        products = fetch_all_products(source)
        kept = 0
        for p in products:
            if not is_figure_like(p, source):
                continue
            img = image_from_product(p)
            if not img:
                continue
            title = str(p.get("title") or "").strip()
            if not title:
                continue
            handle = str(p.get("handle") or title)
            pid = f"{source['id']}:{handle}"[:120]
            if pid in seen:
                continue
            seen.add(pid)
            # Lightweight name/subtitle split mirroring shopify_dump (incl. pipe titles)
            if " | " in title:
                segs = [x.strip() for x in title.split(" | ") if x.strip()]
                right = segs[-1]
                left = " | ".join(segs[:-1])
                name = (right.split(":")[0].strip() or right)
                subtitle = left or str(p.get("product_type") or source["id"])
            else:
                parts = re.split(r"\s+[—–-]\s+", title)
                if len(parts) >= 2:
                    name, subtitle = parts[0].strip(), " - ".join(parts[1:]).strip()
                else:
                    colon = title.split(":")
                    if len(colon) >= 2 and len(colon[0]) < 48:
                        name, subtitle = colon[0].strip(), ":".join(colon[1:]).strip()
                    else:
                        name, subtitle = title, str(p.get("product_type") or source["id"])
            index.append(
                {
                    "id": pid,
                    "shop": source["id"],
                    "company": source["company"],
                    "name": name[:160],
                    "subtitle": subtitle[:160],
                    "line": str(p.get("product_type") or p.get("vendor") or source["id"])[:80],
                    "tags": tag_list(p.get("tags"))[:12],
                    "title": title[:240],
                    "imageUrl": img,
                }
            )
            kept += 1
        print(f"index {source['id']}: raw={len(products)} with_image={kept}")
        time.sleep(0.05)
    # Specialty retailers — vendor→company (Hasbro / Mezco / MAFEX / SHF / Storm / …)
    for feed in RETAILER_FEEDS:
        products = fetch_retailer_products(feed)
        entries = index_entries_from_products(products, feed["id"], infer_retailer_company)
        added = 0
        for e in entries:
            if e["id"] in seen:
                continue
            seen.add(e["id"])
            index.append(e)
            added += 1
        print(f"index {feed['id']}: raw={len(products)} mapped={added}")
        time.sleep(0.05)
    return index


def build_index_from_oneshot(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        if r.get("source") != "shopify" or not r.get("imageUrl"):
            continue
        out.append(
            {
                "id": r["id"],
                "shop": next((t for t in (r.get("tags") or []) if t not in {"archive", "shopify", "figure", r["company"]}), r["company"]),
                "company": r["company"],
                "name": r["name"],
                "subtitle": r["subtitle"],
                "line": r["line"],
                "tags": r.get("tags") or [],
                "title": f"{r['name']} {r['subtitle']}",
                "imageUrl": r["imageUrl"],
            }
        )
    return out


def enrich_index(entries: list[dict]) -> None:
    for p in entries:
        char = product_character_text(p["name"], p["subtitle"], p.get("title") or "")
        p["_char"] = norm(char)
        p["_title"] = norm(p.get("title") or f"{p['name']} {p['subtitle']}")
        p["_blob"] = norm(
            f"{p['name']} {p['subtitle']} {p['line']} {' '.join(p.get('tags') or [])} {p.get('title') or ''}"
        )
        p["_char_toks"] = set(tokens(char))


def score_pair(fig: dict, prod: dict) -> float:
    if fig["company"] != prod["company"]:
        return -1.0
    fam = line_family(fig["line"], fig["company"])
    if fam in BLOCKED_FAMILIES:
        return -1.0
    req = FAMILY_REQUIRE.get(fam)
    if req and not req.search(prod["_blob"]):
        return -1.0

    match_name = figure_match_name(fig["name"])
    fn = significant_name_tokens(match_name)
    if not fn:
        return -1.0

    char = prod["_char"]
    char_toks = prod["_char_toks"]
    title = prod["_title"]

    # Figure name must live in the character-focused text (not franchise-only title).
    fname = norm(match_name)
    # Joined-token fallback (Boss Borot ↔ bossborot, Trap Jaw ↔ trapjaw)
    joined = "".join(fn)
    contiguous = fname in char or fname in title or joined in char.replace(" ", "")
    # Require token set / word-boundary hits — avoid "he" ⊂ "the", "man" ⊂ "human"
    covered = [
        t
        for t in fn
        if t in char_toks or (len(t) >= 4 and re.search(rf"\b{re.escape(t)}\b", char))
    ]
    if not covered and joined and joined in char.replace(" ", ""):
        covered = list(fn)
    if not covered:
        return -1.0
    if len(covered) < max(1, (len(fn) + 1) // 2):
        return -1.0
    # Multi-token names: a lone shared honorific/first-name is not enough
    # (Mr Terrific≠Mr Freeze, Captain UK≠Captain America, Thor Endgame≠Thor Jane Foster)
    if len(fn) >= 2 and len(covered) == 1 and not contiguous:
        return -1.0
    # First significant token must appear in character text (or joined compound hit)
    if fn[0] not in char_toks and fn[0] not in char and not (joined and joined in char.replace(" ", "")):
        return -1.0
    if len(fn) == 1 and fn[0] in WEAK and not contiguous:
        return -1.0
    # Single-token names: must be primary character (reject Warrior⊂Spartan Warrior, Pirate⊂Space Pirate)
    if len(fn) == 1:
        prod_name_toks = significant_name_tokens(prod.get("name") or "")
        prod_sub_toks = significant_name_tokens(prod.get("subtitle") or "")
        primary = prod_name_toks or prod_sub_toks
        # Character may trail franchise tokens ("Masterverse Teela", "X-Men Magneto")
        if primary and fn[0] not in primary and set(fn) != set(primary):
            if fname != norm(prod.get("name") or "") and fname != norm(prod.get("subtitle") or ""):
                return -1.0

    # Anti false-positive: if product looks like line-header + other character,
    # require figure name in subtitle/character prominently.
    if LINE_AS_NAME.search(prod["name"]) and prod.get("subtitle"):
        sub_n = norm(prod["subtitle"])
        if fname not in sub_n and not all(t in set(tokens(prod["subtitle"])) for t in fn):
            # allow if name is in full MotU-style product name (Keldor at end)
            if fname not in norm(prod["name"]) and not all(t in set(tokens(prod["name"])) for t in fn):
                return -1.0

    name_score = 0.0
    if contiguous:
        name_score += 12
    name_score += 8 * len(covered) / len(fn)
    if fname == norm(prod["name"]) or fname == norm(prod.get("subtitle") or ""):
        name_score += 6
    # First-name product titles for multi-token figures (Ash ← Ash Evil Dead / Ash Williams)
    prod_primary = significant_name_tokens(prod.get("name") or "") or significant_name_tokens(
        prod.get("subtitle") or ""
    )
    if len(fn) >= 2 and prod_primary and prod_primary[0] == fn[0] and fn[0] in covered:
        name_score += 8
        contiguous = True
    # Character token present anywhere in product primary tokens
    if len(fn) == 1 and prod_primary and fn[0] in prod_primary:
        name_score += 3

    raw_fs = [t for t in tokens(fig["subtitle"]) if t not in WEAK]
    fs = [
        t
        for t in raw_fs
        if t not in SUBTITLE_NOISE
        and not re.match(r"^(?:w|wave)?\d+[a-z]?$", t)
        and not re.match(r"^\d{4}$", t)
    ]
    # Distinguishing subtitle/wave tokens (Hush, Knightfall, wave numbers) — prefer title hits
    wave_toks = [t for t in raw_fs if re.match(r"^(?:w|wave)?\d+[a-z]?$", t)]
    dist_toks = list(dict.fromkeys(fs + wave_toks))
    if fs:
        hits = sum(1 for t in fs if t in char or t in prod["_blob"])
        sub_score = 5.0 * hits / max(1, len(fs))
        # Meaningful subtitle cues only (ignore Wave6 / Exclusive densify noise).
        # Narrow exception: Classified role titles (Dog Handler, Artillery) and MotU
        # Origins pack cues (Minicomic Collection) rarely appear on specialty retailer
        # titles once the character name already matches contiguously + line family gate.
        if len(fs) >= 2 and hits == 0:
            if fam in {"classified", "origins", "masterverse", "marvel-legends", "black-series", "studio-series", "lightning"} and contiguous:
                sub_score = 0.0  # soft miss — keep name/line score; do not invent a match
            else:
                return -1.0
    else:
        sub_score = 1.5 if raw_fs else 1.0
    if dist_toks:
        title_hits = sum(1 for t in dist_toks if t in prod["_title"] or t in prod["_blob"])
        sub_score += 6.0 * title_hits / max(1, len(dist_toks))
        # Strong bonus when every distinguishing token appears in the product title
        if title_hits == len(dist_toks) and fs:
            sub_score += 4.0
        # Soft penalty: figure has specific subtitle tokens but product title misses all of them
        if fs and title_hits == 0:
            sub_score -= 2.5

    line_score = 4.0 if req and req.search(prod["_blob"]) else 1.0
    if re.search(r"\b(accessories|empty box|backdrop|stand only)\b", prod["_blob"]):
        return -1.0
    # Kids costume multipacks / novelty bundles are weak product photos for catalog AF
    if re.search(r"ben cooper|costume kids|costumed action figure bundle", prod["_blob"]):
        return -1.0
    # "X as Character" crossovers only if figure line/subtitle mentions crossover partner
    if re.search(r"\bas\b.+(dracula|frankenstein|mummy|wolf|creature|bride)", prod["_title"]) or re.search(
        r"(tmnt|turtle).*(x|as).*(universal|dracula|frankenstein)", prod["_blob"]
    ):
        fig_l = norm(f"{fig.get('line','')} {fig.get('subtitle','')} {' '.join(fig.get('tags') or [])}")
        if "tmnt" not in fig_l and "turtle" not in fig_l and "crossover" not in fig_l:
            return -1.0
    # Castlevania / game lines must appear on product
    if "castlevania" in norm(f"{fig['subtitle']} {fig['line']}"):
        if "castlevania" not in prod["_blob"]:
            return -1.0
    # Generic densify class names: product primary name must equal the class token exactly
    gname = norm(figure_match_name(fig["name"]))
    if re.search(r"^(pirate|knight|warrior|thief|fairy|golem|troll|vampire|werewolf|robot)$", gname):
        prod_name_n = norm(prod.get("name") or "")
        if prod_name_n != gname:
            return -1.0
    if gname == "vitruvian":
        if "vitruvian" not in prod["_blob"]:
            return -1.0
        fig_theme = norm(fig.get("subtitle") or "")
        themes = [t for t in ("fantasy", "superhero", "horror", "military", "sci") if t in fig_theme]
        if themes and not any(t in prod["_blob"] for t in themes):
            return -1.0
    # Soft-goods / packaging-only curated rows — no honest figure photo match
    if re.search(r"\bsoft goods\b|softgoods|empty box|backdrop", norm(fig["name"] + " " + fig["subtitle"])):
        return -1.0
    if re.search(r"\beffect\b|accessories|display stand|empty box", norm(fig["name"] + " " + fig["line"])):
        if not re.search(r"\beffect\b|accessories|display stand", prod["_blob"]):
            return -1.0
    # Skip junk curated placeholders
    if re.search(r"^(special exclusive|additional fees|to b order|series \d+)$", norm(fig["name"])):
        return -1.0
    # Hiya Godzilla family: require kaiju cue on product when figure line is Godzilla
    if fam == "hiya-godzilla":
        if not re.search(r"godzilla|kong|ghidorah|mechagodzilla|shimo|mothra|rodan", prod["_blob"]):
            return -1.0
    # EXO-6: skip mixed-media statues unless curated line says statue
    if fig["company"] == "exo6":
        if re.search(r"\bmixed media statue\b", prod["_blob"]) and "statue" not in norm(fig["line"]):
            return -1.0
    # Star Ace: DefoStyle soft vinyl vs 1/6 AF gate
    if fig["company"] == "starace":
        fig_l = norm(fig.get("line") or "")
        if ("1/6" in fig_l or "1:6" in fig_l or "sixth" in fig_l) and "defostyle" in prod["_blob"]:
            if "1/6" not in prod["_blob"] and "1:6" not in prod["_blob"]:
                return -1.0
        if ("defostyle" in fig_l or "soft vinyl" in fig_l) and "defostyle" not in prod["_blob"] and "soft vinyl" not in prod["_blob"]:
            return -1.0
    # Blitzway line gates
    if fig["company"] == "blitzway":
        fig_l = norm(f"{fig['name']} {fig['line']} {fig['subtitle']}")
        if "carbotix" in fig_l and "carbotix" not in prod["_blob"] and "carbote" not in prod["_blob"]:
            return -1.0
        if "figure complex" in fig_l and "figure complex" not in prod["_blob"]:
            if not re.search(r"mazinger|getter|bossborot|aphrodite", prod["_blob"]):
                return -1.0
    # Blokees franchise cues
    if fig["company"] == "blokees":
        fig_l = norm(f"{fig['line']} {fig['subtitle']} {' '.join(fig.get('tags') or [])}")
        if "transformer" in fig_l and "transformer" not in prod["_blob"]:
            return -1.0
        if "ultraman" in fig_l and "ultraman" not in prod["_blob"]:
            return -1.0
        if "mega man" in fig_l and "mega man" not in prod["_blob"] and "megaman" not in prod["_blob"]:
            return -1.0
    # Hasbro line hard gates (retailer titles are noisy)
    if fig["company"] == "hasbro":
        fig_l = norm(f"{fig['line']} {fig['subtitle']} {' '.join(fig.get('tags') or [])}")
        if fam == "marvel-legends" and "marvel legends" not in prod["_blob"]:
            return -1.0
        if fam == "black-series" and "black series" not in prod["_blob"]:
            return -1.0
        if fam == "classified" and not re.search(r"classified|g\.?i\.?\s*joe", prod["_blob"]):
            return -1.0
        if fam == "studio-series" and "studio series" not in prod["_blob"]:
            return -1.0
        if fam == "lightning" and "lightning" not in prod["_blob"]:
            return -1.0
        if fam == "tf-masterpiece":
            if "masterpiece" not in prod["_blob"]:
                return -1.0
            if "studio series" in prod["_blob"] and "masterpiece" not in prod["_blob"]:
                return -1.0
        # Reject roleplay / titanium static / packaging-only
        if re.search(r"roleplay|life size|prop replica|titanium|die cast|static figure", prod["_blob"]):
            return -1.0
    # Mezco One:12
    if fig["company"] == "mezco":
        if not re.search(r"one:?12|mezco", prod["_blob"]):
            return -1.0
        if re.search(r"\b(poster|apparel|pin)\b", prod["_blob"]):
            return -1.0
    # MAFEX
    if fig["company"] == "mafex":
        if "mafex" not in prod["_blob"]:
            return -1.0
    # S.H.Figuarts
    if fig["company"] == "shfiguarts":
        if "figuarts" not in prod["_blob"]:
            return -1.0
        if "figuarts zero" in prod["_blob"]:
            return -1.0
    # Storm Collectibles
    if fig["company"] == "storm":
        # Prefer Storm-titled products; allow franchise cues when shop is storm-hk
        if "storm" not in prod["_blob"] and not re.search(
            r"street fighter|mortal kombat|tekken|king of fighters|baki|final fight|darkstalkers",
            prod["_blob"],
        ):
            return -1.0
        # WWE Elite curated should not take LJN / Superstars-only product shots
    if fig["company"] == "mattel" and "elite" in norm(fig["line"]):
        if re.search(r"\bljn\b", prod["_blob"]) and "elite" not in prod["_blob"]:
            return -1.0

    # Single-token figure vs hyphen-prefixed product character (Viper ← S.A.W.-Viper / Techno-Viper)
    # Space prefixes like "Figure Complex Wolverine" / "X-Men Magneto" are NOT rejects.
    if len(fn) == 1:
        fig_name_raw = (fig.get("name") or "").strip()
        title_raw = prod.get("title") or prod.get("name") or ""
        pref = re.search(
            rf"(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9\.]{{0,20}})[-]+{re.escape(fig_name_raw)}\b",
            title_raw,
            re.I,
        )
        if pref:
            prefix = re.sub(r"[^a-z0-9]", "", pref.group(1).lower())
            # Generic line words — not distinguishing character prefixes
            allow_prefix = {
                "cobra", "the", "joe", "gi", "gijoe", "marvel", "legends", "series",
                "figure", "action", "exclusive", "retro", "classified", "black",
                "studio", "lightning", "hasbro", "star", "wars", "transformers",
            }
            fig_ctx = set(tokens(fig.get("subtitle") or "")) | set(tokens(fig.get("line") or ""))
            fig_ctx_compact = {re.sub(r"[^a-z0-9]", "", t) for t in fig_ctx}
            if prefix and len(prefix) >= 2 and prefix not in allow_prefix and prefix not in fig_ctx and prefix not in fig_ctx_compact:
                return -1.0
    # Short single-token names: require whole-token match in character text (not Gizmo⊂Gizmoduck)
    if len(fn) == 1 and len(fn[0]) <= 6:
        if fn[0] not in char_toks:
            return -1.0
        # reject if only matches inside a longer compound token already handled by char_toks
        # also reject when product title clearly different character compound
        for ct in char_toks:
            if ct != fn[0] and fn[0] in ct and len(ct) > len(fn[0]) + 1:
                # e.g. gizmo in gizmoduck — char_toks has gizmoduck not gizmo, so OK;
                # if tokenizer splits wrong, still guard contiguous word boundary:
                pass
        if not re.search(rf"\b{re.escape(fn[0])}\b", char):
            return -1.0

    # Franchise / line cues for NECA curated rows
    fig_blob = norm(f"{fig['name']} {fig['subtitle']} {fig['line']} {' '.join(fig.get('tags') or [])}")
    if fig["company"] == "neca":
        # Universal Monsters: require universal monsters (reject TMNT crossover / Ben Cooper kids unless stated)
        if "universal" in fig_blob or fam == "neca" and "monster" in norm(fig.get("line") or ""):
            if "universal monster" in fig_blob or "universal monsters" in norm(fig.get("line") or ""):
                if "universal monster" not in prod["_blob"]:
                    return -1.0
                if re.search(r"\btmnt\b|ninja turtle|ben cooper", prod["_blob"]) and "universal monster" in prod["_blob"] and "x" in prod["_title"]:
                    # allow official UM x TMNT only if figure subtitle hints crossover — else reject
                    if "tmnt" not in fig_blob and "turtle" not in fig_blob:
                        return -1.0
        # Aliens / Predator / Halloween / IT cues
        for cue, rx in (
            ("alien", re.compile(r"\baliens?\b|xenomorph|bishop|ripley|hicks", re.I)),
            ("predator", re.compile(r"\bpredator\b", re.I)),
            ("halloween", re.compile(r"halloween|laurie|myers|loomis", re.I)),
            ("pennywise", re.compile(r"pennywise|\bit\b|derry", re.I)),
            ("evil dead", re.compile(r"evil dead|\bash\b", re.I)),
        ):
            if cue in fig_blob or (cue == "pennywise" and "pennywise" in fig_blob):
                if cue == "alien" and re.search(r"\baliens?\b", fig_blob):
                    if not re.search(r"\baliens?\b|xenomorph", prod["_blob"]):
                        return -1.0
                    # reject "Ben Bishop" false positive
                    if "bishop" in fname and "ben bishop" in prod["_blob"] and not re.search(r"\baliens?\b", prod["_blob"]):
                        return -1.0
                if cue == "halloween" and "halloween" in fig_blob:
                    if "halloween" not in prod["_blob"]:
                        return -1.0
                if cue == "pennywise" and "pennywise" in fig_blob:
                    if "pennywise" not in prod["_blob"] and not re.search(r"\bit\b", prod["_blob"]):
                        return -1.0

    # McFarlane / shop.dc: leading CHARACTER (variant) titles — figure must match lead, not parenthetical
    if fig["company"] == "mcfarlane":
        m = re.match(
            r"^([A-Z0-9][A-Za-z0-9\'\.\- ]+?)\s*(?:\(|McFarlane|DC Multiverse)",
            prod.get("title") or prod.get("name") or "",
        )
        if m:
            lead = norm(m.group(1))
            if fname not in lead and not all(t in set(tokens(lead)) for t in fn):
                return -1.0
    # Super7 franchise cues when curated line/subtitle is explicit
    if fig["company"] == "super7":
        fig_l = norm(f"{fig['line']} {fig['subtitle']} {' '.join(fig.get('tags') or [])}")
        for cue, rx in (
            ("gi joe", re.compile(r"g\.?i\.?\s*joe|cobra|classified", re.I)),
            ("thundercat", re.compile(r"thundercat", re.I)),
            ("tmnt|turtle", re.compile(r"tmnt|ninja turtle|teenage mutant", re.I)),
            ("conan", re.compile(r"\bconan\b", re.I)),
            ("motu|masters of the universe|he-man", re.compile(r"masters of the universe|\bmotu\b|masterverse", re.I)),
        ):
            if re.search(cue, fig_l):
                if not rx.search(prod["_blob"]):
                    return -1.0
    # King Kong / Kong figures should not take Godzilla-primary product shots
    if re.search(r"\b(king )?kong\b", fname) or re.search(r"\bkong\b", norm(fig["name"])):
        if re.search(r"\bgodzilla\b", prod["_title"]) and not re.search(r"\bkong\b", prod["_char"]):
            return -1.0
        if re.search(r"godzilla vs\.? kong|godzilla x kong", prod["_blob"]) and re.search(r"godzilla action", prod["_blob"]):
            # product is the Godzilla SKU from a vs/x set
            if not re.search(r"\bkong\b", norm(prod.get("name") or "") + " " + char):
                return -1.0
    # Kaiyodo / Yamaguchi / Revoltech
    if fig["company"] == "kaiyodo":
        if not re.search(r"kaiyodo|revoltech|yamaguchi", prod["_blob"]):
            return -1.0
    # Four Horsemen lines
    if fig["company"] == "fourhorsemen":
        if not re.search(
            r"mythic legions|cosmic legions|figura obscura|infinite legions|four horsemen",
            prod["_blob"],
        ):
            return -1.0
    # Playmates
    if fig["company"] == "playmates":
        if not re.search(r"playmates|tmnt|turtle|exo.?squad|teenage mutant", prod["_blob"]):
            return -1.0
        fig_l = norm(f"{fig['name']} {fig['subtitle']} {fig['line']}")
        # Giant 12" / Turtle Tots / Storage Shell ≠ standard 4.5–5" classic
        if re.search(r"\bgiant\b|12\s*\"\s*figure|storage shell", prod["_blob"]) and not re.search(
            r"giant|storage|12\"", fig_l
        ):
            return -1.0
        if re.search(r"turtle tots|tots raph|tots leo|tots mikey|tots don", prod["_blob"]) and "tot" not in fig_l:
            return -1.0
        if "exo" in fig_l or "exo-squad" in fig_l or "exosquad" in fig_l:
            if not re.search(r"exo.?squad", prod["_blob"]):
                return -1.0
        if re.search(r"soft head", fig_l) and not re.search(r"soft head|soft.?head", prod["_blob"]):
            # allow classic soft-head when product is classic turtle without hard-head cue
            if re.search(r"hard head|mutant mayhem|tales of", prod["_blob"]):
                return -1.0
    # JAKKS
    if fig["company"] == "jakks":
        if not re.search(r"jakks", prod["_blob"]):
            return -1.0
    # Toy Biz (never Hasbro-only ML packaging)
    if fig["company"] == "toybiz":
        if not re.search(r"toy\s*biz|toybiz", prod["_blob"]):
            return -1.0
    # Classic DC Direct / Collectibles
    if fig["company"] == "dcdirect":
        if not re.search(r"dc direct|dc collectibles", prod["_blob"]):
            return -1.0
        if re.search(r"page punchers|mcfarlane\s+dc\s+direct", prod["_blob"]):
            return -1.0
    # Kenner
    if fig["company"] == "kenner":
        if not re.search(r"kenner|super powers", prod["_blob"]):
            return -1.0
        if re.search(r"kenner classics", prod["_blob"]) and "super powers" not in prod["_blob"]:
            return -1.0
    # Loyal Subjects / BST AXN
    if fig["company"] == "loyalsubjects":
        if not re.search(r"loyal subjects|bst axn|the loyal subjects", prod["_blob"]):
            return -1.0
        # BST AXN curated should not take CheeBee / MASK vehicle-only / Angry Birds
        fig_l = norm(f"{fig['line']} {fig['subtitle']}")
        if "bst" in fig_l or "axn" in fig_l:
            if re.search(r"cheebee|angry birds|strawberry shortcake|teletubbies", prod["_blob"]):
                return -1.0
            if re.search(r"\bm\.?a\.?s\.?k\b|mask thunderhawk|mask condor", prod["_blob"]) and "mask" not in fig_l:
                return -1.0
    # Skip obvious Mattel DC Premier mismatches for non-Premier curated lines
    fig_line = norm(fig["line"])
    if fig["company"] == "mattel" and "premier" in prod["_blob"]:
        if "premier" not in fig_line and "total heroes" not in fig_line:
            if fam not in {"wwe", "masterverse", "origins", "jurassic", "motu-generic"}:
                return -1.0

    # Color antonyms: Red Ninja must not take Blue Ninja product art
    fig_colors = COLOR_WORDS & set(tokens(fig["name"] + " " + fig.get("subtitle", "")))
    prod_colors = COLOR_WORDS & set(tokens((prod.get("name") or "") + " " + (prod.get("title") or "")))
    if fig_colors and prod_colors and fig_colors.isdisjoint(prod_colors):
        return -1.0

    # Distinct character compounds / alter-egos
    fig_ctx = norm(f"{fig['name']} {fig.get('subtitle','')} {fig.get('line','')}")
    if re.search(r"miles\s+morales|spider\s*gwen|ghost\s*spider", prod["_blob"]) and not re.search(
        r"miles|gwen|ghost\s*spider", fig_ctx
    ):
        if re.search(r"spider\s*man|spiderman", fname) or fname in {"spider man", "spiderman"}:
            return -1.0
    if re.search(r"who\s*laughs", prod["_blob"]) and "laugh" not in fig_ctx:
        return -1.0
    if re.search(r"old\s*man\s*logan", prod["_blob"]) and not re.search(r"old\s*man|logan", fig_ctx):
        if "wolverine" in fname and "logan" not in fig_ctx:
            return -1.0

    total = name_score + sub_score + line_score
    if not contiguous and sub_score < 2.5:
        return -1.0
    return total


def parse_seed_ids_needing_images() -> list[dict]:
    """Pull seed tuples from figures.ts that have no baked URL yet (best-effort)."""
    # Archive is primary; seed gaps get overlay via id if we can match by reading archive+need only.
    # Seed figures without images are already partially duplicated in curated densify; skip TS parse.
    return []


def heuristic_keep_score(fig: dict) -> float:
    """Fallback ranking when no index product is available for a shared URL."""
    sc = 0.0
    src = str(fig.get("source") or "")
    if src == "shopify":
        sc += 80
    elif src == "curated":
        sc += 40
    elif "densify" in src:
        sc -= 15
    if "image-bake" not in (fig.get("tags") or []) and fig.get("imageUrl"):
        sc += 25  # native/shopify bake-less URL
    sub = (fig.get("subtitle") or "").strip()
    if sub:
        st = [t for t in tokens(sub) if t not in SUBTITLE_NOISE and t not in WEAK]
        sc += min(40, 4 * len(st) + len(sub) / 4)
        if re.search(r"\b(hush|knightfall|year one|long halloween|flashpoint|hush blue)\b", sub, re.I):
            sc += 12
    else:
        sc -= 5
    rd = str(fig.get("releaseDate") or "9999")[:4]
    try:
        sc += max(0, 2100 - int(rd)) / 10
    except ValueError:
        pass
    return sc


def enforce_unique_image_urls(rows: list[dict], index: list[dict], urls: dict[str, str]) -> int:
    """If any imageUrl is on multiple oneshot rows, keep the best-scoring match and clear others."""
    by_url: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        u = r.get("imageUrl")
        if u:
            by_url[u].append(r)
    # Index products by imageUrl for scoring
    prod_by_url: dict[str, list[dict]] = defaultdict(list)
    for p in index:
        u = p.get("imageUrl")
        if u:
            prod_by_url[u].append(p)

    cleared = 0
    for url, group in by_url.items():
        if len(group) < 2:
            continue
        prods = prod_by_url.get(url) or []
        ranked: list[tuple[float, dict]] = []
        for fig in group:
            best = -1.0
            for p in prods:
                if p.get("company") and p["company"] != fig["company"]:
                    continue
                s = score_pair(fig, p)
                if s > best:
                    best = s
            if best < 0:
                best = heuristic_keep_score(fig)
            else:
                # Tie-break with heuristic so shopify / specific subtitle wins close scores
                best += heuristic_keep_score(fig) / 1000.0
            ranked.append((best, fig))
        ranked.sort(key=lambda x: x[0], reverse=True)
        # Keep winner; clear losers
        for _, fig in ranked[1:]:
            fig.pop("imageUrl", None)
            tags = [t for t in (fig.get("tags") or []) if t != "image-bake"]
            fig["tags"] = tags
            urls.pop(fig["id"], None)
            cleared += 1
    return cleared




FAKE_SKU_RE = re.compile(
    r"^(unknown|n/?a|none|null|todo|tbd|-+|\.+|0+|sku|test|placeholder)$",
    re.I,
)


def clean_sku_value(raw) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or FAKE_SKU_RE.match(s):
        return None
    if not re.search(r"[A-Za-z0-9]", s):
        return None
    if len(s) > 64:
        return None
    return s


def build_sku_to_image_entry(sku_index: list[dict]) -> dict[str, dict]:
    """Map uppercase SKU → a representative product entry with imageUrl.

    Same SKU can appear on multiple specialty feeds with different CDN hosts
    (and occasionally a wrong pack shot). Callers that have a figure context
    should use `pick_best_sku_product` to choose among `sku_to_products` instead.
    This single-map helper prefers first-party, then earlier shop id.
    """
    best: dict[str, dict] = {}
    tier_rank = {"first-party": 0, "retailer": 1}

    def rank(e: dict) -> tuple:
        return (
            tier_rank.get(str(e.get("tier") or ""), 9),
            0 if e.get("imageUrl") else 1,
            str(e.get("shop") or ""),
        )

    for raw in sku_index:
        url = raw.get("imageUrl")
        if not url or not str(url).startswith("http"):
            continue
        # Index by GTIN primary and listingSku so legacy listing primaries still
        # rematch photos off the exact storefront code (aliases stay secondary).
        codes = []
        for field in ("sku", "listingSku"):
            c = clean_sku_value(raw.get(field))
            if c and c not in codes:
                codes.append(c)
        if not codes:
            continue
        for sku in codes:
            key = sku.upper()
            entry = dict(raw)
            entry["sku"] = sku
            entry["imageUrl"] = str(url)
            cur = best.get(key)
            if cur is None or rank(entry) < rank(cur):
                best[key] = entry
    return best


def build_sku_to_products(sku_index: list[dict]) -> dict[str, list[dict]]:
    """Map uppercase SKU → all product entries that carry that SKU + imageUrl."""
    out: dict[str, list[dict]] = defaultdict(list)
    seen_url: dict[str, set[str]] = defaultdict(set)
    for raw in sku_index:
        url = raw.get("imageUrl")
        if not url or not str(url).startswith("http"):
            continue
        codes = []
        for field in ("sku", "listingSku"):
            c = clean_sku_value(raw.get(field))
            if c and c not in codes:
                codes.append(c)
        if not codes:
            continue
        u = str(url)
        for sku in codes:
            key = sku.upper()
            if u in seen_url[key]:
                continue
            seen_url[key].add(u)
            entry = dict(raw)
            entry["sku"] = sku
            entry["imageUrl"] = u
            out[key].append(entry)
    return out


def pick_best_sku_product(fig: dict, candidates: list[dict]) -> dict | None:
    """Among products sharing a SKU, prefer title/name match to the figure.

    First-party tier gets a bonus; score_pair breaks retailer pack-shot collisions
    (e.g. Man-Thing barcode reused on an FF 2-pack listing).
    """
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    best: tuple[float, dict] | None = None
    for p in candidates:
        sc = score_pair(fig, p)
        if sc < 0:
            sc = 0.0
        if p.get("tier") == "first-party":
            sc += 50.0
        # Prefer image URL / title that embeds the SKU digits (common on ToyArena)
        sku = clean_sku_value(p.get("sku")) or ""
        blob = f"{p.get('imageUrl') or ''} {p.get('title') or ''} {p.get('handle') or ''}".lower()
        if sku and sku.lower() in blob:
            sc += 8.0
        if best is None or sc > best[0]:
            best = (sc, p)
    return best[1] if best else candidates[0]


def enforce_unique_image_urls_sku_aware(rows: list[dict], urls: dict[str, str]) -> int:
    """Like enforce_unique_image_urls, but SKU-proven (image-sku) rows always win."""
    by_url: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        u = r.get("imageUrl")
        if u:
            by_url[u].append(r)
    cleared = 0
    for url, group in by_url.items():
        if len(group) < 2:
            continue
        ranked: list[tuple[float, dict]] = []
        for fig in group:
            score = heuristic_keep_score(fig)
            if "image-sku" in (fig.get("tags") or []) and clean_sku_value(fig.get("sku")):
                score += 1_000_000.0
            ranked.append((score, fig))
        ranked.sort(key=lambda x: x[0], reverse=True)
        for _, fig in ranked[1:]:
            fig.pop("imageUrl", None)
            tags = [t for t in (fig.get("tags") or []) if t not in ("image-bake", "image-sku")]
            # drop imgsku: provenance tags too
            tags = [t for t in tags if not str(t).startswith("imgsku:")]
            fig["tags"] = tags
            urls.pop(fig["id"], None)
            cleared += 1
    return cleared


def rematch_images_by_sku(
    rows: list[dict],
    sku_to_prod: dict[str, dict],
    *,
    sku_to_products: dict[str, list[dict]] | None = None,
    dry_run: bool = False,
) -> dict:
    """Exact SKU → product imageUrl assignment. Overwrites mismatched prior images.

    Strict 1:1: one imageUrl → one figure; duplicate oneshot SKUs keep the first
    stable id. When two SKUs resolve to the same CDN URL, first-party / earlier
    assignment wins; the other is left unchanged (or emptied if it held the URL).
    """
    # One SKU → one figure (first id wins)
    sku_owner: dict[str, str] = {}
    for r in rows:
        sku = clean_sku_value(r.get("sku"))
        if not sku:
            continue
        sku_owner.setdefault(sku.upper(), r["id"])

    def tier_key(r: dict) -> tuple:
        sku = clean_sku_value(r.get("sku")) or ""
        key = sku.upper()
        if sku_to_products and key in sku_to_products:
            p = pick_best_sku_product(r, sku_to_products[key]) or {}
        else:
            p = sku_to_prod.get(key) or {}
        return (0 if p.get("tier") == "first-party" else 1, r["id"])

    eligible: list[dict] = []
    skipped_dup_sku = 0
    skipped_no_index = 0
    for r in rows:
        sku = clean_sku_value(r.get("sku"))
        if not sku:
            continue
        key = sku.upper()
        if sku_owner.get(key) != r["id"]:
            skipped_dup_sku += 1
            continue
        if key not in sku_to_prod:
            skipped_no_index += 1
            continue
        eligible.append(r)
    eligible.sort(key=tier_key)

    reserved_urls: dict[str, str] = {}  # url → figure id
    changed_mismatch = 0
    filled_empty = 0
    already_correct = 0
    skipped_url_conflict = 0
    samples_changed: list[dict] = []

    def clear_url_holders(url: str, keep_id: str) -> None:
        for other in rows:
            if other["id"] == keep_id:
                continue
            if other.get("imageUrl") != url:
                continue
            # Never clear another SKU-proven reservation
            if reserved_urls.get(url) == other["id"]:
                continue
            if "image-sku" in (other.get("tags") or []) and clean_sku_value(other.get("sku")):
                # Other already SKU-linked to this same URL — conflict handled by reserved
                continue
            other.pop("imageUrl", None)
            tags = [
                t
                for t in (other.get("tags") or [])
                if t not in ("image-bake", "image-sku") and not str(t).startswith("imgsku:")
            ]
            other["tags"] = tags

    for r in eligible:
        sku = clean_sku_value(r.get("sku"))
        assert sku
        key = sku.upper()
        if sku_to_products and key in sku_to_products:
            prod = pick_best_sku_product(r, sku_to_products[key])
            if not prod:
                continue
        else:
            prod = sku_to_prod[key]
        want = prod["imageUrl"]
        have = (r.get("imageUrl") or "").strip()

        owner = reserved_urls.get(want)
        if owner and owner != r["id"]:
            skipped_url_conflict += 1
            continue

        if have == want:
            already_correct += 1
            reserved_urls[want] = r["id"]
            if not dry_run:
                tags = list(r.get("tags") or [])
                if "image-sku" not in tags:
                    tags.append("image-sku")
                if "image-bake" not in tags:
                    tags.append("image-bake")
                shop_tag = f"imgsku:{prod.get('shop')}"
                if shop_tag not in tags and len(tags) < 28:
                    tags.append(shop_tag)
                r["tags"] = tags
            continue

        if dry_run:
            if have:
                changed_mismatch += 1
            else:
                filled_empty += 1
            reserved_urls[want] = r["id"]
            continue

        clear_url_holders(want, r["id"])
        # Re-check after clear in case a SKU-proven peer held it
        if reserved_urls.get(want) and reserved_urls[want] != r["id"]:
            skipped_url_conflict += 1
            continue

        if have:
            changed_mismatch += 1
            if len(samples_changed) < 25:
                samples_changed.append(
                    {
                        "figureId": r["id"],
                        "name": r.get("name"),
                        "sku": sku,
                        "shop": prod.get("shop"),
                        "from": have[:140],
                        "to": want[:140],
                    }
                )
        else:
            filled_empty += 1

        r["imageUrl"] = want
        tags = list(r.get("tags") or [])
        if "image-sku" not in tags:
            tags.append("image-sku")
        if "image-bake" not in tags:
            tags.append("image-bake")
        shop_tag = f"imgsku:{prod.get('shop')}"
        if shop_tag not in tags and len(tags) < 28:
            tags.append(shop_tag)
        r["tags"] = tags
        reserved_urls[want] = r["id"]

    sku_proven_ids = set(reserved_urls.values())
    if not dry_run:
        for r in rows:
            if "image-sku" in (r.get("tags") or []) and r.get("imageUrl"):
                sku_proven_ids.add(r["id"])

    return {
        "eligible": len(eligible),
        "assignedOrConfirmed": already_correct + changed_mismatch + filled_empty,
        "alreadyCorrect": already_correct,
        "changedMismatch": changed_mismatch,
        "filledEmpty": filled_empty,
        "skippedNoIndex": skipped_no_index,
        "skippedUrlConflict": skipped_url_conflict,
        "skippedDupSku": skipped_dup_sku,
        "skuProvenFigureIds": len(sku_proven_ids),
        "reservedUrls": len(reserved_urls),
        "samplesChanged": samples_changed,
        "skuProvenIds": sorted(sku_proven_ids),
    }


def main() -> None:
    fetch_live = "--fetch" in sys.argv or "--live" in sys.argv
    use_cache = "--cache-only" in sys.argv
    rematch = "--rematch" in sys.argv
    sku_first = "--sku-first" in sys.argv or "--sku-rematch" in sys.argv
    sku_only = "--sku-only" in sys.argv
    dry_run = "--dry-run" in sys.argv
    companies_filter = None
    for a in sys.argv:
        if a.startswith("--companies="):
            companies_filter = {x.strip() for x in a.split("=", 1)[1].split(",") if x.strip()}
    # Default: when --sku-first, also allow fuzzy gap-fill unless --sku-only
    min_score = 16.0

    rows = json.loads(ARCHIVE_JSON.read_text())
    before_with = sum(1 for r in rows if r.get("imageUrl"))
    before_total = len(rows)
    sku_rematch_stats: dict | None = None

    if sku_first:
        if not SKU_INDEX_JSON.exists():
            print(f"ERROR: {SKU_INDEX_JSON} missing — run bake-figure-skus.py --fetch first")
            raise SystemExit(1)
        print(f"=== SKU-first image rematch from {SKU_INDEX_JSON.name} ===")
        sku_index = json.loads(SKU_INDEX_JSON.read_text())
        sku_to_prod = build_sku_to_image_entry(sku_index)
        sku_to_products = build_sku_to_products(sku_index)
        # score_pair needs enrich_index fields (_char, etc.)
        flat = [p for group in sku_to_products.values() for p in group]
        enrich_index(flat)
        multi = sum(1 for v in sku_to_products.values() if len(v) > 1)
        print(f"sku→image map size: {len(sku_to_prod)} (multi-CDN SKUs: {multi})")
        rematch_rows = rows
        if companies_filter:
            rematch_rows = [r for r in rows if r.get("company") in companies_filter]
            print(f"SKU-first scoped to {sorted(companies_filter)} ({len(rematch_rows)} rows)")
        sku_rematch_stats = rematch_images_by_sku(
            rematch_rows, sku_to_prod, sku_to_products=sku_to_products, dry_run=dry_run
        )
        print(
            json.dumps(
                {k: sku_rematch_stats[k] for k in (
                    "alreadyCorrect", "changedMismatch", "filledEmpty",
                    "skippedNoIndex", "skippedUrlConflict", "skippedDupSku",
                    "skuProvenFigureIds", "reservedUrls",
                )},
                indent=2,
            )
        )
        if sku_only:
            # Persist SKU rematch only; skip fuzzy
            urls = {r["id"]: r["imageUrl"] for r in rows if r.get("imageUrl")}
            after_with = sum(1 for r in rows if r.get("imageUrl"))
            # Enforce 1:1 among all current URLs; SKU-proven win via image-sku tag boost
            if not dry_run:
                cleared = enforce_unique_image_urls_sku_aware(rows, urls)
                if cleared:
                    print(f"cleared shared imageUrl from {cleared} rows (sku-aware 1:1)")
                urls = {r["id"]: r["imageUrl"] for r in rows if r.get("imageUrl")}
                after_with = sum(1 for r in rows if r.get("imageUrl"))
                URLS_JSON.write_text(json.dumps(urls, indent=2, sort_keys=True) + "\n")
                ARCHIVE_JSON.write_text(json.dumps(rows, indent=2) + "\n")
                stats = {
                    "bakedAt": datetime.now(timezone.utc).isoformat(),
                    "day": date.today().isoformat(),
                    "mode": "sku-only",
                    "before": {"total": before_total, "withImage": before_with, "pct": round(100 * before_with / before_total, 2)},
                    "after": {"total": len(rows), "withImage": after_with, "pct": round(100 * after_with / len(rows), 2)},
                    "skuRematch": {k: v for k, v in sku_rematch_stats.items() if k != "skuProvenIds"},
                    "urlMapSize": len(urls),
                    "sharedUrlsAfter": sum(1 for u, c in Counter(r["imageUrl"] for r in rows if r.get("imageUrl")).items() if c >= 2),
                }
                STATS_JSON.write_text(json.dumps(stats, indent=2) + "\n")
                SKU_REMATCH_STATS_JSON.write_text(json.dumps(stats, indent=2) + "\n")
                print(f"wrote {URLS_JSON} ({len(urls)} urls)")
                print(f"wrote {SKU_REMATCH_STATS_JSON}")
            else:
                print("(dry-run — no files written)")
            return

    if rematch and not sku_first:
        # Drop prior image-bake overlays so we can re-assign under strict 1:1
        # Keep SKU-proven images (image-sku tag) — fuzzy rematch must not wipe them.
        dropped = 0
        for r in rows:
            tags = list(r.get("tags") or [])
            if "image-sku" in tags and r.get("imageUrl"):
                continue
            if "image-bake" in tags and r.get("imageUrl"):
                r.pop("imageUrl", None)
                r["tags"] = [t for t in tags if t != "image-bake"]
                dropped += 1
        print(f"=== Rematch: cleared {dropped} image-bake overlays (kept image-sku) ===")
    need = [r for r in rows if not r.get("imageUrl")]
    if companies_filter:
        need = [r for r in need if r.get("company") in companies_filter]
        print(f"companies filter: {sorted(companies_filter)} need={len(need)}")
    if dry_run and sku_first:
        print("(dry-run after SKU-first — skipping fuzzy persist)")
        return

    if use_cache and INDEX_JSON.exists():
        print(f"=== Using cached index {INDEX_JSON} ===")
        index = json.loads(INDEX_JSON.read_text())
    elif fetch_live:
        print("=== Live Shopify pagination → product image index ===")
        index = build_index_from_live()
        INDEX_JSON.write_text(json.dumps(index, indent=2) + "\n")
        print(f"wrote {INDEX_JSON} ({len(index)} products)")
    else:
        print("=== Index from oneshot Shopify rows (pass --fetch for live) ===")
        index = build_index_from_oneshot(rows)
        # Merge any prior live cache extras
        if INDEX_JSON.exists():
            cached = json.loads(INDEX_JSON.read_text())
            seen = {e["id"] for e in index}
            extra = 0
            for e in cached:
                if e["id"] not in seen and e.get("imageUrl"):
                    index.append(e)
                    seen.add(e["id"])
                    extra += 1
            if extra:
                print(f"merged {extra} cached index entries")

    enrich_index(index)
    by_co: dict[str, list[dict]] = defaultdict(list)
    for p in index:
        by_co[p["company"]].append(p)

    print(f"index size={len(index)} need_images={len(need)} before_pct={100*before_with/before_total:.1f}%")

    cands: list[tuple[float, str, str, dict, dict]] = []
    for fig in need:
        best = None
        best_s = 0.0
        for p in by_co.get(fig["company"], []):
            s = score_pair(fig, p)
            if s > best_s:
                best_s, best = s, p
        if best and best_s >= min_score:
            cands.append((best_s, fig["id"], best["id"], fig, best))

    cands.sort(reverse=True, key=lambda x: x[0])
    used_fig: set[str] = set()
    # Strict 1:1 — one CDN imageUrl assigns to at most ONE figure id (no variant sharing).
    used_urls: set[str] = {r["imageUrl"] for r in rows if r.get("imageUrl")}
    finals: list[tuple[float, dict, dict]] = []
    for s, fid, pid, f, p in cands:
        if fid in used_fig:
            continue
        url = p.get("imageUrl") or ""
        if not url or url in used_urls:
            continue
        used_fig.add(fid)
        used_urls.add(url)
        finals.append((s, f, p))

    # Persist URL map (merge with prior)
    prior_urls: dict[str, str] = {}
    if URLS_JSON.exists():
        prior_urls = json.loads(URLS_JSON.read_text())
    urls = dict(prior_urls)
    patched = 0
    by_id = {r["id"]: r for r in rows}
    for s, f, p in finals:
        urls[f["id"]] = p["imageUrl"]
        row = by_id.get(f["id"])
        if row is not None and not row.get("imageUrl"):
            row["imageUrl"] = p["imageUrl"]
            tags = list(row.get("tags") or [])
            if "image-bake" not in tags:
                tags.append("image-bake")
            row["tags"] = tags
            patched += 1

    # Rematch / enforce: any remaining shared imageUrl → keep best-scoring figure, clear others
    if companies_filter:
        # Scoped bake: only enforce 1:1 among filtered companies (leave Hasbro/ML/etc alone)
        scoped_rows = [r for r in rows if r.get("company") in companies_filter]
        cleared_shared = enforce_unique_image_urls_sku_aware(scoped_rows, urls) if sku_first else enforce_unique_image_urls(scoped_rows, index, urls)
    else:
        cleared_shared = enforce_unique_image_urls_sku_aware(rows, urls) if sku_first else enforce_unique_image_urls(rows, index, urls)
    if cleared_shared:
        print(f"cleared shared imageUrl from {cleared_shared} rows (strict 1:1)")

    # After clears, try one more gap-fill pass with leftover unused product URLs
    need2 = [r for r in rows if not r.get("imageUrl")]
    if companies_filter:
        need2 = [r for r in need2 if r.get("company") in companies_filter]
    used_urls = {r["imageUrl"] for r in rows if r.get("imageUrl")}
    used_fig = {r["id"] for r in rows if r.get("imageUrl")}
    cands2: list[tuple[float, str, str, dict, dict]] = []
    for fig in need2:
        best = None
        best_s = 0.0
        for p in by_co.get(fig["company"], []):
            s = score_pair(fig, p)
            if s > best_s:
                best_s, best = s, p
        if best and best_s >= min_score:
            cands2.append((best_s, fig["id"], best["id"], fig, best))
    cands2.sort(reverse=True, key=lambda x: x[0])
    extra_finals: list[tuple[float, dict, dict]] = []
    for s, fid, pid, f, p in cands2:
        if fid in used_fig:
            continue
        url = p.get("imageUrl") or ""
        if not url or url in used_urls:
            continue
        used_fig.add(fid)
        used_urls.add(url)
        extra_finals.append((s, f, p))
        urls[fid] = url
        row = by_id.get(fid)
        if row is not None and not row.get("imageUrl"):
            row["imageUrl"] = url
            tags = list(row.get("tags") or [])
            if "image-bake" not in tags:
                tags.append("image-bake")
            row["tags"] = tags
            patched += 1
    if extra_finals:
        finals.extend(extra_finals)
        print(f"gap-fill after unique pass: +{len(extra_finals)}")

    if companies_filter:
        scoped_rows2 = [r for r in rows if r.get("company") in companies_filter]
        cleared_shared2 = enforce_unique_image_urls_sku_aware(scoped_rows2, urls) if sku_first else enforce_unique_image_urls(scoped_rows2, index, urls)
    else:
        cleared_shared2 = enforce_unique_image_urls_sku_aware(rows, urls) if sku_first else enforce_unique_image_urls(rows, index, urls)
    if cleared_shared2:
        print(f"second unique pass cleared {cleared_shared2} rows")
        cleared_shared += cleared_shared2

    # Rebuild url map from oneshot (source of truth) + keep orphans only if still on a row
    urls = {r["id"]: r["imageUrl"] for r in rows if r.get("imageUrl")}
    # Merge any prior map entries that still match a row without imageUrl? No — oneshot wins.
    URLS_JSON.write_text(json.dumps(urls, indent=2, sort_keys=True) + "\n")
    ARCHIVE_JSON.write_text(json.dumps(rows, indent=2) + "\n")

    after_with = sum(1 for r in rows if r.get("imageUrl"))
    shared_after = sum(1 for u, c in Counter(r["imageUrl"] for r in rows if r.get("imageUrl")).items() if c >= 2)
    stats = {
        "bakedAt": datetime.now(timezone.utc).isoformat(),
        "day": date.today().isoformat(),
        "minScore": min_score,
        "indexSize": len(index),
        "fetchLive": fetch_live,
        "before": {"total": before_total, "withImage": before_with, "pct": round(100 * before_with / before_total, 2)},
        "after": {"total": len(rows), "withImage": after_with, "pct": round(100 * after_with / len(rows), 2)},
        "matched": len(finals),
        "candidatesAboveThreshold": len(cands),
        "patchedOneshot": patched,
        "clearedSharedImageUrl": cleared_shared,
        "sharedUrlsAfter": shared_after,
        "urlMapSize": len(urls),
        "skuFirst": sku_first,
        "skuRematch": (
            {k: v for k, v in sku_rematch_stats.items() if k != "skuProvenIds"}
            if sku_rematch_stats
            else None
        ),
        "byCompany": dict(Counter(f["company"] for _, f, _ in finals).most_common()),
        "safeguards": [
            "same-company hard gate",
            "blocked families: JLU/DCUC (classic DC Direct unblocked via retailer vendor/title)",
            "line-family regex required when known (Hasbro Legends/Black Series/Classified/Studio/Lightning)",
            "character-focused name match (subtitle for ULTIMATES/ReAction headers)",
            "first significant name token required",
            "multi-token subtitle requires ≥1 hit",
            "prefer product title hits on distinguishing subtitle/wave tokens",
            "one product image URL → at most one figure id (no variant CDN sharing)",
            "SKU-first exact join (product-sku-index) overwrites fuzzy mismatches; fuzzy never overwrites image-sku",
            "after rematch: shared URLs keep best score only; others cleared to placeholder",
            "Mattel DC Premier not used for unrelated curated lines",
            "retailer feeds (ToyArena/CmdStore/Planet/CoolToyDen/AFCollector/Legendz/shop.mattel/Solaris/JBHiFi/AFAC/JapanFigure) vendor→company high-confidence only",
            "Storm HK + Store Horsemen first-party; Pulse/BBTS/EE/Mezco official still blocked",
            "hyphen-prefix only for Techno-Viper style; MOTU trailing-character peel; AFAC CAPS character peel; color antonyms",
        ],
        "samples": [
            {
                "score": round(s, 2),
                "figureId": f["id"],
                "figure": f"{f['name']} / {f['subtitle']} / {f['line']}",
                "product": f"{p['name']} / {p['subtitle']}",
                "imageUrl": p["imageUrl"][:100],
            }
            for s, f, p in finals[:12]
        ],
        "lowSamples": [
            {
                "score": round(s, 2),
                "figureId": f["id"],
                "figure": f"{f['name']} / {f['subtitle']} / {f['line']}",
                "product": f"{p['name']} / {p['subtitle']}",
            }
            for s, f, p in finals[-8:]
        ],
    }
    STATS_JSON.write_text(json.dumps(stats, indent=2) + "\n")
    if sku_first and sku_rematch_stats is not None:
        SKU_REMATCH_STATS_JSON.write_text(json.dumps({
            "bakedAt": stats["bakedAt"],
            "day": stats["day"],
            "mode": "sku-first+fuzzy" if not sku_only else "sku-only",
            "before": stats["before"],
            "after": stats["after"],
            "skuRematch": stats.get("skuRematch"),
            "matchedFuzzy": len(finals),
            "urlMapSize": len(urls),
        }, indent=2) + "\n")
    print(json.dumps({k: stats[k] for k in ("before", "after", "matched", "clearedSharedImageUrl", "sharedUrlsAfter", "skuRematch", "byCompany") if k in stats}, indent=2))
    print(f"wrote {URLS_JSON} ({len(urls)} urls)")
    print(f"patched oneshot imageUrl on {patched} rows")
    leftovers_by_co = Counter(r["company"] for r in rows if not r.get("imageUrl"))
    print("leftovers by company:", dict(leftovers_by_co.most_common(15)))


if __name__ == "__main__":
    main()
