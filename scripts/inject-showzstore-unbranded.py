#!/usr/bin/env python3
"""Densify Showzstore No Brand/KO Transformers listings onto company `unbranded`.

Source pack: scripts/figure_oneshot/showzstore_no_brand_ko_pack.json
(Shelby HTML dump of https://showzstore.com/c/no-brand-ko_0397, pages 1–5, 2026-09-23).

Uses only pack title, product URL, image URL, and price. Listing codes are
aliases. `sku` stays unset (no GTIN on these rows). Does NOT Build Publish Live.
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
STATS = ROOT / "src/data/figure-archive/showzstore-unbranded-inject-stats.json"
PACK = SCRIPTS / "figure_oneshot/showzstore_no_brand_ko_pack.json"
CATALOG = SCRIPTS / "figure_oneshot/showzstore_unbranded_catalog.json"
SOURCE = "inject-showzstore-unbranded"
OFFICIAL_COMPANIES = {"hasbro", "takaratomy", "kenner"}
# Extra words that do not make a shorter combiner listing a different toy.
GROUP_FILLER = {
    "constructicon",
    "stunticon",
    "protectobot",
    "aerialbot",
    "technobot",
    "dinobot",
    "combiner",
    "figure",
    "figures",
    "g1",
}

# Mirrors src/lib/figure-property.ts KNOWN_MAKER, plus makers called out for this pass.
NAMED_MAKER = re.compile(
    r"magic\s*square|wei\s*jiang|weijiang|\bwj[-\s]|black\s*mamba|\bbmb\b|"
    r"toy\s*house\s*factory|\bthf\b|\bbpf\b|new\s*age|newage|fans\s*toys|fanstoys|"
    r"iron\s*factory|unique\s*toys|toyworld|toy\s*world|perfect\s*effect|"
    r"robot\s*paradise|apc\s*toys|moon\s*studio|jx\s*jiang|metalbeast|\bdx9\b|"
    r"mastermind|make\s*toys|maketoys|planet\s*x|x-?transbots|\btfc\b|g-?creation|"
    r"generation\s*toy|zeta\s*toys|mech\s*fans|toy\s*wolf|toywolf|evolution\s*toy|"
    r"fans\s*hobby|fansproject|fans\s*project|transart|bingo\s*toys|cang\s*toys|"
    r"dr\.?\s*wu|herocross|hybrid\s*metal|heatboys|heat\s*boys|\blewin\b|\bdjs\b|"
    r"model\s*wizard|\baoyi\b|zeus\s*toys|infinite\s*transformation|blokees|"
    r"three\s*zero|threezero|yolopark|yolo\s*park|robosen|flame\s*toys|"
    r"super\s*7|super7|kuro\s*kara|naughtica|ocular\s*max|"
    r"vincoroor|rose\s*(?:&|and)?\s*toys|\bbaiwei\b|yuexing|metal\s*club|\bqqt\b|"
    r"\bjinbao\b|\b5u\b|deformation\s*space|dna\s*design|shockwave\s*lab|"
    r"\bbadcube\b|\bosko\b|hasbro|takara(?:\s*tomy)?",
    re.I,
)

NON_TF = re.compile(
    r"patlabor|gaogaigar|gao\s*gai\s*gar|king of (?:the )?braves|\bbatman\b|"
    r"\bgundam\b|\bultraman\b|\bnaruto\b",
    re.I,
)

# Hyphenated house/mold code, compact (POP01B, MP10X, TW1024, DH05),
# and single-letter codes (P60).
CODE_RE = re.compile(
    r"\b([A-Z]{1,5}\d{0,2}-\d{2,4}[A-Z]{0,4}|[A-Z]{2,6}\d{2,4}[A-Z]{0,4}|[A-Z]\d{2,4}[A-Z]{0,2})\b",
    re.I,
)

# Line nicknames the pack extractor treated as product codes. Not an identity.
GENERIC_CODE = {
    "SS86",
    "SS-86",
    "G1",
    "G2",
    "KO",
    "MP",
    "SS",
    "DLX",
    "BW",
    "OP",
    "MPM",
    "WFC",
}

STOP = {
    "the",
    "a",
    "an",
    "of",
    "and",
    "or",
    "for",
    "to",
    "from",
    "party",
    "masterpiece",
    "transformers",
    "transformer",
    "studio",
    "series",
    "movie",
    "class",
    "voyager",
    "leader",
    "commander",
    "figure",
    "figures",
    "version",
    "ver",
    "pack",
    "set",
    "no",
    "brand",
    "ko",
    "copy",
    "with",
    "w",
}

FILLER_RE = re.compile(
    r"\b(?:4th\s+party|no\s+brand|masterpiece|transformers|transformer|"
    r"studio\s+series|movie\s+series|voyager\s+class|leader\s+class)\b",
    re.I,
)
CONDITION_RE = re.compile(
    r"\b(?:loose(?:\s+version|\s+pack)?|no\s+box|white\s+box|factory\s+leaking|"
    r"parts\s+not\s+working|sample)\b|"
    r"\b(?:without|w/o)\s+box\b|\bwith\s+box\b|\bw/\s*box\b",
    re.I,
)


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


def unescape(s: str) -> str:
    return html.unescape(html.unescape(s or "")).replace("\xa0", " ")


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def code_slug(code: str) -> str:
    c = code.strip().upper()
    if "-" in c:
        left, right = c.split("-", 1)
        left_c = re.sub(r"[^A-Z0-9]", "", left)
        right_c = re.sub(r"[^A-Z0-9]", "", right).lower()
        m = re.match(r"^([A-Z]+?)(\d*)$", left_c)
        if m:
            prefix, num = m.groups()
            head = prefix.lower() + (f"-{num}" if num else "")
            return f"{head}-{right_c}" if right_c else head
    compact = re.sub(r"[^A-Z0-9]", "", c)
    m = re.match(r"^([A-Z]+?)(\d+)([A-Z]*)$", compact)
    if m:
        prefix, num, suf = m.groups()
        return f"{prefix.lower()}-{num}{suf.lower()}"
    return slugify(c)


def split_flags(raw_name: str) -> tuple[str, list[str]]:
    s = unescape(raw_name).strip()
    flags = re.findall(r"\[([^\]]+)]", s)
    # Bracket tags are listing status, not the figure name.
    body = re.sub(r"\[[^\]]+]", " ", s)
    body = re.sub(r"\s+", " ", body).strip()
    body = re.sub(r"^(?:4th\s+Party|No\s+Brand)\s+", "", body, flags=re.I).strip()
    body = re.sub(r"^(?:Transformers\s*:\s*|Transformers\s+)", "", body, flags=re.I).strip()
    body = re.sub(r"\s+", " ", body).strip(" -")
    return body, [re.sub(r"\s+", " ", f).strip() for f in flags if f.strip()]


def extract_codes(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for m in CODE_RE.finditer(text.upper()):
        code = m.group(1).upper()
        n = norm_code(code)
        if not n or n in {norm_code(g) for g in GENERIC_CODE} or n in seen:
            continue
        if not re.search(r"[A-Z]", n) or not re.search(r"\d", n):
            continue
        seen.add(n)
        found.append(code)
    return found


def alias_forms(code: str) -> list[str]:
    forms: list[str] = []
    raw = code.strip().upper()
    compact = norm_code(raw)
    hyphen = code_slug(raw).upper()
    for c in (raw, hyphen, compact):
        if c and c not in forms and norm_code(c) not in {norm_code(g) for g in GENERIC_CODE}:
            forms.append(c)
    return forms


def collapse_core(display: str) -> str:
    s = display.lower().replace("&", " and ")
    s = s.replace("w/o", " without ").replace("w/", " with ")
    s = FILLER_RE.sub(" ", s)
    s = CONDITION_RE.sub(" ", s)
    s = CODE_RE.sub(" ", s.upper()).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    toks = [t for t in s.split() if t and t not in STOP]
    return " ".join(toks)


def line_of(text: str) -> str:
    t = text.lower()
    if re.search(r"predaking", t):
        return "Predaking KO"
    if re.search(
        r"menasor|defensor|superion|bruticus|computron|devastator|"
        r"\bcombiner\b|stunticon|protectobot|constructicon|technobot|aerialbot",
        t,
    ):
        return "Combiner KO"
    if "diaclone" in t or re.search(r"\bpop-?0", t):
        return "Diaclone KO"
    if re.search(r"beast wars|\bbw-?\d|\boptimal optimus\b|\bcheetor\b|\btigatron\b|\brhinox\b", t):
        return "BW KO"
    if re.search(r"ss-?86|\bss86\b", t):
        return "SS86 KO"
    if re.search(r"studio series|\bss-?\d", t):
        return "SS KO"
    if re.search(r"\bmpm-?\d|\bmpm\b|movie series|masterpiece movie", t):
        return "MPM KO"
    if re.search(r"masterpiece|\bmp-?\d|\bmpg-?\d", t):
        return "MP KO"
    if re.search(r"\bdlx\b|the last knight|revenge of the fallen|dark of the moon|age of extinction", t):
        return "DLX KO"
    if re.search(r"\bg1\b", t):
        return "G1 KO"
    if "legend" in t:
        return "Legends KO"
    return "KO"


def scale_of(text: str, line: str) -> str:
    t = text.lower()
    if "legend" in t:
        return "Legend"
    if "oversized" in t:
        return "Oversized"
    if re.search(r"\bdlx\b|\bdeluxe\b", t):
        return "DLX"
    if "voyager" in t:
        return "Voyager"
    if re.search(r"\b1/24\b", t):
        return "1/24"
    if "commander" in t and "mp" not in line.lower():
        return "Commander"
    if line == "DLX KO":
        return "DLX"
    if line.startswith("MP"):
        return "MP"
    if line.startswith("SS"):
        return "SS"
    if line.startswith("G1") or line.startswith("Combiner") or line.startswith("Predaking"):
        return "G1"
    if line.startswith("Legend"):
        return "Legend"
    if line.startswith("Diaclone"):
        return "MP"
    if line.startswith("BW"):
        return "BW"
    return "KO"


def subtitle_for(flags: list[str], line: str) -> str:
    if flags:
        return " · ".join(flags)
    return {
        "MP KO": "No-brand Masterpiece copy",
        "MPM KO": "No-brand movie Masterpiece copy",
        "SS KO": "No-brand Studio Series copy",
        "SS86 KO": "No-brand Studio Series 86 copy",
        "G1 KO": "No-brand G1 copy",
        "DLX KO": "No-brand deluxe movie copy",
        "Combiner KO": "No-brand combiner",
        "Predaking KO": "No-brand Predaking limb",
        "Diaclone KO": "No-brand Diaclone copy",
        "BW KO": "No-brand Beast Wars copy",
        "Legends KO": "No-brand legends-scale copy",
        "KO": "No-brand Transformers copy",
    }.get(line, "No-brand Transformers copy")


def release_from_image(url: str) -> str | None:
    # Showzstore CDN folders are YYMM, either .../products/ or .../file/.
    m = re.search(r"/(\d{2})(\d{2})/(?:products|file)/", url)
    if not m:
        return None
    year = 2000 + int(m.group(1))
    month = int(m.group(2))
    if 2015 <= year <= 2026 and 1 <= month <= 12:
        return f"{year:04d}-{month:02d}-01"
    return None


def usable_image(url: str | None) -> str | None:
    if not url or not isinstance(url, str):
        return None
    u = url.strip()
    if not u.startswith("https://"):
        return None
    if not re.search(r"\.(?:jpg|jpeg|png|webp)(?:\.|$)", u, re.I):
        return None
    return u


def rank(item: dict) -> tuple:
    blob = " ".join(item["flags"]).lower() + " " + item["display"].lower()
    return (
        0 if "parts not working" in blob else 1,
        0 if re.search(r"\bsample\b", blob) else 1,
        0 if re.search(r"no box|\bloose\b", blob) else 1,
        0 if "buyer only" in blob else 1,
        int(item["showz_id"]),
    )


DISC_DROP = STOP | {
    "without",
    "extra",
    "led",
    "headsculpt",
    "improved",
    "painting",
    "oversized",
    "masterpiece",
    "version",
    "figure",
    "trailer",
    "with",
}


def clip_slug(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    cut = s[:limit]
    if "-" in cut:
        cut = cut.rsplit("-", 1)[0]
    return cut.strip("-") or s[:limit]


def disc_slug(core: str) -> str:
    toks = [t for t in core.split() if t not in DISC_DROP]
    if not toks:
        toks = [t for t in core.split() if t][:3]
    if len(toks) > 4:
        toks = toks[:2] + toks[-2:]
    return clip_slug(slugify("-".join(toks)) or "alt", 42)


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
        if not c2:
            continue
        if c2 not in cur:
            cur.append(c2)
            added += 1
        to[c2] = figure_id
    if cur:
        by[figure_id] = cur
    return added


def skip_reason(display: str, raw: str) -> str | None:
    blob = f"{display} {raw}"
    if NAMED_MAKER.search(blob):
        return "named-maker"
    if NON_TF.search(blob):
        return "non-tf"
    if re.search(r"\btrailer for\b", blob, re.I):
        return "trailer-only"
    if re.search(r"\baccessory pack\b|\bupgrade kits?\b", blob, re.I):
        return "accessory"
    if re.search(r"\bstatue\b", blob, re.I):
        return "statue"
    return None


def vault_keyword_dupe(display: str) -> str | None:
    t = display.lower()
    if re.search(r"last knight", t) and re.search(r"\bdlx\b|deluxe", t) and "optimus" in t:
        return "unbranded-tlk-dlx-op"
    if "menasor" in t and re.search(r"combiner|set of|stunticon|\bset\b", t):
        return "unbranded-menasor-set"
    if re.search(r"\bdefensor\b", t) and "protectobot" not in t and not re.search(r"\bhot\b|\bblades\b|\bfirst aid\b|\bgroove\b|\bstreetwise\b", t):
        # The existing row is the five-figure Protectobot set, titled "G1 Defensor".
        if re.search(r"\bdefensor\b", t) and not re.search(r"upgrade|kit", t):
            return "unbranded-defensor-set"
    return None


def prepare(pack: dict, rows: list[dict], alias_norm_owner: dict[str, str], id_company: dict[str, str]) -> tuple[list[dict], list[dict]]:
    skipped: list[dict] = []
    pending: list[dict] = []
    unbranded_names = {
        (r.get("name") or "").strip().lower()
        for r in rows
        if r.get("company") == "unbranded"
    }
    unbranded_codes = {
        n for n, owner in alias_norm_owner.items() if id_company.get(owner) == "unbranded" and n
    }

    for raw in pack["include"]:
        showz_id = str(raw.get("id") or "").strip()
        raw_name = str(raw.get("name") or "")
        already = alias_norm_owner.get(norm_code(f"showzstore:{showz_id}"))
        if already:
            skipped.append({"showzId": showz_id, "reason": "already-injected", "title": raw_name, "owner": already})
            continue
        display, flags = split_flags(raw_name)
        image = usable_image(raw.get("image"))
        url = str(raw.get("url") or "").strip()
        if not display:
            skipped.append({"showzId": showz_id, "reason": "empty-name", "title": raw_name})
            continue
        if not image:
            skipped.append({"showzId": showz_id, "reason": "no-image", "title": display})
            continue
        if not url.startswith("https://"):
            skipped.append({"showzId": showz_id, "reason": "no-url", "title": display})
            continue
        reason = skip_reason(display, raw_name)
        if reason:
            skipped.append({"showzId": showz_id, "reason": reason, "title": display})
            continue
        release = release_from_image(image)
        if not release:
            skipped.append({"showzId": showz_id, "reason": "no-release-from-image", "title": display, "image": image})
            continue
        codes = extract_codes(display)
        for extra in raw.get("codes") or []:
            n = norm_code(str(extra))
            if not n or n in {norm_code(g) for g in GENERIC_CODE}:
                continue
            if n not in {norm_code(c) for c in codes} and re.search(r"[A-Z]", n) and re.search(r"\d", n):
                codes.append(str(extra).upper())
        primary = codes[0] if codes else ""
        primary_n = norm_code(primary)
        maker_hit = None
        for code in codes:
            n = norm_code(code)
            owner = alias_norm_owner.get(n) if n else None
            company = id_company.get(owner or "")
            if owner and company and company not in OFFICIAL_COMPANIES and company != "unbranded":
                maker_hit = {"owner": owner, "code": code, "company": company}
                break
        if maker_hit:
            skipped.append({
                "showzId": showz_id,
                "reason": "named-maker-code",
                "title": display,
                **maker_hit,
            })
            continue
        if primary_n and primary_n in unbranded_codes:
            owner = alias_norm_owner.get(primary_n)
            skipped.append({
                "showzId": showz_id,
                "reason": "vault-code-dupe",
                "title": display,
                "code": primary,
                "owner": owner,
            })
            continue
        if display.lower() in unbranded_names:
            skipped.append({"showzId": showz_id, "reason": "vault-name-dupe", "title": display})
            continue
        vault_id = vault_keyword_dupe(display)
        if vault_id:
            skipped.append({"showzId": showz_id, "reason": "vault-listing-dupe", "title": display, "owner": vault_id})
            continue
        price = raw.get("price_usd")
        if price is None:
            msrp = 0.0
        else:
            msrp = float(price)
        text = f"{display} {' '.join(flags)}"
        line = line_of(text)
        item = {
            "showz_id": showz_id,
            "showz_ids": [showz_id],
            "display": display,
            "flags": flags,
            "image": image,
            "url": url,
            "price_usd": price,
            "msrp": msrp,
            "release": release,
            "codes": codes,
            "primary": primary,
            "primary_n": primary_n,
            "core": collapse_core(display),
            "line": line,
            "scale": scale_of(text, line),
            "page": raw.get("page"),
        }
        pending.append(item)

    collapsed = merge_duplicates(pending, skipped)
    return collapsed, skipped


def codes_overlap(a: dict, b: dict) -> bool:
    ca = {norm_code(c) for c in a["codes"] if norm_code(c)}
    cb = {norm_code(c) for c in b["codes"] if norm_code(c)}
    if not ca and not cb:
        return True
    if not ca or not cb:
        return False
    return bool(ca & cb)


def same_product(a: dict, b: dict) -> bool:
    """Collapse the same listing twice. Distinct house codes stay apart."""
    ta = set(a["core"].split())
    tb = set(b["core"].split())
    if len(ta) < 2 or len(tb) < 2:
        return bool(a["core"]) and a["core"] == b["core"] and codes_overlap(a, b)
    if ta == tb:
        return codes_overlap(a, b)
    small, big = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if not small < big:
        return False
    extra = {t for t in (big - small) if not t.isdigit()}
    shared = {t for t in (small & big) if t not in GROUP_FILLER and len(t) > 3}
    # Subset merge is only for uncoded combiner restatements ("Devastator" vs
    # "Constructicon Devastator 6 Figures Set"), never two different SKUs.
    if a["primary_n"] or b["primary_n"]:
        return False
    return bool(shared) and extra <= GROUP_FILLER


def merge_duplicates(pending: list[dict], skipped: list[dict]) -> list[dict]:
    parent = list(range(len(pending)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i in range(len(pending)):
        for j in range(i + 1, len(pending)):
            if same_product(pending[i], pending[j]):
                union(i, j)

    buckets: dict[int, list[dict]] = {}
    for i, item in enumerate(pending):
        buckets.setdefault(find(i), []).append(item)

    collapsed: list[dict] = []
    for items in buckets.values():
        if len(items) == 1:
            collapsed.append(items[0])
            continue
        items.sort(key=rank, reverse=True)
        keep = items[0]
        for other in items[1:]:
            for sid in other["showz_ids"]:
                if sid not in keep["showz_ids"]:
                    keep["showz_ids"].append(sid)
            for c in other["codes"]:
                if norm_code(c) not in {norm_code(x) for x in keep["codes"]}:
                    keep["codes"].append(c)
            # Prefer a house code over a bare official mold number when both exist.
            if keep["primary_n"].startswith(("MP", "SS")) and other["primary"] and not other["primary_n"].startswith(("MP", "SS")):
                keep["primary"] = other["primary"]
                keep["primary_n"] = other["primary_n"]
            skipped.append({
                "showzId": other["showz_id"],
                "reason": "collapsed-duplicate",
                "title": other["display"],
                "keptShowzId": keep["showz_id"],
                "keptTitle": keep["display"],
            })
        collapsed.append(keep)
    return collapsed


def assign_ids(items: list[dict], existing_ids: set[str]) -> None:
    groups: dict[str, list[dict]] = {}
    for item in items:
        if item["primary"]:
            base = "unbranded-" + code_slug(item["primary"])
        else:
            base = "unbranded-" + (slugify(item["core"])[:48] or f"showz-{item['showz_id']}")
        item["base_id"] = base
        groups.setdefault(base, []).append(item)
    used = set(existing_ids)
    for base, group in groups.items():
        group.sort(key=lambda it: it["showz_id"])
        if len(group) == 1 and base not in used:
            group[0]["id"] = base
            used.add(base)
            continue
        for item in group:
            disc = disc_slug(item["core"])
            fid = clip_slug(re.sub(r"-{2,}", "-", f"{base}-{disc}".strip("-")), 64)
            n = 2
            candidate = fid
            while candidate in used:
                candidate = f"{fid}-{n}"
                n += 1
            item["id"] = candidate
            used.add(candidate)


def main() -> None:
    apply = "--apply" in sys.argv
    rows: list[dict] = load_json(ARCHIVE)
    aliases = ensure_alias_doc(load_json(ALIASES))
    pack = load_json(PACK)

    id_company = {r["id"]: r.get("company") for r in rows}
    existing_ids = set(id_company)
    alias_to: dict[str, str] = dict(aliases.get("aliasToFigureId") or {})
    alias_norm_owner: dict[str, str] = {}
    for k, v in alias_to.items():
        n = norm_code(k)
        if n and n not in alias_norm_owner:
            alias_norm_owner[n] = v
    for r in rows:
        for t in r.get("tags") or []:
            if isinstance(t, str) and t.startswith("code:"):
                n = norm_code(t[5:])
                if n and n not in alias_norm_owner:
                    alias_norm_owner[n] = r["id"]

    items, skipped = prepare(pack, rows, alias_norm_owner, id_company)
    assign_ids(items, existing_ids)

    added_rows: list[dict] = []
    dropped_aliases: list[dict] = []
    catalog_items: list[dict] = []
    alias_added = 0

    for item in items:
        rid = item["id"]
        if rid in existing_ids:
            skipped.append({"showzId": item["showz_id"], "reason": "id-exists", "id": rid, "title": item["display"]})
            continue
        keep_aliases: list[str] = []
        seen_alias_n: set[str] = set()
        candidates: list[str] = []
        for code in item["codes"]:
            candidates.extend(alias_forms(code))
        for sid in item["showz_ids"]:
            candidates.append(f"showzstore:{sid}")
        candidates.append(f"id:{rid}")
        for c2 in candidates:
            cleaned = clean_code(c2) or ""
            n = norm_code(cleaned)
            if not cleaned:
                continue
            if n and n in seen_alias_n:
                continue
            owner = alias_to.get(cleaned) or (alias_norm_owner.get(n) if n else None)
            official_id = ""
            if n and not cleaned.startswith("showzstore:") and not cleaned.startswith("id:"):
                slug = code_slug(cleaned)
                for cand in (f"tfmp-{n.lower()}", f"tfmp-{slug}" if slug else ""):
                    if cand and cand in existing_ids:
                        official_id = cand
                        break
            if official_id:
                dropped_aliases.append({
                    "id": rid,
                    "code": cleaned,
                    "reason": "official-mold-code",
                    "owner": official_id,
                    "ownerCompany": id_company.get(official_id),
                })
                continue
            if owner and owner != rid:
                dropped_aliases.append({
                    "id": rid,
                    "code": cleaned,
                    "reason": "alias-collision",
                    "owner": owner,
                    "ownerCompany": id_company.get(owner),
                })
                continue
            if n:
                seen_alias_n.add(n)
            keep_aliases.append(cleaned)

        row = {
            "id": rid,
            "name": item["display"],
            "subtitle": subtitle_for(item["flags"], item["line"]),
            "line": item["line"],
            "company": "unbranded",
            "kind": "figure",
            "releaseDate": item["release"],
            "msrp": item["msrp"],
            "scale": item["scale"],
            "demand": 1.25,
            "tags": [
                "unbranded",
                "transformers",
                "3p",
                "ko",
                "curated",
                SOURCE,
                "src:showzstore",
                *[f"code:{a}" for a in keep_aliases if not a.startswith("id:")],
            ],
            "source": SOURCE,
            "property": "transformers",
            "party": "3p",
            "imageUrl": item["image"],
        }
        added_rows.append(row)
        existing_ids.add(rid)
        id_company[rid] = "unbranded"
        for a in keep_aliases:
            n = norm_code(a)
            if n:
                alias_norm_owner[n] = rid
            alias_to[a] = rid
        if apply:
            alias_added += add_aliases(aliases, rid, keep_aliases)
        catalog_items.append({
            "id": rid,
            "name": item["display"],
            "line": item["line"],
            "scale": item["scale"],
            "releaseDate": item["release"],
            "msrp": item["msrp"],
            "showzstoreProductIds": item["showz_ids"],
            "productUrl": item["url"],
            "imageUrl": item["image"],
            "aliases": [a for a in keep_aliases if not a.startswith("id:")],
            "listingTitle": item["display"],
            "flags": item["flags"],
            "page": item["page"],
            "priceUsd": item["price_usd"],
        })

    by_reason: dict[str, int] = {}
    for s in skipped:
        by_reason[s["reason"]] = by_reason.get(s["reason"], 0) + 1

    summary = {
        "source": SOURCE,
        "retailer": pack.get("source"),
        "pulled": pack.get("pulled"),
        "pages": pack.get("pages"),
        "packInclude": pack.get("include_count"),
        "added": len(added_rows),
        "skipped": len(skipped),
        "skipByReason": by_reason,
        "droppedAliases": len(dropped_aliases),
        "aliasRowsTouched": alias_added,
        "gtin": "none — pack has no barcodes; listing codes and showzstore product ids are aliases only",
        "price": "pack price_usd was null on every include row; msrp stored as 0 rather than invented",
        "sampleIds": [r["id"] for r in added_rows[:12]],
    }
    print(json.dumps(summary, indent=2))
    preview = Path("/tmp/showzstore_unbranded_preview.json")
    write_json(preview, {"summary": summary, "added": catalog_items, "skipped": skipped, "droppedAliases": dropped_aliases})

    if not apply:
        print("dry-run (pass --apply to write oneshot + aliases)")
        return

    rows.extend(added_rows)
    aliases["updatedAt"] = now_iso()
    write_json(ARCHIVE, rows)
    write_json(ALIASES, aliases)
    write_json(CATALOG, {
        "source": pack.get("source"),
        "pulled": pack.get("pulled"),
        "pages": pack.get("pages"),
        "note": "Showzstore no-brand/KO include rows densified onto company unbranded. Prices were null in the pack.",
        "items": catalog_items,
    })
    write_json(STATS, {
        **summary,
        "updatedAt": aliases["updatedAt"],
        "ids": [r["id"] for r in added_rows],
        "skipped": skipped,
        "droppedAliases": dropped_aliases,
        "live": "held — do not Build/Publish Live",
    })
    print(f"wrote {len(added_rows)} rows")


if __name__ == "__main__":
    main()
