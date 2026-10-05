#!/usr/bin/env python3
"""Audit figure imageUrl (oneshot + figure-image-urls overlay) for product mismatches.

Same class of bug as Elektra D&W showing Skrull Elektra & Ronin pack art:
wrong CDN photo attached via fuzzy/Mephitsu bake or a mismatched GTIN join.

For every figure with an image (oneshot and/or overlay):
  (a) If primary GTIN exists in product-sku-index and product title hard-disagrees
      with figure name/subtitle/line → CLEAR image from oneshot + overlay.
  (b) If the image URL appears in product-sku-index / product-image-index for a
      product whose title hard-disagrees (and no co-indexed product high-matches)
      → CLEAR.
  (c) Conservative: only auto-clear high-confidence mismatches; soft flags reported.
  (d) Character-name check strips faction/universe/group prefixes and tolerates
      spacing/minor spelling differences (never key only on a faction first word).
  (e) Never auto-clear when figure GTIN/barcode (or SKU alias) matches the product
      the photo came from — flag soft at most.
  (f) Apply safety cap: if a run would clear more than APPLY_CLEAR_CAP photos,
      write the report only and skip clears.

Optional --refill: SKU-first re-attach image only when GTIN product title
high-confidence matches the figure (never multipack onto single). Never invents.

Prefer empty/placeholder over wrong photo. Comics/UPC untouched. Mephitsu crawl
workers left alone (oneshot / image-map edits only).

Usage:
  python3 scripts/audit-figure-image-mismatches.py              # dry-run report
  python3 scripts/audit-figure-image-mismatches.py --apply
  python3 scripts/audit-figure-image-mismatches.py --apply --refill
"""
from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/workspace/collection-app")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import data_shards  # noqa: E402

from figure_identity import is_gtin, clean_code, tokens, norm_text  # noqa: E402

ARCHIVE_JSON = ROOT / "src/data/figure-archive/oneshot.json"
SKU_INDEX_JSON = ROOT / "src/data/figure-archive/product-sku-index.json"
IMG_INDEX_JSON = ROOT / "src/data/figure-archive/product-image-index.json"
URLS_JSON = ROOT / "src/data/figure-image-urls.json"
REPORT_JSON = ROOT / "src/data/figure-archive/image-mismatch-audit.json"
SKU_AUDIT_JSON = ROOT / "src/data/figure-archive/sku-mismatch-audit.json"
ALIASES_JSON = ROOT / "src/data/figure-sku-aliases.json"

APPLY_CLEAR_CAP = 15  # refuse clears when a single --apply would exceed this
FUZZY_TOKEN_RATIO = 0.84

_spec = importlib.util.spec_from_file_location("bake_figure_images", SCRIPTS / "bake-figure-images.py")
_bfi = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_bfi)

score_pair = _bfi.score_pair
enrich_index = _bfi.enrich_index

PACK_RE = re.compile(
    r"\b(?:2[\s\-]?pack|3[\s\-]?pack|4[\s\-]?pack|two[\s\-]?pack|three[\s\-]?pack|"
    r"2\s*pk|3\s*pk|4\s*pk|multipack|multi[\s\-]?pack|set\s+of\s+\d+|twin\s*packs?)\b",
    re.I,
)
# Dual-character figure titles (He-Man and Battle Cat, Slice & Dice, Long Haul & Hook)
DUAL_NAME_RE = re.compile(
    r"\b\w+(?:\s+\w+){0,3}\s+(?:and|&|vs\.?|versus)\s+\w+",
    re.I,
)

WEAK = {
    "series", "legends", "marvel", "action", "figure", "figures", "hasbro",
    "wave", "exclusive", "edition", "deluxe", "scale", "inch", "black",
    "retro", "vintage", "comic", "comics", "movie", "tv", "the", "and",
    "dc", "multiverse", "classified", "origins", "masterverse", "collection",
    "pack", "set", "anniversary", "studio", "studios", "infinite",
}


# Leading faction / universe / group words — retailer titles often omit these
# ("Autobot Skids" vs "Legacy Deluxe Wave 1 - Skids").
FACTION_WORDS = {
    "autobot", "decepticon", "maximal", "predacon", "terrorcon",
    "dinobot", "insecticon", "constructicon", "stunticon", "combaticon",
    "aerialbot", "protectobot", "seacon", "technobot", "battlecon",
}

