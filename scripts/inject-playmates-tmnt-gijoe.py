#!/usr/bin/env python3
"""Inject Playmates TMNT x G.I. Joe crossover wave + honest Playmates densify.

Sources (verified retailer feeds / product pages):
  - Target PDPs (UPC in page HTML)
  - Forbidden Planet product URLs (UPC path + gtin JSON-LD)
  - Cmdstore Shopify products.json (GTIN sku + CDN images for vehicles)
  - Nerdzoic Shopify products.json (Playmates listing PL* + CDN package images)
  - ToyHabits / Playmates brand page for lineup names (no invented GTINs)

Policy: real images only; GTIN primary when verified; PL*/Target TCIN → aliases;
empty sku/image preferred over wrong. kind=figure (schema has no vehicle).
Does NOT Build Publish Live.
"""
from __future__ import annotations

import json
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
STATS = ROOT / "src/data/figure-archive/playmates-tmnt-gijoe-inject-stats.json"

LINE = "Teenage Mutant Ninja Turtles x G.I. Joe"
COMPANY = "playmates"
RELEASE = "2026-07-01"
SCALE = '4.5"'


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
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
    doc = ensure_alias_doc(doc)
    by = doc["aliasesByFigureId"]
    to = doc["aliasToFigureId"]
    cur = list(by.get(figure_id) or [])
    added = 0
    for c in codes:
        c2 = clean_code(c) or str(c).strip()
        if not c2:
            continue
        # never alias a GTIN that is already primary on another figure via aliasTo
        if c2 not in cur:
            cur.append(c2)
            added += 1
        to[c2] = figure_id
    if cur:
        by[figure_id] = cur
    return added


def row(
    rid: str,
    name: str,
    subtitle: str,
    *,
    line: str = LINE,
    msrp: float = 18.99,
    scale: str = SCALE,
    demand: float = 1.35,
    kind: str = "figure",
    release: str = RELEASE,
    sku: str | None = None,
    image: str | None = None,
    tags: list[str] | None = None,
    source: str = "inject-playmates-tmnt-gijoe",
) -> dict:
    out = {
        "id": rid,
        "name": name,
        "subtitle": subtitle,
        "line": line,
        "company": COMPANY,
        "kind": kind,
        "releaseDate": release,
        "msrp": float(msrp),
        "scale": scale,
        "demand": float(demand),
        "tags": tags
        or [
            "playmates",
            "tmnt",
            "gi-joe",
            "crossover",
            "curated",
            "inject-tmnt-gijoe",
        ],
        "source": source,
        "sku": sku,
        "imageUrl": image,
    }
    return out


# Verified GTINs: Target HTML + Forbidden Planet URL/gtin + Cmdstore Shopify sku/barcode.
# Images: Nerdzoic Shopify CDN (singles/vehicles) / Cmdstore Shopify CDN (vehicles preferred).
NZ = "https://cdn.shopify.com/s/files/1/0535/8125/0722/files"
CMD = "https://cdn.shopify.com/s/files/1/0432/8397/2262/files"
FP = "https://cdn.powered-by-nitrosell.com/product_images/8/1806"

