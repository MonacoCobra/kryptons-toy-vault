#!/usr/bin/env python3
"""Densify Show.Z Store 3rd Party & Official Transformers into the figure oneshot.

Source crawl: https://showzstore.com/c/3rd-party-amp-official-tfs_0371
Pages 1–52, pulled 2026-09-23. Catalog:
  scripts/figure_oneshot/showzstore_3p_official_catalog.json

Mapped makers use existing company slugs. The 122 previously unmapped makers
get company cards (party 3p, property Transformers) and their listings.
Upgrades / non-TF / the refined vault-dupe bucket stay out of the catalog.
Listing codes and Show.Z product ids are aliases. sku stays unset (no GTIN).

Does NOT Build Publish Live.
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/workspace")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_identity import clean_code  # noqa: E402

ARCHIVE = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
STATS = ROOT / "src/data/figure-archive/showzstore-3p-official-inject-stats.json"
CATALOG = SCRIPTS / "figure_oneshot/showzstore_3p_official_catalog.json"
TYPES = ROOT / "src/lib/types.ts"
COMPANIES_TS = ROOT / "src/data/companies.ts"
PROPERTY_TS = ROOT / "src/lib/figure-property.ts"
FIGURES_TS = ROOT / "src/data/figures.ts"

UPLOAD_PACK = Path("/home/ubuntu/.cursor/projects/workspace/uploads/densify-pack-refined_b25b.json")
UPLOAD_UNMAPPED = Path("/home/ubuntu/.cursor/projects/workspace/uploads/map-all-unmapped-brands_a3d8.json")

SOURCE = "inject-showzstore-3p-official"
MARKER = "showzstore-3p-official"

# DJS is already a company card but was missing from the 3P matcher, so Brave
# General rows never landed on Transformers → 3P. The new makers join it.
EXTRA_TF_3P = ["djs"]

PALETTE = [
    "#e63946",
    "#457b9d",
    "#2a9d8f",
    "#e9c46a",
    "#264653",
    "#6a4c93",
    "#c1121f",
    "#fb8500",
    "#023e8a",
    "#1d3557",
    "#9b2226",
    "#0a9396",
    "#bb3e03",
    "#005f73",
    "#ae2012",
    "#94d2bd",
    "#ee9b00",
    "#ca6702",
    "#9b5de5",
    "#00bbf9",
]

# Leading brand phrases that are not the product name. Longest match wins.
EXTRA_BRANDS: dict[str, list[str]] = {
    "takaratomy": ["Takara Tomy", "Takara", "Tomy"],
    "hasbro": ["Hasbro"],
    "magicsquare": ["Magic Square", "MagicSquare"],
    "mastermind": ["Mastermind Creations", "Ocular Max", "Mastermind", "MMC"],
    "xtransbots": ["X-Transbots", "XTransbots", "X Transbots"],
    "drwu": ["Dr. Wu", "Dr.Wu", "Dr Wu"],
    "newage": ["Newage", "New Age"],
    "threezero": ["Threezero", "ThreeZero", "Three Zero", "threezero"],
    "flametoys": ["Flame Toys", "FlameToys"],
    "yolopark": ["Yolopark", "YoloPark", "Yolo Park"],
    "blokees": ["Blokees"],
    "robosen": ["Robosen"],
    "djs": ["Craftsman Toys", "DJS Toys", "DJS"],
    "fanstoys": ["Fans Toys", "FansToys"],
    "ironfactory": ["Iron Factory"],
    "uniquetoys": ["Unique Toys"],
    "toyworld": ["Toy World", "Toyworld"],
    "perfecteffect": ["Perfect Effect"],
    "moonstudio": ["Moon Studio"],
    "maketoys": ["MakeToys", "Make Toys"],
    "planetx": ["Planet X"],
    "generationtoy": ["Generation Toy"],
    "gcreation": ["G-Creation", "G Creation", "GCreation"],
    "zeta": ["Zeta Toys", "Zeta"],
    "toywolf": ["Toy Wolf", "ToyWolf"],
    "fanshobby": ["Fans Hobby", "FansHobby"],
    "fansproject": ["FansProject", "Fans Project"],
    "transart": ["TransArt", "Transart"],
    "cangtoys": ["Cang Toys", "CangToys"],
    "dx9": ["DX9"],
    "tfc": ["TFC"],
    "kfc": ["KFC"],
}

DEFAULT_LINE: dict[str, str] = {
    "newage": "Newage",
    "fanstoys": "Fans Toys",
    "magicsquare": "Magic Square",
    "xtransbots": "XTransbots",
    "djs": "Brave General",
    "drwu": "Dr. Wu",
    "ironfactory": "Iron Factory",
    "dx9": "DX9",
    "mastermind": "Mastermind Creations",
    "maketoys": "MakeToys",
    "planetx": "Planet X",
    "kfc": "KFC",
    "tfc": "TFC",
    "gcreation": "GCreation",
    "generationtoy": "Generation Toy",
    "zeta": "Zeta",
    "toywolf": "ToyWolf",
    "fanshobby": "Fans Hobby",
    "fansproject": "FansProject",
    "transart": "TransArt",
    "cangtoys": "Cang Toys",
    "uniquetoys": "Unique Toys",
    "toyworld": "Toyworld",
    "perfecteffect": "Perfect Effect",
    "moonstudio": "Moon Studio",
    "blokees": "Blokees Transformers",
    "threezero": "threezero",
    "yolopark": "Yolopark AMK",
    "flametoys": "Flame Toys",
    "robosen": "Robosen",
    "hasbro": "Hasbro Transformers",
    "takaratomy": "Takara Tomy Transformers",
}

ONE_P = {"hasbro", "takaratomy"}
TWO_P = {"blokees", "threezero", "yolopark", "flametoys", "robosen"}

STATUS_RES = [
    re.compile(
        r"^\[(Coming Soon|Pre-Order|Pre-order|Sample|Parts not working|No Box|"
        r"Express Shipping|Make To Order|Make to Order|Scratches)\]\s*",
        re.I,
    ),
    re.compile(r"^\[[^\]]*(?:Buyer|buyer) Only\]\s*"),
]

CODE_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9])("
    r"[A-Z]{1,10}(?:[-.][A-Z]{0,8})*[-.]?\d{1,4}(?:[A-Z0-9+]+|[-.][A-Z0-9+]{1,8})*"
    r"|\d{2}[A-Z][-.]?\d{2,4}(?:[-.][A-Z0-9+]{1,6})*"
    r"|\d[A-Z]{1,4}[-.]?\d{2,6}[A-Z0-9+]*"
    r"|MINI\d{2}[A-Z]{0,4}"
    r"|B\.I\.G[-.]?\d{2}"
    r")"
)

VARIANT_RE = re.compile(
    r"\b(?:metallic|chrome|transparent|ghost|shattered|painted|comic|nemesis|exclusive|toy color)\b"
    r"|\b(?:red|blue|gold|silver|black|white|yellow|green|purple|gray|grey|g1|g2|idw|clear)\s+"
    r"(?:version|ver\.?|color|colour|edition)\b"
    r"|\bex\s+version\b"
    r"|\bpremium\s+paint\b|\bpaint\s+version\b"
    r"|\bcog-?less\b|\bcogged\b",
    re.I,
)

# Brand tokens that look like codes (DX9) but are the maker, not a product id.
KNOWN_DISPLAY: dict[str, str] = {
    "takaratomy": "Takara Tomy",
    "hasbro": "Hasbro",
    "magicsquare": "Magic Square",
    "mastermind": "Mastermind Creations",
    "xtransbots": "XTransbots",
    "drwu": "Dr. Wu",
    "newage": "Newage",
    "threezero": "threezero",
    "flametoys": "Flame Toys",
    "yolopark": "Yolopark",
    "blokees": "Blokees",
    "robosen": "Robosen",
    "djs": "DJS",
    "fanstoys": "Fans Toys",
    "ironfactory": "Iron Factory",
    "uniquetoys": "Unique Toys",
    "toyworld": "Toyworld",
    "perfecteffect": "Perfect Effect",
    "moonstudio": "Moon Studio",
    "maketoys": "MakeToys",
    "planetx": "Planet X",
    "generationtoy": "Generation Toy",
    "gcreation": "GCreation",
    "zeta": "Zeta",
    "toywolf": "ToyWolf",
    "fanshobby": "Fans Hobby",
    "fansproject": "FansProject",
    "transart": "TransArt",
    "cangtoys": "Cang Toys",
    "dx9": "DX9",
    "tfc": "TFC",
    "kfc": "KFC",
}

LEADING_NOISE = re.compile(
    r"^(?:masterpiece|transformers|movie(?:\s+series)?|amk(?:\s+pro)?(?:\s+series)?|series)\b[:\s\-]*",
    re.I,
)

SCALE_RES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bMDLX\b", re.I), "MDLX"),
    (re.compile(r"\bDLX\b", re.I), "DLX"),
    (re.compile(r"\b(1\s*/\s*\d{1,3})\b"), "ratio"),
    (re.compile(r"\b(1\s*:\s*\d{1,3})\b"), "ratio"),
    (re.compile(r"\b(titan|commander|leader|voyager|deluxe|legends|core)\s+class\b", re.I), "class"),
    (re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:inch|inches)\b", re.I), "inch"),
    (re.compile(r"\bMP\b"), "MP"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def norm_code(c: str | None) -> str:
    if not c:
        return ""
    return re.sub(r"[^A-Z0-9]", "", str(c).upper())


def code_key(c: str | None) -> str:
    """Identity key for a listing code. Keeps '+' so MP-56 and MP-56+ stay distinct."""
    if not c:
        return ""
    s = str(c).upper().replace(" ", "").replace(".", "")
    s = re.sub(r"(?<=[A-Z0-9])-+(?=[A-Z0-9+])", "", s)
    return re.sub(r"[^A-Z0-9+]", "", s)


def norm_name(s: str) -> str:
    s = html.unescape(s or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def slugify(s: str, limit: int = 48) -> str:
    s = (s or "").lower().replace("'", "").replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:limit].strip("-")


def unescape_title(s: str) -> str:
    s = html.unescape(s or "")
    s = s.replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def brand_phrases(company: str, display: str, aliases: list[str]) -> list[str]:
    phrases = list(EXTRA_BRANDS.get(company, []))
    phrases.append(display)
    phrases.append(f"{display} Toys")
    phrases.extend(aliases)
    phrases.append(display.replace(" ", ""))
    phrases.append(display.replace(" ", "-"))
    # unique, longest first
    seen: set[str] = set()
    out: list[str] = []
    for p in sorted(phrases, key=len, reverse=True):
        key = p.lower().strip()
        if len(key) < 2 or key in seen:
            continue
        seen.add(key)
        out.append(p.strip())
    return out


def strip_status(title: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    s = title.strip()
    changed = True
    while changed:
        changed = False
        for rx in STATUS_RES:
            m = rx.match(s)
            if not m:
                continue
            label = re.sub(r"\s+", " ", m.group(0).strip("[] ")).strip()
            if label and label.lower() not in {n.lower() for n in notes}:
                notes.append(label)
            s = s[m.end() :].strip()
            changed = True
    return s, notes


def strip_brands(title: str, phrases: list[str]) -> str:
    s = title.strip()
    changed = True
    while changed and s:
        changed = False
        low = s.lower()
        for p in phrases:
            pl = p.lower()
            if low.startswith(pl):
                s = s[len(p) :].lstrip(" -–—:|&/")
                changed = True
                break
    return re.sub(r"\s+", " ", s).strip(" -–—")


def brand_norms(company: str, display: str = "", aliases: list[str] | None = None) -> set[str]:
    norms = {norm_code(company)}
    for p in EXTRA_BRANDS.get(company, []):
        n = norm_code(p)
        if n:
            norms.add(n)
    for p in [display, *(aliases or [])]:
        n = norm_code(p)
        if n:
            norms.add(n)
    return {n for n in norms if n}


def extract_codes(title: str, company: str = "", display: str = "", aliases: list[str] | None = None) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for m in CODE_RE.finditer(title.upper()):
        raw = m.group(1).strip(".")
        raw = raw.replace("B.I.G", "BIG")
        nc = norm_code(raw)
        if not nc or nc in seen:
            continue
        if not re.search(r"[A-Z]", nc) or not re.search(r"\d", nc):
            continue
        if len(nc) < 3 or len(nc) > 16:
            continue
        if re.fullmatch(r"(19|20)\d{2}", nc):
            continue
        if company and nc in brand_norms(company, display, aliases):
            continue
        seen.add(nc)
        pretty = raw.upper().replace(" ", "")
        found.append(pretty)
    return found


def variant_set(name: str) -> frozenset[str]:
    return frozenset(m.group(0).lower() for m in VARIANT_RE.finditer(name))


def release_from_image(url: str | None) -> str:
    """Listing image folders on Show.Z are YYMM. Not a street date."""
    if url:
        for yy, mm in re.findall(r"/(\d{2})(\d{2})/", url):
            y, m = int(yy), int(mm)
            if 15 <= y <= 30 and 1 <= m <= 12:
                return f"20{yy}-{mm}-01"
    return "2026-09-01"


def scale_of(title: str) -> str:
    for rx, kind in SCALE_RES:
        m = rx.search(title)
        if not m:
            continue
        if kind == "ratio":
            return re.sub(r"\s+", "", m.group(1))
        if kind == "class":
            return m.group(1).title() + " Class"
        if kind == "inch":
            return f'{m.group(1)}"'
        return kind if kind in {"MP", "DLX", "MDLX"} else m.group(0)
    return ""


def line_for(company: str, title: str, guess: str | None, codes: list[str], display: str) -> str:
    blob = f"{title} {' '.join(codes)}".lower()
    if company == "blokees":
        if "defender" in blob:
            return "Blokees Defender Version"
        if "galaxy" in blob:
            return "Blokees Galaxy Version"
        if "wheels" in blob:
            return "Blokees Wheels"
        if "shining" in blob:
            return "Blokees Shining Version"
        if "classic" in blob:
            return "Blokees Classic Class"
        if "action edition" in blob:
            return "Blokees Action Edition"
        if "champion" in blob:
            return "Blokees Champion Class"
        return "Blokees Transformers"
    if company == "threezero":
        if "mdlx" in blob:
            return "threezero MDLX"
        if "dlx" in blob or guess == "threezero DLX":
            return "threezero DLX"
        if "figzero" in blob or "fig zero" in blob:
            return "threezero FigZero"
        return "threezero"
    if company == "yolopark":
        if "amk pro" in blob:
            return "Yolopark AMK PRO"
        if "amk mini" in blob:
            return "Yolopark AMK Mini"
        return "Yolopark AMK"
    if company == "flametoys":
        if "kuro kara" in blob or re.search(r"\bkkk\b", blob):
            return "Kuro Kara Kuri"
        if "furai" in blob:
            return "Furai Model"
        return "Flame Toys"
    if company == "robosen":
        if "flagship" in blob:
            return "Robosen Flagship"
        if "elite" in blob:
            return "Robosen Elite"
        if re.search(r"\bmini\b", blob):
            return "Robosen Mini"
        if "performance" in blob:
            return "Robosen Performance"
        return "Robosen"
    if company == "magicsquare":
        if re.search(r"\bms-?b\d", blob):
            return "B Series"
        if re.search(r"\bms-?g\d", blob):
            return "G Series"
        return "Magic Square"
    if company == "xtransbots":
        if re.search(r"\bmx-?\d", blob):
            return "XTransbots MX"
        return "XTransbots"
    if company == "mastermind":
        if "ocular max" in blob:
            return "Ocular Max"
        return "Mastermind Creations"
    if company in ONE_P:
        if guess == "Studio Series" or "studio series" in blob:
            return "Transformers Studio Series"
        if guess == "Vintage G1" or ("vintage" in blob and re.search(r"\bg1\b", blob)):
            return "Transformers Vintage G1"
        if guess == "Missing Link" or "missing link" in blob:
            return "Transformers Missing Link"
        if "masterpiece" in blob or re.search(r"\bmp-?\d", blob) or guess == "Masterpiece":
            return "Transformers Masterpiece"
        if company == "hasbro":
            return "Hasbro Transformers"
        return "Takara Tomy Transformers"
    return DEFAULT_LINE.get(company, display)


def kind_for(company: str, title: str) -> str:
    if company in {"blokees", "yolopark"}:
        return "kit"
    if re.search(r"model kits?|gunpla", title, re.I):
        return "kit"
    return "figure"


def party_for(company: str, suggested: str | None) -> str:
    if company in ONE_P:
        return "1p"
    if company in TWO_P:
        return "2p"
    if suggested in {"1p", "2p", "3p"}:
        return suggested
    return "3p"


def short_name(display: str) -> str:
    if len(display) <= 18:
        return display
    parts = display.split()
    s = parts[0]
    for p in parts[1:]:
        nxt = f"{s} {p}"
        if len(nxt) <= 18:
            s = nxt
        else:
            break
    return s


def figure_id(company: str, codes: list[str], name: str) -> str:
    code_bit = slugify(codes[0], 24) if codes else ""
    rest = name
    if codes:
        rest = re.sub(re.escape(codes[0]), " ", name, count=1, flags=re.I)
    name_bit = slugify(rest, 42)
    parts = [company]
    if code_bit and code_bit not in name_bit.split("-"):
        parts.append(code_bit)
    if name_bit:
        parts.append(name_bit)
    rid = "-".join(parts).strip("-")
    return rid[:78].strip("-") or f"{company}-showz"


def normalize_listing(
    raw: dict,
    *,
    company: str,
    display: str,
    aliases: list[str],
    party_suggested: str | None,
    line_guess: str | None,
) -> dict:
    title = unescape_title(raw.get("title_clean") or raw.get("name") or "")
    bare, notes = strip_status(title)
    phrases = brand_phrases(company, display, aliases)
    name = strip_brands(bare, phrases) or bare or title
    while True:
        nxt = LEADING_NOISE.sub("", name).strip(" -–—:")
        if nxt == name or not nxt:
            break
        name = nxt
    codes = extract_codes(bare or title, company, display, aliases)
    subtitle_bits = list(notes)
    subtitle_bits.append(f"Show.Z #{raw['id']}")
    image = raw.get("image") or ""
    if not (isinstance(image, str) and image.startswith("http")):
        image = ""
    price = raw.get("price_usd")
    msrp = float(price) if isinstance(price, (int, float)) else 0.0
    return {
        "showzId": str(raw["id"]),
        "url": raw.get("url") or "",
        "company": company,
        "displayName": display,
        "party": party_for(company, party_suggested),
        "line": line_for(company, bare or title, line_guess, codes, display),
        "name": name,
        "subtitle": " · ".join(subtitle_bits),
        "imageUrl": image,
        "msrp": msrp,
        "releaseDate": release_from_image(image),
        "scale": scale_of(bare or title),
        "kind": kind_for(company, bare or title),
        "codes": codes,
        "variant": sorted(variant_set(name)),
        "page": raw.get("page"),
    }


def build_catalog() -> dict:
    pack = load_json(UPLOAD_PACK)
    unmapped = load_json(UPLOAD_UNMAPPED)
    companies: list[dict] = []
    for c in unmapped["full"]:
        companies.append(
            {
                "id": c["company"],
                "displayName": c["displayName"],
                "aliases": c.get("aliases") or [c["displayName"]],
                "party": "3p",
                "property": "transformers",
                "count": c.get("count"),
            }
        )
    display_for = {c["id"]: c["displayName"] for c in companies}
    alias_for = {c["id"]: c["aliases"] for c in companies}

    # Known vault makers are not new cards. Display phrases live in EXTRA_BRANDS
    # plus a readable fallback of the slug.
    items: list[dict] = []
    for raw in pack["add"]:
        company = raw["company_suggested"]
        display = display_for.get(company) or KNOWN_DISPLAY.get(company, company)
        items.append(
            normalize_listing(
                raw,
                company=company,
                display=display,
                aliases=alias_for.get(company, []),
                party_suggested=raw.get("party_suggested"),
                line_guess=raw.get("line_guess"),
            )
        )
    for c in unmapped["full"]:
        for raw in c["listings"]:
            items.append(
                normalize_listing(
                    raw,
                    company=c["company"],
                    display=c["displayName"],
                    aliases=c.get("aliases") or [],
                    party_suggested="3p",
                    line_guess=None,
                )
            )
    return {
        "source": "https://showzstore.com/c/3rd-party-amp-official-tfs_0371",
        "pulled": "2026-09-23",
        "pages": "1-52",
        "note": (
            "Normalized Show.Z listings. Mapped add-list plus 122 previously "
            "unmapped makers. Upgrades, non-TF, and the refined vault-dupe "
            "bucket are not included. Inject rechecks name+company and strong codes."
        ),
        "inputCounts": {
            "add": len(pack["add"]),
            "unmappedListings": unmapped["total_listings"],
            "newCompanies": len(companies),
            "refinedSkipVaultDupe": pack["refined_counts"]["skip_vault_dupe"],
            "upstreamSkipUpgrade": pack["also_skip_from_crawl"]["skip_upgrade_accessory"],
            "upstreamSkipNotTf": pack["also_skip_from_crawl"]["skip_not_tf"],
        },
        "companies": companies,
        "items": items,
    }


def ensure_alias_doc(doc: dict) -> dict:
    doc.setdefault("version", 1)
    doc.setdefault("policy", "gtin-canonical")
    doc.setdefault("aliasesByFigureId", {})
    doc.setdefault("aliasToFigureId", {})
    doc.setdefault("collapsed", [])
    doc.setdefault("flagged", [])
    return doc


def add_aliases(doc: dict, figure_id: str, codes: list[str]) -> int:
    by = doc["aliasesByFigureId"]
    to = doc["aliasToFigureId"]
    cur = list(by.get(figure_id) or [])
    added = 0
    for c in codes:
        c2 = clean_code(c) or ""
        if not c2 or re.search(r"[\u4e00-\u9fff]", c2) or len(c2) > 48:
            continue
        if c2 not in cur:
            cur.append(c2)
            added += 1
        to[c2] = figure_id
    if cur:
        by[figure_id] = cur
    return added


def company_card(c: dict, index: int) -> str:
    aliases = [a for a in c.get("aliases") or [] if a and a != c["displayName"]]
    blurb = f"Third-party Transformers figures released under the {c['displayName']} name."
    if aliases:
        blurb += " Also listed as " + ", ".join(aliases) + "."
    accent = PALETTE[index % len(PALETTE)]
    return (
        "  {\n"
        f'    id: "{c["id"]}",\n'
        f'    name: {json.dumps(c["displayName"], ensure_ascii=False)},\n'
        f'    short: {json.dumps(short_name(c["displayName"]), ensure_ascii=False)},\n'
        f'    blurb: {json.dumps(blurb, ensure_ascii=False)},\n'
        '    founded: "Various",\n'
        '    hq: "China",\n'
        f'    accent: "{accent}",\n'
        "  },"
    )


def register_companies(companies: list[dict]) -> dict:
    slugs = [c["id"] for c in companies]
    types = TYPES.read_text()
    companies_ts = COMPANIES_TS.read_text()
    prop = PROPERTY_TS.read_text()
    added_types: list[str] = []
    added_cards: list[str] = []
    added_tf: list[str] = []

    missing = [s for s in slugs if f'| "{s}"' not in types]
    if missing:
        if not types.rstrip().endswith('| "gong";') and '| "gong"' not in types.split("export type ItemKind")[0]:
            raise SystemExit("CompanyId union anchor | \"gong\" not found")
        block = "\n".join(f'  | "{s}"' for s in missing)
        types = types.replace('  | "gong";', '  | "gong"\n' + block + ";", 1)
        TYPES.write_text(types)
        added_types = missing

    if MARKER not in companies_ts:
        anchor = '''    accent: "#2d6a4f",
  },
];
'''
        if anchor not in companies_ts:
            raise SystemExit("COMPANIES array anchor not found")
        cards = "\n".join(company_card(c, i) for i, c in enumerate(companies))
        insert = (
            '    accent: "#2d6a4f",\n'
            "  },\n"
            f"  /** {MARKER} */\n"
            + cards
            + "\n];\n"
        )
        companies_ts = companies_ts.replace(anchor, insert, 1)
        COMPANIES_TS.write_text(companies_ts)
        added_cards = slugs

    tf_slugs = []
    for s in EXTRA_TF_3P + slugs:
        if f'"{s}"' not in prop.split("const LEGACY_UNBRANDED_COMPANIES")[0]:
            tf_slugs.append(s)
    if tf_slugs:
        anchor = '  "unbranded",\n]);'
        if anchor not in prop:
            raise SystemExit("TF_3P anchor not found")
        lines = ",\n".join(f'  "{s}"' for s in tf_slugs)
        prop = prop.replace(
            anchor,
            '  "unbranded",\n'
            f"  // {MARKER}: DJS plus Show.Z makers so they stay on Transformers 3P\n"
            + lines
            + ",\n]);",
            1,
        )
        PROPERTY_TS.write_text(prop)
        added_tf = tf_slugs

    figures = FIGURES_TS.read_text()
    banner = f"/** live-rebuild: {MARKER} 2026-09-24 */"
    if not figures.startswith("/** live-rebuild:"):
        figures = banner + "\n" + figures
    else:
        figures = re.sub(r"^/\*\* live-rebuild:.*\*/", banner, figures, count=1)
    FIGURES_TS.write_text(figures)
    return {"types": added_types, "cards": added_cards, "tf3p": added_tf}


def collect_codes(text: str, company: str = "") -> set[str]:
    return set(extract_codes(text, company))


def main() -> None:
    dry = "--dry-run" in sys.argv
    from_uploads = "--from-uploads" in sys.argv or not CATALOG.exists()
    if from_uploads:
        if not UPLOAD_PACK.exists() or not UPLOAD_UNMAPPED.exists():
            raise SystemExit("upload packs missing and catalog not built")
        catalog = build_catalog()
        if not dry:
            write_json(CATALOG, catalog)
    else:
        catalog = load_json(CATALOG)

    items: list[dict] = catalog["items"]
    companies: list[dict] = catalog["companies"]

    rows: list[dict] = load_json(ARCHIVE)
    aliases = ensure_alias_doc(load_json(ALIASES))

    ids = {r["id"] for r in rows}
    name_keys = {(r.get("company"), norm_name(r.get("name") or "")) for r in rows}
    codes_by_company: dict[str, dict[str, frozenset[str]]] = {}
    for r in rows:
        company = r.get("company") or ""
        blob = " ".join(
            [
                r.get("id") or "",
                r.get("name") or "",
                r.get("subtitle") or "",
                " ".join(t[5:] for t in (r.get("tags") or []) if isinstance(t, str) and t.startswith("code:")),
            ]
        )
        bucket = codes_by_company.setdefault(company, {})
        variants = variant_set(f"{r.get('name') or ''} {r.get('subtitle') or ''}")
        for code in collect_codes(blob, company):
            key = code_key(code)
            if len(key) < 3:
                continue
            bucket.setdefault(key, set()).add(variants)

    alias_to: dict[str, str] = aliases.get("aliasToFigureId") or {}
    company_by_id = {r["id"]: r.get("company") for r in rows}
    alias_norm_owner: dict[str, str] = {}
    for code, fid in alias_to.items():
        nc = code_key(code)
        if nc and fid:
            alias_norm_owner.setdefault(nc, fid)

    showz_taken = {norm_code(k) for k in alias_to if norm_code(k).startswith("SHOWZ")}

    added: list[str] = []
    skipped: list[dict] = []
    dropped_aliases: list[dict] = []
    alias_added = 0
    by_company: dict[str, int] = {}
    by_party: dict[str, int] = {}

    for item in items:
        company = item["company"]
        name = item["name"].strip()
        if not name:
            skipped.append({"showzId": item["showzId"], "reason": "empty-name"})
            continue
        showz_alias = f"SHOWZ{item['showzId']}"
        if norm_code(showz_alias) in showz_taken:
            skipped.append({"showzId": item["showzId"], "reason": "showz-alias-exists", "name": name})
            continue
        nkey = (company, norm_name(name))
        if nkey in name_keys:
            skipped.append({"showzId": item["showzId"], "company": company, "reason": "name-exists", "name": name})
            continue

        codes = [c for c in item.get("codes") or []]
        strong = [c for c in codes if len(code_key(c)) >= 3]
        variants = frozenset(item.get("variant") or [])
        # Lead code only. A 2-pack title also names members that may already
        # exist; those stay aliases, not a reason to drop the pack.
        code_dupe = None
        if strong:
            lead = code_key(strong[0])
            seen_variants = codes_by_company.get(company, {}).get(lead)
            if seen_variants is not None and variants in seen_variants:
                code_dupe = lead
        if code_dupe:
            skipped.append(
                {
                    "showzId": item["showzId"],
                    "company": company,
                    "reason": "code-exists",
                    "code": code_dupe,
                    "name": name,
                }
            )
            continue

        rid = figure_id(company, strong, name)
        if rid in ids:
            rid = f"{rid}-{item['showzId']}"[:78].strip("-")
        if rid in ids:
            skipped.append({"showzId": item["showzId"], "reason": "id-exists", "id": rid, "name": name})
            continue

        keep_aliases: list[str] = []
        for raw_code in [showz_alias, *strong]:
            c2 = clean_code(raw_code) or ""
            nc = code_key(c2)
            if not c2 or not nc:
                continue
            owner = alias_to.get(c2) or alias_norm_owner.get(nc)
            if owner and owner != rid:
                dropped_aliases.append(
                    {"id": rid, "code": c2, "reason": "alias-collision", "owner": owner}
                )
                continue
            if c2 not in keep_aliases:
                keep_aliases.append(c2)

        if not any(a.startswith("SHOWZ") for a in keep_aliases):
            skipped.append({"showzId": item["showzId"], "reason": "showz-alias-collision", "name": name})
            continue

        party = item["party"]
        tags = [
            company,
            "transformers",
            party,
            "curated",
            SOURCE,
            "src:showzstore",
            f"showz:{item['showzId']}",
        ]
        if party == "3p":
            tags.insert(3, "ko")
        tags.extend(f"code:{a}" for a in keep_aliases if not a.startswith("SHOWZ"))

        row: dict[str, Any] = {
            "id": rid,
            "name": name,
            "subtitle": item["subtitle"],
            "line": item["line"],
            "company": company,
            "kind": item["kind"],
            "releaseDate": item["releaseDate"],
            "msrp": item["msrp"],
            "scale": item["scale"],
            "demand": 1.0,
            "tags": tags,
            "source": SOURCE,
            "property": "transformers",
            "party": party,
        }
        if item.get("imageUrl"):
            row["imageUrl"] = item["imageUrl"]

        rows.append(row)
        ids.add(rid)
        name_keys.add(nkey)
        showz_taken.add(norm_code(showz_alias))
        company_by_id[rid] = company
        bucket = codes_by_company.setdefault(company, {})
        for c in strong:
            bucket.setdefault(code_key(c), set()).add(variants)
        alias_added += add_aliases(aliases, rid, [*keep_aliases, f"id:{rid}"])
        for a in keep_aliases:
            alias_to[a] = rid
            alias_norm_owner[code_key(a)] = rid
        added.append(rid)
        by_company[company] = by_company.get(company, 0) + 1
        by_party[party] = by_party.get(party, 0) + 1

    from collections import Counter

    skip_counts = Counter(s["reason"] for s in skipped)
    summary = {
        "source": SOURCE,
        "retailer": catalog.get("source"),
        "pulled": catalog.get("pulled"),
        "pages": catalog.get("pages"),
        "dryRun": dry,
        "input": catalog.get("inputCounts"),
        "catalogItems": len(items),
        "newCompanies": len(companies),
        "added": len(added),
        "skipped": len(skipped),
        "skipCounts": dict(skip_counts),
        "byParty": by_party,
        "byCompany": dict(sorted(by_company.items(), key=lambda kv: (-kv[1], kv[0]))),
        "aliasRowsTouched": alias_added,
        "droppedAliases": len(dropped_aliases),
        "oneshotBefore": len(rows) - len(added),
        "oneshotAfter": len(rows),
        "sku": "unset — no GTIN on these Show.Z listings; SHOWZ id and listing codes are aliases",
        "live": "held — do not Build Publish Live",
    }
    print(json.dumps(summary, indent=2))
    print("--- skip samples ---")
    shown: dict[str, int] = {}
    for s in skipped:
        n = shown.get(s["reason"], 0)
        if n >= 6:
            continue
        shown[s["reason"]] = n + 1
        print(json.dumps(s, ensure_ascii=False))
    print("--- name samples ---")
    sample_ids = set(added[:: max(1, len(added) // 18)])
    if not dry:
        pass
    printed = 0
    for row in rows[-len(added) :] if added else []:
        if row["id"] not in sample_ids and printed > 0:
            continue
        if printed >= 18:
            break
        print(f"{row['company']:16} {row['party']} {row['line'][:28]:28} {row['name'][:70]}")
        printed += 1

    if dry:
        return

    reg = register_companies(companies)
    aliases["updatedAt"] = now_iso()
    write_json(ARCHIVE, rows)
    write_json(ALIASES, aliases)
    stats = {
        **summary,
        "updatedAt": aliases["updatedAt"],
        "ids": added,
        "skippedRows": skipped,
        "droppedAliasSamples": dropped_aliases[:80],
        "companyRegistration": {k: len(v) for k, v in reg.items()},
        "companiesCreated": [c["id"] for c in companies],
    }
    write_json(STATS, stats)


if __name__ == "__main__":
    main()
