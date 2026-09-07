#!/usr/bin/env python3
"""Audit oneshot GTIN primaries against product-sku-index titles.

Joins every figure with a GTIN primary sku to product-sku-index rows that carry
that GTIN. Flags high-confidence title mismatches (different character,
multipack vs single, hard theme conflicts). Soft/borderline disagreements are
reported but NOT auto-cleared.

On --apply:
  - Clears high-confidence mismatched primary sku (never invents replacements)
  - Clears sku-proven imageUrl when tied to the mismatched product
  - Optionally reassigns a different GTIN only at very high confidence
  - Writes report JSON under src/data/figure-archive/

Primary sku policy: GTIN only. Comics / UPC untouched. Mephitsu crawl left alone.

Usage:
  python3 scripts/audit-figure-sku-mismatches.py              # dry-run report
  python3 scripts/audit-figure-sku-mismatches.py --apply       # clear + report
  python3 scripts/audit-figure-sku-mismatches.py --apply --rematch
"""
from __future__ import annotations

import argparse
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

from figure_identity import is_gtin, clean_code, tokens, norm_text  # noqa: E402

ARCHIVE_JSON = ROOT / "src/data/figure-archive/oneshot.json"
INDEX_JSON = ROOT / "src/data/figure-archive/product-sku-index.json"
SKU_MAP_JSON = ROOT / "src/data/figure-sku-map.json"
ALIASES_JSON = ROOT / "src/data/figure-sku-aliases.json"
REPORT_JSON = ROOT / "src/data/figure-archive/sku-mismatch-audit.json"

_spec = importlib.util.spec_from_file_location("bake_figure_images", SCRIPTS / "bake-figure-images.py")
_bfi = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_bfi)

score_pair = _bfi.score_pair
enrich_index = _bfi.enrich_index

PACK_RE = re.compile(
    r"\b(?:2[\s\-]?pack|3[\s\-]?pack|4[\s\-]?pack|two[\s\-]?pack|three[\s\-]?pack|"
    r"multipack|multi[\s\-]?pack)\b",
    re.I,
)

# Franchise / packaging noise — never treat as character identity.
WEAK = {
    "series", "legends", "marvel", "action", "figure", "figures", "hasbro",
    "wave", "exclusive", "edition", "deluxe", "scale", "inch", "black",
    "retro", "vintage", "comic", "comics", "movie", "tv", "the", "and",
    "dc", "multiverse", "classified", "origins", "masterverse", "collection",
    "pack", "set", "anniversary", "studio", "studios", "infinite",
}

# Hard theme pairs: product has A-tokens while figure has B-tokens (and not A).
THEME_CONFLICTS: list[tuple[set[str], set[str], str]] = [
    ({"skrull"}, {"deadpool", "wolverine"}, "theme_skrull_vs_dpw"),
    ({"skrull"}, {"natchios", "daredevil"}, "theme_skrull_vs_daredevil"),
    ({"netflix"}, {"deadpool", "wolverine"}, "theme_netflix_vs_dpw"),
    ({"spdr", "sp", "dr"}, {"deadpool", "wolverine"}, "theme_spdr_vs_dpw"),
]

REMATCH_MIN = 22.0  # stricter than bake MIN_SCORE 18


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
    raw = " ".join(
        " ".join(str(x) for x in p) if isinstance(p, list) else str(p or "")
        for p in parts
    )
    return bool(PACK_RE.search(raw))


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


def image_tied_to_product(fig: dict, prod: dict) -> bool:
    """True when figure imageUrl is sku-proven from this product."""
    fig_url = str(fig.get("imageUrl") or "")
    if not fig_url:
        return False
    tags = fig.get("tags") or []
    prod_url = str(prod.get("imageUrl") or "")
    handle = str(prod.get("handle") or "")
    sku = clean_code(prod.get("sku") or prod.get("barcode") or "") or ""
    if prod_url and fig_url == prod_url:
        return True
    if handle and handle in fig_url:
        return True
    if sku and len(sku) >= 8 and sku in fig_url:
        return True
    # image-sku provenance without URL equality still counts if handle/sku embeds
    if "image-sku" in tags and (handle in fig_url or (sku and sku in fig_url)):
        return True
    return False


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

    if is_pack_text(
        prod.get("title"),
        prod.get("name"),
        prod.get("subtitle"),
        prod.get("handle"),
        prod.get("tags"),
    ) and not is_pack_text(
        fig.get("name"),
        fig.get("subtitle"),
        fig.get("line"),
        fig.get("tags"),
    ):
        reasons.append("product_multipack_vs_single")

    if fig_name_toks:
        first = fig_name_toks[0]
        if first not in prod_toks and first not in prod_blob:
            # joined compound (bossborot) fallback
            joined = "".join(fig_name_toks)
            if joined not in prod_blob.replace(" ", ""):
                reasons.append(f"char_missing:{first}")

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
    }
    if any(r in high_triggers for r in reasons):
        return "high"
    if "score_pair_reject" in reasons and any(r.startswith("char_missing:") for r in reasons):
        return "high"
    # score reject alone, low_score, or lone char_missing with decent score → soft
    return "soft"


