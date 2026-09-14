#!/usr/bin/env python3
"""Listing densify from Mephitsu Hasbro + Jazwares hub caches into oneshot.

Cache-only (no crawl). GTIN preferred but not required. Prefer unique CDN images;
empty image over shared/wrong. Cap ~60–100 high-quality AF singles per fire.

Policy (Shelby/Lyra 2026-09-13):
  - Never invent GTINs/titles/codes
  - Dedupe on id, company+line+name+subtitle, company+line+name+year,
    and soft name+company+year+line-family
  - Skip multipacks / vs / sets / vehicles / shared gallery URLs
  - Does NOT Build Publish; does not touch comics
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/workspace/collection-app")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_identity import clean_code, is_gtin  # noqa: E402

ARCHIVE = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
SKU_MAP = ROOT / "src/data/figure-sku-map.json"
URLS = ROOT / "src/data/figure-image-urls.json"
STATS = ROOT / "src/data/figure-archive/mephitsu-listing-densify-stats.json"
ONESHOT_STATS = ROOT / "src/data/figure-archive/oneshot-stats.json"
MEPH_DIR = ROOT / "src/data/figure-archive/mephitsu"

SOURCE = "mephitsu-listing"
CAP = 90  # low-and-slow target within 60–100

MULTI_RE = re.compile(
    r"\b(?:vs\.?|2[\s\-]?pack|3[\s\-]?pack|4[\s\-]?pack|two[\s\-]?pack|"
    r"three[\s\-]?pack|multipack|multi[\s\-]?pack|battle\s*pack)\b",
    re.I,
)
VEHICLE_RE = re.compile(
    r"\b(?:starfighter|x[\s\-]?wing|tie\s|tank|ship|vehicle|warthog|banshee|"
    r"speeder|razor\s*crest|millennium|starship|micro\s*galaxy|fighter|"
    r"interceptor|destroyer|at[\s\-]?at|at[\s\-]?st)\b",
    re.I,
)
SET_RE = re.compile(r"\bset\b", re.I)
NON_AF_RE = re.compile(
    r"\b(?:idol|table|grail\s*table|stones?|prop|diorama|playset|accessory)\b",
    re.I,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def line_family(line: str | None) -> str:
    fam = re.sub(r"\b(series|collection|line)\b", "", norm(line))
    fam = re.sub(r"\s+", " ", fam).strip()
    # collapse gi joe / g.i. joe / classified variants
    fam = fam.replace("g i joe", "gi joe").replace("g.i joe", "gi joe")
    if "classified" in fam or fam == "gi joe":
        return "gi joe classified"
    if "lightning" in fam or "power ranger" in fam:
        return "lightning collection"
    if "indiana" in fam:
        return "indiana jones adventure"
    if "studio series" in fam:
        return "transformers studio series"
    if "world of halo" in fam or fam == "halo":
        return "world of halo"
    if "aew" in fam or "unrivaled" in fam:
        return "aew unrivaled"
    if "pokemon" in fam:
        return "pokemon select"
    if "fortnite" in fam:
        return "fortnite"
    return fam


def slugify(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("é", "e").replace("á", "a").replace("'", "").replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")[:48]


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


def row_key(r: dict) -> str:
    return "|".join(
        [
            (r.get("company") or "").lower(),
            (r.get("line") or "").lower(),
            (r.get("name") or "").lower(),
            (r.get("subtitle") or "").lower(),
        ]
    )


def fingerprint(company: str, line: str, name: str, year: str) -> str:
    return "|".join([company.lower(), norm(line), norm(name), str(year or "")[:4]])


def soft_key(company: str, line: str, name: str, year: str) -> str:
    return "|".join(
        [company.lower(), line_family(line), norm(name), str(year or "")[:4]]
    )


def name_line_key(company: str, line: str, name: str) -> str:
    """Anti-dupe within line-family ignoring year (same SKU listed with placeholder year)."""
    return "|".join([company.lower(), line_family(line), norm(name)])


def map_hasbro_line(raw_line: str, franchise: str | None) -> str | None:
    line = (raw_line or "").strip()
    low = line.lower()
    if "classified" in low or "g.i. joe" in low or "gi joe" in low:
        return "GI Joe Classified"
    if "power ranger" in low:
        return "Lightning Collection"
    if "studio series" in low:
        return "Transformers Studio Series"
    if low == "transformers":
        return "Transformers"  # honest generic; bake may refine
    if "indiana" in low:
        return "Indiana Jones Adventure Series"
    if "street fighter" in low:
        return "Street Fighter"
    if "ghostbuster" in low:
        return "Ghostbusters"
    if "fortnite" in low:
        return "Fortnite"
    if "dungeons" in low or "d&d" in low:
        return "Dungeons & Dragons"
    if "overwatch" in low:
        return "Overwatch"
    if "tron" in low:
        return "Tron"
    if "zelda" in low:
        return "The Legend of Zelda"
    return line or None


def map_jazwares_line(franchise: str | None, name: str) -> str:
    fr = (franchise or "").strip()
    low = fr.lower()
    blob = f"{fr} {name}".lower()
    if "aew" in low or "unrivaled" in blob:
        return "AEW Unrivaled"
    if "fortnite" in low:
        return "Fortnite"
    if "halo" in low:
        return "World of Halo"
    if "pokemon" in low:
        return "Pokemon Select"
    if "fnaf" in low or "five nights" in low:
        return "Five Nights at Freddy's"
    if "call of duty" in low or low == "cod":
        return "Call of Duty"
    return fr if fr and fr.lower() != "jazwares" else "Jazwares"


def defaults_for_line(line: str) -> tuple[float, str, float]:
    """msrp, scale, demand"""
    low = line.lower()
    if "classified" in low:
        return 24.99, '6"', 1.35
    if "lightning" in low:
        return 22.99, '6"', 1.25
    if "indiana" in low:
        return 24.99, '6"', 1.3
    if "street fighter" in low:
        return 29.99, '6"', 1.35
    if "studio series" in low:
        return 24.99, '6"', 1.3
    if line == "Transformers":
        return 24.99, '6"', 1.25
    if "fortnite" in low:
        return 12.99, '4"', 1.3
    if "halo" in low:
        return 14.99, '4"', 1.3
    if "aew" in low:
        return 24.99, '6"', 1.35
    if "pokemon" in low:
        return 24.99, '6"', 1.35
    if "call of duty" in low:
        return 19.99, '6"', 1.3
    if "ghostbuster" in low:
        return 22.99, '6"', 1.25
    return 24.99, '6"', 1.25


def parse_year(p: dict) -> int | None:
    try:
        y = int(str(p.get("year") or "").strip()[:4])
    except ValueError:
        return None
    if y < 1990 or y > 2035:
        return None
    return y


def extract_exclusive(p: dict) -> str | None:
    tags = [t for t in (p.get("tags") or []) if isinstance(t, str)]
    if not any(t.lower() == "exclusive" for t in tags):
        return None
    sub = p.get("subtitle") or ""
    # e.g. "Big Bad Toy Store · 2026 · GI Joe"
    part = sub.split("·")[0].strip() if "·" in sub else ""
    if part and part.lower() not in {"general", "exclusive", ""}:
        return part
    return "Exclusive"


def is_skip_product(p: dict, *, company: str) -> str | None:
    name = p.get("name") or ""
    title = p.get("title") or ""
    tags = [str(t).lower() for t in (p.get("tags") or [])]
    blob = " ".join([name, title, " ".join(tags)])
    if any("multi" in t for t in tags):
        return "multipack-tag"
    if MULTI_RE.search(blob):
        return "vs-multipack"
    if SET_RE.search(name):
        return "set"
    if " & " in name or re.search(r"\band\b", name, re.I):
        # dual figure packs / figure+pet — skip for singles densify
        return "dual-name"
    if VEHICLE_RE.search(name) or VEHICLE_RE.search(title):
        return "vehicle"
    y = parse_year(p)
    if y is None:
        return "no-year"
    if y > 2026:
        return "year>2026"
    if company == "hasbro" and NON_AF_RE.search(name) and "indiana" in (p.get("line") or "").lower():
        # allow character figures; skip obvious props
        if not re.search(
            r"\b(indiana|jones|marion|sallah|short\s*round|toht|belloq|"
            r"rene|renaldo|mola|willie|wu\s*han|kazim|vogel|donovan|"
            r"grail\s*knight|henry|marcus|elaine)\b",
            name,
            re.I,
        ):
            return "non-af-prop"
    fr = (p.get("franchise") or "").lower()
    if company == "jazwares" and fr == "star wars":
        return "star-wars-deprioritized"
    return None


def make_row(
    *,
    rid: str,
    name: str,
    subtitle: str,
    line: str,
    company: str,
    year: int,
    image: str | None,
    exclusive: str | None,
    extra_tags: list[str],
) -> dict:
    msrp, scale, demand = defaults_for_line(line)
    tags = ["mephitsu", "listing-densify", company, SOURCE] + extra_tags
    # dedupe tags preserving order
    seen: set[str] = set()
    tags2 = []
    for t in tags:
        if t and t not in seen:
            seen.add(t)
            tags2.append(t)
    out: dict[str, Any] = {
        "id": rid,
        "name": name,
        "subtitle": subtitle,
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
    if image:
        out["imageUrl"] = image
    if exclusive:
        out["exclusive"] = exclusive
    return out


def stable_id(p: dict) -> str:
    mid = str(p.get("mephitsuId") or p.get("productId") or p.get("handle") or "").strip()
    if mid:
        short = mid.replace("-", "")[:12]
        return f"mph-{short}"
    return f"mph-{slugify(p.get('name') or 'figure')}"


def load_meph_products(name: str) -> list[dict]:
    path = MEPH_DIR / f"{name}.json"
    if not path.exists():
        return []
    doc = load_json(path)
    return list(doc.get("products") or [])


def image_counts(products: list[dict]) -> Counter:
    return Counter(p.get("imageUrl") for p in products if p.get("imageUrl"))


def build_subtitle(p: dict, line: str, year: int) -> str:
    excl = extract_exclusive(p)
    wave = (p.get("wave") or "").strip()
    bits = []
    if excl and excl != "Exclusive":
        bits.append(excl)
    elif excl:
        bits.append("Exclusive")
    if wave and wave.lower() not in {"general", ""}:
        bits.append(wave)
    bits.append(str(year))
    # keep short honest subtitle
    base = " · ".join(bits) if bits else str(year)
    if line and line not in base:
        return f"{line} — {base}" if len(base) < 40 else base
    return base


def main() -> int:
    rows: list[dict] = load_json(ARCHIVE)
    aliases = ensure_alias_doc(load_json(ALIASES) if ALIASES.exists() else {})
    sku_map: dict = load_json(SKU_MAP) if SKU_MAP.exists() else {}
    urls: dict = load_json(URLS) if URLS.exists() else {}
    alias_to = aliases.get("aliasToFigureId") or {}

    ids = {r["id"] for r in rows}
    keys = {row_key(r) for r in rows}
    fps = {
        fingerprint(
            r.get("company") or "",
            r.get("line") or "",
            r.get("name") or "",
            (r.get("releaseDate") or "")[:4],
        )
        for r in rows
    }
    softs = {
        soft_key(
            r.get("company") or "",
            r.get("line") or "",
            r.get("name") or "",
            (r.get("releaseDate") or "")[:4],
        )
        for r in rows
    }
    name_lines = {
        name_line_key(r.get("company") or "", r.get("line") or "", r.get("name") or "")
        for r in rows
    }
    gtin_owned: dict[str, str] = {}
    for r in rows:
        s = clean_code(r.get("sku"))
        if s and is_gtin(s):
            gtin_owned[s] = r["id"]
    used_images = {
        (r.get("imageUrl") or "").strip()
        for r in rows
        if (r.get("imageUrl") or "").strip()
    }

    hasbro = load_meph_products("hasbro")
    jazwares = load_meph_products("jazwares")
    if not hasbro and not jazwares:
        print("ERROR: empty mephitsu caches")
        return 1

    h_img = image_counts(hasbro)
    j_img = image_counts(jazwares)

    candidates: list[tuple[int, str, dict, str, bool]] = []
    # tuple: priority, bucket, product, mapped_line, unique_img

    for p in hasbro:
        reason = is_skip_product(p, company="hasbro")
        if reason:
            continue
        mapped = map_hasbro_line(p.get("line") or "", p.get("franchise"))
        if not mapped:
            continue
        # Priority buckets per fire brief
        y = parse_year(p) or 0
        line_raw = (p.get("line") or "").lower()
        img = (p.get("imageUrl") or "").strip() or None
        unique = bool(img and h_img[img] == 1)
        if mapped == "GI Joe Classified" and 2024 <= y <= 2026:
            pri = 1 if unique else 11
            bucket = "hasbro-gijoe-classified"
        elif mapped in ("Indiana Jones Adventure Series", "Street Fighter"):
            pri = 2 if unique else 12
            bucket = (
                "hasbro-indiana"
                if mapped.startswith("Indiana")
                else "hasbro-street-fighter"
            )
        elif mapped == "Lightning Collection" and 2020 <= y <= 2026:
            # secondary AF fill after Classified/Indiana/SF
            if not unique:
                continue
            pri = 4
            bucket = "hasbro-lightning"
        elif mapped in ("Ghostbusters", "Overwatch", "Dungeons & Dragons", "Tron") and unique:
            pri = 5
            bucket = f"hasbro-{slugify(mapped)}"
        else:
            continue
        # Prefer singles: if tags say Deluxe without Single, still ok for Classified
        tags = [t.lower() for t in (p.get("tags") or [])]
        if "haslab" in tags:
            continue
        candidates.append((pri, bucket, p, mapped, unique))

    for p in jazwares:
        reason = is_skip_product(p, company="jazwares")
        if reason:
            continue
        mapped = map_jazwares_line(p.get("franchise"), p.get("name") or "")
        if mapped in ("Jazwares",):
            continue
        # articulated AF franchises only
        if mapped not in (
            "AEW Unrivaled",
            "Fortnite",
            "World of Halo",
            "Pokemon Select",
            "Five Nights at Freddy's",
            "Call of Duty",
        ):
            continue
        img = (p.get("imageUrl") or "").strip() or None
        unique = bool(img and j_img[img] == 1)
        if not unique:
            # leave image empty only if still high-value; still require unique for this fire
            continue
        pri = 3
        bucket = f"jazwares-{slugify(mapped)}"
        candidates.append((pri, bucket, p, mapped, unique))

    candidates.sort(
        key=lambda t: (
            t[0],
            -(parse_year(t[2]) or 0),
            t[2].get("name") or "",
        )
    )

    added: list[str] = []
    added_detail: list[dict] = []
    skipped: list[dict] = []
    counts: Counter = Counter()
    alias_added = 0
    img_baked = 0

    for pri, bucket, p, mapped_line, unique in candidates:
        if len(added) >= CAP:
            break
        company = (p.get("company") or "").lower()
        if company not in ("hasbro", "jazwares"):
            skipped.append({"name": p.get("name"), "reason": "bad-company"})
            continue
        year = parse_year(p)
        if year is None:
            skipped.append({"name": p.get("name"), "reason": "no-year"})
            continue
        name = (p.get("name") or "").strip()
        if not name:
            skipped.append({"reason": "no-name"})
            continue
        rid = stable_id(p)
        if rid in ids:
            skipped.append({"id": rid, "reason": "id-exists"})
            continue
        # collision with longer/shorter mph id forms
        mid = str(p.get("mephitsuId") or p.get("productId") or "")
        if mid and (f"mph-{mid}" in ids or f"mph-{mid[:12]}" in ids):
            skipped.append({"id": rid, "reason": "mephitsuId-exists"})
            continue

        subtitle = build_subtitle(p, mapped_line, year)
        excl = extract_exclusive(p)
        provisional = {
            "company": company,
            "line": mapped_line,
            "name": name,
            "subtitle": subtitle,
        }
        k = row_key(provisional)
        if k in keys:
            skipped.append({"id": rid, "reason": "key-exists", "key": k})
            continue
        fp = fingerprint(company, mapped_line, name, str(year))
        if fp in fps:
            skipped.append({"id": rid, "reason": "fingerprint-exists", "fp": fp})
            continue
        sk = soft_key(company, mapped_line, name, str(year))
        if sk in softs:
            skipped.append({"id": rid, "reason": "soft-exists", "soft": sk})
            continue
        nl = name_line_key(company, mapped_line, name)
        if nl in name_lines:
            skipped.append({"id": rid, "reason": "name-line-exists", "nl": nl})
            continue

        img = (p.get("imageUrl") or "").strip() or None
        if img:
            cache_counts = h_img if company == "hasbro" else j_img
            if cache_counts[img] != 1 or img in used_images:
                img = None  # empty > shared/wrong

        # Real GTIN only — caches currently withGtin=0 on hub files
        sku = None
        for field in ("barcode", "sku", "listingSku"):
            raw = clean_code(p.get(field))
            if raw and is_gtin(raw):
                if raw in gtin_owned:
                    skipped.append(
                        {
                            "id": rid,
                            "reason": "gtin-exists",
                            "sku": raw,
                            "owner": gtin_owned[raw],
                        }
                    )
                    sku = "COLLIDE"
                    break
                sku = raw
                break
        if sku == "COLLIDE":
            continue

        extra = [slugify(mapped_line)]
        if company == "hasbro" and mapped_line == "GI Joe Classified":
            extra += ["gi-joe", "classified"]
        if mapped_line == "Lightning Collection":
            extra += ["power-rangers", "lightning"]
        if company == "jazwares":
            extra.append(slugify(p.get("franchise") or mapped_line))

        row = make_row(
            rid=rid,
            name=name,
            subtitle=subtitle,
            line=mapped_line,
            company=company,
            year=year,
            image=img,
            exclusive=excl,
            extra_tags=extra,
        )
        if sku:
            row["sku"] = sku
            gtin_owned[sku] = rid

        rows.append(row)
        ids.add(rid)
        keys.add(k)
        fps.add(fp)
        softs.add(sk)
        name_lines.add(nl)
        if img:
            used_images.add(img)
            img_baked += 1
            urls[rid] = img
        added.append(rid)
        counts[bucket] += 1
        als = [f"id:{rid}", f"mephitsu:{mid or rid}"]
        if sku:
            als.append(sku)
        alias_added += add_aliases(aliases, rid, als)
        if sku:
            sku_map[sku] = rid
        added_detail.append(
            {
                "id": rid,
                "name": name,
                "company": company,
                "line": mapped_line,
                "year": year,
                "bucket": bucket,
                "image": bool(img),
                "exclusive": excl,
            }
        )

    write_json(ARCHIVE, rows)
    write_json(ALIASES, aliases)
    write_json(SKU_MAP, sku_map)
    write_json(URLS, urls)

    by_line: Counter = Counter()
    by_company: Counter = Counter()
    for d in added_detail:
        by_line[d["line"]] += 1
        by_company[d["company"]] += 1

    stats = {
        "source": SOURCE,
        "finishedAt": now_iso(),
        "cap": CAP,
        "added": len(added),
        "withImage": img_baked,
        "skipped": len(skipped),
        "counts": dict(counts),
        "byLine": dict(by_line),
        "byCompany": dict(by_company),
        "aliasAdded": alias_added,
        "addedSample": added_detail[:25],
        "addedIds": added,
        "skippedSample": skipped[:40],
        "archiveSize": len(rows),
        "caches": {
            "hasbro": len(hasbro),
            "jazwares": len(jazwares),
        },
    }
    write_json(STATS, stats)

    if ONESHOT_STATS.exists():
        try:
            os_stats = load_json(ONESHOT_STATS)
            os_stats["archiveTotal"] = len(rows)
            os_stats["mephitsuListingDensifyAdded"] = len(added)
            os_stats["mephitsuListingDensifyAt"] = now_iso()
            write_json(ONESHOT_STATS, os_stats)
        except Exception as exc:  # noqa: BLE001
            stats["oneshotStatsError"] = str(exc)
            write_json(STATS, stats)

    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
