#!/usr/bin/env python3
"""Phase A cleanup + Phase B inject for Blokees / Jada / JAKKS / Yolopark / SoSkill.

- Demote non-GTIN primary skus → aliases (these brands only)
- Remove Jada Nano Metalfigs (die-cast, not AF)
- Collapse high-confidence Jada Street Fighter listing↔GTIN / identical dupes
- Inject missing Blokees from blokees.com Shopify (listing→alias; CDN images)
- Inject Yolopark AMK model kits from shop.yolopark.com
- Inject missing Jada / JAKKS from product-sku-index (GTIN when known + CDN image)
- SoSkill: no verified feed — CompanyId only; document rejected sources
- Never invent SKUs/EANs or AI art. Prefer empty image over wrong photo.
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
SKU_INDEX = ROOT / "src/data/figure-archive/product-sku-index.json"
IMG_INDEX = ROOT / "src/data/figure-archive/product-image-index.json"
STATS = ROOT / "src/data/figure-archive/small-brands-inject-stats.json"

BRANDS = {"blokees", "jada", "jakks", "yolopark", "soskill"}
UA = "KryptonsToyVault/1.0 (personal collection; permanent archive dump)"
WEAK = {
    "the", "and", "of", "a", "an", "series", "version", "class", "champion",
    "galaxy", "defender", "blokees", "transformers", "gundam", "action",
    "figure", "figures", "model", "kit", "kits", "jada", "toys", "jakks",
    "pacific", "wave", "deluxe", "exclusive", "inch", "scale", "amk", "pro",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def tokens(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9']+", (s or "").lower()) if t not in WEAK and len(t) > 1}


def fetch_products(base: str, max_pages: int = 20) -> list[dict]:
    out: list[dict] = []
    for page in range(1, max_pages + 1):
        url = f"{base.rstrip('/')}/products.json?limit=250&page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.loads(r.read())
        ps = d.get("products") or []
        if not ps:
            break
        out.extend(ps)
        if len(ps) < 250:
            break
        time.sleep(0.4)
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


def demote_listing_primaries(rows: list[dict], aliases: dict, sku_map: dict) -> dict:
    cleared = 0
    details = []
    for r in rows:
        if r.get("company") not in BRANDS:
            continue
        sku = clean_code(r.get("sku"))
        if not sku or is_gtin(sku):
            continue
        add_aliases(aliases, r["id"], [sku])
        details.append({"id": r["id"], "company": r["company"], "listing": sku})
        r.pop("sku", None)
        if r["id"] in sku_map and not is_gtin(clean_code(sku_map.get(r["id"]))):
            sku_map.pop(r["id"], None)
        tags = r.get("tags") or []
        if isinstance(tags, list):
            r["tags"] = [t for t in tags if t not in {"sku-bake", "sku-gtin"}]
        cleared += 1
    return {"cleared": cleared, "details": details[:80]}


def remove_nano_metalfigs(rows: list[dict], aliases: dict, sku_map: dict, urls: dict) -> list[str]:
    drop = []
    kept = []
    for r in rows:
        line = (r.get("line") or "").lower()
        name = (r.get("name") or "").lower()
        if r.get("company") == "jada" and (
            "nano metalfig" in line or "nano metalfig" in name or "nano chase" in name
        ):
            drop.append(r["id"])
            aliases.get("aliasesByFigureId", {}).pop(r["id"], None)
            sku_map.pop(r["id"], None)
            urls.pop(r["id"], None)
            continue
        kept.append(r)
    rows[:] = kept
    to = aliases.get("aliasToFigureId") or {}
    for k, v in list(to.items()):
        if v in drop:
            to.pop(k, None)
    return drop


def collapse_jada_sf_dupes(rows: list[dict], aliases: dict, sku_map: dict, urls: dict) -> dict:
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r.get("company") != "jada":
            continue
        blob = f"{r.get('line')} {r.get('subtitle')}".lower()
        if "street" not in blob and "fighter" not in blob:
            continue
        by[r["name"].lower().strip()].append(r)

    collapsed = []
    flagged = []
    drop_ids: set[str] = set()

    for name, group in by.items():
        if len(group) < 2:
            continue
        gtins = []
        for r in group:
            s = clean_code(r.get("sku"))
            if s and is_gtin(s):
                gtins.append((r, s))
        uniq_gtin = {g for _, g in gtins}
        if len(uniq_gtin) > 1:
            flagged.append({
                "name": name,
                "ids": [r["id"] for r in group],
                "gtins": sorted(uniq_gtin),
                "reason": "distinct GTINs — leave both",
            })
            continue

        def rank(r: dict) -> tuple:
            s = clean_code(r.get("sku"))
            has_g = 1 if s and is_gtin(s) else 0
            has_img = 1 if r.get("imageUrl") or r["id"] in urls else 0
            prefer_id = 1 if r["id"].startswith("jada-sf-") else 0
            return (has_g, has_img, prefer_id)

        keep = sorted(group, key=rank, reverse=True)[0]
        for r in group:
            if r["id"] == keep["id"]:
                continue
            codes = []
            s = clean_code(r.get("sku"))
            if s:
                codes.append(s)
            codes.extend((aliases.get("aliasesByFigureId") or {}).get(r["id"]) or [])
            add_aliases(aliases, keep["id"], codes)
            if not keep.get("imageUrl") and r.get("imageUrl"):
                keep["imageUrl"] = r["imageUrl"]
            if keep["id"] not in urls and r["id"] in urls:
                urls[keep["id"]] = urls[r["id"]]
            if keep["id"] not in sku_map and r["id"] in sku_map:
                sm = sku_map[r["id"]]
                if is_gtin(clean_code(sm)):
                    sku_map[keep["id"]] = sm
            drop_ids.add(r["id"])
            sku_map.pop(r["id"], None)
            urls.pop(r["id"], None)
            (aliases.get("aliasesByFigureId") or {}).pop(r["id"], None)
            collapsed.append({"keepId": keep["id"], "dropId": r["id"], "name": name})
            aliases.setdefault("collapsed", []).append({
                "keepId": keep["id"], "dropId": r["id"], "reason": "jada SF same-name",
            })

    if drop_ids:
        rows[:] = [r for r in rows if r["id"] not in drop_ids]
        to = aliases.get("aliasToFigureId") or {}
        for k, v in list(to.items()):
            if v in drop_ids:
                to.pop(k, None)
    for f in flagged:
        aliases.setdefault("flagged", []).append(f)
    return {"collapsed": collapsed, "flagged": flagged}


def existing_keys(rows: list[dict]) -> tuple[set[str], set[str]]:
    ids = {r["id"] for r in rows}
    keys = {f"{r['name']}|{r.get('subtitle')}|{r.get('line')}|{r.get('company')}".lower() for r in rows}
    return ids, keys


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


def blokees_keep(title: str, tags: Any) -> bool:
    blob = f"{title} {' '.join(tags) if isinstance(tags, list) else tags or ''}"
    if re.search(r"\b(t-?shirt|hoodie|mug|sticker|poster|plush|keychain|acrylic|magnet|apparel|gift.?card)\b", blob, re.I):
        return False
    if re.search(r"\b(daadoos mate|daadoos nest|daadoos art|mokoo|buddy emblem)\b", blob, re.I):
        return False
    if re.search(r"\bwheels\b", blob, re.I) and not re.search(r"champion|galaxy|defender|model kit", blob, re.I):
        return False
    return bool(re.search(
        r"champion class|galaxy version|defender version|shining version|legend edition|"
        r"model kit|ultraman|saint seiya|gundam|transformers|marvel rivals|star wars|"
        r"naruto|evangelion|herospire|terraventure|jurassic|dc defender|astral rally",
        blob, re.I,
    ))


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


def inject_blokees(rows: list[dict], aliases: dict) -> dict:
    products = fetch_products("https://blokees.com", 10)
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
        handle = str(p.get("handle") or slug(title))
        rid = f"sf-blokees-{handle}"[:80]
        if rid in ids:
            skipped["id"] += 1
            continue
        name, subtitle = split_title(title)
        line = "Blokees"
        tl = title.lower()
        if "champion class" in tl:
            line = "Blokees Champion Class"
        elif "galaxy version" in tl:
            line = "Blokees Galaxy Version"
        elif "defender version" in tl:
            line = "Blokees Defender Version"
        elif "shining version" in tl:
            line = "Blokees Shining Version"
        elif "legend edition" in tl:
            line = "Blokees Legend Edition"
        key = f"{name}|{subtitle or line}|{line}|blokees".lower()
        if key in keys:
            skipped["key"] += 1
            continue
        if soft_name_hit(name, existing_names) and len(tokens(name)) <= 3 and len(tokens(title)) <= 6:
            skipped["soft_name"] += 1
            continue

        variant = (p.get("variants") or [{}])[0] or {}
        listing = clean_code(variant.get("sku")) or (str(variant.get("sku")).strip() if variant.get("sku") else None)
        barcode = clean_code(variant.get("barcode"))
        primary = barcode if barcode and is_gtin(barcode) else None
        if listing and listing in known_codes and not primary:
            skipped["known_listing"] += 1
            continue

        img = None
        for im in p.get("images") or []:
            src = (im or {}).get("src")
            if src and str(src).startswith("http"):
                img = str(src)
                break

        msrp = parse_money(variant.get("price")) or 24.99
        row = {
            "id": rid,
            "name": name[:120],
            "subtitle": (subtitle or line)[:120],
            "line": line[:80],
            "company": "blokees",
            "kind": "figure",
            "releaseDate": date_from(p, "2024-01-01"),
            "msrp": round(float(msrp), 2),
            "scale": '6"',
            "demand": 1.0,
            "tags": ["archive", "shopify", "blokees", "figure", "inject-small-brands"],
            "source": "shopify",
        }
        if primary:
            row["sku"] = primary
        if img:
            row["imageUrl"] = img
        rows.append(row)
        ids.add(rid)
        keys.add(key)
        existing_names.add(name)
        if listing:
            add_aliases(aliases, rid, [listing])
            known_codes.add(listing)
        added.append(rid)
    return {"fetched": len(products), "added": len(added), "skipped": dict(skipped), "ids": added[:40]}


def yolopark_keep(title: str) -> bool:
    if re.search(r"\b(key-?chain|keychain|acrylic|magnet|sticker|card\b|fridge|apparel|t-?shirt|mug|poster|wooden playset|peppa)\b", title, re.I):
        return False
    return bool(re.search(r"\b(AMK|Model Kit|Mech Model)\b", title, re.I))


def inject_yolopark(rows: list[dict], aliases: dict) -> dict:
    products = fetch_products("https://shop.yolopark.com", 10)
    ids, keys = existing_keys(rows)
    added = []
    skipped = Counter()
    for p in products:
        title = str(p.get("title") or "").strip()
        if not title or not yolopark_keep(title):
            skipped["filter"] += 1
            continue
        handle = str(p.get("handle") or slug(title))
        rid = f"sf-yolopark-{handle}"[:80]
        if rid in ids:
            skipped["id"] += 1
            continue
        name, subtitle = split_title(title)
        m = re.search(r"-\s*([\d.]+cm\s+)?(.+?)\s+Model Kit", title, re.I)
        if m:
            name = m.group(2).strip()
        line = "Yolopark AMK"
        if re.search(r"AMK PRO", title, re.I):
            line = "Yolopark AMK PRO"
        elif re.search(r"AMK Mini", title, re.I):
            line = "Yolopark AMK Mini"
        fran = ""
        for pat, lab in [
            (r"Beast Wars", "Beast Wars"),
            (r"Rise of the Beasts", "Rise of the Beasts"),
            (r"The Last Knight", "The Last Knight"),
            (r"Bumblebee", "Bumblebee"),
            (r"Generation 1|\bG1\b", "Generation 1"),
            (r"Voltes V", "Voltes V"),
            (r"SHURATO", "Shurato"),
            (r"Transformers", "Transformers"),
        ]:
            if re.search(pat, title, re.I):
                fran = lab
                break
        subtitle = fran or subtitle or line
        key = f"{name}|{subtitle}|{line}|yolopark".lower()
        if key in keys:
            skipped["key"] += 1
            continue
        variant = (p.get("variants") or [{}])[0] or {}
        listing = clean_code(variant.get("sku")) or (str(variant.get("sku")).strip() if variant.get("sku") else None)
        barcode = clean_code(variant.get("barcode"))
        primary = barcode if barcode and is_gtin(barcode) else None
        img = None
        for im in p.get("images") or []:
            src = (im or {}).get("src")
            if src and str(src).startswith("http"):
                img = str(src)
                break
        scale = '7"'
        cm = re.search(r"([\d.]+)\s*cm", title, re.I)
        if cm:
            try:
                scale = f'{round(float(cm.group(1)) / 2.54, 1)}"'
            except Exception:
                pass
        msrp = parse_money(variant.get("price")) or 39.99
        row = {
            "id": rid,
            "name": name[:120],
            "subtitle": subtitle[:120],
            "line": line,
            "company": "yolopark",
            "kind": "kit",
            "releaseDate": date_from(p, "2023-01-01"),
            "msrp": round(float(msrp), 2),
            "scale": scale,
            "demand": 1.0,
            "tags": ["archive", "shopify", "yolopark", "amk", "kit", "inject-small-brands"],
            "source": "shopify",
        }
        if primary:
            row["sku"] = primary
        if img:
            row["imageUrl"] = img
        rows.append(row)
        ids.add(rid)
        keys.add(key)
        if listing:
            add_aliases(aliases, rid, [listing])
        added.append(rid)
    return {"fetched": len(products), "added": len(added), "skipped": dict(skipped), "ids": added[:40]}


def inject_from_sku_index(rows: list[dict], aliases: dict, company: str) -> dict:
    index = load_json(SKU_INDEX)
    img_index = load_json(IMG_INDEX) if IMG_INDEX.exists() else []
    img_by_id = {e.get("id"): e.get("imageUrl") for e in img_index if e.get("imageUrl")}
    img_by_title = {}
    for e in img_index:
        if e.get("company") == company and e.get("imageUrl") and e.get("title"):
            img_by_title[e["title"].lower()] = e["imageUrl"]

    ids, keys = existing_keys(rows)
    existing_names = {r["name"].lower() for r in rows if r.get("company") == company}
    known_gtin = {
        clean_code(r.get("sku"))
        for r in rows
        if r.get("company") == company and is_gtin(clean_code(r.get("sku")))
    }

    cands = [p for p in index if p.get("company") == company]
    added = []
    skipped = Counter()
    seen_title = set()

    for p in cands:
        title = str(p.get("title") or "").strip()
        if not title:
            skipped["no_title"] += 1
            continue
        tl = title.lower()
        if tl in seen_title:
            skipped["dup_title"] += 1
            continue
        seen_title.add(tl)
        if re.search(r"\b(nano metalfig|die.?cast|hot wheels|bag clip|keychain|plush)\b", tl):
            skipped["non_af"] += 1
            continue
        sku = clean_code(p.get("sku"))
        gtin = sku if sku and is_gtin(sku) else None
        listing = sku if sku and not gtin else None
        if gtin and gtin in known_gtin:
            skipped["known_gtin"] += 1
            continue

        # Skip multipacks / damaged / non-single AF
        if re.search(r"\b(\d[\s-]?pack|bundle|multipack|sub[- ]standard|damaged|empty box|accessory set|you lose|playset|battle set)\b", tl):
            skipped["pack"] += 1
            continue

        name = title
        name = re.sub(r"^\s*(?:sdcc\s*\d{4}\s*)?", "", name, flags=re.I)
        name = re.sub(r"^\s*jada\s*toys\s*", "", name, flags=re.I)
        name = re.sub(r"^\s*jakks(?:\s*pacific)?\s*", "", name, flags=re.I)
        name = re.sub(r"\b\d+(?:\.\d+)?\s*inch\b", " ", name, flags=re.I)
        name = re.sub(r"\b1/?12(?:\s*scale)?\b", " ", name, flags=re.I)
        name = re.sub(r"\baction\s+figures?\b", " ", name, flags=re.I)
        name = re.sub(r"\bultra\s+street\s+fighter\s+ii(?:\s*:\s*the\s+final\s+challengers)?\b", "Street Fighter", name, flags=re.I)
        name = re.sub(r"\bstreet\s+fighter\s*2\b", "Street Fighter", name, flags=re.I)
        name = re.sub(r"\s+", " ", name).strip(" -|")
        parts = re.split(r"\s+[—–-]\s+", name)
        if len(parts) >= 2:
            # prefer last segment if it looks like character name
            last = parts[-1].strip()
            if 1 < len(last) < 60 and not re.search(r"street fighter|universal|marvel|nintendo", last, re.I):
                name = last
            elif len(parts) >= 2:
                name = parts[-1].strip()
        # strip leftover line prefixes
        name = re.sub(r"^(?:deluxe|exclusive|wave\s*\d+)\s*[-:]?\s*", "", name, flags=re.I).strip()
        name = name[:120] or title[:120]
        # If still looks like full retailer title, try character after " - "
        if len(name) > 48 and " - " in title:
            name = title.split(" - ")[-1].strip()[:120]
        # Strip franchise prefix only when a solid character name remains
        stripped = re.sub(r"^(?:street\s*fighter(?:\s*\d+)?|universal\s*monsters?|mega\s*man|megaman|sonic(?:\s*the\s*hedgehog)?|super\s*mario|world\s*of\s*nintendo)\s*[-:]?\s*", "", name, flags=re.I).strip()
        stripped = re.sub(r"\s+", " ", stripped).strip(" -|")
        if stripped and len(tokens(stripped)) >= 1 and not re.match(r"^(with|and|item|set|figure|deluxe)\b", stripped, re.I):
            name = stripped
        name = re.sub(r"\s+", " ", name).strip(" -|") or name
        if (
            len(tokens(name)) < 1
            or re.match(r"^(with|and|item|set|figure|deluxe|exclusive)\b", name, re.I)
            or len(name) < 3
        ):
            skipped["bad_name"] += 1
            continue

        if name.lower() in existing_names:
            skipped["name"] += 1
            continue
        # soft token collision with existing (avoid Ryu deluxe vs Ryu)
        if soft_name_hit(name, existing_names) and len(tokens(name)) <= 3:
            skipped["soft_name"] += 1
            continue

        line = "Jada Toys" if company == "jada" else "JAKKS Pacific"
        if company == "jada":
            if "street fighter" in tl:
                line = "Jada Street Fighter"
            elif "universal monster" in tl:
                line = "Jada Universal Monsters"
            elif re.search(r"\bmarvel\b|spider-?man|iron man|deadpool", tl):
                line = "Jada Marvel"
            elif re.search(r"\bdc\b|batman|superman|wonder woman", tl):
                line = "Jada DC"
            elif "megaman" in tl or "mega man" in tl:
                line = "Jada Mega Man"
            elif "cyberpunk" in tl:
                line = "Jada Cyberpunk"
            elif "invincible" in tl:
                line = "Jada Invincible"
        else:
            if "sonic" in tl:
                line = "JAKKS Sonic"
            elif "mario" in tl or "nintendo" in tl or "zelda" in tl or "link" in tl:
                line = "JAKKS Nintendo"
            elif re.search(r"\bwwe\b", tl):
                line = "JAKKS WWE"
            elif "universal monster" in tl:
                line = "JAKKS Universal Monsters"
            elif "primal age" in tl or "masters of the universe" in tl:
                line = "MotU Primal Age"

        subtitle = str(p.get("line") or p.get("shop") or line)[:120]
        key = f"{name}|{subtitle}|{line}|{company}".lower()
        if key in keys:
            skipped["key"] += 1
            continue

        img = p.get("imageUrl") or img_by_id.get(p.get("id")) or img_by_title.get(tl)
        if not img and not gtin:
            skipped["no_img_no_gtin"] += 1
            continue

        handle = slug(name)[:60]
        rid = f"inj-{company}-{handle}"[:80]
        n = 2
        base = rid
        while rid in ids:
            rid = f"{base}-{n}"[:80]
            n += 1

        row = {
            "id": rid,
            "name": name,
            "subtitle": subtitle,
            "line": line,
            "company": company,
            "kind": "figure",
            "releaseDate": "2022-01-01",
            "msrp": 24.99 if company == "jakks" else 29.99,
            "scale": '4"' if company == "jakks" and "sonic" in tl else '6"',
            "demand": 1.0,
            "tags": ["archive", "retailer-index", company, "figure", "inject-small-brands"],
            "source": "curated",
        }
        if gtin:
            row["sku"] = gtin
            known_gtin.add(gtin)
        if img:
            row["imageUrl"] = img
        rows.append(row)
        ids.add(rid)
        keys.add(key)
        existing_names.add(name.lower())
        if listing:
            add_aliases(aliases, rid, [listing])
        added.append(rid)

    return {"candidates": len(cands), "added": len(added), "skipped": dict(skipped), "ids": added[:40]}


def counts(rows: list[dict], urls: dict) -> dict:
    out = {}
    for b in sorted(BRANDS):
        sub = [r for r in rows if r.get("company") == b]
        out[b] = {
            "rows": len(sub),
            "sku": sum(1 for r in sub if r.get("sku")),
            "img": sum(1 for r in sub if r.get("imageUrl") or r["id"] in urls),
            "gtin": sum(1 for r in sub if is_gtin(clean_code(r.get("sku")))),
        }
    return out


def main() -> int:
    apply = "--dry-run" not in sys.argv
    rows = load_json(ARCHIVE)
    aliases = ensure_alias_doc(load_json(ALIASES) if ALIASES.exists() else {})
    sku_map = load_json(SKU_MAP) if SKU_MAP.exists() else {}
    urls = load_json(URLS) if URLS.exists() else {}
    if not isinstance(sku_map, dict):
        sku_map = {}
    if not isinstance(urls, dict):
        urls = {}

    before = counts(rows, urls)
    report: dict[str, Any] = {"at": now_iso(), "before": before, "apply": apply}

    report["demote"] = demote_listing_primaries(rows, aliases, sku_map)
    report["nanoRemoved"] = remove_nano_metalfigs(rows, aliases, sku_map, urls)
    report["jadaCollapse"] = collapse_jada_sf_dupes(rows, aliases, sku_map, urls)
    report["blokeesInject"] = inject_blokees(rows, aliases)
    report["yoloparkInject"] = inject_yolopark(rows, aliases)
    report["jadaInject"] = inject_from_sku_index(rows, aliases, "jada")
    report["jakksInject"] = inject_from_sku_index(rows, aliases, "jakks")
    report["soskill"] = {
        "added": 0,
        "note": "No verified Shopify products.json with variant.sku/GTIN; CompanyId reserved only",
        "rejected": [
            "https://soskill.com / www.soskill.com — SSL/EOF, not usable JSON",
            "https://soskilltoys.com — HTML (not Shopify products.json)",
            "https://soskill.myshopify.com — 404",
            "https://topgkstore.com — non-JSON / bot interstitial",
            "CmdStore/ToyArena/Nerdzoic/HobbyFigures/AFCollector page samples — 0 SoSkill vendor hits",
        ],
    }

    after = counts(rows, urls)
    report["after"] = after
    aliases["updatedAt"] = now_iso()

    print(json.dumps({
        "before": before,
        "after": after,
        "demote": report["demote"]["cleared"],
        "nano": report["nanoRemoved"],
        "jadaCollapsed": len(report["jadaCollapse"]["collapsed"]),
        "jadaFlagged": len(report["jadaCollapse"]["flagged"]),
        "blokeesAdded": report["blokeesInject"]["added"],
        "yoloparkAdded": report["yoloparkInject"]["added"],
        "jadaAdded": report["jadaInject"]["added"],
        "jakksAdded": report["jakksInject"]["added"],
    }, indent=2))

    if apply:
        write_json(ARCHIVE, rows)
        write_json(ALIASES, aliases)
        write_json(SKU_MAP, sku_map)
        write_json(URLS, urls)
        write_json(STATS, report)
        print(f"wrote {ARCHIVE}")
    else:
        write_json(Path("/tmp/small-brands-inject-dry.json"), report)
        print("dry-run only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
