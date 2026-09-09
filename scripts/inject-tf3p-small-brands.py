#!/usr/bin/env python3
"""Inject Shu Shu Papa Big Figs + Lewin + DJS Skybreaker + zero/thin TF 3P densify.

Sources (verified retailer pages / Shopify, 2026-09):
  - Target exclusive Big Figs Optimus (UPC 850081574071) — TFW2005 stock photo CDN
  - The Chosen Prime: Lewin / DJS / Unique Toys / Toyworld / Perfect Effect /
    Robot Paradise / TFC Toys / Moon Studio product pages + CDN images
  - TFSafari Shopify products.json: APC Toys / Gear Factory

Policy: real CDN/retailer images only; GTIN primary when known; listing codes
as aliases; empty sku over invented; homage product name primary + character in
subtitle. kind=figure. Does NOT Build Publish Live.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote

ROOT = Path("/workspace/collection-app")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_identity import clean_code, is_gtin  # noqa: E402

ARCHIVE = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
SKU_MAP = ROOT / "src/data/figure-sku-map.json"
URLS = ROOT / "src/data/figure-image-urls.json"
STATS = ROOT / "src/data/figure-archive/tf3p-small-brands-inject-stats.json"
CATALOG = SCRIPTS / "figure_oneshot/tf3p_densify_catalog.json"
APC_CATALOG = SCRIPTS / "figure_oneshot/apc_tfsafari_catalog.json"

SOURCE = "inject-tf3p-small-brands"

# Homage / character hints for 3P product names
HOMAGE = {
    "skybreaker": "IDW Ultra Magnus homage",
    "steel fortress": "FOC Metroplex homage",
    "atlas": "MP-scale Optimus Prime homage",
    "spike": "Spike Witwicky homage",
    "desperado": "MP Starscream homage",
    "buzz guardian": "Bumblebee homage",
    "dumb": "Huffer homage",
    "dumber": "Pipes homage",
    "red dasher": "Sideswipe homage",
    "sworder": "Drift homage",
    "peru kill": "Perceptor homage",
    "nero": "Nemesis Prime homage",
    "challenger": "Ultra Magnus homage",
    "dragoon": "Springer homage",
    "ordin": "Devastator homage",
    "rage winterchill": "Dinobot homage",
    "sky burst": "Silverbolt homage",
    "fierce hot": "Hot Spot homage",
    "blue baron": "Air Raid homage",
    "black baron": "Skydive homage",
    "red baron": "Fireflight homage",
    "alert": "First Aid homage",
    "knight orion": "Optimus Prime homage",
    "freedom leader": "Optimus Prime homage",
    "constructor": "Devastator homage",
    "whisky jack": "Whirl homage",
    "mega doragon": "Dragon Predaking homage",
    "dark warrior": "Black Rodimus homage",
    "honor warrior": "Rodimus homage",
    "godforce warrior": "God Ginrai homage",
    "jetforce revive prime": "Powermaster Optimus homage",
    "nemesis gorira": "Optimus Primal homage",
    "psychro knight": "Ice Predaking homage",
    "beast gorira": "Optimus Primal homage",
    "acoustic wave": "Soundwave homage",
    "acoustic blaster": "Blaster homage",
    "jakiro": "Abominus limb homage",
    "poseidon": "Seacons combiner homage",
    "dark savior": "Optimus Prime homage",
    "ice wolf": "Ultra Magnus homage",
    "tyrant": "Megatron homage",
    "lucifer": "Abominus limb homage",
    "astaroth": "Abominus limb homage",
    "hades": "Predaking homage",
    "attack prime": "TFP Optimus Prime homage",
    "dark master": "TFP Megatron homage",
    "angel engine": "TFP Arcee homage",
    "red gladiator": "TFP Cliffjumper homage",
    "galaxy mob": "TFP Vehicon homage",
    "night countess": "TFP Airachnid homage",
    "bossy flame": "TFP Galvatron homage",
    "evil voice": "TFP Soundwave homage",
    "demonic wisper": "TFP Soundwave homage",
    "serpent bell": "TFP Soundwave homage",
    "wander warrior": "TFP Wheeljack homage",
    "giant hammer": "TFP Bulkhead homage",
    "gale": "TFP Dreadwing homage",
    "bolt": "TFP Skyquake homage",
    "green zone": "Computron limb homage",
    "cool peak": "Computron limb homage",
    "moon shine": "Computron limb homage",
    "iron arm": "Computron limb homage",
    "ice land": "Computron limb homage",
    "dark night": "Computron limb homage",
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


def strip_brand_prefix(title: str, prefixes: list[str]) -> str:
    t = title.strip()
    for p in prefixes:
        if t.lower().startswith(p.lower()):
            t = t[len(p) :].lstrip(" -–—:")
    return t.strip(" .")


def parse_code_name(raw: str) -> tuple[str, str | None]:
    """Extract product code + display name from retailer title."""
    t = raw.strip()
    # e.g. Unique Toys R-05B DESPERADO (Special Paint)
    m = re.match(
        r"^(?:Unique Toys|Toyworld|Perfect Effect|Robot Paradise|TFC Toys|TFC|Moon Studio|"
        r"LewinResources|Lewin Resources|W-Resources|Great General Toys|DJS(?: Toys)?|"
        r"APC Toys(?:\s*\(Gear Factory\))?|Gear Factory \(Aka APC Toys\))\s+",
        t,
        re.I,
    )
    if m:
        t = t[m.end() :].strip()
    code = None
    m2 = re.match(
        r"^((?:TW-)?[A-Z]{1,4}-?[A-Z]?\d{1,3}[A-Z]{0,4}|STC-?\d+[A-Z]*|PC-?\d+[A-Z]*|"
        r"DX\d+[A-Z]*|MS-?\d+|RP-?\d+[A-Z]*|GF-?\d+|APC-?\d+[A-Z]*|DJS-?BS?\d+|"
        r"BS-?\d+|M-?\d+|LWH?-?\d+[A-Z]*|S\d+|P\d+|PN|HNBA-EX|ST-?\d+[A-Z]*)\s+",
        t,
        re.I,
    )
    if m2:
        code = m2.group(1).upper()
        t = t[m2.end() :].strip()
    # normalize code spacing
    if code:
        code = code.replace(" ", "")
    return t, code


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
    demand: float = 1.4,
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
        "tags": tags or [company, "transformers", "3p", "curated", SOURCE],
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
                codes.add(t[5:].upper())
        # also scan id suffixes
    return ids, names, codes


def main() -> None:
    rows: list[dict] = load_json(ARCHIVE)
    aliases = ensure_alias_doc(load_json(ALIASES) if ALIASES.exists() else {})
    sku_map: dict = load_json(SKU_MAP) if SKU_MAP.exists() else {}
    urls: dict = load_json(URLS) if URLS.exists() else {}
    catalog = load_json(CATALOG)
    apc_rows = load_json(APC_CATALOG)

    ids, name_keys, _ = existing_keys(rows)
    # Also index by company+part-like aliases already present
    alias_to = aliases.get("aliasToFigureId") or {}

    added: list[str] = []
    skipped: list[dict] = []
    counts: dict[str, int] = {
        "shushupapa": 0,
        "lewin": 0,
        "djs": 0,
        "tfc": 0,
        "uniquetoys": 0,
        "toyworld": 0,
        "perfecteffect": 0,
        "robotparadise": 0,
        "apctoys": 0,
        "moonstudio": 0,
    }
    alias_added = 0
    img_baked = 0
    gtin_set: list[str] = []

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
        # dedupe by alias codes already mapped
        for c in alias_codes:
            c2 = clean_code(c) or str(c).strip()
            if c2 and c2 in alias_to and alias_to[c2] != rid:
                skipped.append({"id": rid, "reason": "alias-collision", "code": c2})
                return False
        # strip None sku
        if not row.get("sku"):
            row.pop("sku", None)
        if not row.get("imageUrl"):
            row.pop("imageUrl", None)
        rows.append(row)
        ids.add(rid)
        name_keys.add((company, name.lower()))
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
            gtin_set.append(clean_code(row["sku"]) or "")
            tags = row.get("tags") or []
            if "sku-gtin" not in tags:
                tags = list(tags) + ["sku-gtin", "sku-bake"]
                row["tags"] = tags
        if row.get("imageUrl"):
            urls[rid] = row["imageUrl"]
            img_baked += 1
            tags = row.get("tags") or []
            if "image-bake" not in tags:
                row["tags"] = list(tags) + ["image-bake"]
        return True

    # ---------- 1) Shu Shu Papa / Big Figs ----------
    bigfigs_img = (
        "https://news.tfw2005.com/wp-content/uploads/sites/10/2026/08/"
        "Big-Figs-30-inch-Transformers-Optimus-Prime-01.jpg"
    )
    inject(
        make_row(
            "ssp-bigfigs-optimus-30",
            "Optimus Prime",
            'Big Figs 30" — Target exclusive, non-transforming',
            line="Big Figs",
            company="shushupapa",
            msrp=34.99,
            scale='30"',
            release="2026-08-01",
            demand=1.55,
            sku="850081574071",
            image=bigfigs_img,
            tags=[
                "shushupapa",
                "bigfigs",
                "transformers",
                "licensed",
                "target-exclusive",
                "curated",
                SOURCE,
            ],
        ),
        ["850081574071", "TCIN-95056707", "DPCI-087-06-1711", "BIGFIGS-OP-30"],
    )

    # ---------- 2) Lewin / W-Resources ----------
    lewin_specs = [
        (
            "lewin-01-atlas-final",
            "Atlas",
            "Lewin-01 Final Version — MP-scale Optimus Prime homage",
            "Lewin-01 Atlas",
            '28"',
            499.99,
            "2023-01-01",
            "lw01fwatlas",
            ["LW-01FV", "LEWIN-01-FV"],
        ),
        (
            "lewin-01-atlas",
            "Atlas",
            "Lewin-01 — MP-scale Optimus Prime homage",
            "Lewin-01 Atlas",
            '28"',
            379.99,
            "2022-01-01",
            "lwatlas",
            ["LW-01", "LEWIN-01"],
        ),
        (
            "lewin-01a-atlas-captain-america",
            "Atlas",
            "Lewin-01A Captain America deco — MP-scale Optimus homage",
            "Lewin-01 Atlas",
            '28"',
            419.99,
            "2022-06-01",
            "lw01aatlasca",
            ["LW-01A", "LEWIN-01A"],
        ),
        (
            "lewin-lwh-01-spike",
            "Spike Deformation Soldier",
            "LWH-01 — Spike Witwicky homage",
            "LWH-01 Spike",
            '6"',
            79.99,
            "2023-06-01",
            "lwh01spike",
            ["LW-H01", "LWH-01"],
        ),
        (
            "lewin-m01-steel-fortress",
            "Steel Fortress",
            "M-01 — FOC Metroplex homage (~120cm)",
            "M-01 Steel Fortress",
            "120cm",
            1499.99,
            "2024-01-01",
            "wrm01ironfortress-2",
            ["WR-M01", "M-01", "WR-M01-2", "WR-M01-3"],
        ),
    ]
    must_by_slug = {m["slug"]: m for m in catalog.get("must") or []}
    for rid, name, sub, line, scale, msrp, release, slug, codes in lewin_specs:
        src = must_by_slug.get(slug) or {}
        img = src.get("image")
        inject(
            make_row(
                rid,
                name,
                sub,
                line=line,
                company="lewin",
                msrp=msrp,
                scale=scale,
                release=release,
                image=img,
                tags=["lewin", "w-resources", "transformers", "3p", "curated", SOURCE],
            ),
            codes + ([src.get("part")] if src.get("part") else []),
        )

    # ---------- 3) DJS / Craftsman / Great General ----------
    djs = must_by_slug.get("djsbs01") or {}
    inject(
        make_row(
            "djs-bs01-skybreaker",
            "Skybreaker",
            "DJS-BS01 — IDW Ultra Magnus homage (MP-scale)",
            line="Brave General",
            company="djs",
            msrp=float(djs.get("price") or 210.99),
            scale="MP",
            release="2026-08-01",
            image=djs.get("image"),
            tags=["djs", "craftsman", "greatgeneral", "transformers", "3p", "curated", SOURCE],
        ),
        ["DJS-BS01", "BS-01", "GGT-DJSBS01", djs.get("part") or ""],
    )

    # ---------- helpers for Chosen Prime brand catalogs ----------
    def skip_title(title: str) -> bool:
        low = title.lower()
        return any(
            x in low
            for x in (
                "upgrade kit",
                "accessory pack",
                "accessory package",
                "joints accessory",
                "perfect combiner upgrade",
                "pc-14",
                "pc-21",
                "pc-22",
                "pc-23",
                "pc-24",
            )
        )

    brand_map = {
        "uniquetoys": ("uniquetoys", "Unique Toys", '1:24', "2018-01-01"),
        "toyworld": ("toyworld", "Toyworld", '1:24', "2018-01-01"),
        "perfecteffect": ("perfecteffect", "Perfect Effect", '1:24', "2017-01-01"),
        "robotparadise": ("robotparadise", "Robot Paradise", "MP", "2020-01-01"),
        "tfctoys": ("tfc", "TFC Toys", '1:24', "2016-01-01"),
        "moonstudio": ("moonstudio", "Moon Studio", '1:24', "2021-01-01"),
    }

    for cat_key, items in (catalog.get("catalogs") or {}).items():
        if cat_key not in brand_map:
            continue
        company, brand_label, scale, release = brand_map[cat_key]
        for item in items:
            title = item.get("name") or ""
            if skip_title(title):
                skipped.append({"id": item.get("slug"), "reason": "upgrade-or-accessory", "title": title})
                continue
            display, parsed_code = parse_code_name(title)
            # Prefer part number from page
            part = item.get("part") or parsed_code
            if not display:
                display = title
            # Clean remaining brand crumbs
            display = strip_brand_prefix(
                display,
                [
                    "Unique Toys",
                    "Toyworld",
                    "Perfect Effect",
                    "Robot Paradise",
                    "TFC Toys",
                    "TFC",
                    "Moon Studio",
                    "HADES",
                ],
            )
            # Title-case product name; keep known all-caps product names readable
            pname = display
            # If still starts with code, strip
            if part and pname.upper().startswith(str(part).upper()):
                pname = pname[len(part) :].strip(" -–—")
            # Special: "Satan Combiner S05 JAKIRO" style already parsed
            # Build nice name: take first clause before paren as name if long
            paren = re.search(r"\(([^)]+)\)", pname)
            variant = paren.group(1).strip() if paren else None
            core = re.sub(r"\([^)]*\)", "", pname).strip(" -–—")
            # Prefer last token group as product name when core has many words
            # e.g. "Satan Combiner S05 JAKIRO" -> Jakiro if S05 stripped already
            core2 = re.sub(
                r"^(Satan Combiner|Supreme Tactical Commander(?: Nuclear Blast)?|"
                r"Poseidon Combiner Set|Poseidon Noir Combiner Set|"
                r"Radiatron Combiner Te\w*|HADES \(Renewal Version\) Combiner Set of 6|"
                r"HADES Renewal)\s*",
                "",
                core,
                flags=re.I,
            ).strip()
            if not core2:
                core2 = core
            # Name = primary product callsign
            tokens = core2.split()
            if len(tokens) >= 2 and tokens[0].upper() in {
                "SUPREME",
                "NUCLEAR",
                "SATAN",
                "POISEDON",
            }:
                name = tokens[-1].title() if tokens[-1].isupper() else tokens[-1]
            else:
                # Keep multi-word names like "Buzz Guardian", "Red Dasher"
                name = " ".join(
                    w.title() if w.isupper() and len(w) > 2 else w for w in tokens
                )
                name = re.sub(r"\b(Of|The|And)\b", lambda m: m.group(0).lower(), name)
                # Fix all-caps words
                name = " ".join(
                    (w.capitalize() if w.isupper() else w) for w in name.split()
                )

            # Better name extraction for known patterns like "R-05B DESPERADO"
            mname = re.search(
                r"\b([A-Z][A-Z0-9\-]*(?:\s+[A-Z][A-Z0-9\-]*){0,3})\b(?:\s*\(|$)",
                strip_brand_prefix(title, [brand_label]),
            )
            # Prefer explicit product nickname after code in original title
            mnick = re.search(
                r"(?:^|\s)(?:[A-Z]{1,3}-?[A-Z]?\d+[A-Z]*)\s+([A-Z][A-Z0-9]+(?:\s+[A-Z][A-Z0-9]+)*)",
                strip_brand_prefix(title, [brand_label]),
            )
            if mnick:
                name = " ".join(w.capitalize() for w in mnick.group(1).split())

            # Manual overrides for clarity
            low_title = title.lower()
            overrides = [
                ("desperado", "Desperado"),
                ("buzz guardian", "Buzz Guardian"),
                ("red dasher", "Red Dasher"),
                ("dogs of war", "Dogs of War"),
                ("black challenger", "Black Challenger"),
                ("rage winterchill", "Rage Winterchill"),
                ("sky burst", "Sky Burst"),
                ("fierce hot", "Fierce Hot"),
                ("blue baron", "Blue Baron"),
                ("black baron", "Black Baron"),
                ("red baron", "Red Baron"),
                ("knight orion", "Knight Orion"),
                ("freedom leader", "Freedom Leader"),
                ("whisky jack", "Whisky Jack"),
                ("mega doragon", "Mega Doragon"),
                ("dark warrior", "Dark Warrior"),
                ("honor warrior", "Honor Warrior"),
                ("godforce warrior", "Godforce Warrior"),
                ("jetforce revive prime", "Jetforce Revive Prime"),
                ("nemesis gorira", "Nemesis Gorira"),
                ("psychro knight", "Psychro Knight"),
                ("beast gorira", "Beast Gorira"),
                ("acoustic blaster", "Acoustic Blaster"),
                ("acoustic wave", "Acoustic Wave"),
                ("dark savior", "Dark Savior"),
                ("ice wolf", "Ice Wolf"),
                ("monkey king", "Monkey King"),
                ("sun wukong", "Monkey King"),
                ("green zone", "Green Zone"),
                ("cool peak", "Cool Peak"),
                ("moon shine", "Moon Shine"),
                ("iron arm", "Iron Arm"),
                ("ice land", "Ice Land"),
                ("dark night", "Dark Night"),
                ("poseidon noir", "Poseidon Noir"),
                ("poseidon", "Poseidon"),
                ("hades", "Hades"),
                ("ordin", "Ordin"),
                ("ragnaros", "Ragnaros"),
                ("sworder", "Sworder"),
                ("peru kill", "Peru Kill"),
                ("constructor", "Constructor"),
                ("baron set", "Baron Set"),
                ("orange constructor", "Orange Constructor"),
            ]
            for key, pretty in overrides:
                if key in low_title:
                    name = pretty
                    break

            hm = homage_for(title) or homage_for(name)
            subtitle_bits = []
            if part:
                subtitle_bits.append(str(part))
            if variant:
                subtitle_bits.append(variant)
            if hm:
                subtitle_bits.append(hm)
            subtitle = " — ".join(subtitle_bits) if subtitle_bits else brand_label

            line = brand_label
            if "satan" in low_title:
                line = "Satan Combiner"
            elif "poseidon" in low_title:
                line = "Poseidon"
            elif "hades" in low_title:
                line = "Hades"
            elif "stc-" in low_title or "supreme tactical" in low_title or "st-01" in low_title:
                line = "Supreme Tactical Commander"
            elif "radiatron" in low_title or cat_key == "moonstudio":
                line = "Radiatron"
            elif "ordin" in low_title:
                line = "Ordin Combiner"
            elif "ragnaros" in low_title:
                line = "Ragnaros"
            elif re.search(r"\bDX\d+", title, re.I):
                line = "DX Series"
            elif re.search(r"\bRP-\d+", title, re.I):
                line = "Acoustic Series"
            elif re.search(r"\bTW-FS", title, re.I):
                line = "FS Series"
            elif re.search(r"\bTW-C", title, re.I):
                line = "Constructor"
            elif re.search(r"\bTW-F", title, re.I):
                line = "F Series"
            elif re.search(r"\bR-\d+", title, re.I) and company == "uniquetoys":
                line = "R Series"

            code_slug = slugify(part or item.get("slug") or name)
            rid = f"{company}-{code_slug}"
            # Avoid collision with existing tfc6-* placeholders — new real names OK
            msrp = float(item.get("price") or 99.99)
            img = item.get("image")
            tags = [company, "transformers", "3p", "curated", SOURCE]
            if part:
                tags.append(f"code:{part}")

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
                    image=img,
                    tags=tags,
                ),
                [part or "", item.get("slug") or "", f"TCP-{item.get('slug')}"],
            )

    # ---------- APC Toys from TFSafari ----------
    seen_apc: set[str] = set()
    for item in apc_rows:
        title = item.get("title") or ""
        code = (item.get("code") or "").upper().replace(" ", "")
        # normalize APC001 -> APC-001
        code = re.sub(r"^APC(\d)", r"APC-\1", code)
        code = re.sub(r"^GF(\d)", r"GF-\1", code)
        if not code:
            skipped.append({"reason": "apc-no-code", "title": title})
            continue
        # dedupe exact code (keep first = often newer variant listing)
        # allow variants with letter suffix
        if code in seen_apc and code in {"APC-001"}:
            # second APC-001 is original vs JP — distinguish
            if "2.0" in title or "Japan" in title or "Jap" in title:
                code = "APC-001JP"
            else:
                code = "APC-001"
        if code in seen_apc and "2.0" not in title:
            # skip exact duplicate code without new suffix
            if code != "APC-001JP":
                skipped.append({"reason": "apc-dup-code", "code": code, "title": title})
                continue
        seen_apc.add(code)

        # Name from title
        name = "Attack Prime"
        overrides = [
            ("mirror evil", "Attack Prime Mirror Evil"),
            ("attack prime", "Attack Prime"),
            ("dark master", "Dark Master"),
            ("evil god", "Dark Master Evil God"),
            ("angel engine", "Angel Engine"),
            ("red gladiator", "Red Gladiator"),
            ("galaxy mob", "Galaxy Mob"),
            ("airgeneral", "Galaxy Mob Airgeneral"),
            ("airforce", "Galaxy Mob Airforce"),
            ("night countess", "Night Countess"),
            ("bossy flame", "Bossy Flame"),
            ("evil voice", "Evil Voice"),
            ("demonic wisper", "Demonic Whisper"),
            ("serpent bell", "Serpent Bell"),
            ("wander warrior", "Wander Warrior"),
            ("giant hammer", "Giant Hammer"),
            ("gale", "Gale"),
            ("bolt", "Bolt"),
        ]
        low = title.lower()
        for key, pretty in overrides:
            if key in low:
                name = pretty
                break
        hm = homage_for(title) or homage_for(name)
        variant_bits = []
        for v in (
            "Zombie",
            "Pink",
            "Japan",
            "Jap",
            "2.0",
            "Shattered Glass",
            "Mirror Evil",
            "Battle Damaged",
            "Evil God",
            "Silver",
            "Black Cobra",
            "Momo",
        ):
            if v.lower() in low and v.lower() not in name.lower():
                variant_bits.append(v)
        sub_parts = [code]
        if variant_bits:
            sub_parts.append(", ".join(variant_bits[:2]))
        if hm:
            sub_parts.append(hm)
        subtitle = " — ".join(sub_parts)
        rid = f"apctoys-{slugify(code)}"
        # GF figures still company apctoys
        inject(
            make_row(
                rid,
                name,
                subtitle,
                line="TFP Homage",
                company="apctoys",
                msrp=float(item.get("price") or 39.99),
                scale='6"',
                release=item.get("published") or "2022-01-01",
                image=item.get("image"),
                tags=["apctoys", "transformers", "3p", "4p", "curated", SOURCE, f"code:{code}"],
            ),
            [code, code.replace("-", ""), item.get("sku_listing") or "", item.get("handle") or ""],
        )

    aliases["updatedAt"] = now_iso()
    aliases["stats"] = {
        **(aliases.get("stats") or {}),
        "tf3pSmallBrandsInjectAt": now_iso(),
        "tf3pSmallBrandsAliasAdds": alias_added,
    }

    write_json(ARCHIVE, rows)
    write_json(ALIASES, aliases)
    write_json(SKU_MAP, sku_map)
    write_json(URLS, urls)

    stats = {
        "at": now_iso(),
        "addedTotal": len(added),
        "counts": counts,
        "gtinPrimaryCount": len(gtin_set),
        "gtins": gtin_set,
        "aliasAdded": alias_added,
        "imagesBaked": img_baked,
        "skipped": skipped[:60],
        "skippedCount": len(skipped),
        "sampleAdded": added[:40],
        "mustPresent": {
            "ssp-bigfigs-optimus-30": "ssp-bigfigs-optimus-30" in ids,
            "djs-bs01-skybreaker": "djs-bs01-skybreaker" in ids,
            "lewin-m01-steel-fortress": "lewin-m01-steel-fortress" in ids,
            "lewin-01-atlas-final": "lewin-01-atlas-final" in ids,
        },
        "notes": [
            "Big Figs Optimus: Target UPC 850081574071; image from TFW2005 stock CDN (Target API blocked)",
            "Lewin/DJS/UT/TW/PE/RP/TFC/Moon: The Chosen Prime retailer CDN",
            "APC Toys: TFSafari Shopify CDN",
            "Beitai: not found on Chosen Prime / TFSafari — skipped",
            "Skipped Perfect Effect PC upgrade kits and TFC accessory packs",
            "Did NOT Build Publish Live",
        ],
    }
    write_json(STATS, stats)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
