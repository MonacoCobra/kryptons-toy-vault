#!/usr/bin/env python3
"""Model-kits pass: Blokees, Flame Toys, Bandai Gunpla/SW kits, SoSkill probe.

- Blokees: re-fetch blokees.com; mark Champion/Galaxy/Defender/etc. as kind=kit;
  densify missing CDN images; listing codes → aliases; GTIN primary only if real.
- Flame Toys: specialty Shopify (ToyArena + Planet AF); inject Furai Model as kit;
  densify images on existing rows; KKK/Furai Action stay figure when assembled AF.
- Bandai: Gunpla (HG/RG/MG/PG/EG/SD) + Star Wars vehicle/model kits + other Bandai
  hobby plastic kits from specialty Shopify (Gundam Planet, USA Gundam Store,
  ToyArena, Japan Figure, ToyDojo). Never reclass SHFiguarts / Robot Spirits AF.
- SoSkill: probe feeds; leave 0 rows if still blocked (never invent).
- Never invent SKUs/EANs or AI art. Prefer empty image over wrong.
- Does NOT touch comics/UPC.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/workspace/collection-app")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_identity import clean_code, is_gtin  # noqa: E402
from figure_oneshot.shopify_dump import slug, split_title  # noqa: E402

ARCHIVE = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
SKU_MAP = ROOT / "src/data/figure-sku-map.json"
URLS = ROOT / "src/data/figure-image-urls.json"
STATS = ROOT / "src/data/figure-archive/model-kits-inject-stats.json"

UA = "KryptonsToyVault/1.0 (personal collection; permanent archive dump)"
WEAK = {
    "the", "and", "of", "a", "an", "series", "version", "class", "champion",
    "galaxy", "defender", "blokees", "transformers", "gundam", "action",
    "figure", "figures", "model", "kit", "kits", "flame", "toys", "furai",
    "kuro", "kara", "kuri", "plastic", "cm", "ver", "reissue", "preorder",
    "pre-order", "edition", "shining", "legend", "classic", "warrior", "armor",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def tokens(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9']+", (s or "").lower()) if t not in WEAK and len(t) > 1}


def fetch_products(base: str, max_pages: int = 60) -> list[dict]:
    out: list[dict] = []
    for page in range(1, max_pages + 1):
        url = f"{base.rstrip('/')}/products.json?limit=250&page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.loads(r.read())
        except Exception:
            break
        ps = d.get("products") or []
        if not ps:
            break
        out.extend(ps)
        if len(ps) < 250:
            break
        time.sleep(0.2)
    return out


def fetch_collection(base: str, handle: str, max_pages: int = 10) -> list[dict]:
    out: list[dict] = []
    for page in range(1, max_pages + 1):
        url = f"{base.rstrip('/')}/collections/{handle}/products.json?limit=250&page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.loads(r.read())
        except Exception:
            break
        ps = d.get("products") or []
        if not ps:
            break
        out.extend(ps)
        if len(ps) < 250:
            break
        time.sleep(0.2)
    return out


def ensure_alias_doc(doc: dict) -> dict:
    doc.setdefault("version", 1)
    doc.setdefault("policy", "gtin-canonical")
    doc.setdefault("aliasesByFigureId", {})
    doc.setdefault("aliasToFigureId", {})
    doc.setdefault("collapsed", [])
    doc.setdefault("flagged", [])
    return doc


def add_aliases(doc: dict, figure_id: str, codes: list[str]) -> int:
    doc = ensure_alias_doc(doc)
    by = doc["aliasesByFigureId"]
    to = doc["aliasToFigureId"]
    cur = list(by.get(figure_id) or [])
    added = 0
    for c in codes:
        c2 = clean_code(c) or str(c).strip()
        if not c2:
            continue
        if c2 not in cur:
            cur.append(c2)
            added += 1
        to[c2] = figure_id
    if cur:
        by[figure_id] = cur
    return added


def parse_money(v: Any) -> float:
    try:
        n = float(re.sub(r"[^0-9.]", "", str(v or "")))
        return n if n == n else 0.0
    except Exception:
        return 0.0


def date_from(p: dict, fallback: str = "2024-01-01") -> str:
    for raw in (p.get("published_at"), p.get("created_at"), p.get("updated_at")):
        if not raw:
            continue
        d = str(raw)[:10]
        if re.match(r"^\d{4}-\d{2}-\d{2}$", d) and d >= "1980-01-01":
            return d
    return fallback


def first_image(p: dict) -> str | None:
    for im in p.get("images") or []:
        src = (im or {}).get("src")
        if src and str(src).startswith("http"):
            return str(src)
    return None


def existing_keys(rows: list[dict]) -> tuple[set[str], set[str]]:
    ids = {r["id"] for r in rows}
    keys = {f"{r['name']}|{r.get('subtitle')}|{r.get('line')}|{r.get('company')}".lower() for r in rows}
    return ids, keys


def brand_counts(rows: list[dict], urls: dict, brands: set[str]) -> dict:
    out = {}
    for b in sorted(brands):
        sub = [r for r in rows if r.get("company") == b]
        kinds = Counter(r.get("kind") or "figure" for r in sub)
        out[b] = {
            "rows": len(sub),
            "figure": kinds.get("figure", 0),
            "kit": kinds.get("kit", 0),
            "sku": sum(1 for r in sub if r.get("sku")),
            "img": sum(1 for r in sub if r.get("imageUrl") or r["id"] in urls),
            "gtin": sum(1 for r in sub if is_gtin(clean_code(r.get("sku")))),
        }
    return out


# ---- Blokees ----

SOFT_FIGURE_RE = re.compile(
    r"daalamode|daavibe|fantastics|precool|daadoos|mokoo|buddy emblem|wheels|"
    r"t-?shirt|hoodie|mug|sticker|poster|plush|keychain|acrylic|magnet|apparel|gift.?card",
    re.I,
)

KIT_LINE_RE = re.compile(
    r"champion class|galaxy version|\bgv\d*\b|defender version|shining version|"
    r"legend edition|classic class|action edition|herospire|model kit|"
    r"terraventure|yearly version|gundam",
    re.I,
)


def blokees_keep(title: str, tags: Any) -> bool:
    blob = f"{title} {' '.join(tags) if isinstance(tags, list) else tags or ''}"
    if re.search(
        r"\b(t-?shirt|hoodie|mug|sticker|poster|plush|keychain|acrylic|magnet|apparel|gift.?card)\b",
        blob,
        re.I,
    ):
        return False
    if re.search(r"\b(daadoos mate|daadoos nest|daadoos art|mokoo|buddy emblem)\b", blob, re.I):
        return False
    if re.search(r"\bwheels\b", blob, re.I) and not KIT_LINE_RE.search(blob):
        return False
    return bool(
        re.search(
            r"champion class|galaxy version|defender version|shining version|legend edition|"
            r"classic class|action edition|model kit|ultraman|saint seiya|gundam|transformers|"
            r"marvel rivals|star wars|naruto|evangelion|herospire|terraventure|jurassic|"
            r"dc defender|astral rally|mega man|deadpool|infinity saga|yearly version",
            blob,
            re.I,
        )
    )


def blokees_is_kit(title: str, line: str = "") -> bool:
    blob = f"{title} {line}"
    if SOFT_FIGURE_RE.search(blob):
        # DaaLaMode / Fantastics / preCOOL are display figures, not assembleable kits
        return False
    return bool(KIT_LINE_RE.search(blob))


def blokees_line(title: str) -> str:
    tl = title.lower()
    if "champion class" in tl:
        return "Blokees Champion Class"
    if "galaxy version" in tl or re.search(r"\bgv\d+", tl):
        return "Blokees Galaxy Version"
    if "defender version" in tl:
        return "Blokees Defender Version"
    if "shining version" in tl:
        return "Blokees Shining Version"
    if "legend edition" in tl:
        return "Blokees Legend Edition"
    if "classic class" in tl:
        return "Blokees Classic Class"
    if "action edition" in tl:
        return "Blokees Action Edition"
    if "herospire" in tl and "warrior" in tl:
        return "Blokees Herospire Warrior"
    if "herospire" in tl and "armor" in tl:
        return "Blokees Herospire Armor"
    if "herospire" in tl:
        return "Blokees Herospire"
    if "gundam" in tl:
        return "Blokees Gundam"
    if "transformers" in tl:
        return "Blokees Transformers"
    return "Blokees"


def blokees_name_from_title(title: str) -> tuple[str, str]:
    """Better character extraction than bare split_title for Blokees pipes."""
    cleaned = re.sub(r"\s+", " ", title).strip()
    cleaned = re.sub(r"\s*\|\s*BLOKEES\s*(?:\(Pre-Order\))?\s*$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*\|\s*Blokees\s*$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+MODEL KITS?\s*$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*\(Pre-Order\)\s*$", "", cleaned, flags=re.I)

    # "Franchise Champion Class NN Character"
    m = re.search(
        r"(?:champion class|classic class|action edition|legend edition)\s*\d*\s*[-:]?\s*(.+)$",
        cleaned,
        re.I,
    )
    if m:
        name = m.group(1).strip(" |:-")
        name = re.sub(r"\s+MODEL KITS?\s*$", "", name, flags=re.I).strip()
        if name and name.lower() not in {"blokees", "model kits"}:
            return name[:120], cleaned[:120]

    # pipe form: left franchise, right character
    if " | " in cleaned:
        parts = [p.strip() for p in cleaned.split(" | ") if p.strip()]
        if len(parts) >= 2:
            right = parts[-1]
            if right.lower() not in {"blokees"} and len(right) < 80:
                return right[:120], " | ".join(parts[:-1])[:120]

    name, subtitle = split_title(cleaned)
    if name.lower() in {"blokees", "blo kees"} or name.upper() == "BLOKEES":
        # fallback: strip brand words from full title
        name = re.sub(r"^blokees\s*[|:-]?\s*", "", cleaned, flags=re.I).strip()
    return (name or cleaned)[:120], (subtitle or cleaned)[:120]


def soft_name_hit(name: str, existing_names: set[str]) -> bool:
    nt = tokens(name)
    if not nt:
        return False
    for en in existing_names:
        et = tokens(en)
        if not et:
            continue
        if name.lower() == en.lower():
            return True
        inter = nt & et
        if len(inter) >= max(1, min(len(nt), len(et))) and len(inter) / max(len(nt), len(et)) >= 0.85:
            return True
    return False


def reclass_and_densify_blokees(rows: list[dict], aliases: dict, urls: dict) -> dict:
    products = fetch_products("https://blokees.com", 12)
    by_handle = {str(p.get("handle") or ""): p for p in products}
    # also index by soft title tokens for curated blk-* rows
    feed_by_name: list[tuple[set[str], dict]] = []
    for p in products:
        title = str(p.get("title") or "")
        if not blokees_keep(title, p.get("tags")):
            continue
        name, _ = blokees_name_from_title(title)
        feed_by_name.append((tokens(name) | tokens(title), p))

    reclassed = 0
    imaged = 0
    aliased = 0
    names_fixed = 0
    kept_figure = 0

    for r in rows:
        if r.get("company") != "blokees":
            continue
        rid = r["id"]
        handle = rid[len("sf-blokees-") :] if rid.startswith("sf-blokees-") else None
        p = by_handle.get(handle) if handle else None

        # match curated rows without handle
        if not p:
            rt = tokens(r.get("name") or "") | tokens(r.get("subtitle") or "") | tokens(r.get("line") or "")
            best = None
            best_score = 0.0
            for ft, fp in feed_by_name:
                if not rt or not ft:
                    continue
                inter = rt & ft
                if not inter:
                    continue
                score = len(inter) / max(len(rt), len(ft))
                if score > best_score:
                    best_score = score
                    best = fp
            if best and best_score >= 0.55:
                p = best

        title_blob = ""
        if p:
            title_blob = str(p.get("title") or "")
        else:
            title_blob = f"{r.get('name')} {r.get('subtitle')} {r.get('line')}"

        line = blokees_line(title_blob) if p else (r.get("line") or "Blokees")
        is_kit = blokees_is_kit(title_blob, line)
        if is_kit:
            if r.get("kind") != "kit":
                reclassed += 1
            r["kind"] = "kit"
            tags = list(r.get("tags") or [])
            if "kit" not in tags:
                tags.append("kit")
            if "figure" in tags:
                tags = [t for t in tags if t != "figure"]
            r["tags"] = tags
            if p and line and r.get("line") != line:
                r["line"] = line
        else:
            kept_figure += 1
            r["kind"] = "figure"

        if p:
            # fix garbage names
            name, subtitle = blokees_name_from_title(str(p.get("title") or ""))
            if name and (
                (r.get("name") or "").lower() in {"blokees", "blo kees"}
                or (r.get("name") or "").upper() == "BLOKEES"
                or len(r.get("name") or "") < 2
            ):
                r["name"] = name
                if subtitle:
                    r["subtitle"] = subtitle[:120]
                names_fixed += 1

            img = first_image(p)
            if img and not r.get("imageUrl") and rid not in urls:
                r["imageUrl"] = img
                urls[rid] = img
                imaged += 1
            elif img and not r.get("imageUrl") and rid in urls:
                r["imageUrl"] = urls[rid]
            elif img and r.get("imageUrl"):
                pass
            elif img:
                # fill overlay map even if row already has url
                urls.setdefault(rid, img)

            variant = (p.get("variants") or [{}])[0] or {}
            listing = clean_code(variant.get("sku")) or (
                str(variant.get("sku")).strip() if variant.get("sku") else None
            )
            barcode = clean_code(variant.get("barcode"))
            if barcode and is_gtin(barcode):
                r["sku"] = barcode
            if listing:
                aliased += add_aliases(aliases, rid, [listing])

    # inject missing kits from feed
    ids, keys = existing_keys(rows)
    existing_names = {r["name"] for r in rows if r.get("company") == "blokees"}
    known_codes = set()
    for r in rows:
        if r.get("company") != "blokees":
            continue
        if r.get("sku"):
            known_codes.add(clean_code(r["sku"]) or r["sku"])
        for a in (aliases.get("aliasesByFigureId") or {}).get(r["id"]) or []:
            known_codes.add(a)

    added = []
    skipped = Counter()
    for p in products:
        title = str(p.get("title") or "").strip()
        if not title or not blokees_keep(title, p.get("tags")):
            skipped["filter"] += 1
            continue
        if not blokees_is_kit(title):
            # still inject soft figures? only densify existing — skip new soft merch
            if SOFT_FIGURE_RE.search(title):
                skipped["soft_merch"] += 1
                continue
            # non-kit keepable AF already covered; skip new unless clearly a kit line
            skipped["non_kit"] += 1
            continue
        handle = str(p.get("handle") or slug(title))
        rid = f"sf-blokees-{handle}"[:80]
        if rid in ids:
            skipped["id"] += 1
            continue
        name, subtitle = blokees_name_from_title(title)
        line = blokees_line(title)
        key = f"{name}|{subtitle or line}|{line}|blokees".lower()
        if key in keys:
            skipped["key"] += 1
            continue
        if soft_name_hit(name, existing_names) and len(tokens(name)) <= 3:
            skipped["soft_name"] += 1
            continue
        variant = (p.get("variants") or [{}])[0] or {}
        listing = clean_code(variant.get("sku")) or (
            str(variant.get("sku")).strip() if variant.get("sku") else None
        )
        barcode = clean_code(variant.get("barcode"))
        primary = barcode if barcode and is_gtin(barcode) else None
        if listing and listing in known_codes and not primary:
            skipped["known_listing"] += 1
            continue
        img = first_image(p)
        msrp = parse_money(variant.get("price")) or 24.99
        row = {
            "id": rid,
            "name": name[:120],
            "subtitle": (subtitle or line)[:120],
            "line": line[:80],
            "company": "blokees",
            "kind": "kit",
            "releaseDate": date_from(p, "2024-01-01"),
            "msrp": round(float(msrp), 2),
            "scale": '6"',
            "demand": 1.0,
            "tags": ["archive", "shopify", "blokees", "kit", "inject-model-kits"],
            "source": "shopify",
        }
        if primary:
            row["sku"] = primary
        if img:
            row["imageUrl"] = img
            urls[rid] = img
        rows.append(row)
        ids.add(rid)
        keys.add(key)
        existing_names.add(name)
        if listing:
            add_aliases(aliases, rid, [listing])
            known_codes.add(listing)
        added.append(rid)

    return {
        "fetched": len(products),
        "reclassedToKit": reclassed,
        "keptFigure": kept_figure,
        "imagesAdded": imaged,
        "namesFixed": names_fixed,
        "aliasAdds": aliased,
        "added": len(added),
        "skipped": dict(skipped),
        "ids": added[:40],
        "feed": "https://blokees.com",
    }


# ---- Flame Toys ----

def flame_is_kit(title: str, product_type: str = "") -> bool:
    blob = f"{title} {product_type}"
    if re.search(r"furai\s*action", blob, re.I):
        return False  # pre-assembled AF
    if re.search(r"kuro\s*kara\s*kuri|kara\s*kuri\s*combine|go!\s*kuro", blob, re.I):
        return False  # premium assembled AF / combiners
    return bool(
        re.search(r"furai\s*model|furai\s*\d+|model\s*kit|plastic\s*model", blob, re.I)
        or (re.search(r"\bmodel kit\b", product_type or "", re.I))
    )


def flame_line(title: str, is_kit: bool) -> str:
    tl = title.lower()
    if is_kit or "furai" in tl:
        return "Furai Model"
    if "kuro kara kuri" in tl or "kara kuri" in tl:
        return "Kuro Kara Kuri"
    if "furai action" in tl:
        return "Furai Action"
    if "combine" in tl:
        return "Go! Kuro Kara Combine"
    return "Flame Toys"


def flame_name_from_title(title: str) -> tuple[str, str]:
    cleaned = re.sub(r"\s+", " ", title).strip()
    cleaned = re.sub(r"^flame\s*toys\s+", "", cleaned, flags=re.I)
    # strip leading franchise / line prefixes
    cleaned2 = re.sub(
        r"^(?:transformers|tengen topppa gurren lagann|power rangers|mighty morphin power rangers)\s+",
        "",
        cleaned,
        flags=re.I,
    )
    cleaned2 = re.sub(
        r"^(?:furai\s*model|furai\s*action|furai\s*\d+|kuro\s*kara\s*kuri|go!\s*kuro\s*kara\s*combine)\s+",
        "",
        cleaned2,
        flags=re.I,
    )
    cleaned2 = re.sub(r"\bplastic\s+model\s+kit\b", " ", cleaned2, flags=re.I)
    cleaned2 = re.sub(r"\bmodel\s+kit\b", " ", cleaned2, flags=re.I)
    cleaned2 = re.sub(r"\baction\s+figures?\b", " ", cleaned2, flags=re.I)
    cleaned2 = re.sub(r"\b\d+\s*cm\b", " ", cleaned2, flags=re.I)
    cleaned2 = re.sub(r"\s+", " ", cleaned2).strip(" -|:")
    # size remnants
    name = cleaned2 or cleaned
    # character often last meaningful chunk
    m = re.search(
        r"((?:SG\s+)?(?:Optimus Prime|Megatron|Bumblebee|Starscream|Skywarp|Thundercracker|"
        r"Drift|Arcee|Windblade|Nemesis Prime|Ultra Magnus|Devastator|Big Convoy|"
        r"Beast Megatron|Lazengann|Thunder Megazord|Dino Megazord|"
        r"Red Ranger|Blue Ranger|Yellow Ranger|Pink Ranger|Black Ranger|"
        r"Wingblade Optimus Prime)(?:[^|]*)?)$",
        name,
        re.I,
    )
    if m:
        name = m.group(1).strip()
    name = re.sub(r"\s*\{", " (", name)
    name = re.sub(r"\}", ")", name)
    return name[:120], cleaned[:120]


def collect_flame_products() -> tuple[list[dict], list[str], list[str]]:
    feeds_used = []
    feeds_rejected = []
    seen_handles: set[str] = set()
    out: list[dict] = []

    # ToyArena full vendor scan (already verified)
    try:
        ta = fetch_products("https://www.toyarena.com", 55)
        n = 0
        for p in ta:
            vendor = str(p.get("vendor") or "")
            title = str(p.get("title") or "")
            if re.search(r"flame\s*toys|\bfurai\b|kuro\s*kara", f"{vendor} {title}", re.I):
                # skip Yolopark false positives
                if "yolopark" in vendor.lower():
                    continue
                h = str(p.get("handle") or title)
                key = f"ta:{h}"
                if key in seen_handles:
                    continue
                seen_handles.add(key)
                p["_feed"] = "toyarena"
                out.append(p)
                n += 1
        feeds_used.append(f"https://www.toyarena.com (Flame Toys vendor hits={n})")
    except Exception as e:
        feeds_rejected.append(f"https://www.toyarena.com — {e}")

    # Planet AF collection + vendor
    try:
        col = fetch_collection("https://www.planetactionfigures.co.uk", "flame-toys", 5)
        pa = fetch_products("https://www.planetactionfigures.co.uk", 25)
        n = 0
        for p in col + pa:
            vendor = str(p.get("vendor") or "")
            title = str(p.get("title") or "")
            if vendor.lower() == "flame toys" or re.search(r"\bfurai\b|kuro\s*kara", title, re.I):
                h = str(p.get("handle") or title)
                key = f"pa:{h}"
                if key in seen_handles:
                    continue
                # prefer not to dup by title soft
                seen_handles.add(key)
                p["_feed"] = "planet-af"
                out.append(p)
                n += 1
        feeds_used.append(f"https://www.planetactionfigures.co.uk (Flame Toys hits≈{n})")
    except Exception as e:
        feeds_rejected.append(f"https://www.planetactionfigures.co.uk — {e}")

    # first-party rejected
    for base in [
        "https://flametoys.com",
        "https://www.flametoys.com",
        "https://shop.flametoys.com",
        "https://store.flametoys.com",
    ]:
        feeds_rejected.append(f"{base} — SSL/EOF or no products.json (first-party blocked)")

    return out, feeds_used, feeds_rejected


def inject_flame_toys(rows: list[dict], aliases: dict, urls: dict) -> dict:
    products, feeds_used, feeds_rejected = collect_flame_products()

    # densify images + reclass existing Gundam Furai-style AF rows as kits
    densified = 0
    reclassed = 0
    for r in rows:
        if r.get("company") != "flametoys":
            continue
        line = (r.get("line") or "").lower()
        name = (r.get("name") or "").lower()
        # curated "Flame Toys AF" Gundam entries are Furai-style model kits
        if line == "flame toys af" or (line.startswith("flame") and "gundam" in name):
            if r.get("kind") != "kit":
                reclassed += 1
            r["kind"] = "kit"
            r["line"] = "Furai Model"
            tags = list(r.get("tags") or [])
            if "kit" not in tags:
                tags.append("kit")
            r["tags"] = [t for t in tags if t != "figure"]
        # KKK / Special stay figure
        elif "kuro kara kuri" in line:
            r["kind"] = "figure"

        if r.get("imageUrl") or r["id"] in urls:
            continue
        rt = tokens(r.get("name") or "")
        if not rt:
            continue
        best = None
        best_score = 0.0
        for p in products:
            name2, _ = flame_name_from_title(str(p.get("title") or ""))
            ft = tokens(name2)
            if not ft:
                continue
            inter = rt & ft
            if not inter:
                continue
            score = len(inter) / max(len(rt), len(ft))
            # require character token match not just transformers
            if score > best_score:
                best_score = score
                best = p
        if best and best_score >= 0.5:
            img = first_image(best)
            if img:
                r["imageUrl"] = img
                urls[r["id"]] = img
                densified += 1
                variant = (best.get("variants") or [{}])[0] or {}
                listing = clean_code(variant.get("sku")) or (
                    str(variant.get("sku")).strip() if variant.get("sku") else None
                )
                barcode = clean_code(variant.get("barcode"))
                if barcode and is_gtin(barcode) and not r.get("sku"):
                    r["sku"] = barcode
                if listing:
                    add_aliases(aliases, r["id"], [listing])

    # inject missing Furai Model kits (+ optional assembled AF only if clearly missing)
    ids, keys = existing_keys(rows)
    existing_names = {r["name"].lower() for r in rows if r.get("company") == "flametoys"}
    known_codes = set()
    for r in rows:
        if r.get("company") != "flametoys":
            continue
        if r.get("sku"):
            known_codes.add(clean_code(r["sku"]) or r["sku"])
        for a in (aliases.get("aliasesByFigureId") or {}).get(r["id"]) or []:
            known_codes.add(a)

    added_kits = []
    added_figures = []
    skipped = Counter()
    seen_title = set()

    for p in products:
        title = str(p.get("title") or "").strip()
        if not title:
            skipped["no_title"] += 1
            continue
        tl = title.lower()
        if tl in seen_title:
            skipped["dup_title"] += 1
            continue
        seen_title.add(tl)
        pt = str(p.get("product_type") or "")
        is_kit = flame_is_kit(title, pt)
        # Prefer kits; also allow KKK / Furai Action as figure densify injects
        is_af = bool(
            re.search(r"kuro\s*kara\s*kuri|furai\s*action|kara\s*kuri\s*combine", title, re.I)
        )
        if not is_kit and not is_af:
            skipped["filter"] += 1
            continue

        handle = str(p.get("handle") or slug(title))
        feed = p.get("_feed") or "shop"
        rid = f"sf-flametoys-{feed}-{handle}"[:80]
        if rid in ids:
            skipped["id"] += 1
            continue
        name, subtitle = flame_name_from_title(title)
        if not name or name.lower() in {"flame toys", "furai", "model kit"}:
            skipped["bad_name"] += 1
            continue
        line = flame_line(title, is_kit)
        # Same character can exist as both KKK (figure) and Furai Model (kit) — only skip same line
        if any(
            r.get("company") == "flametoys"
            and (r.get("name") or "").lower() == name.lower()
            and (r.get("line") or "").lower() == line.lower()
            for r in rows
        ):
            skipped["soft_name"] += 1
            continue
        key = f"{name}|{subtitle or line}|{line}|flametoys".lower()
        if key in keys:
            skipped["key"] += 1
            continue

        variant = (p.get("variants") or [{}])[0] or {}
        listing = clean_code(variant.get("sku")) or (
            str(variant.get("sku")).strip() if variant.get("sku") else None
        )
        barcode = clean_code(variant.get("barcode"))
        primary = barcode if barcode and is_gtin(barcode) else None
        if listing and listing in known_codes and not primary:
            skipped["known_listing"] += 1
            continue

        img = first_image(p)
        if not img:
            skipped["no_image"] += 1
            continue  # prefer empty over wrong — but for NEW rows require real CDN

        msrp = parse_money(variant.get("price")) or (69.99 if is_kit else 299.99)
        # convert GBP-ish planet prices already in local currency — keep as listed
        kind = "kit" if is_kit else "figure"
        scale = '6"' if is_kit else '8"'
        cm = re.search(r"([\d.]+)\s*cm", title, re.I)
        if cm:
            try:
                scale = f'{round(float(cm.group(1)) / 2.54, 1)}"'
            except Exception:
                pass

        row = {
            "id": rid,
            "name": name[:120],
            "subtitle": (subtitle or line)[:120],
            "line": line,
            "company": "flametoys",
            "kind": kind,
            "releaseDate": date_from(p, "2020-01-01"),
            "msrp": round(float(msrp), 2),
            "scale": scale,
            "demand": 1.1 if not is_kit else 1.0,
            "tags": [
                "archive",
                "shopify",
                "flametoys",
                kind,
                "inject-model-kits",
                feed,
            ],
            "source": "shopify",
            "imageUrl": img,
        }
        if primary:
            row["sku"] = primary
        rows.append(row)
        urls[rid] = img
        ids.add(rid)
        keys.add(key)
        existing_names.add(name.lower())
        if listing:
            add_aliases(aliases, rid, [listing])
            known_codes.add(listing)
        if is_kit:
            added_kits.append(rid)
        else:
            added_figures.append(rid)

    return {
        "productsSeen": len(products),
        "feedsUsed": feeds_used,
        "feedsRejected": feeds_rejected,
        "reclassedGundamToKit": reclassed,
        "imagesDensified": densified,
        "kitsAdded": len(added_kits),
        "figuresAdded": len(added_figures),
        "kitIds": added_kits[:40],
        "figureIds": added_figures[:20],
        "skipped": dict(skipped),
    }



# ---- Bandai Gunpla / Star Wars / hobby kits ----

BANDAI_AF_RE = re.compile(
    r"shfiguarts|s\.h\.?\s*figuarts|robot spirits|gundam universe|metal build|"
    r"metal robot|nxedge|chogokin|figuarts zero|tamashii nations|"
    r"g frame|msi[aá]|the robot spirits|soul of chogokin|super robot chogokin|"
    r"ichibansho|banpresto|vibration stars|dx chogokin",
    re.I,
)

BANDAI_SKIP_RE = re.compile(
    r"\b(tool|tools|paint|marker|cement|nipper|cutter|sandpaper|masking|"
    r"water slide|waterslide|decal sheet|led unit only|display base only|"
    r"action base only|stand only|t-?shirt|hoodie|mug|plush|acrylic|"
    r"keychain|apparel|poster|gift card|insurance|trading card|booster)\b",
    re.I,
)

BANDAI_KIT_RE = re.compile(
    r"\b(HG|HGUC|HGBF|HGBD|HGCE|HGTWFM|HGAW|HGAC|HGIBO|RG|MG|MGEX|PG|EG|SD|BB)\b|"
    r"high grade|real grade|master grade|perfect grade|entry grade|"
    r"gunpla|plastic model|model kit|1/144|1/100|1/60|1/48|1/12|"
    r"vehicle model|figure-?rise|30\s*minutes?\s*missions|30mm|"
    r"30\s*minutes?\s*sisters|30\s*minutes?\s*fantasy|full mechanics|"
    r"re[:\s-]?born|re[:\s-]?rise|pok[eé]mon plamo|star wars",
    re.I,
)


def extract_jan_gtin(*raws: Any) -> str | None:
    """Prefer barcode GTIN; else JAN/UPC digits embedded in listing SKU / image URL."""
    for raw in raws:
        if not raw:
            continue
        c = clean_code(raw)
        if c and is_gtin(c):
            return c
        s = str(raw)
        m = re.search(r"(45\d{11}|49\d{11}|0\d{12}|\d{12,14})", s)
        if m:
            cand = m.group(1)
            if is_gtin(cand):
                return cand
        digits = re.sub(r"\D", "", s)
        if len(digits) in (12, 13, 14) and is_gtin(digits):
            return digits
    return None


def bandai_is_vendor(vendor: str, title: str = "") -> bool:
    blob = f"{vendor} {title}"
    if re.search(r"kotobukiya|good smile|max factory|furyu|megahouse|plum|"
                 r"aoshima|tamiya|hasegawa|wave|modely|yolopark|blokees|"
                 r"flame toys|simp\b|plamod|3rd party|dspiae|gaahleri", blob, re.I):
        # allow if title still clearly Bandai Gunpla branded
        if not re.search(r"\bbandai\b|gunpla|hguc|\brg\b.*gundam", blob, re.I):
            return False
    return bool(
        re.search(
            r"bandai|banpresto|spirits:\s*hobby|bandai spirits|bandai hobby|"
            r"bandai namco",
            vendor,
            re.I,
        )
        or re.search(r"^bandai\b|\bbandai\b.*\b(hg|rg|mg|pg|eg|sd|gunpla|model kit)", title, re.I)
    )


def bandai_is_kit_product(p: dict) -> bool:
    title = str(p.get("title") or "")
    vendor = str(p.get("vendor") or "")
    ptype = str(p.get("product_type") or "")
    tags = p.get("tags")
    tag_s = " ".join(tags) if isinstance(tags, list) else str(tags or "")
    blob = f"{title} {vendor} {ptype} {tag_s}"

    if BANDAI_SKIP_RE.search(blob):
        return False
    pt = ptype.strip().lower()
    if pt in {"tools", "tools (search only)", "accessories", "insurance", "paint",
              "decal", "detail part", "ak interactive", "dspiae"}:
        return False

    # Hard exclude AF lines even if Bandai vendor
    if BANDAI_AF_RE.search(blob):
        # only keep if clearly a plastic model grade kit title
        if not BANDAI_KIT_RE.search(title):
            return False
        # Metal Build / Robot Spirits titled with "model kit" still AF
        if re.search(r"metal build|robot spirits|shfiguarts|gundam universe|figuarts", blob, re.I):
            return False

    if not bandai_is_vendor(vendor, title):
        # USA store / ToyArena sometimes vendor=Bandai omitted but title has Gunpla grades
        if not (
            re.search(r"gunpla|gundam", blob, re.I)
            and BANDAI_KIT_RE.search(blob)
            and re.search(r"model kit|plastic model|1/144|1/100|1/60|high grade|real grade", blob, re.I)
        ):
            return False
        # still require bandai signal somewhere for non-gundam
        if not re.search(r"bandai|gunpla|gundam|star wars", blob, re.I):
            return False

    if not BANDAI_KIT_RE.search(blob) and not re.search(r"model kit|gunpla|plastic model", ptype, re.I):
        return False

    # Skip pure option-part packs without a mobile suit name? Keep 30MM option sets as kits.
    if re.search(r"\b(water slide decal|decal set)\b", title, re.I) and not re.search(
        r"\b(HG|RG|MG|PG|EG|SD)\b|gundam|model kit", title, re.I
    ):
        return False

    return True


def bandai_grade_line(title: str, ptype: str = "", tags: str = "") -> tuple[str, str, str]:
    """Return (line, subtitle_hint, scale_default)."""
    blob = f"{title} {ptype} {tags}"
    if re.search(r"star wars|mandalorian|millennium falcon|x-wing|tie fighter|"
                 r"razor crest|slave i|starfighter|at-st|at-at|bb-8|grogu", blob, re.I) and re.search(
        r"model kit|vehicle model|1/\d+|scale model|plastic model", blob, re.I
    ):
        if re.search(r"vehicle model", blob, re.I):
            return "Star Wars Vehicle Model", "Star Wars Vehicle Model", "1/144"
        return "Star Wars Model Kit", "Star Wars Model Kit", "1/12"
    if re.search(r"MGEX", blob, re.I):
        return "Master Grade", "MGEX", "1/100"
    if re.search(r"perfect grade|\bPG\b", blob, re.I):
        return "Perfect Grade", "Perfect Grade", "1/60"
    if re.search(r"master grade|\bMG\b", blob, re.I):
        return "Master Grade", "Master Grade", "1/100"
    if re.search(r"real grade|\bRG\b", blob, re.I):
        return "Real Grade", "Real Grade", "1/144"
    if re.search(r"entry grade|\bEG\b", blob, re.I):
        return "Entry Grade", "Entry Grade", "1/144"
    if re.search(r"HGUC|HGBF|HGBD|HGCE|HGTWFM|HGAW|HGAC|HGIBO|high grade|\bHG\b", blob, re.I):
        return "High Grade", "High Grade", "1/144"
    if re.search(r"\bSD\b|BB Senshi|cross silhouette|sangoku|bb warrior", blob, re.I):
        return "SD Gundam", "SD Gundam", "SD"
    if re.search(r"figure-?rise", blob, re.I):
        return "Figure-rise", "Figure-rise", "1/12"
    if re.search(r"30\s*minutes?\s*sisters", blob, re.I):
        return "30 Minutes Sisters", "30 Minutes Sisters", "1/144"
    if re.search(r"30\s*minutes?\s*fantasy", blob, re.I):
        return "30 Minutes Fantasy", "30 Minutes Fantasy", "1/144"
    if re.search(r"30\s*minutes?\s*missions|30mm", blob, re.I):
        return "30 Minutes Missions", "30 Minutes Missions", "1/144"
    if re.search(r"full mechanics", blob, re.I):
        return "Full Mechanics", "Full Mechanics", "1/100"
    if re.search(r"pok[eé]mon plamo", blob, re.I):
        return "Pokémon Plamo", "Pokémon Plamo", "—"
    if re.search(r"gunpla|gundam|1/144|1/100|1/60|plastic model|model kit", blob, re.I):
        return "Gunpla", "Gunpla", "1/144"
    return "Bandai Hobby", "Bandai Hobby", "1/144"


def bandai_name_from_title(title: str, line: str) -> tuple[str, str]:
    cleaned = re.sub(r"\s+", " ", title).strip()
    cleaned = re.sub(r"&amp;", "&", cleaned)
    cleaned = re.sub(r"^(?:bandai\s*(?:spirits)?\s*)+", "", cleaned, flags=re.I)
    cleaned = re.sub(r"^gundam\s+", "", cleaned, flags=re.I)
    # scale first so grade tokens become leading
    cleaned2 = re.sub(r"\b\d+/\d+\s*(?:scale)?\b", " ", cleaned, flags=re.I)
    cleaned2 = re.sub(
        r"\b(?:HGUC|HGBF|HGBD|HGCE|HGTWFM|HGAW|HGAC|HGIBO|HG|RG|MGEX|MG|PG|EG|SD)\b\s*"
        r"(?:#?\d+\s*)?",
        " ",
        cleaned2,
        flags=re.I,
    )
    cleaned2 = re.sub(
        r"\b(?:high grade|real grade|master grade(?:\s*2\.0)?|perfect grade(?:\s*unleashed)?|"
        r"entry grade|figure-?rise(?:\s*standard)?|full mechanics)\b",
        " ",
        cleaned2,
        flags=re.I,
    )
    cleaned2 = re.sub(r"\bplastic\s+model(?:\s+kit)?\b", " ", cleaned2, flags=re.I)
    cleaned2 = re.sub(r"\bmodel\s+kits?\b", " ", cleaned2, flags=re.I)
    cleaned2 = re.sub(r"\bgunpla\b", " ", cleaned2, flags=re.I)
    cleaned2 = re.sub(r"\s+", " ", cleaned2).strip(" -|:.#")
    cleaned2 = re.sub(r"^star wars\s*(?::\s*)?", "", cleaned2, flags=re.I).strip()
    cleaned2 = re.sub(
        r"^(?:a new hope|the empire strikes back|return of the jedi|"
        r"the force awakens|the last jedi|the rise of skywalker|"
        r"the mandalorian(?:\s+and\s+grogu)?|revenge of the sith|"
        r"attack of the clones|the phantom menace)\s+",
        "",
        cleaned2,
        flags=re.I,
    )
    cleaned2 = re.sub(r"^vehicle model\s*#?\d*\s*", "", cleaned2, flags=re.I).strip()
    cleaned2 = re.sub(r"\(\s*pre-?order\s*\)", "", cleaned2, flags=re.I).strip()
    name = re.sub(r"\s+", " ", cleaned2 or cleaned).strip()[:120]
    # unwrap leftover leading punctuation from partial strip
    name = name.strip(" -|:.#()")
    if name.startswith("(") and ")" in name:
        name = name.strip("()")
    subtitle = line[:120]
    return name or cleaned[:120], subtitle


def collect_bandai_products() -> tuple[list[dict], list[str], list[str]]:
    feeds_used: list[str] = []
    feeds_rejected: list[str] = []
    seen: set[str] = set()
    out: list[dict] = []

    def add(p: dict, feed: str) -> None:
        if not bandai_is_kit_product(p):
            return
        handle = str(p.get("handle") or p.get("title") or "")
        variant = (p.get("variants") or [{}])[0] or {}
        jan = extract_jan_gtin(
            variant.get("barcode"),
            variant.get("sku"),
            first_image(p) or "",
        )
        if jan:
            key = f"jan:{jan}"
            if key in seen:
                return
            seen.add(key)
        else:
            title_key = f"t:{(p.get('title') or '').strip().lower()}"
            feed_key = f"{feed}:{(handle or '').lower()}"
            if title_key in seen or feed_key in seen:
                return
            seen.add(title_key)
            seen.add(feed_key)
        p = dict(p)
        p["_feed"] = feed
        if jan:
            p["_jan"] = jan
        out.append(p)

    # --- Gundam Planet (primary; strong BANDAI SPIRITS: Hobby + JAN in sku) ---
    try:
        gp = fetch_products("https://www.gundamplanet.com", 55)
        n = 0
        for p in gp:
            vendor = str(p.get("vendor") or "")
            if not re.search(r"bandai|spirits:\s*hobby", vendor, re.I):
                continue
            before = len(out)
            add(p, "gundamplanet")
            if len(out) > before:
                n += 1
        feeds_used.append(f"https://www.gundamplanet.com (Bandai hobby kits≈{n})")
    except Exception as e:
        feeds_rejected.append(f"https://www.gundamplanet.com — {e}")

    # --- USA Gundam Store (Star Wars kits + Bandai gunpla) ---
    try:
        usa = fetch_products("https://www.usagundamstore.com", 80)
        n = 0
        for p in usa:
            vendor = str(p.get("vendor") or "")
            title = str(p.get("title") or "")
            if not (
                re.search(r"^bandai$|bandai", vendor, re.I)
                or re.search(r"star wars", title, re.I)
            ):
                continue
            before = len(out)
            add(p, "usagundamstore")
            if len(out) > before:
                n += 1
        feeds_used.append(f"https://www.usagundamstore.com (Bandai/SW kits≈{n})")
    except Exception as e:
        feeds_rejected.append(f"https://www.usagundamstore.com — {e}")

    # --- ToyArena Gundam collection ---
    try:
        ta = fetch_collection("https://www.toyarena.com", "gundam", 8)
        n = 0
        for p in ta:
            before = len(out)
            add(p, "toyarena")
            if len(out) > before:
                n += 1
        feeds_used.append(f"https://www.toyarena.com/collections/gundam (kits≈{n})")
    except Exception as e:
        feeds_rejected.append(f"https://www.toyarena.com/collections/gundam — {e}")

    # --- Japan Figure grade collections ---
    for handle in ("hg", "rg", "mg", "plastic-model"):
        try:
            jf = fetch_collection("https://www.japan-figure.com", handle, 6 if handle != "plastic-model" else 4)
            n = 0
            for p in jf:
                if not re.search(r"bandai", f"{p.get('vendor')} {p.get('title')}", re.I):
                    continue
                before = len(out)
                add(p, "japan-figure")
                if len(out) > before:
                    n += 1
            feeds_used.append(f"https://www.japan-figure.com/collections/{handle} (Bandai≈{n})")
        except Exception as e:
            feeds_rejected.append(f"https://www.japan-figure.com/collections/{handle} — {e}")

    # --- ToyDojo Bandai collection (kit filter) ---
    try:
        td = fetch_collection("https://www.toydojo.com", "bandai", 6)
        n = 0
        for p in td:
            before = len(out)
            add(p, "toydojo")
            if len(out) > before:
                n += 1
        feeds_used.append(f"https://www.toydojo.com/collections/bandai (kits≈{n})")
    except Exception as e:
        feeds_rejected.append(f"https://www.toydojo.com/collections/bandai — {e}")

    # Rejected first-party / HLJ / etc.
    for base, why in [
        ("https://shop.bandai.com", "HTML storefront, no products.json"),
        ("https://bandai-hobby.net", "HTML, no products.json"),
        ("https://www.bandaihobbyusa.com", "HTML, no products.json"),
        ("https://p-bandai.com", "404 / no products.json"),
        ("https://p-bandai.us", "DNS miss"),
        ("https://www.hlj.com", "404 on products.json (blocked)"),
        ("https://www.hobby-link.com", "SSL hostname mismatch"),
        ("https://www.newtype.us", "HTML (non-Shopify JSON)"),
        ("https://www.amiami.com", "406 / non-Shopify"),
        ("https://www.plazajapan.com", "404 on products.json"),
    ]:
        feeds_rejected.append(f"{base} — {why}")

    return out, feeds_used, feeds_rejected


def densify_seed_gunpla(urls: dict, sku_map: dict, aliases: dict, products: list[dict]) -> dict:
    """Fill CDN image + GTIN overlays for seed gp-* rows (figures.ts) without inventing."""
    seed_specs = [
        ("gp-rg-rx78", "rx-78-2", "real grade"),
        ("gp-rg-sazabi", "sazabi", "real grade"),
        ("gp-rg-wing-zero", "wing gundam zero", "real grade"),
        ("gp-rg-god", "god gundam", "real grade"),
        ("gp-rg-hi-nu", "hi-nu", "real grade"),
        ("gp-rg-nu", "nu gundam", "real grade"),
        ("gp-mg-unicorn", "unicorn gundam", "master grade"),
        ("gp-mg-zaku", "zaku ii", "master grade"),
        ("gp-mg-exia", "exia", "master grade"),
        ("gp-mg-barbatos", "barbatos", "master grade"),
        ("gp-hg-aerial", "aerial", "high grade"),
        ("gp-eg-rx78", "rx-78-2", "entry grade"),
        ("gp-pg-strike", "strike freedom", "perfect grade"),
        ("gp-pg-unicorn", "unicorn gundam", "perfect grade"),
    ]
    imaged = 0
    skued = 0
    for sid, name_key, grade_key in seed_specs:
        if sid in urls and sku_map.get(sid):
            continue
        best = None
        best_score = 0.0
        for p in products:
            title = str(p.get("title") or "").lower()
            tags = " ".join(p.get("tags") if isinstance(p.get("tags"), list) else [str(p.get("tags") or "")])
            line, sub, _ = bandai_grade_line(str(p.get("title") or ""), str(p.get("product_type") or ""), tags)
            if grade_key not in f"{line} {sub}".lower() and grade_key not in title:
                continue
            if name_key not in title:
                continue
            # prefer exact-ish
            score = 0.6
            if re.search(rf"\b{re.escape(name_key)}\b", title):
                score += 0.2
            if grade_key in title:
                score += 0.1
            if score > best_score:
                best_score = score
                best = p
        if not best or best_score < 0.7:
            continue
        img = first_image(best)
        if img and sid not in urls:
            urls[sid] = img
            imaged += 1
        variant = (best.get("variants") or [{}])[0] or {}
        jan = best.get("_jan") or extract_jan_gtin(
            variant.get("barcode"), variant.get("sku"), img or ""
        )
        listing = clean_code(variant.get("sku")) or (
            str(variant.get("sku")).strip() if variant.get("sku") else None
        )
        if jan and not sku_map.get(sid):
            sku_map[sid] = jan
            skued += 1
        if listing:
            add_aliases(aliases, sid, [listing])
    return {"seedImages": imaged, "seedSkus": skued}


def inject_bandai_kits(rows: list[dict], aliases: dict, urls: dict, sku_map: dict) -> dict:
    products, feeds_used, feeds_rejected = collect_bandai_products()
    seed_stats = densify_seed_gunpla(urls, sku_map, aliases, products)

    # Never reclass existing Bandai AF rows (Robot Spirits / Gundam Universe / etc.)
    af_left_alone = sum(
        1
        for r in rows
        if r.get("company") == "bandai" and (r.get("kind") or "figure") != "kit"
    )

    ids, keys = existing_keys(rows)
    # also respect seed key space so UI merge won't hide imaged oneshot behind bare seed
    # Use grade lines for new rows (LINES_BY_COMPANY tags); seed keeps line=Gunpla.
    existing_bandai_kit_names = {
        (r.get("name") or "").lower()
        for r in rows
        if r.get("company") == "bandai" and r.get("kind") == "kit"
    }
    known_codes: set[str] = set()
    for r in rows:
        if r.get("company") != "bandai":
            continue
        if r.get("sku"):
            known_codes.add(clean_code(r["sku"]) or r["sku"])
        for a in (aliases.get("aliasesByFigureId") or {}).get(r["id"]) or []:
            known_codes.add(a)
    for v in sku_map.values():
        if isinstance(v, str):
            known_codes.add(clean_code(v) or v)

    added: list[str] = []
    skipped = Counter()
    by_line: Counter = Counter()
    gtin_n = 0

    for p in products:
        title = str(p.get("title") or "").strip()
        if not title:
            skipped["no_title"] += 1
            continue
        tags = " ".join(p.get("tags") if isinstance(p.get("tags"), list) else [str(p.get("tags") or "")])
        line, sub_hint, scale_default = bandai_grade_line(title, str(p.get("product_type") or ""), tags)
        name, subtitle = bandai_name_from_title(title, sub_hint)
        if not name or len(name) < 2 or name.lower() in {
            "bandai", "gundam", "gunpla", "model kit", "plastic model", "star wars"
        }:
            skipped["bad_name"] += 1
            continue

        handle = str(p.get("handle") or slug(title))
        feed = p.get("_feed") or "shop"
        rid = f"sf-bandai-{feed}-{handle}"[:80]
        if rid in ids:
            skipped["id"] += 1
            continue

        key = f"{name}|{subtitle}|{line}|bandai".lower()
        if key in keys:
            skipped["key"] += 1
            continue
        # soft skip near-duplicate names on same line
        if name.lower() in existing_bandai_kit_names:
            # allow same MS across grades (RX-78 EG vs RG) — only skip same line
            if any(
                r.get("company") == "bandai"
                and r.get("kind") == "kit"
                and (r.get("name") or "").lower() == name.lower()
                and (r.get("line") or "").lower() == line.lower()
                for r in rows
            ):
                skipped["soft_name"] += 1
                continue

        variant = (p.get("variants") or [{}])[0] or {}
        listing = clean_code(variant.get("sku")) or (
            str(variant.get("sku")).strip() if variant.get("sku") else None
        )
        img = first_image(p)
        jan = p.get("_jan") or extract_jan_gtin(variant.get("barcode"), variant.get("sku"), img or "")
        if listing and listing in known_codes and not jan:
            skipped["known_listing"] += 1
            continue
        if jan and jan in known_codes:
            skipped["known_gtin"] += 1
            continue

        # Prefer empty image over wrong — allow new rows without image
        scale = scale_default
        m = re.search(r"\b(1/\d+)\b", title)
        if m:
            scale = m.group(1)
        msrp = parse_money(variant.get("price")) or 25.0

        row = {
            "id": rid,
            "name": name[:120],
            "subtitle": (subtitle or line)[:120],
            "line": line[:80],
            "company": "bandai",
            "kind": "kit",
            "releaseDate": date_from(p, "2015-01-01"),
            "msrp": round(float(msrp), 2),
            "scale": scale,
            "demand": 1.0,
            "tags": [
                "archive",
                "shopify",
                "bandai",
                "kit",
                "gunpla" if "star wars" not in line.lower() else "star-wars",
                "inject-model-kits",
                feed,
                slug(line)[:32],
            ],
            "source": "shopify",
        }
        if jan:
            row["sku"] = jan
            gtin_n += 1
        if img:
            row["imageUrl"] = img
            urls[rid] = img
        rows.append(row)
        ids.add(rid)
        keys.add(key)
        existing_bandai_kit_names.add(name.lower())
        if jan:
            known_codes.add(jan)
        if listing:
            add_aliases(aliases, rid, [listing])
            known_codes.add(listing)
        added.append(rid)
        by_line[line] += 1

    return {
        "productsSeen": len(products),
        "feedsUsed": feeds_used,
        "feedsRejected": feeds_rejected,
        "kitsAdded": len(added),
        "withGtin": gtin_n,
        "byLine": dict(by_line),
        "afRowsLeftAlone": af_left_alone,
        "seedDensify": seed_stats,
        "kitIds": added[:50],
        "skipped": dict(skipped),
    }


# ---- SoSkill ----

def probe_soskill() -> dict:
    rejected = []
    candidates = [
        "https://soskill.com",
        "https://www.soskill.com",
        "https://soskilltoys.com",
        "https://www.soskilltoys.com",
        "https://soskill.myshopify.com",
        "https://shop.soskill.com",
        "https://soskill.store",
        "https://shop.soskilltoys.com",
        "https://soskillofficial.com",
        "https://topgkstore.com",
    ]
    found = None
    for base in candidates:
        url = f"{base.rstrip('/')}/products.json?limit=50"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read()
            if raw[:1] == b"<":
                rejected.append(f"{base} — HTML, not Shopify products.json")
                continue
            d = json.loads(raw)
            ps = d.get("products") or []
            # check vendor hits
            hits = [
                p
                for p in ps
                if re.search(r"soskill|so\s*skill", f"{p.get('vendor')} {p.get('title')}", re.I)
            ]
            if ps and (hits or "soskill" in base.lower()):
                found = {"base": base, "products": len(ps), "vendorHits": len(hits)}
                break
            rejected.append(f"{base} — JSON but 0 usable SoSkill products")
        except Exception as e:
            rejected.append(f"{base} — {type(e).__name__}: {e}")

    # specialty sample (ToyArena already scanned in flame pass context)
    rejected.append("ToyArena/PlanetAF full scans — 0 SoSkill vendor hits")
    rejected.append("showzstore.com / robotkingdom.com — non-Shopify or blocked")

    if found:
        return {"found": found, "added": 0, "note": "Feed found but inject deferred pending GTIN audit", "rejected": rejected}
    return {
        "added": 0,
        "note": "No verified Shopify products.json; CompanyId reserved; leave 0 rather than invent",
        "rejected": rejected,
    }


def main() -> int:
    apply = "--dry-run" not in sys.argv
    bandai_only = "--bandai-only" in sys.argv
    rows = load_json(ARCHIVE)
    aliases = ensure_alias_doc(load_json(ALIASES) if ALIASES.exists() else {})
    sku_map = load_json(SKU_MAP) if SKU_MAP.exists() else {}
    urls = load_json(URLS) if URLS.exists() else {}
    if not isinstance(sku_map, dict):
        sku_map = {}
    if not isinstance(urls, dict):
        urls = {}

    brands = {"blokees", "flametoys", "soskill", "yolopark", "bandai"}
    before = brand_counts(rows, urls, brands)
    report: dict[str, Any] = {"at": now_iso(), "before": before, "apply": apply, "bandaiOnly": bandai_only}

    if not bandai_only:
        report["blokees"] = reclass_and_densify_blokees(rows, aliases, urls)
        report["flametoys"] = inject_flame_toys(rows, aliases, urls)
        report["soskill"] = probe_soskill()
    else:
        report["blokees"] = {"skipped": True, "note": "--bandai-only"}
        report["flametoys"] = {"skipped": True, "note": "--bandai-only"}
        report["soskill"] = {"skipped": True, "note": "--bandai-only", "added": 0}

    report["bandai"] = inject_bandai_kits(rows, aliases, urls, sku_map)

    after = brand_counts(rows, urls, brands)
    report["after"] = after
    report["ui"] = {
        "kitsFilter": "src/routes/figures/index.tsx view=kits filters kind===kit",
        "lineTags": "LINES_BY_COMPANY picks up High Grade / Real Grade / Master Grade / Perfect Grade / Entry Grade / SD Gundam / Figure-rise / 30MM / Star Wars Vehicle Model",
        "change": "Bandai kits appear under Kits; existing Bandai AF rows untouched",
    }
    aliases["updatedAt"] = now_iso()

    summary = {
        "before": before,
        "after": after,
        "bandai": {
            "kitsAdded": report["bandai"]["kitsAdded"],
            "withGtin": report["bandai"]["withGtin"],
            "byLine": report["bandai"]["byLine"],
            "afLeftAlone": report["bandai"]["afRowsLeftAlone"],
            "seedDensify": report["bandai"]["seedDensify"],
            "feedsUsed": report["bandai"]["feedsUsed"],
            "feedsRejected": report["bandai"]["feedsRejected"][:8],
        },
        "soskill": report.get("soskill", {}).get("added", 0),
    }
    print(json.dumps(summary, indent=2))

    if apply:
        write_json(ARCHIVE, rows)
        write_json(ALIASES, aliases)
        write_json(SKU_MAP, sku_map)
        write_json(URLS, urls)
        write_json(STATS, report)
        print(f"wrote {ARCHIVE}")
        print(f"wrote {STATS}")
    else:
        write_json(Path("/tmp/model-kits-inject-dry.json"), report)
        print("dry-run only → /tmp/model-kits-inject-dry.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