def strip_sku_tags(tags: list[str]) -> list[str]:
    drop_exact = {
        "sku-bake",
        "sku-gtin",
        "sku-alias",
        "image-sku",
    }
    out: list[str] = []
    for t in tags:
        if t in drop_exact:
            continue
        if t.startswith("sku:") or t.startswith("alias:") or t.startswith("imgsku:"):
            continue
        out.append(t)
    return out


def clear_mismatch(
    fig: dict,
    prod: dict,
    *,
    clear_image: bool,
) -> dict[str, Any]:
    before_sku = fig.get("sku")
    before_img = fig.get("imageUrl")
    action: dict[str, Any] = {
        "figureId": fig["id"],
        "clearedSku": before_sku,
        "clearedImage": False,
        "productTitle": prod.get("title") or prod.get("name"),
        "shop": prod.get("shop"),
    }
    if "sku" in fig:
        del fig["sku"]
    tags = list(fig.get("tags") or [])
    if clear_image and before_img:
        del fig["imageUrl"]
        action["clearedImage"] = True
        action["clearedImageUrl"] = before_img
        tags = [t for t in tags if t not in ("image-bake", "image-sku") and not str(t).startswith("imgsku:")]
    fig["tags"] = strip_sku_tags(tags)
    # Drop listing aliases that belong to the mismatched product
    return action


def sync_sku_map(rows: list[dict]) -> None:
    sku_map: dict[str, str] = {}
    if SKU_MAP_JSON.exists():
        try:
            prev = json.loads(SKU_MAP_JSON.read_text())
            if isinstance(prev, dict):
                sku_map = {k: str(v) for k, v in prev.items() if clean_code(v)}
        except Exception:
            sku_map = {}
    by_id = {r["id"]: r for r in rows}
    # Remove map entries whose oneshot row no longer has that sku / has no sku
    for fid in list(sku_map.keys()):
        row = by_id.get(fid)
        if not row:
            continue
        cur = clean_code(row.get("sku"))
        if not cur or cur != sku_map[fid]:
            del sku_map[fid]
    for r in rows:
        s = clean_code(r.get("sku"))
        if s and is_gtin(s):
            sku_map[r["id"]] = s
    SKU_MAP_JSON.write_text(json.dumps(sku_map, indent=2, ensure_ascii=False) + "\n")


def drop_figure_aliases(figure_id: str, codes: list[str] | None = None) -> list[str]:
    """Remove aliases for a figure (all, or specific codes). Returns removed."""
    if not ALIASES_JSON.exists():
        return []
    try:
        doc = json.loads(ALIASES_JSON.read_text())
    except Exception:
        return []
    if not isinstance(doc, dict):
        return []
    by = doc.get("aliasesByFigureId")
    rev = doc.get("aliasToFigureId")
    if not isinstance(by, dict):
        return []
    existing = list(by.get(figure_id) or [])
    if not existing:
        return []
    if codes is None:
        remove = list(existing)
    else:
        want = {c.upper() for c in codes}
        remove = [c for c in existing if c.upper() in want]
    if not remove:
        return []
    remove_u = {c.upper() for c in remove}
    by[figure_id] = [c for c in existing if c.upper() not in remove_u]
    if not by[figure_id]:
        del by[figure_id]
    if isinstance(rev, dict):
        for c in remove:
            if rev.get(c) == figure_id:
                del rev[c]
            # case variants
            for k in list(rev.keys()):
                if k.upper() == c.upper() and rev.get(k) == figure_id:
                    del rev[k]
    doc["updatedAt"] = datetime.now(timezone.utc).isoformat()
    ALIASES_JSON.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    return remove