GIJOE_SINGLES = [
    # id, name, subtitle, gtin, pl_alias, image, msrp, demand
    (
        "pm-tmnt-gijoe-leo-snake-eyes",
        "Leonardo x Snake Eyes",
        "Snake Eyes x Leo",
        "043377819011",
        "PL81986",
        f"{NZ}/imgi_129_ef481bc58f3b4bd0a4a7c91e814fe7bfxl.jpg?v=1779640342",
        18.99,
        1.45,
    ),
    (
        "pm-tmnt-gijoe-raph-roadblock",
        "Raphael x Roadblock",
        "Roadblock x Raph",
        "043377819059",
        "PL81905",
        f"{NZ}/imgi_134_17a6f2aaecea46fabb006059c82337b1xl.jpg?v=1779640304",
        18.99,
        1.4,
    ),
    (
        "pm-tmnt-gijoe-mikey-shipwreck",
        "Michelangelo x Shipwreck",
        "Shipwreck x Mikey",
        "043377819042",
        "PL81904",
        f"{NZ}/imgi_151_2a50d2547aca470bae4d4702e7579597xl.jpg?v=1779640261",
        18.99,
        1.4,
    ),
    (
        "pm-tmnt-gijoe-don-dial-tone",
        "Donatello x Dial-Tone",
        "Dial-Tone x Donnie",
        "043377819028",
        "PL81902",
        f"{NZ}/imgi_129_7944db59b8bc4937b81935c72c0cf928xl.jpg?v=1779640218",
        18.99,
        1.35,
    ),
    (
        "pm-tmnt-gijoe-shredder-cobra-commander",
        "Shredder x Cobra Commander",
        "Cobra Commander x Shredder",
        "043377819035",
        "PL81903",
        f"{NZ}/imgi_141_d33b085172cb43b594efec3930a62804xl.jpg?v=1779640181",
        18.99,
        1.45,
    ),
    (
        "pm-tmnt-gijoe-krang-destro",
        "Krang Droid x Destro",
        "Destro x Krang",
        "043377819325",
        "PL81988",
        f"{NZ}/imgi_131_4dc3a57e870e4dca93bb717590db4c92xl.jpg?v=1779640138",
        18.99,
        1.45,
    ),
    (
        "pm-tmnt-gijoe-bebop-ripper",
        "Bebop x Ripper",
        "Ripper x Bebop",
        "043377819332",
        "PL81933",
        f"{NZ}/imgi_126_ae01c67492154d3681eb3f45e6209ea4xl.jpg?v=1779640078",
        18.99,
        1.35,
    ),
    (
        "pm-tmnt-gijoe-rocksteady-buzzer",
        "Rocksteady x Buzzer",
        "Buzzer x Rocksteady",
        "043377819349",
        "PL81934",
        f"{NZ}/imgi_139_6ab12574fdd24e8180133a54bb88c176xl.jpg?v=1779640053",
        18.99,
        1.35,
    ),
    (
        "pm-tmnt-gijoe-slash-storm-shadow",
        "Slash x Storm Shadow",
        "Storm Shadow x Slash",
        "043377819363",
        "PL81936",
        f"{NZ}/imgi_130_a0aae690b311495fa252c7ee67a068daxl.jpg?v=1779640004",
        18.99,
        1.4,
    ),
]

GIJOE_VEHICLES = [
    (
        "pm-tmnt-gijoe-awe-shell-striker",
        "AWE Shell-Striker with Scarlett x April",
        "All-Weather and Environment Shell-Striker Vehicle",
        "043377819264",
        "PL81926",
        f"{CMD}/teenage-mutant-ninja-turtles-x-gi-joe-awe-shell-striker-with-scarlett-x-april-043377819264.jpg?v=1787608002",
        44.99,
        1.5,
        '5"',
    ),
    (
        "pm-tmnt-gijoe-turtle-fly-copter",
        "Turtle-Fly Copter",
        "Mobile Strike Force Assault Copter",
        "043377819318",
        "PL81931",
        f"{CMD}/teenage-mutant-ninja-turtles-gi-joe-turtle-fly-copter-043377819318.jpg?v=1787608161",
        50.99,
        1.45,
        '5"',
    ),
]

# Amazon exclusive variant — no verified GTIN found; image from nerdzoic retail copter
# is the non-exclusive box, so leave image empty rather than wrong.
GIJOE_EXCLUSIVES_NO_GTIN = [
    (
        "pm-tmnt-gijoe-turtle-fly-copter-amazon-wild-bill",
        "Turtle-Fly Copter with Raphael x Wild Bill",
        "Amazon Exclusive Mobile Strike Force Assault Copter",
        None,  # no verified GTIN
        [],
        None,  # prefer empty over wrong (retail copter art is figure-less)
        59.99,
        1.5,
        '5"',
        ["playmates", "tmnt", "gi-joe", "crossover", "amazon-exclusive", "inject-tmnt-gijoe"],
    ),
]

