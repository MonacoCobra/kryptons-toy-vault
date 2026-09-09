#!/usr/bin/env python3
"""Inject JAKKS DC x Sonic crossover + densify Sonic 2.5"/5" (honest feeds).

Sources (verified):
  - Target PDPs (gtin13 / UPC in HTML + scene7 CDN images)
  - GoFigment Shopify product JSON (Tails/Cyborg multipack GTIN + CDN)
  - CmdStore product-sku-index (GTIN + Shopify CDN for standard Sonic)
  - JAKKS Pacific product pages (SKU aliases only when GTIN unverified)
  - ToyNewsI / SEGAbits for later-wave names (no invented GTINs)

Policy: real images only; GTIN primary when verified; Target TCIN / JAKKS SKU
→ aliases; empty sku/image over wrong. Does NOT Build Publish Live.
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
STATS = ROOT / "src/data/figure-archive/jakks-dc-sonic-inject-stats.json"

COMPANY = "jakks"
LINE_DC = "DC x Sonic"
LINE_25 = "Sonic 2.5-inch"
LINE_5 = "Sonic 5-inch"
LINE_4 = "Sonic 4-inch"
LINE_MOVIE = "Sonic Movie"
RELEASE_DC = "2025-10-01"
SRC = "inject-jakks-dc-sonic"

TGT = "https://target.scene7.com/is/image/Target"
CMD = "https://cdn.shopify.com/s/files/1/0216/0984/0740/files"
GOF = "https://cdn.shopify.com/s/files/1/0653/2019/0054/files"


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
        if c2 not in cur:
            cur.append(c2)
            added += 1
        to[c2] = figure_id
    if cur:
        by[figure_id] = cur
    return added


def tgt(guest: str) -> str:
    return f"{TGT}/{guest}?wid=800&hei=800&qlt=85"


def row(
    rid: str,
    name: str,
    subtitle: str,
    *,
    line: str,
    msrp: float,
    scale: str,
    demand: float = 1.35,
    kind: str = "figure",
    release: str = RELEASE_DC,
    sku: str | None = None,
    image: str | None = None,
    tags: list[str] | None = None,
    source: str = SRC,
) -> dict:
    return {
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
            "jakks",
            "sonic",
            "dc",
            "crossover",
            "curated",
            "inject-dc-sonic",
        ],
        "source": source,
        "sku": sku,
        "imageUrl": image,
    }


# --- DC x Sonic 5" singles (Target gtin13 verified) ---
# id, name, subtitle, gtin, tcin, jakks_sku, image, msrp, demand
DC_SINGLES_5 = [
    (
        "jk-sonic-dc-sonic-flash-5in",
        "Sonic as The Flash",
        "5-inch",
        "192995429024",
        "94501599",
        "429024",
        tgt("GUEST_93b5900f-5c5e-4e4c-ab5d-684c18af1430"),
        14.99,
        1.55,
    ),
    (
        "jk-sonic-dc-shadow-batman-5in",
        "Shadow as Batman",
        "5-inch",
        "192995429055",
        "94763561",
        "429055",
        tgt("GUEST_48df7d27-53c3-4629-aca0-2360009103a4"),
        14.99,
        1.6,
    ),
    (
        "jk-sonic-dc-knuckles-superman-5in",
        "Knuckles as Superman",
        "5-inch",
        "192995429031",
        "94763563",
        "429031",
        tgt("GUEST_38b0b13e-eb4c-480f-916f-732267664351"),
        14.99,
        1.5,
    ),
    (
        "jk-sonic-dc-silver-green-lantern-5in",
        "Silver as Green Lantern",
        "5-inch",
        "192995429086",
        "94501598",
        "429086",
        tgt("GUEST_d55805e1-3f09-4014-89a2-0f56e50367c0"),
        14.99,
        1.45,
    ),
]

# Amy 5" single: JAKKS SKU 429174 confirmed; Target GTIN not verified → sku empty
DC_SINGLES_5_NO_GTIN = [
    (
        "jk-sonic-dc-amy-wonder-woman-5in",
        "Amy as Wonder Woman",
        "5-inch",
        None,
        None,
        "429174",
        None,
        14.99,
        1.5,
    ),
    (
        "jk-sonic-dc-tails-cyborg-5in",
        "Tails as Cyborg",
        "5-inch",
        None,
        None,
        None,
        None,
        14.99,
        1.4,
    ),
    (
        "jk-sonic-dc-rouge-catwoman-5in",
        "Rouge as Catwoman",
        "5-inch",
        None,
        None,
        None,
        None,
        14.99,
        1.45,
        "2026-06-01",
    ),
]

# 2.5"/5" hero multipacks
DC_MULTIPACKS = [
    (
        "jk-sonic-dc-amy-ww-multipack",
        "Amy as Wonder Woman & Wonder Woman",
        "2.5/5-inch Multipack",
        "192995430938",
        "94763587",
        "430938",
        tgt("GUEST_ac6da561-1789-44d0-98d6-51d17ca08b43"),
        19.99,
        1.45,
        '2.5"/5"',
    ),
    (
        "jk-sonic-dc-silver-gl-multipack",
        "Silver as Green Lantern & Green Lantern",
        "2.5/5-inch Multipack",
        "192995430976",
        "94763586",
        "430976",
        tgt("GUEST_8cf15ef9-6373-46df-8843-d7a7625e0e22"),
        19.99,
        1.4,
        '2.5"/5"',
    ),
    (
        "jk-sonic-dc-shadow-batman-multipack",
        "Shadow as Batman & Batman",
        "2.5/5-inch Multipack",
        "192995430952",
        "94501609",
        "430952",
        tgt("GUEST_622bb492-30b1-46fa-9484-e1aac829abc8"),
        19.99,
        1.5,
        '2.5"/5"',
    ),
    (
        "jk-sonic-dc-knuckles-superman-multipack",
        "Knuckles as Superman & Superman",
        "2.5/5-inch Multipack",
        "192995430945",
        "94501608",
        "430945",
        tgt("GUEST_05edf9fc-7af1-43c3-823e-38c361e27f81"),
        19.99,
        1.45,
        '2.5"/5"',
    ),
    (
        "jk-sonic-dc-sonic-flash-multipack",
        "Sonic as The Flash & The Flash",
        "2.5/5-inch Multipack",
        "192995430921",
        "94763588",
        "430921",
        tgt("GUEST_8eef48f4-f855-4262-8ced-ea84c84615c3"),
        19.99,
        1.5,
        '2.5"/5"',
    ),
    (
        "jk-sonic-dc-tails-cyborg-multipack",
        "Tails as Cyborg & Cyborg",
        "2.5/5-inch Multipack",
        "192995430969",
        None,
        "430964",
        f"{GOF}/CyborgandTails.png?v=1774645152",
        19.99,
        1.45,
        '2.5"/5"',
    ),
]

DC_SETS = [
    (
        "jk-sonic-dc-power-vs-speed",
        "Power vs. Speed Pack",
        "Sonic Flash / Silver GL / Shadow Batman + 7-inch Darkseid",
        "192995429093",
        "94418625",
        "429094",
        tgt("GUEST_6410634c-14ea-4d6b-a169-5e78d095a828"),
        54.99,
        1.7,
        '5"/7"',
    ),
    (
        "jk-sonic-dc-shadow-batmobile",
        "Batmobile + Shadow as Batman",
        "2.5-inch Shadow-fied Batmobile",
        "192995429116",
        "94725151",
        "429116",
        tgt("GUEST_67541e2b-9353-4875-ba24-222bc5d59902"),
        29.99,
        1.55,
        '2.5"',
        "2026-03-01",
    ),
]

# Later waves / blind bags — names honest, no invented GTIN/image
DC_LATER = [
    (
        "jk-sonic-dc-blaze-starfire-5in",
        "Blaze as Starfire",
        "5-inch",
        '5"',
        14.99,
        1.4,
        "2026-06-01",
    ),
    (
        "jk-sonic-dc-eggman-lex-5in",
        "Dr. Eggman as Lex Luthor",
        "5-inch",
        '5"',
        14.99,
        1.35,
        "2026-06-01",
    ),
    (
        "jk-sonic-dc-rouge-catwoman-2-5in",
        "Rouge as Catwoman",
        "2.5-inch",
        '2.5"',
        6.99,
        1.3,
        "2026-06-01",
    ),
    (
        "jk-sonic-dc-blaze-starfire-multipack",
        "Blaze as Starfire & Starfire",
        "2.5/5-inch Multipack Series 3",
        '2.5"/5"',
        19.99,
        1.4,
        "2026-06-01",
    ),
    (
        "jk-sonic-dc-eggman-lex-multipack",
        "Dr. Eggman as Lex Luthor & Lex Luthor",
        "2.5/5-inch Multipack Series 3",
        '2.5"/5"',
        19.99,
        1.35,
        "2026-06-01",
    ),
    (
        "jk-sonic-dc-mystery-minis-s1",
        "DC x Sonic Mystery Minis Series 1",
        "Blind Bag Assortment",
        '2.5"',
        5.99,
        1.25,
        "2025-10-01",
    ),
]

# Densify: cmdstore GTINs (2.5" = "3 Inch Mini"; 5" movie; 4" articulated)
# id, name, subtitle, line, scale, gtin, image, msrp, release, demand
DENSIFY_GTIN = [
    # 2.5-inch Wave 9
    (
        "jk-sonic-25-wave9-sonic",
        "Sonic",
        "2.5-inch Wave 9",
        LINE_25,
        '2.5"',
        "192995403772",
        f"{CMD}/sonic-the-hedgehog-basic-wave-9-sonic-192995403772.jpg?v=1686087199",
        5.99,
        "2023-06-01",
        1.2,
    ),
    (
        "jk-sonic-25-wave9-tails",
        "Tails",
        "2.5-inch Wave 9",
        LINE_25,
        '2.5"',
        "192995412149",
        f"{CMD}/sonic-the-hedgehog-basic-wave-9-tails-192995412149.jpg?v=1686087214",
        5.99,
        "2023-06-01",
        1.15,
    ),
    (
        "jk-sonic-25-wave9-metal-sonic",
        "Metal Sonic",
        "2.5-inch Wave 9",
        LINE_25,
        '2.5"',
        "192995414389",
        f"{CMD}/sonic-the-hedgehog-basic-wave-9-metal-sonic-192995414389.jpg?v=1686108910",
        5.99,
        "2023-06-01",
        1.25,
    ),
    (
        "jk-sonic-25-wave9-mighty",
        "Mighty",
        "2.5-inch Wave 9",
        LINE_25,
        '2.5"',
        "192995408913",
        f"{CMD}/sonic-the-hedgehog-basic-wave-9-mighty-192995408913.jpg?v=1686108910",
        5.99,
        "2023-06-01",
        1.2,
    ),
    (
        "jk-sonic-25-wave9-ray",
        "Ray",
        "2.5-inch Wave 9",
        LINE_25,
        '2.5"',
        "192995414396",
        f"{CMD}/sonic-the-hedgehog-basic-wave-9-ray-192995414396.jpg?v=1686108911",
        5.99,
        "2023-06-01",
        1.2,
    ),
    # 2.5-inch Wave 20
    (
        "jk-sonic-25-wave20-espio",
        "Espio",
        "2.5-inch Wave 20",
        LINE_25,
        '2.5"',
        "192995420823",
        f"{CMD}/sonic-the-hedgehog-wave-20-espio-192995420823.jpg?v=1749505838",
        5.99,
        "2025-06-01",
        1.2,
    ),
    (
        "jk-sonic-25-wave20-knuckles",
        "Knuckles",
        "2.5-inch Wave 20",
        LINE_25,
        '2.5"',
        "192995403710",
        f"{CMD}/sonic-the-hedgehog-wave-20-knuckles-192995403710.jpg?v=1749505621",
        5.99,
        "2025-06-01",
        1.2,
    ),
    (
        "jk-sonic-25-wave20-tails",
        "Tails",
        "2.5-inch Wave 20",
        LINE_25,
        '2.5"',
        "192995416529",
        f"{CMD}/sonic-the-hedgehog-wave-20-tails-192995416529.jpg?v=1749505621",
        5.99,
        "2025-06-01",
        1.15,
    ),
    (
        "jk-sonic-25-egg-mobile-battle-set",
        "Egg Mobile Battle Set",
        "2.5-inch Box Set",
        LINE_25,
        '2.5"',
        "192995414440",
        f"{CMD}/sonic-the-hedgehog-box-set-egg-mobile-battle-set-192995414440.jpg?v=1736293931",
        24.99,
        "2024-12-01",
        1.3,
    ),
    (
        "jk-sonic-25-friends-rivals-10pk",
        "Friends and Rivals",
        "2.5-inch 10-Pack",
        LINE_25,
        '2.5"',
        "192995422476",
        tgt("GUEST_45a99d52-b945-4ce3-960c-78e298ec472f"),
        39.99,
        "2025-01-01",
        1.35,
    ),
    (
        "jk-sonic-25-8bit-3pk",
        "8-Bit Sonic 3-Pack",
        "2.5-inch Exclusive",
        LINE_25,
        '2.5"',
        "192995428898",
        tgt("GUEST_f5266c14-95eb-495b-a86c-f4db0fdc193c"),
        19.99,
        "2025-10-01",
        1.35,
    ),
    (
        "jk-sonic-movie3-minis-5pk",
        "Movie 3 Mini Figures 5-Pack",
        "Wave 3 Bundle",
        LINE_MOVIE,
        '2.5"',
        "192995425811",
        f"{CMD}/sonic-the-hedgehog-movie-wave-3-5-pack-bundle-192995425811.jpg?v=1749505838",
        29.99,
        "2025-01-01",
        1.3,
    ),
    # 5-inch Movie densify
    (
        "jk-sonic-movie-w1-sonic-5in",
        "Sonic",
        "Movie Wave 1 5-inch",
        LINE_5,
        '5"',
        "192995423978",
        f"{CMD}/sonic-the-hedgehog-movie-wave-1-sonic-192995423978.jpg?v=1736293880",
        14.99,
        "2024-12-01",
        1.35,
    ),
    (
        "jk-sonic-movie-w1-tails-5in",
        "Tails",
        "Movie Wave 1 5-inch",
        LINE_5,
        '5"',
        "192995424005",
        f"{CMD}/sonic-the-hedgehog-movie-wave-1-tails-192995424005.jpg?v=1736293894",
        14.99,
        "2024-12-01",
        1.25,
    ),
    (
        "jk-sonic-movie-w2-super-sonic-5in",
        "Super Sonic",
        "Movie Wave 2 5-inch",
        LINE_5,
        '5"',
        "192995424029",
        f"{CMD}/sonic-the-hedgehog-movie-wave-2-super-sonic-192995424029.jpg?v=1736293910",
        14.99,
        "2024-12-01",
        1.45,
    ),
    (
        "jk-sonic-movie-w2-knuckles-5in",
        "Knuckles",
        "Movie Wave 2 5-inch",
        LINE_5,
        '5"',
        "192995424036",
        f"{CMD}/sonic-the-hedgehog-movie-wave-2-knuckles-192995424036.jpg?v=1736293909",
        14.99,
        "2024-12-01",
        1.35,
    ),
    (
        "jk-sonic-movie-w3-super-shadow-5in",
        "Super Shadow",
        "Movie Wave 3 5-inch",
        LINE_5,
        '5"',
        "192995429536",
        f"{CMD}/sonic-the-hedgehog-movie-wave-3-super-shadow-192995429536.jpg?v=1749505622",
        14.99,
        "2025-01-01",
        1.5,
    ),
    (
        "jk-sonic-movie-w3-knuckles-5in",
        "Knuckles",
        "Movie Wave 3 5-inch",
        LINE_5,
        '5"',
        "192995430204",
        f"{CMD}/sonic-the-hedgehog-movie-wave-3-knuckles-192995430204.jpg?v=1749505838",
        14.99,
        "2025-01-01",
        1.35,
    ),
    # 4-inch articulated Wave 18/20
    (
        "jk-sonic-4in-w18-sonic",
        "Sonic",
        "4-inch Articulated Wave 18",
        LINE_4,
        '4"',
        "192995412354",
        f"{CMD}/sonig-the-hedgehog-articulated-wave-18-sonic-192995412354.jpg?v=1738004972",
        11.99,
        "2024-12-01",
        1.25,
    ),
    (
        "jk-sonic-4in-w18-amy",
        "Amy",
        "4-inch Articulated Wave 18",
        LINE_4,
        '4"',
        "192995423091",
        f"{CMD}/sonig-the-hedgehog-articulated-wave-18-amy-192995423091.jpg?v=1738004972",
        11.99,
        "2024-12-01",
        1.2,
    ),
    (
        "jk-sonic-4in-w18-metal-sonic",
        "Metal Sonic",
        "4-inch Articulated Wave 18",
        LINE_4,
        '4"',
        "192995423213",
        f"{CMD}/sonig-the-hedgehog-articulated-wave-18-metal-sonic-192995423213.jpg?v=1738004972",
        11.99,
        "2024-12-01",
        1.3,
    ),
    (
        "jk-sonic-4in-w18-vector",
        "Vector",
        "4-inch Articulated Wave 18",
        LINE_4,
        '4"',
        "192995414297",
        f"{CMD}/sonig-the-hedgehog-articulated-wave-18-vector-192995414297.jpg?v=1738004972",
        11.99,
        "2024-12-01",
        1.15,
    ),
    (
        "jk-sonic-4in-w20-espio",
        "Espio",
        "4-inch Wave 20",
        LINE_4,
        '4"',
        "192995414310",
        f"{CMD}/sonic-the-hedgehog-wave-20-espio-192995414310.jpg?v=1749505621",
        11.99,
        "2025-06-01",
        1.2,
    ),
    (
        "jk-sonic-4in-w20-tails",
        "Tails",
        "4-inch Wave 20",
        LINE_4,
        '4"',
        "192995430198",
        f"{CMD}/sonic-the-hedgehog-wave-20-tails-192995430198.jpg?v=1749505838",
        11.99,
        "2025-06-01",
        1.2,
    ),
    (
        "jk-sonic-35th-4in-3pk",
        "35th Anniversary Classic / Sonic / 16-Bit",
        "4-inch 3-Pack",
        LINE_4,
        '4"',
        "192995431416",
        tgt("GUEST_fbf3e2c4-7d5c-4e5b-bf21-ea2056bd2d3d"),
        29.99,
        "2026-01-01",
        1.4,
    ),
    (
        "jk-sonic-giant-mecha-vs-sonic",
        "Giant Mecha Sonic vs Sonic",
        "Feature Exclusive",
        LINE_5,
        '5"',
        "192995429840",
        tgt("GUEST_73212765-1688-49e8-8764-e867f7eac187"),
        49.99,
        "2025-10-01",
        1.5,
    ),
]

# Wave 22 2.5" characters — assortment UPC known; singles not individually verified
DENSIFY_NO_GTIN = [
    (
        "jk-sonic-25-wave22-trip",
        "Trip the Sungazer",
        "2.5-inch Wave 22",
        LINE_25,
        '2.5"',
        5.99,
        "2026-01-01",
        1.35,
    ),
    (
        "jk-sonic-25-wave22-ballhog",
        "Ballhog",
        "2.5-inch Wave 22",
        LINE_25,
        '2.5"',
        5.99,
        "2026-01-01",
        1.25,
    ),
    (
        "jk-sonic-25-wave22-assortment",
        "Wave 22 Assortment",
        "2.5-inch 5pc (Sonic/Shadow/Trip/Ray/Ballhog)",
        LINE_25,
        '2.5"',
        29.99,
        "2026-01-01",
        1.3,
        ["192995426054"],  # assortment UPC as alias only (case pack, not single primary)
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

    def inject(r: dict, alias_codes: list[str] | None = None) -> bool:
        nonlocal alias_added, img_baked
        rid = r["id"]
        if rid in by_id:
            skipped.append({"id": rid, "reason": "id-exists"})
            return False
        sku = clean_code(r.get("sku"))
        if sku and is_gtin(sku):
            owner = sku_owners.get(sku)
            if owner and owner != rid:
                skipped.append({"id": rid, "reason": f"gtin-owned-by:{owner}", "sku": sku})
                return False
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
            img_tag = "img:target" if "scene7.com" in (r["imageUrl"] or "") else (
                "img:gofigment" if "0653/2019" in (r["imageUrl"] or "") else "img:cmdstore"
            )
            if "image-bake" not in r["tags"]:
                r["tags"] = list(r["tags"]) + ["image-bake", img_tag]
        if alias_codes:
            alias_added += add_aliases(aliases, rid, alias_codes)
        return True

    cross_singles = cross_mp = cross_sets = cross_later = densify_n = 0

    for rid, name, sub, gtin, tcin, jsku, img, msrp, demand in DC_SINGLES_5:
        r = row(
            rid, name, sub, line=LINE_DC, msrp=msrp, scale='5"', demand=demand,
            sku=gtin, image=img,
        )
        als = [x for x in [tcin and f"tcin:{tcin}", jsku and f"jakks:{jsku}", f"id:{rid}"] if x]
        if inject(r, als):
            cross_singles += 1

    for item in DC_SINGLES_5_NO_GTIN:
        rid, name, sub, gtin, tcin, jsku, img, msrp, demand = item[:9]
        release = item[9] if len(item) > 9 else RELEASE_DC
        r = row(
            rid, name, sub, line=LINE_DC, msrp=msrp, scale='5"', demand=demand,
            release=release, sku=gtin, image=img,
            tags=["jakks", "sonic", "dc", "crossover", "curated", "inject-dc-sonic"],
        )
        als = [x for x in [tcin and f"tcin:{tcin}", jsku and f"jakks:{jsku}", f"id:{rid}"] if x]
        if inject(r, als):
            cross_singles += 1

    for item in DC_MULTIPACKS:
        rid, name, sub, gtin, tcin, jsku, img, msrp, demand, scale = item
        r = row(
            rid, name, sub, line=LINE_DC, msrp=msrp, scale=scale, demand=demand,
            sku=gtin, image=img,
            tags=["jakks", "sonic", "dc", "crossover", "multipack", "curated", "inject-dc-sonic"],
        )
        als = [x for x in [tcin and f"tcin:{tcin}", jsku and f"jakks:{jsku}", f"id:{rid}"] if x]
        if inject(r, als):
            cross_mp += 1

    for item in DC_SETS:
        rid, name, sub, gtin, tcin, jsku, img, msrp, demand, scale = item[:10]
        release = item[10] if len(item) > 10 else RELEASE_DC
        r = row(
            rid, name, sub, line=LINE_DC, msrp=msrp, scale=scale, demand=demand,
            release=release, sku=gtin, image=img,
            tags=["jakks", "sonic", "dc", "crossover", "set", "curated", "inject-dc-sonic"],
        )
        als = [x for x in [tcin and f"tcin:{tcin}", jsku and f"jakks:{jsku}", f"id:{rid}"] if x]
        if inject(r, als):
            cross_sets += 1

    for rid, name, sub, scale, msrp, demand, release in DC_LATER:
        r = row(
            rid, name, sub, line=LINE_DC, msrp=msrp, scale=scale, demand=demand,
            release=release, sku=None, image=None,
            tags=["jakks", "sonic", "dc", "crossover", "curated", "inject-dc-sonic", "later-wave"],
        )
        if inject(r, [f"id:{rid}"]):
            cross_later += 1

    for rid, name, sub, line, scale, gtin, img, msrp, release, demand in DENSIFY_GTIN:
        r = row(
            rid, name, sub, line=line, msrp=msrp, scale=scale, demand=demand,
            release=release, sku=gtin, image=img,
            tags=["jakks", "sonic", "curated", "inject-sonic-densify"],
            source="inject-jakks-sonic-densify",
        )
        if inject(r, [f"id:{rid}"]):
            densify_n += 1

    for item in DENSIFY_NO_GTIN:
        rid, name, sub, line, scale, msrp, release, demand = item[:8]
        extra_als = item[8] if len(item) > 8 else []
        r = row(
            rid, name, sub, line=line, msrp=msrp, scale=scale, demand=demand,
            release=release, sku=None, image=None,
            tags=["jakks", "sonic", "curated", "inject-sonic-densify"],
            source="inject-jakks-sonic-densify",
        )
        if inject(r, [f"id:{rid}"] + list(extra_als)):
            densify_n += 1

    aliases["updatedAt"] = now_iso()
    aliases.setdefault("stats", {})
    aliases["stats"]["jakksDcSonicInject"] = {
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
        "crossoverSingles": cross_singles,
        "crossoverMultipacks": cross_mp,
        "crossoverSets": cross_sets,
        "crossoverLaterWave": cross_later,
        "crossoverTotal": cross_singles + cross_mp + cross_sets + cross_later,
        "densifySonic": densify_n,
        "addedIds": added,
        "gtins": gtin_set,
        "skipped": skipped,
        "aliasAdded": alias_added,
        "imagesBaked": img_baked,
        "oneshotCount": len(rows),
        "notes": [
            "DC x Sonic Target exclusives Fall 2025+; Amy 5-inch / Tails 5-inch / Rouge 5-inch: JAKKS confirmed, Target GTIN not verified → empty sku",
            "Later-wave Blaze/Eggman/mystery minis: names from ToyNewsI — no GTIN/image yet",
            "Wave 22 assortment UPC 192995426054 stored as alias on assortment row only",
            "CmdStore '3 Inch Mini' mapped to Sonic 2.5-inch (JAKKS retail scale)",
        ],
    }
    write_json(STATS, stats)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