def try_rematch(
    fig: dict,
    index_prepared_by_co: dict[str, list[dict]],
    reserved: set[str],
) -> tuple[str, dict] | None:
    """High-confidence rematch only. Returns (gtin, product) or None.

    Conservative gates (prefer empty over wrong):
      - same company (pool already gated)
      - contiguous full figure name as word(s) in product blob
      - every significant name token present
      - reject multipack / "A & B" / "set of N" unless figure is multipack
      - reject when figure name is only a proper suffix of a longer character
        (Storm ⊂ Johnny Storm, Ghost ⊂ Ghost Rider)
      - score_pair >= REMATCH_MIN
    """
    company = fig.get("company")
    pool = index_prepared_by_co.get(company) or []
    if not pool:
        return None
    fig_is_multi = is_pack_text(
        fig.get("name"), fig.get("subtitle"), fig.get("line"), fig.get("tags")
    )
    fig_toks = name_tokens(fig.get("name") or "")
    if not fig_toks:
        return None
    fname = norm_text(fig.get("name") or "")
    best: tuple[float, dict] | None = None
    amp_re = re.compile(r"\b\w+\s+(?:and|&)\s+\w+", re.I)
    set_of_re = re.compile(r"\bset of \d+\b", re.I)
    for p in pool:
        gtin = clean_code(p.get("sku"))
        if not gtin or not is_gtin(gtin):
            continue
        if gtin.upper() in reserved:
            continue
        title = p.get("title") or p.get("name") or ""
        prod_multi = is_pack_text(
            p.get("title"), p.get("name"), p.get("subtitle"), p.get("handle"), p.get("tags")
        ) or bool(set_of_re.search(title))
        if not fig_is_multi and (prod_multi or ("&" in title and not fname in norm_text(title).split("&")[0])):
            # bare "&" multipacks (Cassian Andor & B2EMO) — skip unless figure is pack
            if "&" in title or prod_multi:
                continue
        prod_blob = blob_of(p.get("title"), p.get("name"), p.get("subtitle"), p.get("handle"))
        if not fname or fname not in prod_blob:
            continue
        # word-boundary contiguous (avoid storm⊂johnny storm via token check below)
        if not re.search(rf"(?:^|\s){re.escape(fname)}(?:\s|$)", prod_blob):
            continue
        prod_toks = tokens(prod_blob)
        prod_tok_set = set(prod_toks)
        if not all(t in prod_tok_set for t in fig_toks):
            continue
        # Proper-suffix / longer-name trap: a product token that endswith figure
        # token but is longer (johnny≠storm already separate; ghost⊂ghost+rider
        # when figure is single-token "ghost" and product has ghost+rider).
        if len(fig_toks) == 1:
            ft = fig_toks[0]
            idxs = [i for i, t in enumerate(prod_toks) if t == ft]
            if not idxs:
                continue
            fig_ctx = set(tokens(blob_of(fig.get("subtitle"), fig.get("line"), fig.get("name"))))
            # Ghost Rider (after) or Johnny Storm (before): neighboring strong
            # name token not in figure context ⇒ different character.
            neighbors: list[str] = []
            for i in idxs:
                if i + 1 < len(prod_toks) and prod_toks[i + 1] not in WEAK:
                    neighbors.append(prod_toks[i + 1])
                if i > 0 and prod_toks[i - 1] not in WEAK:
                    neighbors.append(prod_toks[i - 1])
            strong = [n for n in neighbors if len(n) >= 4 and n not in fig_ctx]
            if strong:
                continue
        sc = score_pair(fig, p)
        if sc < REMATCH_MIN:
            continue
        if best is None or sc > best[0]:
            best = (sc, p)
    if not best:
        return None
    sc, p = best
    gtin = clean_code(p.get("sku"))
    assert gtin
    return gtin, p