# Walmart exclusive 2-packs — lineup confirmed (ToyHabits); no honest GTIN feed found.
GIJOE_WALMART_2PACKS = [
    (
        "pm-tmnt-gijoe-2pk-leo-bebop",
        "Snake Eyes x Leo vs Ripper x Bebop",
        "Walmart Exclusive 2-Pack",
    ),
    (
        "pm-tmnt-gijoe-2pk-raph-rocksteady",
        "Roadblock x Raph vs Buzzer x Rocksteady",
        "Walmart Exclusive 2-Pack",
    ),
    (
        "pm-tmnt-gijoe-2pk-don-krang",
        "Dial-Tone x Donnie vs Destro x Krang",
        "Walmart Exclusive 2-Pack",
    ),
    (
        "pm-tmnt-gijoe-2pk-mikey-shredder",
        "Shipwreck x Mikey vs Cobra Commander x Shredder",
        "Walmart Exclusive 2-Pack",
    ),
]

# Densify: free GTINs only (not already primary on another oneshot row).
DENSIFY = [
    (
        "pm-tmnt-godzilla-mikey-ghidorah",
        "Michelangelo x Ghidorah",
        "TMNT x Godzilla",
        "Teenage Mutant Ninja Turtles x Godzilla",
        "043377846734",
        f"{CMD}/teenage-mutant-ninja-turtles-x-godzilla-godzilla-mikey-x-ghidorah-043377846734.jpg?v=1773860223",
        19.99,
        '6"',
        "2025-06-01",
        1.35,
    ),
    (
        "pm-tmnt-last-ronin",
        "The Last Ronin",
        "The Last Ronin",
        "TMNT The Last Ronin",
        "043377812050",
        f"{CMD}/teenage-mutant-ninja-turtles-the-last-ronin-the-last-ronin-043377812050.jpg?v=1762467126",
        29.99,
        '5"',
        "2024-06-01",
        1.5,
    ),
    (
        "pm-tmnt-last-ronin-raph",
        "Raphael",
        "The Last Ronin",
        "TMNT The Last Ronin",
        "043377812043",
        f"{CMD}/teenage-mutant-ninja-turtles-the-last-ronin-raphael-043377812043.jpg?v=1762467126",
        29.99,
        '5"',
        "2024-06-01",
        1.4,
    ),
    (
        "pm-tmnt-mutations-raph",
        "Raphael",
        "Mutations",
        "TMNT Mutations",
        "043377833642",
        f"{CMD}/teenage-mutant-ninja-turtles-mutations-raphael-043377833642.jpg?v=1766012189",
        14.99,
        '6"',
        "2025-01-01",
        1.25,
    ),
    (
        "pm-tmnt-bw-comic-raph",
        "Raphael",
        "B&W Comic Series",
        "TMNT B&W Comic Series",
        "043377817864",
        f"{CMD}/teenage-mutant-ninja-turtles-comic-series-raphael-043377817864.jpg?v=1741192816",
        11.99,
        '4"',
        "2024-03-01",
        1.2,
    ),
    (
        "pm-tmnt-1988-remastered-pack",
        "1988 Remastered Pack",
        "Classic Remastered Multipack",
        "TMNT Classic Collection",
        "043377846963",
        f"{CMD}/teenage-mutant-ninja-turtles-1988-remastered-pack-043377846963.jpg?v=1762467127",
        49.99,
        '5"',
        "2025-06-01",
        1.3,
    ),
]

