#!/usr/bin/env python3
"""Inject Jazwares Halo + Pokémon densify (Wicked Cool Toys / Vault).

Sources (verified feeds / product pages):
  - shop.jazwares.com Shopify products.json + vault-halo / pokemon vault
  - HissTank collector UPC checklist (early World of Halo / Spartan Collection)
  - ToyWiz PDPs (Select GTINs + BigCommerce CDN images)
  - jazwarespokemon.fandom.com MediaWiki (Select 6" lineup + wikia CDN package art)
  - upcitemdb / Amazon / Target corroboration for 191726* Jazwares GTINs

Policy: real CDN images only; GTIN primary when verified; HLW*/PKW*/FNF* → aliases;
empty sku/image preferred over wrong. company=jazwares. kind=figure.
Does NOT Build Publish Live.
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
STATS = ROOT / "src/data/figure-archive/jazwares-halo-pokemon-inject-stats.json"

COMPANY = "jazwares"
SOURCE = "inject-jazwares-halo-pokemon"
JW_CDN = "https://cdn.shopify.com/s/files/1/0566/3676/8329"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def slugify(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("é", "e").replace("á", "a").replace("'", "").replace("'", "")
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
    release: str = "2021-10-01",
    sku: str | None = None,
    image: str | None = None,
    tags: list[str] | None = None,
    source: str = SOURCE,
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
        "tags": tags or ["jazwares", "curated", "inject-jazwares-halo-pokemon"],
        "source": source,
        "sku": sku,
        "imageUrl": image,
    }


# --- Verified early World of Halo / Spartan Collection GTINs (HissTank checklist) ---
# HLW listing codes are aliases; GTIN is primary when attached.
HALO_EARLY_GTIN: dict[str, str] = {
    "HLW0002": "191726377870",  # Master Chief 4"
    "HLW0003": "191726377887",  # Pilot
    "HLW0004": "191726377894",  # UNSC Marine A
    "HLW0005": "191726377900",  # Jackal Sniper
    "HLW0006": "191726377917",  # Brute Captain
    "HLW0007": "191726377924",  # Spartan Mk VII 4"
    "HLW0009": "191726377948",  # MC vs Brute Chieftain 2-pack
    "HLW0011": "191726377962",  # Spartan Mk V + Jega 2-pack
    "HLW0012": "191726377955",  # Marine + Grunt 2-pack
    "HLW0016": "191726378020",  # Warthog + Master Chief
    # Spartan Collection 6.5"
    "HLW0018": "191726378044",  # Master Chief 6.5"
    "SC-KAT": "191726378068",  # Kat-B320
    "SC-MK7": "191726378075",  # Spartan Mk VII 6.5"
    "SC-MK5V": "191726378082",  # Spartan Mk V [V]
}

# Early wave not always on vault shop — inject with GTIN, empty image (no honest CDN).
HALO_EARLY_EXTRA = [
    # id, name, subtitle, line, scale, msrp, release, gtin, aliases, tags_extra
    (
        "jz-halo-woh-master-chief-assault-rifle",
        "Master Chief",
        "World of Halo — Assault Rifle",
        "World of Halo",
        '4"',
        9.99,
        "2020-10-01",
        "191726377870",
        ["HLW0002"],
        [],
    ),
    (
        "jz-halo-woh-pilot",
        "The Pilot",
        "World of Halo",
        "World of Halo",
        '4"',
        9.99,
        "2020-10-01",
        "191726377887",
        ["HLW0003"],
        [],
    ),
    (
        "jz-halo-woh-unsc-marine-a",
        "UNSC Marine",
        "World of Halo — Marine A",
        "World of Halo",
        '4"',
        9.99,
        "2020-10-01",
        "191726377894",
        ["HLW0004"],
        [],
    ),
    (
        "jz-halo-woh-jackal-sniper",
        "Jackal Sniper",
        "World of Halo",
        "World of Halo",
        '4"',
        9.99,
        "2020-10-01",
        "191726377900",
        ["HLW0005"],
        [],
    ),
    (
        "jz-halo-woh-brute-captain",
        "Brute Captain",
        "World of Halo",
        "World of Halo",
        '4"',
        9.99,
        "2020-10-01",
        "191726377917",
        ["HLW0006"],
        [],
    ),
    (
        "jz-halo-woh-spartan-mk-vii",
        "Spartan Mk VII",
        "World of Halo",
        "World of Halo",
        '4"',
        9.99,
        "2020-10-01",
        "191726377924",
        ["HLW0007"],
        [],
    ),
    (
        "jz-halo-woh-2pk-spartan-mkv-jega",
        "Spartan Mk V (B) vs Jega 'Rdomnai",
        "World of Halo 2-Pack",
        "World of Halo",
        '4"',
        19.99,
        "2020-10-01",
        "191726377962",
        ["HLW0011"],
        ["2-pack"],
    ),
    (
        "jz-halo-woh-2pk-marine-grunt",
        "UNSC Marine B vs Grunt Conscript",
        "World of Halo 2-Pack",
        "World of Halo",
        '4"',
        19.99,
        "2020-10-01",
        "191726377955",
        ["HLW0012"],
        ["2-pack"],
    ),
    (
        "jz-halo-sc-kat-b320",
        "Kat-B320",
        "Spartan Collection",
        "Halo Spartan Collection",
        '6.5"',
        19.99,
        "2020-10-01",
        "191726378068",
        [],
        [],
    ),
    (
        "jz-halo-sc-spartan-mk-vii",
        "Spartan Mk VII",
        "Spartan Collection",
        "Halo Spartan Collection",
        '6.5"',
        19.99,
        "2020-10-01",
        "191726378075",
        [],
        [],
    ),
    (
        "jz-halo-sc-spartan-mk-v-v",
        "Spartan Mk V (V)",
        "Spartan Collection",
        "Halo Spartan Collection",
        '6.5"',
        19.99,
        "2020-10-01",
        "191726378082",
        [],
        [],
    ),
]


def parse_halo_shop(product: dict) -> dict | None:
    """Map a shop.jazwares.com Halo product into an injectable row."""
    title = (product.get("title") or "").strip()
    if not title:
        return None
    v = (product.get("variants") or [{}])[0]
    hlw = clean_code(v.get("sku")) or ""
    price = float(v.get("price") or 0) or 19.99
    img = None
    for im in product.get("images") or []:
        src = im.get("src")
        if src and "cdn.shopify.com" in src:
            img = src
            break
    body = re.sub(r"<[^>]+>", " ", product.get("body_html") or "")
    blob = f"{title} {body}".lower()

    # Skip pure costume/roleplay soft goods? Keep helmet/sword as Halo line densify.
    tags = ["jazwares", "halo", "wicked-cool-toys", "curated", "inject-jazwares-halo-pokemon"]
    line = "World of Halo"
    scale = '4"'
    demand = 1.35
    release = "2021-06-01"
    if product.get("published_at"):
        release = str(product["published_at"])[:10]
    elif product.get("created_at"):
        release = str(product["created_at"])[:10]

    name = title
    subtitle = "World of Halo"

    if "spartan collection" in blob or "6-inch" in blob or "6.5" in blob or hlw in {"HLW0018", "HLW0408", "HLW0409"}:
        line = "Halo Spartan Collection"
        scale = '6.5"'
        subtitle = "Spartan Collection"
        demand = 1.4
    if "vault collection" in blob:
        line = "Halo Master Chief Vault Collection"
        scale = '4"'
        subtitle = title.replace("Halo Master Chief Vault Collection", "").strip(" ()") or "Vault Collection"
        demand = 1.45
        tags.append("multipack")
    if "warthog" in blob or "mantis" in blob or "banshee" in blob or "mongoose" in blob:
        tags.append("vehicle")
        demand = 1.45
        if "warthog" in blob:
            scale = '4"'
            line = "World of Halo"
            name = "Warthog with Master Chief"
            subtitle = "World of Halo Deluxe Vehicle"
        elif "mantis" in blob:
            name = "UNSC Mantis and Spartan EVA"
            subtitle = "World of Halo Deluxe Vehicle"
        elif "banshee" in blob:
            name = "Banished Banshee and Elite Enforcer"
            subtitle = "World of Halo Vehicle"
    if "2-pack" in blob or " vs" in blob or "versus" in blob or "two figure" in blob or "figure pack" in blob:
        tags.append("2-pack")
    title_l = title.lower()
    if "helmet" in title_l:
        tags.append("roleplay")
        scale = "1:1"
        line = "Halo Roleplay"
        subtitle = "Deluxe Helmet"
        demand = 1.3
    if "energy sword" in title_l:
        tags.append("roleplay")
        scale = "1:1"
        line = "Halo Roleplay"
        subtitle = "Electronic Energy Sword"
        demand = 1.25
    if "big shot" in blob:
        tags.append("multipack")
        subtitle = "Big Shot Battle Pack"
        demand = 1.4

    # Clean display names for shop titles that already include Halo prefix
    if name.lower().startswith("halo "):
        name = name[5:].strip()
    if name.lower().startswith("master chief") and "vault" not in subtitle.lower():
        pass

    # Stable id from HLW when present
    if hlw and re.match(r"^HLW\d+", hlw, re.I):
        rid = f"jz-halo-{hlw.lower()}"
    else:
        rid = f"jz-halo-{slugify(name)}"

    # GTIN: only when HLW maps to verified early checklist OR barcode present
    gtin = clean_code(v.get("barcode")) if is_gtin(v.get("barcode")) else None
    if not gtin:
        # Warthog: shop HLW0072 ≈ early HLW0016 same vehicle pack — attach known UPC
        if hlw == "HLW0072":
            gtin = HALO_EARLY_GTIN["HLW0016"]
        elif hlw in HALO_EARLY_GTIN:
            gtin = HALO_EARLY_GTIN[hlw]

    aliases = [a for a in [hlw, f"id:{rid}"] if a]
    if hlw == "HLW0072":
        aliases.append("HLW0016")

    return {
        "row": row(
            rid,
            name,
            subtitle,
            line=line,
            msrp=price,
            scale=scale,
            demand=demand,
            release=release,
            sku=gtin,
            image=img,
            tags=tags,
        ),
        "aliases": aliases,
    }


# --- Pokémon Select 6" Super-Articulated (wiki lineup + ToyWiz GTINs where known) ---
WIKI_IMG = {
    "charizard-w1": "https://static.wikia.nocookie.net/jazwarespokemon/images/7/78/SelectArticulatedW1_Charizard.png/revision/latest?cb=20240305193424",
    "greninja": "https://static.wikia.nocookie.net/jazwarespokemon/images/5/5a/SelectArticulatedW1_Greninja.png/revision/latest?cb=20240305193423",
    "articuno": "https://static.wikia.nocookie.net/jazwarespokemon/images/d/d8/SelectArticulatedW1_Articuno.png/revision/latest?cb=20240305193420",
    "rayquaza-w1": "https://static.wikia.nocookie.net/jazwarespokemon/images/6/69/SelectArticulatedW1_Rayquaza.png/revision/latest?cb=20240305193424",
    "lucario": "https://static.wikia.nocookie.net/jazwarespokemon/images/e/e6/SelectArticulatedW2_Lucario.png/revision/latest?cb=20240305193424",
    "zapdos": "https://static.wikia.nocookie.net/jazwarespokemon/images/8/88/SelectArticulatedW2_Zapdos.png/revision/latest?cb=20240305193424",
    "moltres": "https://static.wikia.nocookie.net/jazwarespokemon/images/f/fd/SelectArticulatedW3_Moltres.png/revision/latest?cb=20240305193423",
    "typhlosion": "https://static.wikia.nocookie.net/jazwarespokemon/images/a/ad/SelectArticulatedW4_Typhlosion.png/revision/latest?cb=20240305193426",
    "dragapult": "https://static.wikia.nocookie.net/jazwarespokemon/images/5/5c/SelectArticulatedW4_Dragapult.png/revision/latest?cb=20240305193426",
    "samurott": "https://static.wikia.nocookie.net/jazwarespokemon/images/0/03/SelectArticulatedW4_Samurott.png/revision/latest?cb=20240305193427",
    "mewtwo-w5": "https://static.wikia.nocookie.net/jazwarespokemon/images/d/de/SelectArticulatedW5_Mewtwo.png/revision/latest?cb=20240305193426",
    "suicune": "https://static.wikia.nocookie.net/jazwarespokemon/images/d/d2/SelectArticulatedW5_Suicune.png/revision/latest?cb=20240305193426",
    "tyranitar": "https://static.wikia.nocookie.net/jazwarespokemon/images/3/32/SelectArticulatedW5_Tyranitar.png/revision/latest?cb=20240305201440",
    "garchomp-w6": "https://static.wikia.nocookie.net/jazwarespokemon/images/3/31/SelectArticulatedW6_Garchomp.png/revision/latest?cb=20240305193426",
    "raikou": "https://static.wikia.nocookie.net/jazwarespokemon/images/2/29/SelectArticulatedW6_Raikou.png/revision/latest?cb=20240305193429",
    "mp-charizard-garchomp": "https://static.wikia.nocookie.net/jazwarespokemon/images/7/71/SelectArticulatedMultiPack_Charizard_Garchomp.png/revision/latest?cb=20240305202720",
    "entei": "https://static.wikia.nocookie.net/jazwarespokemon/images/e/e5/SelectArticulatedW7_Entei.png/revision/latest?cb=20240305193429",
    "flygon": "https://static.wikia.nocookie.net/jazwarespokemon/images/0/02/SelectArticulatedW7_Flygon.png/revision/latest?cb=20240305193429",
    "toxtricity": "https://static.wikia.nocookie.net/jazwarespokemon/images/0/02/SelectArticulatedW7_Toxtricity.png/revision/latest?cb=20240305193429",
    "golisopod": "https://static.wikia.nocookie.net/jazwarespokemon/images/5/59/SelectArticulatedW8_Golisopod.png/revision/latest?cb=20250112185916",
    "ceruledge": "https://static.wikia.nocookie.net/jazwarespokemon/images/7/77/SelectArticulatedW8_Ceruledge.png/revision/latest?cb=20240716035919",
    "zeraora": "https://static.wikia.nocookie.net/jazwarespokemon/images/5/5c/SelectArticulatedW8_Zeraora.png/revision/latest?cb=20250112185959",
    "mega-charizard-x": "https://static.wikia.nocookie.net/jazwarespokemon/images/6/67/SelectArticulatedW9_Mega_Charizard_X.png/revision/latest?cb=20250112185939",
    "deoxys": "https://static.wikia.nocookie.net/jazwarespokemon/images/0/0c/SelectArticulatedW9_Deoxys_%28Normal_Forme%29.png/revision/latest?cb=20250112190019",
    "cinderace": "https://static.wikia.nocookie.net/jazwarespokemon/images/3/3b/SelectArticulatedW9_Cinderace.png/revision/latest?cb=20250112190027",
    "noivern": "https://static.wikia.nocookie.net/jazwarespokemon/images/e/e7/SelectArticulatedW10_Noivern.png/revision/latest?cb=20251216041711",
    "armarouge": "https://static.wikia.nocookie.net/jazwarespokemon/images/6/6f/SelectArticulatedW10_Armarouge.png/revision/latest?cb=20251213164027",
    "gallade": "https://static.wikia.nocookie.net/jazwarespokemon/images/0/01/SelectArticulatedW10_Gallade.png/revision/latest?cb=20251213164103",
    "mega-charizard-y": "https://static.wikia.nocookie.net/jazwarespokemon/images/2/26/SelectArticulatedW11_Mega_Charizard_Y.png/revision/latest?cb=20251111223019",
    "rayquaza-w11": "https://static.wikia.nocookie.net/jazwarespokemon/images/e/e7/SelectArticulatedW11_Rayquaza.png/revision/latest?cb=20260702212158",
    "garchomp-w11": "https://static.wikia.nocookie.net/jazwarespokemon/images/b/bf/SelectArticulatedW11_Garchomp.png/revision/latest?cb=20260702212213",
    "scizor": "https://static.wikia.nocookie.net/jazwarespokemon/images/3/3e/SelectArticulatedW11_Scizor.png/revision/latest?cb=20260221160605",
    "mega-lucario": "https://static.wikia.nocookie.net/jazwarespokemon/images/a/ae/SelectArticulatedW12_Mega_Lucario.png/revision/latest?cb=20260522222633",
    "incineroar": "https://static.wikia.nocookie.net/jazwarespokemon/images/2/24/SelectArticulatedW12_Incineroar.png/revision/latest?cb=20260522222654",
    "blastoise": "https://static.wikia.nocookie.net/jazwarespokemon/images/c/c4/SelectArticulatedW12_Blastoise.png/revision/latest?cb=20260626163824",
    "mewtwo-w12": "https://static.wikia.nocookie.net/jazwarespokemon/images/4/47/SelectArticulatedW12_Mewtwo.png/revision/latest?cb=20260713215725",
}

# Prefer ToyWiz BigCommerce CDN when we have a verified PDP image for GTIN rows
TOYWIZ_IMG = {
    "mega-charizard-x": "https://cdn11.bigcommerce.com/s-0kvv9/products/524584/images/801768/megacharizardselect__29815.1736539200.1280.1280.jpg?c=2",
    "gallade": "https://cdn11.bigcommerce.com/s-0kvv9/products/567189/images/860300/galladeselect__36285.1765401600.1280.1280.jpg?c=2",
    "armarouge": "https://cdn11.bigcommerce.com/s-0kvv9/products/567188/images/860299/armarougeselect__25105.1765401600.1280.1280.jpg?c=2",
    "noivern": "https://cdn11.bigcommerce.com/s-0kvv9/products/568065/images/861665/noivernselect__73108.1765660800.1280.1280.jpg?c=2",
    "mega-charizard-y": "https://cdn11.bigcommerce.com/s-0kvv9/products/586445/images/887501/191726828358__24056.1773100800.1280.1280.jpg?c=2",
    "iridescent": "https://cdn11.bigcommerce.com/s-0kvv9/products/570704/images/865307/191726911340__25794.1766966400.1280.1280.jpg?c=2",
    "eevee-evo": "https://cdn11.bigcommerce.com/s-0kvv9/products/559551/images/847633/191726760672__32236.1761696000.1280.1280.jpg?c=2",
}

# Load live og:image overrides if present (from scrape)
_tw = Path("/tmp/toywiz_imgs.json")
if _tw.exists():
    try:
        _tw_data = json.loads(_tw.read_text())
        for k, meta in _tw_data.items():
            if meta.get("img"):
                TOYWIZ_IMG[k] = meta["img"]
    except Exception:
        pass


def poke_img(key: str) -> str | None:
    return TOYWIZ_IMG.get(key) or WIKI_IMG.get(key)


# name, wave_subtitle, img_key, release, gtin, aliases, demand
POKEMON_SELECT_6 = [
    ("Charizard", "Select Wave 1", "charizard-w1", "2021-06-01", None, [], 1.4),
    ("Greninja", "Select Wave 1", "greninja", "2021-06-01", None, [], 1.35),
    ("Articuno", "Select Wave 1", "articuno", "2021-09-01", None, [], 1.35),
    ("Rayquaza", "Select Wave 1", "rayquaza-w1", "2021-10-01", None, [], 1.4),
    ("Lucario", "Select Wave 2", "lucario", "2022-06-01", None, [], 1.4),
    ("Zapdos", "Select Wave 2", "zapdos", "2022-06-01", None, [], 1.35),
    ("Moltres", "Select Wave 3", "moltres", "2022-10-01", None, [], 1.35),
    ("Typhlosion", "Select Wave 4", "typhlosion", "2023-03-01", None, [], 1.3),
    ("Dragapult", "Select Wave 4", "dragapult", "2023-03-01", None, [], 1.3),
    ("Samurott", "Select Wave 4", "samurott", "2023-03-01", None, [], 1.3),
    ("Mewtwo", "Select Wave 5", "mewtwo-w5", "2023-09-01", None, [], 1.45),
    ("Suicune", "Select Wave 5", "suicune", "2023-09-01", None, [], 1.35),
    ("Tyranitar", "Select Wave 5", "tyranitar", "2023-09-01", None, [], 1.4),
    ("Garchomp", "Select Wave 6", "garchomp-w6", "2023-10-01", None, [], 1.4),
    ("Raikou", "Select Wave 6", "raikou", "2023-11-01", None, [], 1.35),
    ("Entei", "Select Wave 7", "entei", "2024-03-01", None, [], 1.35),
    ("Flygon", "Select Wave 7", "flygon", "2024-03-01", None, [], 1.3),
    ("Toxtricity", "Select Wave 7", "toxtricity", "2024-03-01", None, [], 1.3),
    ("Golisopod", "Select Wave 8", "golisopod", "2024-08-01", None, [], 1.3),
    ("Ceruledge", "Select Wave 8", "ceruledge", "2024-08-01", None, [], 1.35),
    ("Zeraora", "Select Wave 8", "zeraora", "2024-08-01", None, [], 1.35),
    ("Mega Charizard X", "Select Wave 9 — Target Exclusive", "mega-charizard-x", "2025-01-01", "191726509042", ["PKW3428"], 1.55),
    ("Deoxys (Normal Forme)", "Select Wave 9", "deoxys", "2025-01-01", None, [], 1.4),
    ("Cinderace", "Select Wave 9", "cinderace", "2025-01-01", None, [], 1.35),
    ("Noivern", "Select Wave 10 — Target Exclusive", "noivern", "2025-12-01", "191726758105", [], 1.4),
    ("Armarouge", "Select Wave 10 — Target Exclusive", "armarouge", "2025-12-01", "191726758129", [], 1.4),
    ("Gallade", "Select Wave 10 — Target Exclusive", "gallade", "2025-12-01", "191726758112", [], 1.4),
    ("Mega Charizard Y", "Select Wave 11", "mega-charizard-y", "2026-03-01", "191726828358", [], 1.5),
    ("Rayquaza", "Select Wave 11", "rayquaza-w11", "2026-03-01", None, [], 1.35),
    ("Garchomp", "Select Wave 11", "garchomp-w11", "2026-03-01", None, [], 1.35),
    ("Scizor", "Select Wave 11", "scizor", "2026-03-01", None, [], 1.35),
    ("Mega Lucario", "Select Wave 12", "mega-lucario", "2026-06-01", None, [], 1.45),
    ("Incineroar", "Select Wave 12", "incineroar", "2026-06-01", None, [], 1.35),
    ("Blastoise", "Select Wave 12", "blastoise", "2026-06-01", None, [], 1.4),
    ("Mewtwo", "Select Wave 12", "mewtwo-w12", "2026-07-01", None, [], 1.4),
]

POKEMON_SELECT_EXTRA = [
    (
        "jz-poke-select-mp-charizard-garchomp",
        "Charizard & Garchomp",
        "Select Super-Articulated Multi-Pack",
        "Pokemon Select",
        '6"',
        49.99,
        "2023-11-01",
        None,
        poke_img("mp-charizard-garchomp"),
        ["multipack"],
    ),
    (
        "jz-poke-select-iridescent-kanto-4pk",
        "Bulbasaur, Squirtle, Charmander & Pikachu",
        "Select Iridescent Shine 4-Pack",
        "Pokemon Select",
        '3"',
        24.99,
        "2026-01-01",
        "191726911340",
        poke_img("iridescent"),
        ["multipack", "iridescent"],
    ),
    (
        "jz-poke-select-eevee-evo-4pk",
        "Eevee, Leafeon, Glaceon & Sylveon",
        "Select Evolution Pack — Special Finish",
        "Pokemon Select",
        '3"',
        24.99,
        "2025-10-01",
        "191726760672",
        poke_img("eevee-evo"),
        ["multipack", "evolution"],
    ),
    (
        "jz-poke-special-series-kanto-first-partners",
        "Kanto Region First Partners Figure Set",
        "Pokemon Special Series — Vault Exclusive",
        "Pokemon Special Series",
        "mixed",
        99.99,
        "2025-06-01",
        None,
        f"{JW_CDN}/files/PKW3549_Pokemon_SpecialSeriesKanto1stPartnerfigset_Vault_IPF_lpr.jpg?v=1749147879",
        ["multipack", "vault", "special-series"],
    ),
]

# Light densify: a handful of FNAF articulated vault figures (current Jazwares AF, not Squish).
FNAF_LIGHT = [
    (
        "jz-fnaf-toy-freddy-5in",
        "Toy Freddy",
        "5-Inch Articulated Figure",
        "Five Nights at Freddy's",
        '5"',
        12.99,
        "2023-01-01",
        "FNF0002",
    ),
    (
        "jz-fnaf-toy-bonnie-5in",
        "Toy Bonnie",
        "5-Inch Articulated Figure",
        "Five Nights at Freddy's",
        '5"',
        12.99,
        "2023-01-01",
        "FNF0099",
    ),
    (
        "jz-fnaf-toy-chica-5in",
        "Toy Chica",
        "5-Inch Articulated Figure",
        "Five Nights at Freddy's",
        '5"',
        12.99,
        "2023-01-01",
        "FNF0101",
    ),
    (
        "jz-fnaf-mangle-5in",
        "Mangle",
        "5-Inch Articulated Figure",
        "Five Nights at Freddy's",
        '5"',
        12.99,
        "2023-01-01",
        "FNF0100",
    ),
    (
        "jz-fnaf-golden-freddy-office",
        "Golden Freddy Office Set",
        "5-Inch Articulated Figure",
        "Five Nights at Freddy's",
        '5"',
        19.99,
        "2023-01-01",
        "FNF0023",
    ),
    (
        "jz-cod-ghost-mandible",
        "Ghost (Mandible)",
        "Call of Duty",
        "Call of Duty",
        '6"',
        35.00,
        "2023-01-01",
        "COD0069",
    ),
]


def load_shop_halo() -> list[dict]:
    """Return raw Shopify product dicts for Halo."""
    for path in (Path("/tmp/jazwares_halo_raw.json"), Path("/tmp/jazwares_products.json")):
        if not path.exists():
            continue
        ps = json.loads(path.read_text())
        if path.name == "jazwares_halo_raw.json":
            return ps
        out = []
        for p in ps:
            blob = " ".join(
                [
                    p.get("title") or "",
                    " ".join(p.get("tags") or []),
                    p.get("vendor") or "",
                ]
            ).lower()
            if "halo" in blob:
                out.append(p)
        return out
    return []


def shop_product_from_halo_export(h: dict) -> dict:
    """Pass-through raw Shopify product dict."""
    return h


def fnaf_shop_images() -> dict[str, str]:
    """Map FNF*/COD* sku → shop CDN image."""
    path = Path("/tmp/jazwares_products.json")
    if not path.exists():
        return {}
    ps = json.loads(path.read_text())
    out: dict[str, str] = {}
    for p in ps:
        v = (p.get("variants") or [{}])[0]
        sku = clean_code(v.get("sku"))
        if not sku:
            continue
        imgs = [i.get("src") for i in (p.get("images") or []) if i.get("src")]
        if imgs:
            out[sku] = imgs[0]
    return out


def main() -> None:
    rows: list[dict] = load_json(ARCHIVE)
    by_id = {r["id"]: r for r in rows}
    # Existing pokemon under ANY company — avoid name+company dupes for jazwares
    existing_jz_names = {
        (
            (r.get("name") or "").strip().lower(),
            (r.get("line") or "").strip().lower(),
            (r.get("subtitle") or "").strip().lower(),
        )
        for r in rows
        if (r.get("company") or "").lower() == "jazwares"
    }
    sku_owners: dict[str, str] = {}
    for r in rows:
        s = clean_code(r.get("sku"))
        if s and is_gtin(s):
            sku_owners.setdefault(s, r["id"])

    aliases = ensure_alias_doc(load_json(ALIASES))
    sku_map: dict[str, str] = load_json(SKU_MAP)
    urls: dict[str, str] = load_json(URLS)
    shop_imgs = fnaf_shop_images()

    added: list[str] = []
    skipped: list[dict] = []
    gtin_set: list[str] = []
    alias_added = 0
    img_baked = 0
    counts = {"halo": 0, "pokemon": 0, "other": 0}

    def inject(r: dict, alias_codes: list[str] | None = None) -> bool:
        nonlocal alias_added, img_baked
        rid = r["id"]
        if rid in by_id:
            skipped.append({"id": rid, "reason": "id-exists"})
            return False
        key = (
            (r.get("name") or "").strip().lower(),
            (r.get("line") or "").strip().lower(),
            (r.get("subtitle") or "").strip().lower(),
        )
        if key in existing_jz_names:
            skipped.append({"id": rid, "reason": "name-line-subtitle-dupe"})
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
        existing_jz_names.add(key)
        added.append(rid)
        if r.get("sku") and is_gtin(str(r["sku"])):
            sku_map[rid] = str(r["sku"])
            if "sku-bake" not in r["tags"]:
                r["tags"] = list(r["tags"]) + ["sku-bake", "sku-gtin"]
        if r.get("imageUrl"):
            urls[rid] = r["imageUrl"]
            img_baked += 1
            tag = "img:jazwares-shop" if "0566/3676/8329" in (r["imageUrl"] or "") else (
                "img:toywiz" if "bigcommerce.com" in (r["imageUrl"] or "") else "img:wikia"
            )
            if "image-bake" not in r["tags"]:
                r["tags"] = list(r["tags"]) + ["image-bake", tag]
        if alias_codes:
            alias_added += add_aliases(aliases, rid, alias_codes)
        return True

    # A) Halo from shop vault
    for h in load_shop_halo():
        parsed = parse_halo_shop(shop_product_from_halo_export(h))
        if not parsed:
            continue
        if inject(parsed["row"], parsed["aliases"]):
            counts["halo"] += 1

    # A2) Early-wave Halo extras (GTIN known; image empty)
    for rid, name, sub, line, scale, msrp, release, gtin, als, extra_tags in HALO_EARLY_EXTRA:
        tags = ["jazwares", "halo", "wicked-cool-toys", "curated", "inject-jazwares-halo-pokemon", "early-wave"] + list(
            extra_tags
        )
        r = row(
            rid,
            name,
            sub,
            line=line,
            msrp=msrp,
            scale=scale,
            release=release,
            demand=1.35,
            sku=gtin,
            image=None,
            tags=tags,
        )
        if inject(r, list(als) + [f"id:{rid}"]):
            counts["halo"] += 1

    # B) Pokemon Select 6"
    for name, sub, img_key, release, gtin, als, demand in POKEMON_SELECT_6:
        rid = f"jz-poke-select-{slugify(img_key if img_key else name)}"
        # Prefer stable ids for waves with same character
        if img_key.endswith("-w1") or img_key.endswith("-w5") or img_key.endswith("-w6") or img_key.endswith("-w11") or img_key.endswith("-w12"):
            rid = f"jz-poke-select-{slugify(img_key)}"
        else:
            rid = f"jz-poke-select-{slugify(name)}"
            if "Wave 11" in sub and name in {"Rayquaza", "Garchomp"}:
                rid = f"jz-poke-select-{slugify(name)}-w11"
            if "Wave 12" in sub and name == "Mewtwo":
                rid = "jz-poke-select-mewtwo-w12"
            if "Wave 5" in sub and name == "Mewtwo":
                rid = "jz-poke-select-mewtwo-w5"
            if "Wave 6" in sub and name == "Garchomp":
                rid = "jz-poke-select-garchomp-w6"
            if "Wave 1" in sub and name == "Rayquaza":
                rid = "jz-poke-select-rayquaza-w1"
            if "Wave 1" in sub and name == "Charizard":
                rid = "jz-poke-select-charizard-w1"
        img = poke_img(img_key)
        tags = ["jazwares", "pokemon", "pokemon-select", "curated", "inject-jazwares-halo-pokemon"]
        if "Exclusive" in sub:
            tags.append("target-exclusive")
        r = row(
            rid,
            name,
            sub,
            line="Pokemon Select",
            msrp=24.99 if not gtin or name.startswith("Mega") else 19.99,
            scale='6"',
            release=release,
            demand=demand,
            sku=gtin,
            image=img,
            tags=tags,
        )
        # Mega Charizard X MSRP from Amazon ~39.97 Target exclusive
        if "Mega Charizard" in name or "Mega Lucario" in name:
            r["msrp"] = 32.99
        if inject(r, list(als) + [f"id:{rid}"]):
            counts["pokemon"] += 1

    # B2) Pokemon Select extras + Special Series
    for rid, name, sub, line, scale, msrp, release, gtin, img, extra in POKEMON_SELECT_EXTRA:
        tags = ["jazwares", "pokemon", "curated", "inject-jazwares-halo-pokemon"] + list(extra)
        if "Select" in line:
            tags.append("pokemon-select")
        r = row(
            rid,
            name,
            sub,
            line=line,
            msrp=msrp,
            scale=scale,
            release=release,
            demand=1.4,
            sku=gtin,
            image=img,
            tags=tags,
        )
        als = [f"id:{rid}"]
        if rid.endswith("kanto-first-partners"):
            als.append("PKW3549")
        if inject(r, als):
            counts["pokemon"] += 1

    # C) Light other densify (FNAF / CoD) with shop CDN images
    for rid, name, sub, line, scale, msrp, release, listing in FNAF_LIGHT:
        img = shop_imgs.get(listing)
        tags = ["jazwares", "curated", "inject-jazwares-halo-pokemon", "inject-jazwares-light"]
        if "Freddy" in line or "fnaf" in rid:
            tags.append("fnaf")
        if "Call of Duty" in line:
            tags.append("call-of-duty")
        r = row(
            rid,
            name,
            sub,
            line=line,
            msrp=msrp,
            scale=scale,
            release=release,
            demand=1.25,
            sku=None,  # no verified GTIN
            image=img,
            tags=tags,
        )
        if inject(r, [listing, f"id:{rid}"]):
            counts["other"] += 1

    aliases["updatedAt"] = now_iso()
    aliases["stats"] = {
        **(aliases.get("stats") or {}),
        "jazwaresHaloPokemonInjectAt": now_iso(),
        "jazwaresHaloPokemonAliasAdds": alias_added,
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
        "skipped": skipped[:40],
        "skippedCount": len(skipped),
        "sampleAdded": added[:25],
        "notes": [
            "Halo: shop.jazwares vault + early-wave HissTank GTINs",
            "Pokemon: Select 6\" wiki lineup + ToyWiz GTINs + Special Series Kanto vault",
            "Sonic classic AF not found on current shop (Squishmallows only) — skipped",
            "Bandai/Jakks Pokemon left untouched (different company)",
            "Did NOT Build Publish Live",
        ],
    }
    write_json(STATS, stats)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
