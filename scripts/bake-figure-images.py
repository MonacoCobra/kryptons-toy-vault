#!/usr/bin/env python3
"""Bake real Shopify CDN product images onto curated/placeholder figures.

No generative AI. Builds a searchable product→image index from AF Shopify
storefronts (same shops as figure-storefronts / oneshot), fuzzy-matches
catalog rows that lack imageUrl, and persists high-confidence hits only.

Outputs:
  - src/data/figure-image-urls.json  (id → CDN URL, comic-cover-urls style)
  - patches imageUrl on matching rows in src/data/figure-archive/oneshot.json
  - src/data/figure-archive/image-bake-stats.json
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
FIGURES_TS = ROOT / "src/data/figures.ts"

STOP = set(
    "the a an of and or for to with from series wave deluxe exclusive edition "
    "figure figures action ver version vol volume pack set new toys toy scale "
    "ultimate ultimates reaction collectibles collection comic comics movie "
    "multipack boxed bundle pack".split()
)
WEAK = set("man men boy girl king queen lord lady black white red blue green glow robot pack".split())

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
}

# Curated lines with no honest Shopify counterpart on our feeds — never match.
BLOCKED_FAMILIES = {"jlu", "dcuc", "dcd"}


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
    return company


def product_character_text(name: str, subtitle: str, title: str = "") -> str:
    """Where the character usually lives for noisy Shopify titles."""
    n, s, t = name or "", subtitle or "", title or ""
    full = t or f"{n} {s}"
    # Pipe titles: last segment is usually the character
    if " | " in full:
        segs = [x.strip() for x in full.split(" | ") if x.strip()]
        if segs:
            char = segs[-1].split(":")[0].strip()
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
    {"id": "toyarena", "baseUrl": "https://www.toyarena.com", "pageLimit": 250, "maxPages": 40},
    {"id": "cmdstore", "baseUrl": "https://www.cmdstore.ca", "pageLimit": 250, "maxPages": 45},
    {"id": "planet-af", "baseUrl": "https://www.planetactionfigures.co.uk", "pageLimit": 250, "maxPages": 25},
]

RETAILER_SKIP = re.compile(
    r"\b(roleplay|life size|prop replica|die cast|static figure|model kit|gunpla|"
    r"figuarts zero|statue|plush|funko|\bpop\b|trading card|pokemon|soft goods|"
    r"empty box|backdrop|t-?shirt|hoodie|mug|poster|apparel|enamel|pin set|"
    r"blind box flat|gift card|nendoroid|pop up parade|scale figure|"
    r"non-scale figure|vibration stars)\b",
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
    if RETAILER_SKIP.search(blob):
        return None
    # Specific lines first
    if re.search(r"\bmafex\b", bl):
        return "mafex"
    if re.search(r"figuarts", bl) and not re.search(r"figuarts zero", bl):
        return "shfiguarts"
    if re.search(r"one:?12|mezco", bl):
        return "mezco"
    if re.search(r"storm collect", bl) or re.match(r"storm\b", vendor, re.I):
        return "storm"
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
    if re.search(r"mcfarlane|dc multiverse", bl) and not re.search(r"marvel legends", bl):
        return "mcfarlane"
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
    if re.search(r"four horsemen|mythic legions|figura obscura", bl):
        return "fourhorsemen"
    if re.search(r"joytoy|joy toy", bl):
        return "joytoy"
    if re.search(r"hot toys", bl):
        return "hottoys"
    if re.search(r"\bkaiyodo\b|revoltech", bl):
        return "kaiyodo"
    if re.search(r"\bfigma\b", bl) or re.search(r"good smile", bl) and re.search(r"\bfigma\b", bl):
        return "figma"
    if re.search(r"beast kingdom", bl):
        return "beastkingdom"
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
        time.sleep(0.12)
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
    covered = [t for t in fn if t in char_toks or t in char]
    if not covered and joined and joined in char.replace(" ", ""):
        covered = list(fn)
    if not covered:
        return -1.0
    if len(covered) < max(1, (len(fn) + 1) // 2):
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
        if primary and fn[0] != primary[0] and set(fn) != set(primary):
            # allow exact whole-name equality only
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

    fs = [t for t in tokens(fig["subtitle"]) if t not in WEAK]
    if fs:
        hits = sum(1 for t in fs if t in char or t in prod["_blob"])
        sub_score = 5.0 * hits / len(fs)
        # Strong wave/subtitle identity: if ≥2 tokens and zero hits, reject
        if len(fs) >= 2 and hits == 0:
            return -1.0
    else:
        sub_score = 1.0

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

    # Single-token figure vs prefixed product character (Viper ← S.A.W.-Viper / Techno-Viper)
    if len(fn) == 1:
        fig_name_raw = (fig.get("name") or "").strip()
        title_raw = prod.get("title") or prod.get("name") or ""
        # Only the token immediately before Name (handles S.A.W.-Viper / Techno Viper)
        pref = re.search(
            rf"(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9\.]{{0,20}})[-\s]+{re.escape(fig_name_raw)}\b",
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
    # Skip obvious Mattel DC Premier mismatches for non-Premier curated lines
    fig_line = norm(fig["line"])
    if fig["company"] == "mattel" and "premier" in prod["_blob"]:
        if "premier" not in fig_line and "total heroes" not in fig_line:
            if fam not in {"wwe", "masterverse", "origins", "jurassic", "motu-generic"}:
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


def main() -> None:
    fetch_live = "--fetch" in sys.argv or "--live" in sys.argv
    use_cache = "--cache-only" in sys.argv
    min_score = 16.0

    rows = json.loads(ARCHIVE_JSON.read_text())
    before_with = sum(1 for r in rows if r.get("imageUrl"))
    before_total = len(rows)
    need = [r for r in rows if not r.get("imageUrl")]

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
    # Product may paint multiple variants of the SAME character name (shared CDN shot).
    # Still block cross-character reuse of one product.
    prod_claimed_name: dict[str, str] = {}
    finals: list[tuple[float, dict, dict]] = []
    for s, fid, pid, f, p in cands:
        if fid in used_fig:
            continue
        claim = norm(figure_match_name(f["name"]))
        prev = prod_claimed_name.get(pid)
        if prev is not None and prev != claim:
            continue
        used_fig.add(fid)
        prod_claimed_name[pid] = claim
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

    URLS_JSON.write_text(json.dumps(urls, indent=2, sort_keys=True) + "\n")
    ARCHIVE_JSON.write_text(json.dumps(rows, indent=2) + "\n")

    after_with = sum(1 for r in rows if r.get("imageUrl"))
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
        "urlMapSize": len(urls),
        "byCompany": dict(Counter(f["company"] for _, f, _ in finals).most_common()),
        "safeguards": [
            "same-company hard gate",
            "blocked families: JLU/DCUC/DC Direct (no honest Shopify line)",
            "line-family regex required when known (Hasbro Legends/Black Series/Classified/Studio/Lightning)",
            "character-focused name match (subtitle for ULTIMATES/ReAction headers)",
            "first significant name token required",
            "multi-token subtitle requires ≥1 hit",
            "one product image → one character name (variants may share CDN shot)",
            "Mattel DC Premier not used for unrelated curated lines",
            "retailer feeds (ToyArena/CmdStore/Planet) vendor→company high-confidence only",
            "Storm first-party stormco.com.hk; Pulse/BBTS/EE/Mezco official still blocked",
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
    print(json.dumps({k: stats[k] for k in ("before", "after", "matched", "byCompany")}, indent=2))
    print(f"wrote {URLS_JSON} ({len(urls)} urls)")
    print(f"patched oneshot imageUrl on {patched} rows")
    leftovers_by_co = Counter(r["company"] for r in rows if not r.get("imageUrl"))
    print("leftovers by company:", dict(leftovers_by_co.most_common(15)))


if __name__ == "__main__":
    main()