# Shell Spin / Mutations Leo-Don-Mikey: honest Cmdstore images exist, but those
# GTINs are already wrongly primary on unrelated oneshot rows — add with EMPTY
# primary sku (images only) to avoid inventing remaps in this pass.
DENSIFY_IMAGE_ONLY = [
    (
        "pm-tmnt-shell-spin-leo",
        "Leonardo",
        "Shell Spin",
        "TMNT Shell Spin",
        f"{CMD}/teenage-mutant-ninja-turtles-shell-spin-leonardo-043377838296.jpg?v=1766012235",
        11.99,
        '5"',
        "2025-01-01",
        ["043377838296"],  # listing alias only — already claimed as primary elsewhere
    ),
    (
        "pm-tmnt-shell-spin-don",
        "Donatello",
        "Shell Spin",
        "TMNT Shell Spin",
        f"{CMD}/teenage-mutant-ninja-turtles-shell-spin-donatello-043377838302.jpg?v=1766012235",
        11.99,
        '5"',
        "2025-01-01",
        ["043377838302"],
    ),
    (
        "pm-tmnt-shell-spin-mikey",
        "Michelangelo",
        "Shell Spin",
        "TMNT Shell Spin",
        f"{CMD}/teenage-mutant-ninja-turtles-shell-spin-mikey-michelangelo-043377838319.jpg?v=1766012224",
        11.99,
        '5"',
        "2025-01-01",
        ["043377838319"],
    ),
    (
        "pm-tmnt-shell-spin-raph",
        "Raphael",
        "Shell Spin",
        "TMNT Shell Spin",
        f"{CMD}/teenage-mutant-ninja-turtles-shell-spin-raphael-043377838326.jpg?v=1766012166",
        11.99,
        '5"',
        "2025-01-01",
        ["043377838326"],
    ),
    (
        "pm-tmnt-mutations-leo",
        "Leonardo",
        "Mutations",
        "TMNT Mutations",
        f"{CMD}/teenage-mutant-ninja-turtles-mutations-leonardo-043377833611.jpg?v=1766012224",
        14.99,
        '6"',
        "2025-01-01",
        ["043377833611"],
    ),
    (
        "pm-tmnt-mutations-don",
        "Donatello",
        "Mutations",
        "TMNT Mutations",
        f"{CMD}/teenage-mutant-ninja-turtles-mutations-donatello-043377833628.jpg?v=1766012212",
        14.99,
        '6"',
        "2025-01-01",
        ["043377833628"],
    ),
    (
        "pm-tmnt-mutations-mikey",
        "Michelangelo",
        "Mutations",
        "TMNT Mutations",
        f"{CMD}/teenage-mutant-ninja-turtles-mutations-michelangelo-043377833635.jpg?v=1766012201",
        14.99,
        '6"',
        "2025-01-01",
        ["043377833635"],
    ),
]


