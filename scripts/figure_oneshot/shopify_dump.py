"""Fetch ALL paginated Shopify products from AF storefronts and map to catalog rows."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from typing import Any

UA = "KryptonsToyVault/1.0 (personal collection; permanent archive dump)"
FLOOR = "1980-01-01"

# Mirrors src/lib/figure-storefronts.ts (+ verified extras)
STOREFRONTS = [
    {"id": "super7", "baseUrl": "https://super7.com", "company": "super7"},
    {
        "id": "goodsmile-us",
        "baseUrl": "https://goodsmileus.com",
        "company": "figma",
        "requireHint": re.compile(r"\b(figma|action figure)\b", re.I),
        # Prefer articulated; skip statues/nendoroid/plush in filter below
    },
    {"id": "bossfight", "baseUrl": "https://bossfightstudio.com", "company": "bossfight"},
    {"id": "loyalsubjects", "baseUrl": "https://theloyalsubjects.com", "company": "loyalsubjects"},
    {
        "id": "mattel-creations",
        "baseUrl": "https://creations.mattel.com",
        "company": "mattel",
        "requireHint": re.compile(
            r"masterverse|masters of the universe|wwe|elite|jurassic|monster high|"
            r"dc universe|hammond|action figure|origins|revelation",
            re.I,
        ),
    },
    {"id": "premiumdna", "baseUrl": "https://www.premiumdnatoys.com", "company": "premiumdna"},
    {"id": "hiya", "baseUrl": "https://www.hiyatoys.com", "company": "hiya"},
    {"id": "mondo", "baseUrl": "https://www.mondoshop.com", "company": "mondo"},
    {
        "id": "shop-dc",
        "baseUrl": "https://shop.dc.com",
        "company": "mcfarlane",  # current AF SKUs are mostly McFarlane Multiverse
        "requireHint": re.compile(
            r"action figure|dc multiverse|mcfarlane collector",
            re.I,
        ),
    },
    {
        "id": "valaverse",
        "baseUrl": "https://www.valaverse.com",
        "company": "valaverse",
        "requireHint": re.compile(r"action force|figure|trooper|gear|pack", re.I),
    },
    {
        "id": "neca-store",
        "baseUrl": "https://store.necaonline.com",
        "company": "neca",
        "requireHint": re.compile(
            r"action figure|figure|ultimate|scale|tmnt|predator|alien|horror",
            re.I,
        ),
    },
]

SKIP_TYPE = re.compile(
    r"\b(apparel|shirt|hoodie|hat|cap|sock|sticker|figpin|enamel|poster|print|mug|bag|"
    r"wallet|blanket|keychain|lanyard|gift.?card|digital|barbie|doll|little people|"
    r"plush|soft toy|board game|drinkware|puzzle|skatedeck|soapies|membership|vinyl art|minico|nendoroid|pop up parade|"
    r"huggy|rubber mascot|button|t-?shirt|tee|pin\b|tiki|water bottle|printful)\b",
    re.I,
)
# Soft vinyl / sofubi OK for Super7/Mondo collector lines; skip plain "Vinyl" art toys if poster-like
FIGURE_HINT = re.compile(
    r"\b(figure|figurine|mafex|figuarts|figma|mezco|legends|classified|black series|"
    r"soft.?vinyl|sofubi|reactors|ultimates|reaction|h\.?a\.?c\.?k\.?s|bst axn|"
    r"masterverse|exquisite|1/?12|1/?6|action)\b",
    re.I,
)
SKIP_TITLE = re.compile(
    r"\b(poster|lithograph|print only|t-?shirt|hoodie|mug|pin set|enamel pin|"
    r"blind box flat|gift card|digital download|nendoroid|pop up parade|"
    r"scale figure|non-scale figure)\b",
    re.I,
)


def slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:60] or "item"


def tag_list(tags: Any) -> list[str]:
    if isinstance(tags, list):
        return [str(t) for t in tags]
    if isinstance(tags, str):
        return [t.strip() for t in tags.split(",") if t.strip()]
    return []


def fetch_page(base_url: str, path: str, page: int) -> list[dict] | None:
    url = f"{base_url.rstrip('/')}{path}?limit=50&page={page}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read()
            if raw[:1] == b"<":
                return None
            data = json.loads(raw)
            return list(data.get("products") or [])
    except Exception:
        return None


def fetch_all_products(source: dict, max_pages: int = 100) -> list[dict]:
    path = source.get("productsPath") or "/products.json"
    out: list[dict] = []
    for page in range(1, max_pages + 1):
        products = fetch_page(source["baseUrl"], path, page)
        if products is None:
            if page == 1:
                break
            break
        if not products:
            break
        out.extend(products)
        if len(products) < 50:
            break
        time.sleep(0.12)
    return out


def is_figure_like(p: dict, source: dict) -> bool:
    ptype = str(p.get("product_type") or "")
    title = str(p.get("title") or "")
    tags = " ".join(tag_list(p.get("tags")))
    blob = f"{ptype} {title} {tags}"
    if SKIP_TYPE.search(ptype) or SKIP_TYPE.search(title) or SKIP_TITLE.search(title):
        return False
    # Good Smile: articulated figma / action figure only
    if source["id"] == "goodsmile-us":
        if not re.search(r"\b(figma|action figure)\b", blob, re.I):
            return False
        if re.search(r"\b(nendoroid|scale figure|plush|parade)\b", blob, re.I):
            return False
    # Mondo: articulated scales / figures; skip posters/pins/apparel
    if source["id"] == "mondo":
        if re.search(r"\b(poster|pin|t-?shirt|mug|tiki)\b", blob, re.I):
            return False
        if not re.search(r"\b(1/?12|1/?6|figure|soft vinyl|vinyl figure)\b", blob, re.I):
            return False
    # Valaverse: Action Force AF shop — keep figures/gear packs; skip comics/fees/apparel
    if source["id"] == "valaverse":
        if re.search(r"\b(comic book|mws_fee|apparel|t-?shirt|hoodie|mug|sticker|poster)\b", blob, re.I):
            return False
        return True
    # NECA store: AF / Ultimate / scale figures; skip pins/plush/apparel/replicas
    if source["id"] == "neca-store":
        if re.search(
            r"\b(enamel|pin|plush|apparel|t-?shirt|hoodie|mug|poster|replica|prop|crate|diorama|knocker|dunny|blind box|accessory set)\b",
            blob,
            re.I,
        ):
            return False
        if not re.search(r"\b(action figure|figure|ultimate|scale)\b", blob, re.I):
            return False
    # shop.dc.com: AF only (skip merch/statues/funko/plush)
    if source["id"] == "shop-dc":
        if re.search(
            r"\b(funko|barbie|plush|statue|resin|poster|apparel|t-?shirt|hoodie|mug|pin|jewelry|key.?chain|replica|popcorn|standee)\b",
            blob,
            re.I,
        ):
            return False
        if not re.search(r"action figure", blob, re.I):
            return False
    req = source.get("requireHint")
    if req and not req.search(blob):
        return False
    if FIGURE_HINT.search(blob) or re.search(r"figures?", ptype, re.I):
        return True
    if source["company"] in {"bossfight", "loyalsubjects", "super7", "hiya", "premiumdna", "valaverse", "neca"}:
        return True
    return False


def kind_for(p: dict) -> str:
    blob = f"{p.get('product_type') or ''} {p.get('title') or ''} {' '.join(tag_list(p.get('tags')))}"
    if re.search(r"\b(gunpla|plamo|model kit|hguc|\brg |\bmg |\bpg )\b", blob, re.I):
        return "kit"
    return "figure"


def scale_for(p: dict, kind: str) -> str:
    blob = f"{p.get('title') or ''} {' '.join(tag_list(p.get('tags')))} {p.get('body_html') or ''}"
    m = re.search(r"\b(1/\d+)\b", blob) or re.search(r'\b(\d+(?:\.\d+)?")\b', blob)
    if m:
        return m.group(1)
    return "1/144" if kind == "kit" else '6"'


def parse_money(v: Any) -> float:
    try:
        n = float(re.sub(r"[^0-9.]", "", str(v or "")))
        return n if n == n else 0.0
    except Exception:
        return 0.0


def date_from(p: dict, fallback: str) -> str:
    for raw in (p.get("published_at"), p.get("created_at"), p.get("updated_at")):
        if not raw:
            continue
        d = str(raw)[:10]
        if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            if d < FLOOR:
                return FLOOR
            return d
    return fallback


def split_title(title: str) -> tuple[str, str]:
    cleaned = re.sub(r"\s+", " ", title).strip()
    parts = re.split(r"\s+[—–-]\s+", cleaned)
    if len(parts) >= 2:
        return parts[0].strip(), " - ".join(parts[1:]).strip()
    colon = cleaned.split(":")
    if len(colon) >= 2 and len(colon[0]) < 48:
        return colon[0].strip(), ":".join(colon[1:]).strip()
    return cleaned, ""


def map_product(p: dict, source: dict) -> dict | None:
    title = str(p.get("title") or "").strip()
    if not title or not is_figure_like(p, source):
        return None
    name, subtitle = split_title(title)
    if not name:
        return None
    kind = kind_for(p)
    # Archive is action figures; skip kits unless Bandai-like (we map goodsmile kits out mostly)
    if kind != "figure":
        return None
    variant = (p.get("variants") or [{}])[0] or {}
    msrp = parse_money(variant.get("price")) or 24.99
    images = p.get("images") or []
    image_url = None
    for im in images:
        src = (im or {}).get("src")
        if src and str(src).startswith("http"):
            image_url = str(src)
            break
    tags = {"archive", "shopify", source["id"], source["company"], "figure"}
    for t in tag_list(p.get("tags"))[:8]:
        tags.add(t.lower())
    exclusive = next((t for t in tag_list(p.get("tags")) if re.search(r"exclusive", t, re.I)), None)
    handle = p.get("handle") or slug(name)
    rid = f"sf-{source['id']}-{handle}"[:80]
    return {
        "id": rid,
        "name": name[:120],
        "subtitle": (subtitle or str(p.get("product_type") or source["id"]))[:120],
        "line": str(p.get("product_type") or p.get("vendor") or source["id"])[:80],
        "company": source["company"],
        "kind": "figure",
        "releaseDate": date_from(p, "2020-01-01"),
        "msrp": round(float(msrp), 2),
        "scale": scale_for(p, kind),
        "demand": 1.0,
        "tags": sorted(tags),
        "sku": variant.get("sku") or None,
        "exclusive": exclusive,
        "imageUrl": image_url,
        "source": "shopify",
    }


def dump_all_storefronts() -> tuple[list[dict], dict]:
    rows: list[dict] = []
    stats: dict[str, Any] = {"by_shop": {}, "raw": {}, "kept": {}}
    seen_ids: set[str] = set()
    for source in STOREFRONTS:
        products = fetch_all_products(source)
        stats["raw"][source["id"]] = len(products)
        kept = 0
        for p in products:
            fig = map_product(p, source)
            if not fig:
                continue
            if fig["id"] in seen_ids:
                continue
            seen_ids.add(fig["id"])
            rows.append(fig)
            kept += 1
        stats["kept"][source["id"]] = kept
        print(f"shopify {source['id']}: raw={len(products)} kept={kept}")
    stats["total"] = len(rows)
    return rows, stats