# Continuity / group phrases stripped from the start of a figure name (repeatable).
_NAME_PREFIX_RES: list[re.Pattern[str]] = [
    re.compile(r"^the\s+thirteen\s+", re.I),
    re.compile(r"^robots\s+in\s+disguise(?:\s+\d+)?(?:\s+universe)?\s+", re.I),
    re.compile(r"^rescue\s+bots?(?:\s+universe)?\s+", re.I),
    re.compile(
        r"^beast\s+wars(?:\s+(?:ii|2|neo))?(?:\s+universe)?\s+",
        re.I,
    ),
    re.compile(r"^g1\s+triple\s+changer\s+", re.I),
    re.compile(r"^evolution\s+", re.I),  # POTP "Evolution Optimus Prime"
    re.compile(r"^fugitive\s+", re.I),
    # "<continuity> Universe …" (Armada/G1/Prime/Infernac/Comic/…)
    re.compile(
        r"^(?:armada|g1|g2|prime|predacon|cybertron|diaclone|animated|"
        r"cyberverse|energon|infernac|comic|victory|beast|rescue|"
        r"transformers)\s+universe\s+",
        re.I,
    ),
    # Generic single-token "X Universe " (keeps "Masters of the Universe" intact —
    # that phrase has "of the" between masters and universe).
    re.compile(r"^[a-z0-9]+\s+universe\s+", re.I),
    # Bare faction word at start
    re.compile(
        r"^(?:" + "|".join(sorted(FACTION_WORDS)) + r")\s+",
        re.I,
    ),
]


def strip_faction_universe_prefix(name: str) -> str:
    """Remove leading faction/universe/group prefixes; repeat until stable."""
    n = (name or "").strip()
    # Work on a display-ish string; keep original separators for readability.
    prev = None
    while prev != n:
        prev = n
        for rx in _NAME_PREFIX_RES:
            n2 = rx.sub("", n, count=1).strip()
            if n2 != n:
                n = n2
                break
    return n