def fix_elektra_aliases() -> list[str]:
    """D&W Elektra carried Netflix / Daredevil / 3-pack listing aliases — drop them."""
    return drop_figure_aliases("ml5-ml-elektra-movie-dpw")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="Clear high-confidence mismatches")
    ap.add_argument(
        "--rematch",
        action="store_true",
        help="After clear, attempt high-confidence GTIN reassignment",
    )
    ap.add_argument("--dry-run", action="store_true", help="Force report-only (default)")
    args = ap.parse_args()
    apply = bool(args.apply) and not args.dry_run

    rows: list[dict] = json.loads(ARCHIVE_JSON.read_text())
    index: list[dict] = json.loads(INDEX_JSON.read_text())
    by_gtin = build_gtin_index(index)

    audited = 0
    no_index = 0
    high_flags: list[dict] = []
    soft_flags: list[dict] = []
    cleared: list[dict] = []
    reassigned: list[dict] = []

    # Precompute reserved GTINs
    reserved: set[str] = set()
    for r in rows:
        s = clean_code(r.get("sku"))
        if s and is_gtin(s):
            reserved.add(s.upper())

    rematch_pool: dict[str, list[dict]] | None = None
    if apply and args.rematch:
        prepared = []
        for raw in index:
            s = clean_code(raw.get("sku"))
            if s and is_gtin(s):
                prepared.append(dict(raw))
        enrich_index(prepared)
        rematch_pool = defaultdict(list)
        for p in prepared:
            rematch_pool[p["company"]].append(p)

    for fig in rows:
        sku = clean_code(fig.get("sku"))
        if not sku or not is_gtin(sku):
            continue
        audited += 1
        cands = lookup_gtin(by_gtin, sku)
        if not cands:
            no_index += 1
            continue
        score, prod = pick_best_product(fig, cands)
        reasons = detect_reasons(fig, prod, score)
        level = classify(reasons)
        if level == "ok":
            continue
        entry = {
            "figureId": fig["id"],
            "name": fig.get("name"),
            "subtitle": fig.get("subtitle"),
            "line": fig.get("line"),
            "company": fig.get("company"),
            "sku": sku,
            "productTitle": prod.get("title") or prod.get("name"),
            "productId": prod.get("id"),
            "shop": prod.get("shop"),
            "score": round(score, 2),
            "reasons": reasons,
            "level": level,
            "imageTied": image_tied_to_product(fig, prod),
            "imageUrl": fig.get("imageUrl"),
        }
        if level == "high":
            high_flags.append(entry)
        else:
            soft_flags.append(entry)

    elektra_aliases_removed: list[str] = []
    if apply:
        by_id = {r["id"]: r for r in rows}
        for entry in high_flags:
            fig = by_id[entry["figureId"]]
            # re-resolve product
            cands = lookup_gtin(by_gtin, entry["sku"])
            score, prod = pick_best_product(fig, cands)
            clear_img = image_tied_to_product(fig, prod)
            action = clear_mismatch(fig, prod, clear_image=clear_img)
            action["reasons"] = entry["reasons"]
            # free reserved
            if entry["sku"].upper() in reserved:
                reserved.discard(entry["sku"].upper())
            cleared.append(action)

            if args.rematch and rematch_pool is not None:
                hit = try_rematch(fig, rematch_pool, reserved)
                if hit:
                    gtin, p = hit
                    fig["sku"] = gtin
                    tags = list(fig.get("tags") or [])
                    if "sku-bake" not in tags:
                        tags.append("sku-bake")
                    if "sku-gtin" not in tags:
                        tags.append("sku-gtin")
                    shop_tag = f"sku:{p.get('shop')}"
                    if shop_tag not in tags and len(tags) < 24:
                        tags.append(shop_tag)
                    fig["tags"] = tags
                    # Prefer product image when we cleared and product has one
                    if action.get("clearedImage") and p.get("imageUrl"):
                        # only if not multipack mismatch path — rematch already forbids multipack
                        fig["imageUrl"] = p["imageUrl"]
                        if "image-sku" not in tags:
                            tags.append("image-sku")
                        img_tag = f"imgsku:{p.get('shop')}"
                        if img_tag not in tags and len(tags) < 24:
                            tags.append(img_tag)
                        fig["tags"] = tags
                    reserved.add(gtin.upper())
                    reassigned.append(
                        {
                            "figureId": fig["id"],
                            "newSku": gtin,
                            "productTitle": p.get("title") or p.get("name"),
                            "shop": p.get("shop"),
                            "score": round(score_pair(fig, p), 2),
                        }
                    )

        # Targeted Elektra alias cleanup (wrong Netflix/Daredevil/3-pack listings)
        elektra_aliases_removed = fix_elektra_aliases()

        ARCHIVE_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
        sync_sku_map(rows)

    report = {
        "auditedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if apply else "dry-run",
        "rematch": bool(args.rematch and apply),
        "counts": {
            "oneshotRows": len(rows),
            "auditedGtinPrimaries": audited,
            "noIndexHit": no_index,
            "highMismatches": len(high_flags),
            "softMismatches": len(soft_flags),
            "cleared": len(cleared),
            "reassigned": len(reassigned),
            "elektraAliasesRemoved": len(elektra_aliases_removed),
        },
        "reasonCounts": dict(Counter(r for e in high_flags for r in e["reasons"])),
        "cleared": cleared,
        "reassigned": reassigned,
        "elektraAliasesRemoved": elektra_aliases_removed,
        "highFlags": high_flags,
        "softFlags": soft_flags,
        "notes": [
            "High = auto-cleared on --apply (multipack-vs-single, hard theme, score_reject+char_missing).",
            "Soft = reported only (borderline); not cleared.",
            "Primary sku remains GTIN-only; empty when no high-confidence rematch.",
            "Comics/UPC and Mephitsu crawl paths untouched.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    print(f"audited={audited} high={len(high_flags)} soft={len(soft_flags)} no_index={no_index}")
    print(f"cleared={len(cleared)} reassigned={len(reassigned)} apply={apply}")
    print(f"report={REPORT_JSON}")
    if elektra_aliases_removed:
        print(f"elektra aliases removed: {elektra_aliases_removed}")
    # spotlight Elektra
    for e in high_flags:
        if e["figureId"] == "ml5-ml-elektra-movie-dpw":
            print(f"ELEKTRA: {e['reasons']} → {e['productTitle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