def main() -> None:
    rows: list[dict] = load_json(ARCHIVE)
    by_id = {r["id"]: r for r in rows}
    sku_owners: dict[str, str] = {}
    for r in rows:
        s = clean_code(r.get("sku"))
        if s and is_gtin(s):
            sku_owners.setdefault(s, r["id"])

    aliases = ensure_alias_doc(load_json(ALIASES))
    sku_map: dict[str, str] = load_json(SKU_MAP)
    urls: dict[str, str] = load_json(URLS)

    added: list[str] = []
    skipped: list[dict] = []
    gtin_set: list[str] = []
    alias_added = 0
    img_baked = 0

    def inject(r: dict, alias_codes: list[str] | None = None, *, allow_claimed_gtin_as_alias_only: bool = False) -> bool:
        nonlocal alias_added, img_baked
        rid = r["id"]
        if rid in by_id:
            skipped.append({"id": rid, "reason": "id-exists"})
            return False
        sku = clean_code(r.get("sku"))
        if sku and is_gtin(sku):
            owner = sku_owners.get(sku)
            if owner and owner != rid:
                if allow_claimed_gtin_as_alias_only:
                    r["sku"] = None
                    alias_codes = list(alias_codes or []) + [sku]
                else:
                    skipped.append({"id": rid, "reason": f"gtin-owned-by:{owner}", "sku": sku})
                    return False
            else:
                sku_owners[sku] = rid
                gtin_set.append(sku)
        rows.append(r)
        by_id[rid] = r
        added.append(rid)
        if r.get("sku") and is_gtin(str(r["sku"])):
            sku_map[rid] = str(r["sku"])
            if "sku-bake" not in r["tags"]:
                r["tags"] = list(r["tags"]) + ["sku-bake", "sku-gtin"]
        if r.get("imageUrl"):
            urls[rid] = r["imageUrl"]
            img_baked += 1
            if "image-bake" not in r["tags"]:
                r["tags"] = list(r["tags"]) + ["image-bake", "img:cmdstore" if "0432/8397" in (r["imageUrl"] or "") else "img:nerdzoic"]
        if alias_codes:
            alias_added += add_aliases(aliases, rid, alias_codes)
        return True

    crossover_singles = crossover_vehicles = crossover_2packs = crossover_amazon = densify_n = 0

    for rid, name, sub, gtin, pl, img, msrp, demand in GIJOE_SINGLES:
        r = row(
            rid,
            name,
            sub,
            msrp=msrp,
            demand=demand,
            sku=gtin,
            image=img,
        )
        if inject(r, [pl, f"id:{rid}"]):
            crossover_singles += 1

    for rid, name, sub, gtin, pl, img, msrp, demand, scale in GIJOE_VEHICLES:
        r = row(
            rid,
            name,
            sub,
            msrp=msrp,
            demand=demand,
            scale=scale,
            sku=gtin,
            image=img,
            tags=[
                "playmates",
                "tmnt",
                "gi-joe",
                "crossover",
                "vehicle",
                "curated",
                "inject-tmnt-gijoe",
            ],
        )
        if inject(r, [pl, f"id:{rid}"]):
            crossover_vehicles += 1

    for rid, name, sub, gtin, als, img, msrp, demand, scale, tags in GIJOE_EXCLUSIVES_NO_GTIN:
        r = row(
            rid,
            name,
            sub,
            msrp=msrp,
            demand=demand,
            scale=scale,
            sku=gtin,
            image=img,
            tags=tags,
        )
        if inject(r, als + [f"id:{rid}"]):
            crossover_amazon += 1

    for rid, name, sub in GIJOE_WALMART_2PACKS:
        r = row(
            rid,
            name,
            sub,
            msrp=34.99,
            demand=1.4,
            sku=None,
            image=None,
            tags=[
                "playmates",
                "tmnt",
                "gi-joe",
                "crossover",
                "walmart-exclusive",
                "2-pack",
                "curated",
                "inject-tmnt-gijoe",
            ],
        )
        if inject(r, [f"id:{rid}"]):
            crossover_2packs += 1

    for rid, name, sub, line, gtin, img, msrp, scale, release, demand in DENSIFY:
        r = row(
            rid,
            name,
            sub,
            line=line,
            msrp=msrp,
            scale=scale,
            release=release,
            demand=demand,
            sku=gtin,
            image=img,
            tags=["playmates", "tmnt", "curated", "inject-playmates-densify"],
            source="inject-playmates-densify",
        )
        if inject(r, [f"id:{rid}"]):
            densify_n += 1

    for rid, name, sub, line, img, msrp, scale, release, claimed in DENSIFY_IMAGE_ONLY:
        r = row(
            rid,
            name,
            sub,
            line=line,
            msrp=msrp,
            scale=scale,
            release=release,
            demand=1.2,
            sku=None,
            image=img,
            tags=["playmates", "tmnt", "curated", "inject-playmates-densify", "sku-conflict-deferred"],
            source="inject-playmates-densify",
        )
        # Do NOT put conflicted GTINs into aliases pointing here — that would steal
        # aliasToFigureId from the current (wrong) primary owner. Image-only densify.
        if inject(r, [f"id:{rid}"]):
            densify_n += 1

    aliases["updatedAt"] = now_iso()
    aliases.setdefault("stats", {})
    aliases["stats"]["playmatesTmntGijoeInject"] = {
        "at": now_iso(),
        "added": len(added),
        "aliasAdded": alias_added,
    }

    write_json(ARCHIVE, rows)
    write_json(ALIASES, aliases)
    write_json(SKU_MAP, sku_map)
    write_json(URLS, urls)

    stats = {
        "at": now_iso(),
        "crossoverSingles": crossover_singles,
        "crossoverVehicles": crossover_vehicles,
        "crossoverWalmart2Packs": crossover_2packs,
        "crossoverAmazonExclusive": crossover_amazon,
        "crossoverTotal": crossover_singles + crossover_vehicles + crossover_2packs + crossover_amazon,
        "densifyOtherPlaymates": densify_n,
        "addedIds": added,
        "gtins": gtin_set,
        "skipped": skipped,
        "aliasAdded": alias_added,
        "imagesBaked": img_baked,
        "oneshotCount": len(rows),
        "notes": [
            "Walmart 2-packs and Amazon Wild Bill copter: no verified GTIN/image — empty preferred over wrong",
            "Shell Spin / Mutations Leo-Don-Mikey: images baked, primary sku left empty due to pre-existing GTIN ownership conflicts",
            "Target Leo PDP copy mentions 2-pack but UPC 043377819011 matches Forbidden Planet single Snake Eyes x Leonardo",
        ],
    }
    write_json(STATS, stats)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