def compact_alnum(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def character_name_tokens(name: str) -> list[str]:
    """Significant character tokens after stripping faction/universe prefixes."""
    stripped = strip_faction_universe_prefix(name)
    toks = name_tokens(stripped)
    # Drop any residual faction words (e.g. "Autobot Peacemaker" mid-name after lead strip)
    return [t for t in toks if t not in FACTION_WORDS]


def token_matches_product(tok: str, prod_toks: set[str], prod_blob: str) -> bool:
    """Exact / compacted / fuzzy token match against a product title blob."""
    if not tok:
        return True
    if tok in prod_toks or tok in prod_blob:
        return True
    prod_compact = compact_alnum(prod_blob)
    if tok in prod_compact or compact_alnum(tok) in prod_compact:
        return True
    # Fuzzy vs individual product tokens
    for pt in prod_toks:
        if difflib.SequenceMatcher(None, tok, pt).ratio() >= FUZZY_TOKEN_RATIO:
            return True
        if difflib.SequenceMatcher(None, compact_alnum(tok), compact_alnum(pt)).ratio() >= FUZZY_TOKEN_RATIO:
            return True
    # Spaced retailer spellings: "beach comber" ↔ beachcomber; "shadow striker" ↔ shadowstriker
    words = prod_blob.split()
    for i in range(len(words)):
        for j in range(i + 1, min(i + 4, len(words) + 1)):
            chunk = "".join(words[i:j])
            if chunk == tok:
                return True
            if difflib.SequenceMatcher(None, tok, chunk).ratio() >= FUZZY_TOKEN_RATIO:
                return True
    return False


def load_sku_aliases() -> dict[str, list[str]]:
    if not ALIASES_JSON.exists():
        return {}
    try:
        doc = json.loads(ALIASES_JSON.read_text())
    except Exception:
        return {}
    raw = doc.get("aliasesByFigureId") or {}
    out: dict[str, list[str]] = {}
    for fid, aliases in raw.items():
        if isinstance(aliases, list):
            out[str(fid)] = [str(a) for a in aliases]
    return out


def figure_identity_codes(fig: dict, aliases_by_id: dict[str, list[str]]) -> set[str]:
    """Figure GTIN/sku plus known listing aliases (normalized)."""
    codes: set[str] = set()

    def add(raw: Any) -> None:
        c = clean_code(raw)
        if not c or str(c).startswith("id:"):
            return
        codes.add(c)
        if c.isdigit():
            codes.add(c.lstrip("0") or "0")

    add(fig.get("sku"))
    add(fig.get("barcode"))
    add(fig.get("gtin"))
    for a in aliases_by_id.get(str(fig.get("id") or ""), []) or []:
        add(a)
    return codes


def product_identity_codes(prod: dict) -> set[str]:
    codes: set[str] = set()

    def add(raw: Any) -> None:
        c = clean_code(raw)
        if not c:
            return
        codes.add(c)
        if c.isdigit():
            codes.add(c.lstrip("0") or "0")

    for field in ("sku", "barcode", "listingSku"):
        add(prod.get(field))
    return codes


def codes_overlap(fig_codes: set[str], prod: dict) -> bool:
    if not fig_codes:
        return False
    return bool(fig_codes & product_identity_codes(prod))


THEME_CONFLICTS: list[tuple[set[str], set[str], str]] = [
    ({"skrull"}, {"deadpool", "wolverine"}, "theme_skrull_vs_dpw"),
    ({"skrull"}, {"natchios", "daredevil"}, "theme_skrull_vs_daredevil"),
    ({"netflix"}, {"deadpool", "wolverine"}, "theme_netflix_vs_dpw"),
    ({"spdr", "sp", "dr"}, {"deadpool", "wolverine"}, "theme_spdr_vs_dpw"),
]

# URL path cues that scream multipack / wrong theme even without index title
# Word-ish boundaries so "92_package" / "W2_package" do NOT match.
URL_PACK_RE = re.compile(
    r"(?:^|[^A-Za-z0-9])(?:2|3|4|two|three)[\-_]?packs?(?:[^A-Za-z0-9]|$)"
    r"|(?:^|[^A-Za-z0-9])(?:multipack|multi[\-_]?pack|two[\-_]?pack)(?:[^A-Za-z0-9]|$)",
    re.I,
)
URL_SKRULL_RE = re.compile(r"skrull", re.I)

REFILL_MIN = 22.0
URL_KEEP_MIN = 18.0  # if any co-indexed product scores this high, keep image


def name_tokens(s: str) -> list[str]:
    return [t for t in tokens(s) if t not in WEAK and len(t) > 1]


def blob_of(*parts: Any) -> str:
    bits: list[str] = []
    for p in parts:
        if isinstance(p, list):
            bits.extend(str(x) for x in p if x)
        elif p:
            bits.append(str(p))
    return norm_text(" ".join(bits))


def is_pack_text(*parts: Any) -> bool:
    """Product/figure pack cue via explicit pack language (not bare 'and')."""
    raw = " ".join(
        " ".join(str(x) for x in p) if isinstance(p, list) else str(p or "")
        for p in parts
    )
    return bool(PACK_RE.search(raw))


def figure_is_pack(fig: dict) -> bool:
    """Figure-side multipack: pack language OR dual-character name/subtitle/id."""
    if is_pack_text(
        fig.get("name"),
        fig.get("subtitle"),
        fig.get("line"),
        fig.get("tags"),
        fig.get("id"),
    ):
        return True
    # id slugs: ...-3-pack-..., ...-box-set..., ...-2pk...
    fid = str(fig.get("id") or "")
    if re.search(r"(?:^|[-_])(?:2|3|4)[\-_]?packs?(?:$|[-_])|(?:^|[-_])(?:2|3|4)pk(?:$|[-_])|box[\-_]?set|multipack", fid, re.I):
        return True
    name_sub = f"{fig.get('name') or ''} {fig.get('subtitle') or ''}"
    return bool(DUAL_NAME_RE.search(name_sub))


def norm_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return ""
    return u.split("?")[0].rstrip("/")


def build_gtin_index(index: list[dict]) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)
    for raw in index:
        codes: list[str] = []
        for field in ("sku", "barcode"):
            s = clean_code(raw.get(field))
            if s and is_gtin(s) and s not in codes:
                codes.append(s)
        if not codes:
            continue
        pid = str(raw.get("id") or raw.get("productId") or id(raw))
        for c in codes:
            if pid in seen[c]:
                continue
            seen[c].add(pid)
            by[c].append(raw)
    return by


