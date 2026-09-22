#!/usr/bin/env python3
"""Inject Wei Jiang / THF / Black Mamba / BPF / Magic Square (+ JX Jiang peer)
densify from The Chosen Prime + TFSafari honest product feeds.

Policy: real CDN images only; GTIN primary when known (none invented);
retailer listing codes as aliases; empty sku over invented; dedupe against
existing oneshot ids/names/codes. Does NOT Build Publish Live.
"""
from __future__ import annotations

import json
import re
import sys
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
STATS = ROOT / "src/data/figure-archive/tf3p-ko-priority-inject-stats.json"
CATALOG = SCRIPTS / "figure_oneshot/tf3p_ko_priority_catalog.json"

SOURCE = "inject-tf3p-ko-priority"

HOMAGE = {
    "battle commander": "MP Optimus Prime homage",
    "fire scorpion": "Scorponok homage",
    "hide shadow": "Blackout homage",
    "commander": "Optimus Prime homage",
    "armed cannon": "Ironhide homage",
    "steel guard": "Jazz homage",
    "megamaster": "Powermaster Optimus homage",
    "battle hornet": "Bumblebee homage",
    "alcee": "Arcee homage",
    "ultima guard": "Ultra Magnus homage",
    "omega drone": "Omega Supreme homage",
    "winged dragon": "Predaking limb homage",
    "cold dragon": "Predaking limb homage",
    "hyper magnum": "MP Ultra Magnus homage",
    "sonic wave": "MP Soundwave homage",
    "soundblaster": "MP Soundblaster homage",
    "tape corps": "Cassette warriors homage",
    "dynastron": "MP Dynastra / Metroplex homage",
    "volcanicus": "POTP Volcanicus homage",
    "lieutenant": "WFC Siege Ultra Magnus homage",
    "adjutant": "Ultra Magnus homage",
    "chief of staff": "Sixshot homage",
    "pterosaur": "Swoop homage",
    "triceratops": "Sludge homage",
    "brontosaurus": "Sludge/Snarl homage",
    "tyrannosaurus": "Grimlock homage",
    "space shuttle": "Sky Lynx homage",
    "tornado": "Jetfire homage",
    "night tracer": "Nightbeat homage",
    "munitioner": "Hot Rod / Rodimus homage",
    "heavy gunner": "Ultra Magnus / Impactor homage",
    "arms dealer": "Swindle homage",
    "light of justice": "Optimus Prime homage",
    "light of peace": "Optimus Prime homage",
    "light of freedom": "Optimus Prime homage",
    "light of victory": "Optimus Prime homage",
    "dark lord": "Megatron homage",
    "star commander": "Star Convoy homage",
    "mirror commander": "Nemesis Prime homage",
    "spock": "Spock / Shockwave homage",
    "doomsday": "Grimlock homage",
    "overlords": "Overlord homage",
    "overlord": "Overlord homage",
    "eniac": "Technobot / Computron homage",
    "truck boy": "Optimus Prime homage",
    "blueberry girl": "Arcee homage",
    "peach girl": "Arcee homage",
    "little ninja": "Nightbird homage",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def slugify(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("'", "").replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")[:72]


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
        # skip Chinese / junk retailer SKUs
        if re.search(r"[\u4e00-\u9fff]", c2):
            continue
        if len(c2) > 48:
            continue
        if c2 not in cur:
            cur.append(c2)
            added += 1
        to[c2] = figure_id
    if cur:
        by[figure_id] = cur
    return added


def homage_for(name: str) -> str | None:
    low = name.lower()
    for key, sub in HOMAGE.items():
        if key in low:
            return sub
    return None


def norm_code(c: str | None) -> str:
    if not c:
        return ""
    return re.sub(r"[^A-Z0-9]", "", str(c).upper())


def ms_display_code(part: str | None) -> str | None:
    """MST-B60 / MSB60 / MS-B60 -> MS-B60; MST-MS07 -> MS-07; MST-G04 -> G04."""
    if not part:
        return None
    p = part.strip().upper().replace(" ", "")
    p = re.sub(r"^MST-", "", p)
    p = re.sub(r"^MST", "", p)
    if p.startswith("MSB"):
        p = "MS-B" + p[3:]
    elif re.match(r"^B\d", p):
        p = "MS-" + p
    elif re.match(r"^MS\d", p) and not p.startswith("MS-"):
        p = "MS-" + p[2:]
    elif p.startswith("MS") and not p.startswith("MS-") and not p.startswith("MSB"):
        # MS07 already handled; MS-B ok
        if re.match(r"^MS[A-Z]", p):
            pass
    if p.startswith("BLOJ"):
        return "MS-BLOJV2" if "V2" in p else p
    return p


def pretty_name_from_title(title: str, brand_prefixes: list[str]) -> str:
    t = title.strip()
    t = re.sub(r"^【[^】]*】\s*", "", t)
    for p in brand_prefixes:
        if t.lower().startswith(p.lower()):
            t = t[len(p) :].lstrip(" -–—:")
    # strip leading codes
    t = re.sub(
        r"^(?:MST-?)?(?:MS-?B?\d+[A-Z+]*|MS-?P?\d+[A-Z]*|G\d+[A-Z]*|WJ-?[A-Z0-9-]+|"
        r"JX-?[A-Z0-9-]+|THF-?\d+[A-Z0-9]*|BPF-?[A-Z0-9-]+|BMB[-\s]?|"
        r"(?:DP|GS|LS|NS|PS|MX|MC|KH)-?\d+[A-Z+]*)\s+",
        "",
        t,
        flags=re.I,
    )
    # drop KO parentheticals clutter for name core — keep as variant later
    core = re.sub(r"\([^)]*\)", " ", t)
    core = re.sub(r"\s+", " ", core).strip(" -–—/")
    # Prefer first 1-5 word product nickname (often ALL CAPS on TCP)
    m = re.match(r"^([A-Z][A-Z0-9]+(?:\s+[A-Z][A-Z0-9]+){0,4})\b", core)
    if m and len(m.group(1)) >= 3:
        name = " ".join(w.capitalize() for w in m.group(1).split())
        return name
    # Title-ish
    words = core.split()[:6]
    name = " ".join(w.capitalize() if w.isupper() else w for w in words)
    name = re.sub(r"\b(Of|The|And|For|With)\b", lambda m: m.group(0).lower(), name)
    return name.strip() or core[:48]


def skip_title(title: str) -> bool:
    low = title.lower()
    return any(
        x in low
        for x in (
            "upgrade kit",
            "upgrade parts",
            "upgrade armor",
            "background/base",
            "base plate",
            "magic villa",
            "replacement head",
            "accessory kit",
            "joints accessory",
        )
    )


def make_row(
    rid: str,
    name: str,
    subtitle: str,
    *,
    line: str,
    company: str,
    msrp: float,
    scale: str,
    release: str = "2020-01-01",
    demand: float = 1.35,
    sku: str | None = None,
    image: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    return {
        "id": rid,
        "name": name,
        "subtitle": subtitle,
        "line": line,
        "company": company,
        "kind": "figure",
        "releaseDate": release,
        "msrp": float(msrp),
        "scale": scale,
        "demand": float(demand),
        "tags": tags or [company, "transformers", "3p", "ko", "curated", SOURCE],
        "source": SOURCE,
        "sku": sku,
        "imageUrl": image,
    }


def existing_keys(rows: list[dict]) -> tuple[set[str], set[str], set[str]]:
    ids = {r["id"] for r in rows}
    names = {(r.get("company"), (r.get("name") or "").lower()) for r in rows}
    codes: set[str] = set()
    for r in rows:
        for t in r.get("tags") or []:
            if isinstance(t, str) and t.startswith("code:"):
                codes.add(norm_code(t[5:]))
        # also from name MS-B60
        blob = f"{r.get('id','')} {r.get('name','')} {r.get('subtitle','')}"
        for m in re.finditer(r"(?:MS-?B|MSB|WJ-|THF-|BPF-|JX-)[A-Z0-9-]+", blob, re.I):
            codes.add(norm_code(m.group(0)))
    return ids, names, codes


def ms_base_exists(code: str, existing_bases: set[str]) -> bool:
    """True if code is exact base MS-B## (no letter suffix) already in archive."""
    c = ms_display_code(code) or code
    m = re.match(r"^MS-B(\d+)$", c or "", re.I)
    if not m:
        return False
    return f"MSB{m.group(1)}" in existing_bases


def main() -> None:
    rows: list[dict] = load_json(ARCHIVE)
    aliases = ensure_alias_doc(load_json(ALIASES) if ALIASES.exists() else {})
    sku_map: dict = load_json(SKU_MAP) if SKU_MAP.exists() else {}
    urls: dict = load_json(URLS) if URLS.exists() else {}
    catalog = load_json(CATALOG)

    before_total = len(rows)
    ids, name_keys, code_keys = existing_keys(rows)
    alias_to = aliases.get("aliasToFigureId") or {}

    # Magic Square base numbers already present (MSB01..MSB60 placeholders)
    ms_bases: set[str] = set()
    for r in rows:
        if (r.get("company") or "").lower() != "magicsquare":
            continue
        for m in re.finditer(r"MS-?B(\d+)\b", f"{r.get('name','')} {r.get('id','')}", re.I):
            ms_bases.add(f"MSB{m.group(1)}")

    added: list[str] = []
    skipped: list[dict] = []
    counts: dict[str, int] = {}
    alias_added = 0
    img_baked = 0

    def inject(row: dict, alias_codes: list[str]) -> bool:
        nonlocal alias_added, img_baked
        rid = row["id"]
        company = row["company"]
        name = row["name"]
        if rid in ids:
            skipped.append({"id": rid, "reason": "id-exists"})
            return False
        if (company, name.lower()) in name_keys:
            skipped.append({"id": rid, "reason": "name-exists", "name": name})
            return False
        for c in alias_codes:
            c2 = clean_code(c) or str(c).strip()
            if not c2 or re.search(r"[\u4e00-\u9fff]", c2):
                continue
            nc = norm_code(c2)
            if nc and nc in code_keys:
                skipped.append({"id": rid, "reason": "code-exists", "code": c2})
                return False
            if c2 in alias_to and alias_to[c2] != rid:
                skipped.append({"id": rid, "reason": "alias-collision", "code": c2})
                return False
        if not row.get("sku"):
            row.pop("sku", None)
        if not row.get("imageUrl"):
            row.pop("imageUrl", None)
        rows.append(row)
        ids.add(rid)
        name_keys.add((company, name.lower()))
        for c in alias_codes:
            nc = norm_code(c)
            if nc:
                code_keys.add(nc)
        added.append(rid)
        counts[company] = counts.get(company, 0) + 1
        als = [a for a in alias_codes if a]
        als.append(f"id:{rid}")
        alias_added += add_aliases(aliases, rid, als)
        for a in als:
            a2 = clean_code(a) or str(a).strip()
            if a2:
                alias_to[a2] = rid
        if row.get("sku") and is_gtin(clean_code(row["sku"]) or ""):
            sku_map[rid] = clean_code(row["sku"])
            tags = list(row.get("tags") or [])
            if "sku-gtin" not in tags:
                row["tags"] = tags + ["sku-gtin", "sku-bake"]
        if row.get("imageUrl"):
            urls[rid] = row["imageUrl"]
            img_baked += 1
            tags = list(row.get("tags") or [])
            if "image-bake" not in tags:
                row["tags"] = tags + ["image-bake"]
        return True

    def process_item(
        item: dict,
        *,
        company: str,
        brand_prefixes: list[str],
        line_default: str,
        scale: str,
        release: str,
        demand: float = 1.35,
        tags_extra: list[str] | None = None,
        ms_mode: bool = False,
    ) -> None:
        title = item.get("name") or ""
        if skip_title(title):
            skipped.append({"reason": "accessory", "title": title})
            return
        part_raw = item.get("part")
        part = ms_display_code(part_raw) if ms_mode else (part_raw or None)
        if ms_mode and part:
            # Normalize MST leftovers
            part = ms_display_code(part)
        if ms_mode and part and ms_base_exists(part, ms_bases):
            skipped.append({"reason": "ms-base-exists", "part": part, "title": title})
            return

        name = pretty_name_from_title(title, brand_prefixes)
        # Manual cleanups
        if company == "weijiang" and not name:
            name = pretty_name_from_title(re.sub(r"^Wei Jiang\s+", "", title, flags=re.I), [])
        if company == "bpf":
            name = re.sub(r"^BPF\s+", "", name, flags=re.I).strip() or name
        if company == "toyhousefactory":
            name = re.sub(r"^Toy House Factory\s+(THF-?\d+[A-Z0-9]*\s+)?", "", title, flags=re.I)
            name = pretty_name_from_title(name, [])

        hm = homage_for(title) or homage_for(name)
        variant = None
        pm = re.search(r"\(([^)]+)\)", title)
        if pm:
            variant = pm.group(1).strip()
            if len(variant) > 60:
                variant = variant[:57] + "…"

        sub_bits = []
        if part:
            sub_bits.append(str(part))
        if variant and variant.lower() not in (name or "").lower():
            sub_bits.append(variant)
        if hm:
            sub_bits.append(hm)
        subtitle = " — ".join(sub_bits) if sub_bits else line_default

        line = line_default
        low = title.lower()
        if company == "magicsquare":
            if re.search(r"\bMS-?0?\d", part or title, re.I) and "MS-B" not in (part or ""):
                line = "MS Scale"
            elif re.search(r"\bG\d+", part or title, re.I):
                line = "G Series"
            else:
                line = "B Series"
        elif company == "weijiang":
            if "robot force" in low or "mpp" in low:
                line = "Robot Force"
            elif re.search(r"\bM-\d+", title, re.I):
                line = "M Series"
            else:
                line = "Wei Jiang"
        elif company == "jxjiang":
            line = "MetalBeast"
        elif company == "blackmamba":
            line = "BMB"
        elif company == "toyhousefactory":
            line = "THF"
        elif company == "bpf":
            line = "BPF"

        code_slug = slugify(part or item.get("slug") or name)
        rid = f"{company}-{code_slug}"
        msrp = float(item.get("price") or 49.99)
        img = item.get("image")
        tags = [company, "transformers", "3p", "ko", "curated", SOURCE]
        if tags_extra:
            tags.extend(tags_extra)
        if part:
            tags.append(f"code:{part}")
        if item.get("source"):
            tags.append(f"src:{item['source']}")

        alias_codes = [part or "", item.get("slug") or "", item.get("retailer_sku") or ""]
        if part_raw and part_raw != part:
            alias_codes.append(part_raw)

        inject(
            make_row(
                rid,
                name,
                subtitle,
                line=line,
                company=company,
                msrp=msrp,
                scale=scale,
                release=release,
                demand=demand,
                image=img,
                tags=tags,
            ),
            alias_codes,
        )

    cats = catalog.get("catalogs") or {}

    for item in cats.get("weijiang") or []:
        process_item(
            item,
            company="weijiang",
            brand_prefixes=["Wei Jiang", "WJ Toys", "WJ"],
            line_default="Wei Jiang",
            scale="MP",
            release="2018-01-01",
            demand=1.4,
        )

    for item in cats.get("weijiang_tfsafari") or []:
        process_item(
            item,
            company="weijiang",
            brand_prefixes=["4th Party", "WJ", "Wei Jiang", "WeiJiang", "KO / WJ", "No Brand NB WJ Weijiang"],
            line_default="Wei Jiang",
            scale='9"',
            release="2022-01-01",
            demand=1.35,
            tags_extra=["tfsafari"],
        )

    for item in cats.get("jxjiang") or []:
        process_item(
            item,
            company="jxjiang",
            brand_prefixes=["JX Jiang"],
            line_default="MetalBeast",
            scale="MP",
            release="2024-01-01",
            demand=1.45,
            tags_extra=["peer"],
        )

    for item in cats.get("magicsquare_tcp") or []:
        process_item(
            item,
            company="magicsquare",
            brand_prefixes=["Magic Square Toys", "Magic Square"],
            line_default="B Series",
            scale='1:24',
            release="2019-01-01",
            demand=1.35,
            ms_mode=True,
        )

    for item in cats.get("magicsquare_tfsafari") or []:
        process_item(
            item,
            company="magicsquare",
            brand_prefixes=["Magic Square MS-Toys", "Magic Square MS Toys", "Magic Square", "MS-Toys"],
            line_default="B Series",
            scale='4"',
            release="2024-01-01",
            demand=1.4,
            ms_mode=True,
            tags_extra=["tfsafari"],
        )

    for item in cats.get("blackmamba") or []:
        process_item(
            item,
            company="blackmamba",
            brand_prefixes=["4th Party BMB Black Mamba", "4th Party BMB", "BMB Black Mamba", "Black Mamba", "BMB"],
            line_default="BMB",
            scale="OS",
            release="2020-01-01",
            demand=1.4,
            tags_extra=["tfsafari"],
        )

    for item in cats.get("toyhousefactory") or []:
        process_item(
            item,
            company="toyhousefactory",
            brand_prefixes=["4th Party KO Toy House Factory", "Toy House Factory", "THF"],
            line_default="THF",
            scale="MP",
            release="2017-01-01",
            demand=1.35,
            tags_extra=["tfsafari"],
        )

    for item in cats.get("bpf") or []:
        process_item(
            item,
            company="bpf",
            brand_prefixes=["4th party BPF", "BPF"],
            line_default="BPF",
            scale="OS",
            release="2020-01-01",
            demand=1.3,
            tags_extra=["tfsafari"],
        )

    write_json(ARCHIVE, rows)
    write_json(ALIASES, aliases)
    write_json(SKU_MAP, sku_map)
    write_json(URLS, urls)

    after_total = len(rows)
    # per-company totals
    from collections import Counter

    co = Counter((r.get("company") or "") for r in rows)
    report = {
        "tf3pKoPriorityInjectAt": now_iso(),
        "source": SOURCE,
        "beforeTotal": before_total,
        "afterTotal": after_total,
        "added": len(added),
        "addedIdsSample": added[:40],
        "skipped": len(skipped),
        "skippedSample": skipped[:40],
        "aliasAdds": alias_added,
        "imagesBaked": img_baked,
        "perCompanyAdds": counts,
        "perCompanyTotals": {
            k: co.get(k, 0)
            for k in [
                "weijiang",
                "jxjiang",
                "blackmamba",
                "toyhousefactory",
                "bpf",
                "magicsquare",
            ]
        },
    }
    write_json(STATS, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