def lookup_gtin(by_gtin: dict[str, list[dict]], sku: str) -> list[dict]:
    if sku in by_gtin:
        return by_gtin[sku]
    stripped = sku.lstrip("0") or "0"
    for k, v in by_gtin.items():
        if k.lstrip("0") == stripped:
            return v
    return []


def build_url_index(indexes: list[list[dict]]) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)
    for index in indexes:
        for raw in index:
            u = norm_url(str(raw.get("imageUrl") or ""))
            if not u:
                continue
            pid = str(raw.get("id") or raw.get("productId") or id(raw))
            if pid in seen[u]:
                continue
            seen[u].add(pid)
            by[u].append(raw)
    return by


def pick_best_product(fig: dict, cands: list[dict]) -> tuple[float, dict]:
    prepared = [dict(p) for p in cands]
    enrich_index(prepared)
    best: tuple[float, dict] | None = None
    for p in prepared:
        sc = score_pair(fig, p)
        if best is None or sc > best[0]:
            best = (sc, p)
    assert best is not None
    return best


def detect_reasons(fig: dict, prod: dict, score: float) -> list[str]:
    reasons: list[str] = []
    fig_name_toks = name_tokens(fig.get("name") or "")
    prod_blob = blob_of(
        prod.get("title"),
        prod.get("name"),
        prod.get("subtitle"),
        prod.get("handle"),
        prod.get("tags"),
    )
    fig_blob = blob_of(fig.get("name"), fig.get("subtitle"), fig.get("line"))
    prod_toks = set(tokens(prod_blob))

    if score < 0:
        reasons.append("score_pair_reject")
    elif score < 10:
        reasons.append(f"low_score:{score:.1f}")

    # Title/handle only — Mephitsu tags often mark "Multi-Pack" on per-character pages.
    if is_pack_text(
        prod.get("title"),
        prod.get("name"),
        prod.get("subtitle"),
        prod.get("handle"),
    ) and not figure_is_pack(fig):
        reasons.append("product_multipack_vs_single")

    # Character check: ignore faction/universe prefixes; match remaining tokens
    # with spacing/hyphen normalization and light fuzzy tolerance.
    # Pass when ANY remaining character token hits the product (e.g. "Laser Optimus
    # Prime" vs title ending in "Optimus Prime", or "Powerlinx Hot Shot" vs "Hot Shot").
    char_toks = character_name_tokens(fig.get("name") or "")
    if not char_toks:
        char_toks = fig_name_toks
    if char_toks:
        any_hit = any(token_matches_product(t, prod_toks, prod_blob) for t in char_toks)
        joined = "".join(char_toks)
        joined_hit = joined in compact_alnum(prod_blob) or token_matches_product(
            joined, prod_toks, prod_blob
        )
        if not any_hit and not joined_hit:
            reasons.append(f"char_missing:{char_toks[0]}")

    for prod_need, fig_need, label in THEME_CONFLICTS:
        if prod_need & set(tokens(prod_blob)) and fig_need & set(tokens(fig_blob)):
            if not (prod_need & set(tokens(fig_blob))):
                reasons.append(label)

    return reasons


def classify(reasons: list[str]) -> str:
    """high | soft | ok — only high is auto-cleared."""
    if not reasons:
        return "ok"
    high_triggers = {
        "product_multipack_vs_single",
        "theme_skrull_vs_dpw",
        "theme_skrull_vs_daredevil",
        "theme_netflix_vs_dpw",
        "theme_spdr_vs_dpw",
        "url_path_multipack",
        "url_path_skrull_theme",
        "prior_sku_audit_cleared_url",
    }
    if any(r in high_triggers for r in reasons):
        return "high"
    if "score_pair_reject" in reasons and any(r.startswith("char_missing:") for r in reasons):
        return "high"
    return "soft"


def strip_image_tags(tags: list[str]) -> list[str]:
    out: list[str] = []
    for t in tags:
        if t in ("image-bake", "image-sku", "img:mephitsu"):
            continue
        if str(t).startswith("imgsku:") or str(t).startswith("img:"):
            continue
        out.append(t)
    return out


def effective_image(fig: dict, overlay: dict[str, str]) -> str | None:
    oneshot = (fig.get("imageUrl") or "").strip() or None
    ov = (overlay.get(fig["id"]) or "").strip() or None
    return oneshot or ov


def clear_figure_image(fig: dict, overlay: dict[str, str], *, reason_url: str | None) -> dict[str, Any]:
    before_oneshot = fig.get("imageUrl")
    before_overlay = overlay.get(fig["id"])
    action: dict[str, Any] = {
        "figureId": fig["id"],
        "clearedOneshot": False,
        "clearedOverlay": False,
        "clearedImageUrl": reason_url or before_oneshot or before_overlay,
    }
    if before_oneshot:
        del fig["imageUrl"]
        action["clearedOneshot"] = True
    if fig["id"] in overlay:
        del overlay[fig["id"]]
        action["clearedOverlay"] = True
    # Also drop any other overlay keys pointing at the same bad URL
    bad = action.get("clearedImageUrl")
    if bad:
        for k, v in list(overlay.items()):
            if v == bad:
                del overlay[k]
                action["clearedOverlay"] = True
    fig["tags"] = strip_image_tags(list(fig.get("tags") or []))
    return action


def load_prior_cleared_urls() -> set[str]:
    out: set[str] = set()
    if SKU_AUDIT_JSON.exists():
        try:
            doc = json.loads(SKU_AUDIT_JSON.read_text())
        except Exception:
            doc = None
        else:
            for row in doc.get("cleared") or []:
                u = (row.get("clearedImageUrl") or "").strip()
                if u:
                    out.add(u)
                    out.add(norm_url(u))
    # Cumulative ledger survives report rewrites that replace `cleared` with this run only.
    if REPORT_JSON.exists():
        try:
            report = json.loads(REPORT_JSON.read_text())
        except Exception:
            report = None
        else:
            for raw in report.get("clearedUrlLedger") or []:
                u = (raw or "").strip() if isinstance(raw, str) else ""
                if u:
                    out.add(u)
                    out.add(norm_url(u))
    return out


def url_path_reasons(fig: dict, img: str) -> list[str]:
    """Hard cues embedded in the CDN path / filename."""
    reasons: list[str] = []
    path = norm_url(img)
    fig_is_pack = figure_is_pack(fig)
    fig_blob = blob_of(fig.get("name"), fig.get("subtitle"), fig.get("line"))
    if URL_PACK_RE.search(path) and not fig_is_pack:
        reasons.append("url_path_multipack")
    if URL_SKRULL_RE.search(path):
        fig_toks = set(tokens(fig_blob))
        if "skrull" not in fig_toks and (
            {"deadpool", "wolverine"} & fig_toks or "daredevil" in fig_toks or "natchios" in fig_toks
        ):
            reasons.append("url_path_skrull_theme")
    return reasons


def try_refill(fig: dict, by_gtin: dict[str, list[dict]]) -> tuple[str, dict, float] | None:
    """SKU-first image refill when GTIN product high-confidence matches."""
    sku = clean_code(fig.get("sku"))
    if not sku or not is_gtin(sku):
        return None
    cands = lookup_gtin(by_gtin, sku)
    if not cands:
        return None
    score, prod = pick_best_product(fig, cands)
    img = (prod.get("imageUrl") or "").strip()
    if not img:
        return None
    if score < REFILL_MIN:
        return None
    reasons = detect_reasons(fig, prod, score)
    if classify(reasons) == "high":
        return None
    # Contiguous name gate (same spirit as SKU rematch)
    fname = norm_text(fig.get("name") or "")
    prod_blob = blob_of(prod.get("title"), prod.get("name"), prod.get("subtitle"), prod.get("handle"))
    if not fname or fname not in prod_blob:
        return None
    if not re.search(rf"(?:^|\s){re.escape(fname)}(?:\s|$)", prod_blob):
        return None
    fig_toks = name_tokens(fig.get("name") or "")
    if not fig_toks or not all(t in set(tokens(prod_blob)) for t in fig_toks):
        return None
    fig_is_multi = figure_is_pack(fig)
    prod_multi = is_pack_text(
        prod.get("title"), prod.get("name"), prod.get("subtitle"), prod.get("handle")
    )
    if prod_multi and not fig_is_multi:
        return None
    return img, prod, score


def audit_figure(
    fig: dict,
    img: str,
    *,
    by_gtin: dict[str, list[dict]],
    by_url: dict[str, list[dict]],
    prior_cleared: set[str],
    aliases_by_id: dict[str, list[str]] | None = None,
) -> dict[str, Any] | None:
    """Return flag entry or None if ok."""
    reasons: list[str] = []
    evidence: dict[str, Any] = {"imageUrl": img}

    # Prior SKU-audit cleared URL reattached somehow
    if img in prior_cleared or norm_url(img) in prior_cleared:
        reasons.append("prior_sku_audit_cleared_url")

    # URL path cues
    reasons.extend(url_path_reasons(fig, img))

    # (a) GTIN → product title
    sku = clean_code(fig.get("sku"))
    if sku and is_gtin(sku):
        cands = lookup_gtin(by_gtin, sku)
        if cands:
            score, prod = pick_best_product(fig, cands)
            rs = detect_reasons(fig, prod, score)
            evidence["gtin"] = sku
            evidence["gtinScore"] = round(score, 2)
            evidence["gtinTitle"] = prod.get("title") or prod.get("name")
            evidence["gtinShop"] = prod.get("shop")
            for r in rs:
                reasons.append(f"gtin:{r}")

    # If GTIN product is a strong clean match and image equals that product shot, trust it
    gtin_trust = False
    if evidence.get("gtinScore") is not None and evidence["gtinScore"] >= URL_KEEP_MIN:
        gtin_flat = [r.split(":", 1)[1] for r in reasons if r.startswith("gtin:")]
        if classify(gtin_flat) != "high":
            gtin_trust = True

    # (b) URL reverse lookup — only clear when best co-indexed product hard-disagrees
    nu = norm_url(img)
    url_prods = by_url.get(nu) or []
    if url_prods and not gtin_trust:
        sample = url_prods[:12]
        prepared = [dict(p) for p in sample]
        enrich_index(prepared)
        scored: list[tuple[float, dict, list[str]]] = []
        for p in prepared:
            sc = score_pair(fig, p)
            rs = detect_reasons(fig, p, sc)
            scored.append((sc, p, rs))
        scored.sort(key=lambda x: x[0], reverse=True)
        best_sc, best_p, best_rs = scored[0]
        evidence["urlBestScore"] = round(best_sc, 2)
        evidence["urlBestTitle"] = best_p.get("title") or best_p.get("name")
        evidence["urlBestShop"] = best_p.get("shop")
        evidence["urlProductCount"] = len(url_prods)

        # Keep when a co-indexed product is a strong non-high-mismatch match
        if best_sc >= URL_KEEP_MIN and classify(best_rs) != "high":
            pass
        else:
            high_all = all(classify(rs) == "high" for _, _, rs in scored)
            best_level = classify(best_rs)
            if best_level == "high" or high_all:
                for r in best_rs:
                    tag = f"url:{r}"
                    if tag not in reasons:
                        reasons.append(tag)
            elif best_rs and best_sc < 10:
                for r in best_rs:
                    tag = f"url:{r}"
                    if tag not in reasons:
                        reasons.append(tag)

    if not reasons:
        return None

    flat: list[str] = []
    for r in reasons:
        if r.startswith("gtin:") or r.startswith("url:"):
            flat.append(r.split(":", 1)[1])
        else:
            flat.append(r)
    level = classify(flat)
    # Demote path-only multipack when reverse-lookup title is a strong non-mismatch match
    # (e.g. Daft Punk "Human After All" card art filename contains 2pack).
    if level == "high":
        high_bodies = [x for x in flat if classify([x]) == "high"]
        only_path_pack = high_bodies and all(x == "url_path_multipack" for x in high_bodies)
        url_sc = evidence.get("urlBestScore")
        if only_path_pack and url_sc is not None and url_sc >= URL_KEEP_MIN:
            level = "soft"
            reasons.append("demoted:url_path_multipack_strong_title")

    # Never auto-clear when the figure's own barcode/GTIN (or SKU alias) matches
    # the product the photo came from. Only the photo's reverse-indexed product(s)
    # and/or a GTIN-joined product that actually supplies this imageUrl count —
    # a bare GTIN hit on a different listing must not demote a real mismatch.
    fig_codes = figure_identity_codes(fig, aliases_by_id or {})
    photo_match = False
    if fig_codes:
        for p in url_prods:
            if codes_overlap(fig_codes, p):
                photo_match = True
                break
        if not photo_match and evidence.get("gtin"):
            sku = clean_code(fig.get("sku"))
            if sku and is_gtin(sku):
                for p in lookup_gtin(by_gtin, sku):
                    if not codes_overlap(fig_codes, p):
                        continue
                    if norm_url(str(p.get("imageUrl") or "")) == nu:
                        photo_match = True
                        break
    if photo_match:
        evidence["barcodeMatchedPhotoProduct"] = True
        if "barcode_match_photo_product" not in reasons:
            reasons.append("barcode_match_photo_product")
        if level == "high":
            level = "soft"
            reasons.append("demoted:barcode_match_photo_product")

    return {
        "figureId": fig["id"],
        "name": fig.get("name"),
        "subtitle": fig.get("subtitle"),
        "line": fig.get("line"),
        "company": fig.get("company"),
        "sku": fig.get("sku"),
        "reasons": reasons,
        "level": level,
        "evidence": evidence,
        "tags": [t for t in (fig.get("tags") or []) if "image" in str(t) or str(t).startswith("img")],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="Clear high-confidence image mismatches")
    ap.add_argument(
        "--refill",
        action="store_true",
        help="After clear, SKU-first refill when GTIN product high-confidence matches",
    )
    ap.add_argument("--dry-run", action="store_true", help="Force report-only (default)")
    args = ap.parse_args()
    apply = bool(args.apply) and not args.dry_run

    rows: list[dict] = json.loads(ARCHIVE_JSON.read_text())
    sku_index: list[dict] = data_shards.load_array(SKU_INDEX_JSON)
    img_index: list[dict] = json.loads(IMG_INDEX_JSON.read_text()) if IMG_INDEX_JSON.exists() else []
    overlay: dict[str, str] = {}
    if URLS_JSON.exists():
        raw_ov = json.loads(URLS_JSON.read_text())
        if isinstance(raw_ov, dict):
            overlay = {str(k): str(v) for k, v in raw_ov.items() if v}

    print("Building GTIN + URL indexes…")
    by_gtin = build_gtin_index(sku_index)
    by_url = build_url_index([sku_index, img_index])
    prior_cleared = load_prior_cleared_urls()
    aliases_by_id = load_sku_aliases()
    print(
        f"gtins={len(by_gtin)} urls={len(by_url)} prior_cleared_urls={len(prior_cleared)} "
        f"sku_alias_figs={len(aliases_by_id)}"
    )

    audited = 0
    high_flags: list[dict] = []
    soft_flags: list[dict] = []

    for fig in rows:
        img = effective_image(fig, overlay)
        if not img:
            continue
        audited += 1
        flag = audit_figure(
            fig,
            img,
            by_gtin=by_gtin,
            by_url=by_url,
            prior_cleared=prior_cleared,
            aliases_by_id=aliases_by_id,
        )
        if not flag:
            continue
        if flag["level"] == "high":
            high_flags.append(flag)
        else:
            soft_flags.append(flag)

    cleared: list[dict] = []
    refilled: list[dict] = []
    overlay_dropped = 0
    apply_blocked_by_cap = False

    if apply and len(high_flags) > APPLY_CLEAR_CAP:
        apply_blocked_by_cap = True
        print(
            f"SAFETY CAP: would clear {len(high_flags)} photos "
            f"(>{APPLY_CLEAR_CAP}); writing report only — human review required."
        )
        apply = False

    if apply:
        by_id = {r["id"]: r for r in rows}
        for entry in high_flags:
            fig = by_id[entry["figureId"]]
            img = effective_image(fig, overlay)
            action = clear_figure_image(fig, overlay, reason_url=img)
            action["reasons"] = entry["reasons"]
            action["name"] = entry.get("name")
            action["subtitle"] = entry.get("subtitle")
            action["evidence"] = entry.get("evidence")
            cleared.append(action)

            if args.refill:
                hit = try_refill(fig, by_gtin)
                if hit:
                    new_img, prod, sc = hit
                    # Never re-attach a prior-cleared bad URL
                    if new_img in prior_cleared or norm_url(new_img) in prior_cleared:
                        pass
                    else:
                        fig["imageUrl"] = new_img
                        overlay[fig["id"]] = new_img
                        tags = list(fig.get("tags") or [])
                        if "image-sku" not in tags:
                            tags.append("image-sku")
                        if "image-bake" not in tags:
                            tags.append("image-bake")
                        shop = prod.get("shop")
                        if shop:
                            t = f"imgsku:{shop}"
                            if t not in tags and len(tags) < 24:
                                tags.append(t)
                        fig["tags"] = tags
                        refilled.append(
                            {
                                "figureId": fig["id"],
                                "newImageUrl": new_img,
                                "productTitle": prod.get("title") or prod.get("name"),
                                "shop": shop,
                                "score": round(sc, 2),
                                "sku": clean_code(fig.get("sku")),
                            }
                        )

        ARCHIVE_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
        URLS_JSON.write_text(json.dumps(overlay, indent=2, ensure_ascii=False) + "\n")
        overlay_dropped = sum(1 for a in cleared if a.get("clearedOverlay"))

    mode = "apply" if apply else ("dry-run-cap-blocked" if apply_blocked_by_cap else "dry-run")
    report = {
        "auditedAt": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "refill": bool(args.refill and apply),
        "applyClearCap": APPLY_CLEAR_CAP,
        "applyBlockedByCap": apply_blocked_by_cap,
        "counts": {
            "oneshotRows": len(rows),
            "auditedWithImage": audited,
            "highMismatches": len(high_flags),
            "softMismatches": len(soft_flags),
            "cleared": len(cleared),
            "refilled": len(refilled),
            "overlayDropped": overlay_dropped,
            "overlayRemaining": len(overlay),
            "wouldHaveCleared": len(high_flags) if apply_blocked_by_cap else len(cleared),
        },
        "reasonCounts": dict(
            Counter(
                (r.split(":", 1)[1] if r.startswith(("gtin:", "url:")) else r)
                for e in high_flags
                for r in e["reasons"]
            )
        ),
        "cleared": cleared,
        "refilled": refilled,
        "highFlags": high_flags,
        "softFlags": soft_flags[:500],  # cap soft dump
        "softFlagsTruncated": max(0, len(soft_flags) - 500),
        "notes": [
            "High = auto-cleared on --apply (multipack-vs-single, hard theme, score_reject+char_missing, URL path cues, prior SKU-audit cleared URL).",
            "Soft = reported only; not cleared.",
            "Character check strips faction/universe/group prefixes and tolerates spacing/minor spelling (fuzzy).",
            "Barcode/GTIN (or SKU alias) match to the photo's product demotes high→soft; never auto-cleared.",
            f"Apply safety cap: if high clears would exceed {APPLY_CLEAR_CAP}, report only (mode dry-run-cap-blocked).",
            "Clears BOTH oneshot.imageUrl and figure-image-urls.json (resolveFigureImageUrl falls through to overlay).",
            "Refill is GTIN-only, high-confidence, never multipack→single, never invents SKUs/images.",
            "Comics/UPC and Mephitsu crawl paths untouched.",
        ],
    }
    # Keep every URL this audit has ever cleared. `cleared` stays per-run;
    # rewriting the report must not drop earlier clears from the bake block list.
    ledger: set[str] = set()
    if REPORT_JSON.exists():
        try:
            prior_doc = json.loads(REPORT_JSON.read_text())
        except Exception:
            prior_doc = None
        if isinstance(prior_doc, dict):
            for raw in prior_doc.get("clearedUrlLedger") or []:
                u = (raw or "").strip() if isinstance(raw, str) else ""
                if u:
                    ledger.add(u)
            for row in prior_doc.get("cleared") or []:
                if isinstance(row, dict):
                    u = (row.get("clearedImageUrl") or "").strip()
                    if u:
                        ledger.add(u)
    for row in cleared:
        u = (row.get("clearedImageUrl") or "").strip()
        if u:
            ledger.add(u)
    report["clearedUrlLedger"] = sorted(ledger)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    print(f"audited={audited} high={len(high_flags)} soft={len(soft_flags)}")
    print(
        f"cleared={len(cleared)} refilled={len(refilled)} apply={apply} "
        f"cap_blocked={apply_blocked_by_cap}"
    )
    print(f"report={REPORT_JSON}")
    # Spotlight Elektra / D&W
    for e in high_flags + soft_flags:
        fid = e["figureId"]
        if "elektra" in fid.lower() or "elektra" in (e.get("name") or "").lower():
            print(f"ELEKTRA {e['level']}: {fid} reasons={e['reasons']} title={e.get('evidence', {}).get('gtinTitle') or e.get('evidence', {}).get('urlBestTitle')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
