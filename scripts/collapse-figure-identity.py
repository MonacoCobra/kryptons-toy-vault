#!/usr/bin/env python3
"""Collapse clear figure-identity duplicates; GTIN canonical, listing codes → aliases.

Dry-run by default. Pass --apply to write:
  - src/data/figure-archive/oneshot.json (rows merged)
  - src/data/figure-sku-aliases.json
  - src/data/figure-sku-map.json / figure-image-urls.json refreshed for survivors
  - src/data/figure-archive/identity-collapse-stats.json

Usage:
  python3 scripts/collapse-figure-identity.py            # dry-run
  python3 scripts/collapse-figure-identity.py --apply
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_identity import (  # noqa: E402
    clean_code,
    collect_alias_codes,
    identity_group_key,
    image_score,
    is_gtin,
    is_listing_code,
    keep_rank,
    listing_embeds_in_gtin,
    prefer_canonical_sku,
    sku_kind,
    wave_subtitle_core,
)

ARCHIVE_JSON = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES_JSON = ROOT / "src/data/figure-sku-aliases.json"
SKU_MAP_JSON = ROOT / "src/data/figure-sku-map.json"
URLS_JSON = ROOT / "src/data/figure-image-urls.json"
STATS_JSON = ROOT / "src/data/figure-archive/identity-collapse-stats.json"
ONESHOT_STATS = ROOT / "src/data/figure-archive/oneshot-stats.json"

# Shelby-confirmed Deadpool & Wolverine Marvel Legends listing↔GTIN pairs.
# keepId should already hold (or receive) the GTIN; dropId is collapsed away.
CURATED_MERGES: list[dict] = [
    {
        "keepId": "ml5-ml-cassandra-nova",
        "dropId": "mlc-cassandra-nova",
        "reason": "D&W Cassandra: EAN 5010996359605 vs HAS359605 listing",
    },
    {
        "keepId": "ml5-ml-deadpool-wolverine-movie",
        "dropId": "mlc-deadpool-movie",
        "reason": "D&W Deadpool: EAN 5010996283757 vs MLDEADM3 listing",
    },
    {
        "keepId": "ml5-ml-x23-movie-dpw",
        "dropId": "mlc-x23-movie",
        "reason": "D&W X-23: EAN 5010996359629 vs HAS359629 listing",
    },
    {
        "keepId": "mlc-nicepool",
        "dropId": "ml5-ml-nicepool",
        "reason": "D&W Nicepool: identical character/line/wave, neither SKU yet — keep earlier curated row",
    },
]

# Explicit non-merges Shelby named but evidence shows distinct GTINs / products.
CURATED_FLAGS: list[dict] = [
    {
        "ids": ["mlc-wolverine-movie", "ml5-ml-wolverine-movie-dpw"],
        "reason": (
            "D&W Wolverine pair named by Shelby, but rows carry distinct GTINs "
            "(5010996267245 Legacy Collection vs 5010996283764 Wave 2) — leave both"
        ),
    },
]

# Extra listing/assort codes that retailers use for the same GTIN figure (no row drop).
CURATED_ALIASES: list[dict] = [
    {
        "figureId": "ml5-ml-cassandra-nova",
        "aliases": ["HAS359605", "G2370", "HASG2370", "HSG2370"],
        "reason": "D&W Cassandra Nova assort/listing codes seen on ToyArena/InDemand/HobbyFigures/Kitsap",
    },
    {
        "figureId": "ml5-ml-deadpool-wolverine-movie",
        "aliases": ["MLDEADM3"],
        "reason": "D&W Deadpool LegendzToys listing code",
    },
    {
        "figureId": "ml5-ml-x23-movie-dpw",
        "aliases": ["HAS359629"],
        "reason": "D&W X-23 ToyArena listing code",
    },
]


def load_aliases() -> dict:
    if ALIASES_JSON.exists():
        return json.loads(ALIASES_JSON.read_text())
    return {
        "version": 1,
        "policy": "gtin-canonical",
        "aliasesByFigureId": {},
        "aliasToFigureId": {},
        "collapsed": [],
        "flagged": [],
    }


def merge_alias_maps(base: dict, figure_id: str, codes: list[str]) -> None:
    bucket = base.setdefault("aliasesByFigureId", {}).setdefault(figure_id, [])
    rev = base.setdefault("aliasToFigureId", {})
    for c in codes:
        cu = c  # preserve original casing
        if cu not in bucket:
            bucket.append(cu)
        # First writer wins for reverse map; do not steal another figure's alias
        prev = rev.get(cu.upper()) or rev.get(cu)
        # Normalize reverse keys to uppercase for lookup stability
        rev_key = cu.upper()
        if prev and prev != figure_id:
            continue
        rev[rev_key] = figure_id


def pick_best_image(keep: dict, drop: dict) -> str | None:
    ku, du = keep.get("imageUrl"), drop.get("imageUrl")
    if image_score(du) > image_score(ku):
        return du
    return ku or du


def apply_merge(keep: dict, drop: dict, aliases_doc: dict, reason: str) -> dict | None:
    """Mutate keep; return collapse record or None if unsafe."""
    ksku = clean_code(keep.get("sku"))
    dsku = clean_code(drop.get("sku"))

    # Distinct GTINs → refuse
    if is_gtin(ksku) and is_gtin(dsku) and ksku != dsku:
        return None

    canonical = prefer_canonical_sku(ksku, dsku)
    if is_gtin(ksku) and is_gtin(dsku) and ksku != dsku:
        return None
    # If both listing / none, keep whatever prefer returns (may be listing until GTIN bake)
    if canonical is None and is_gtin(ksku) and is_gtin(dsku):
        return None

    # Prefer GTIN on the surviving row
    if canonical and is_gtin(canonical):
        keep["sku"] = canonical
    elif not ksku and dsku and is_gtin(dsku):
        keep["sku"] = dsku
    elif not ksku and dsku and not is_gtin(dsku):
        # Surviving row had no sku; drop had listing only — leave sku empty so future
        # GTIN bake can fill; listing goes to aliases.
        keep["sku"] = None
    elif ksku and is_listing_code(ksku) and dsku and is_gtin(dsku):
        keep["sku"] = dsku

    alias_codes = collect_alias_codes(keep, drop, canonical=clean_code(keep.get("sku")))
    # If keep still has a listing as sku (no GTIN known), don't also alias that same code
    if keep.get("sku") and is_listing_code(keep["sku"]):
        alias_codes = [c for c in alias_codes if c.upper() != str(keep["sku"]).upper()]

    best_img = pick_best_image(keep, drop)
    if best_img:
        keep["imageUrl"] = best_img

    # Prefer better (earlier/real) release date when keep has placeholder far-future
    try:
        ky = int(str(keep.get("releaseDate") or "9999")[:4])
        dy = int(str(drop.get("releaseDate") or "9999")[:4])
        if ky > 2030 and 1980 <= dy <= 2030:
            keep["releaseDate"] = drop["releaseDate"]
    except ValueError:
        pass

    # Merge tags lightly
    tags = list(keep.get("tags") or [])
    for t in drop.get("tags") or []:
        if t not in tags and len(tags) < 28:
            tags.append(t)
    if "identity-collapse" not in tags:
        tags.append("identity-collapse")
    keep["tags"] = tags

    merge_alias_maps(aliases_doc, keep["id"], alias_codes)
    # Also record dropped id as a soft alias key for lookups
    merge_alias_maps(aliases_doc, keep["id"], [f"id:{drop['id']}"])

    return {
        "keepId": keep["id"],
        "dropId": drop["id"],
        "canonicalSku": keep.get("sku"),
        "aliasesAdded": alias_codes,
        "reason": reason,
        "keepRank": keep_rank(keep),
        "dropRank": keep_rank(drop),
    }


def auto_candidates(rows: list[dict]) -> list[tuple[dict, dict, str]]:
    """High-confidence auto pairs: same identity key, one GTIN + one listing (or empty)."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        groups[identity_group_key(r)].append(r)

    out: list[tuple[dict, dict, str]] = []
    for key, group in groups.items():
        if len(group) < 2:
            continue
        # Skip groups with 2+ distinct GTINs
        gtins = {clean_code(r.get("sku")) for r in group if is_gtin(r.get("sku"))}
        if len(gtins) > 1:
            continue
        # Pair best GTIN row with listing-only near-dupes
        ranked = sorted(group, key=keep_rank, reverse=True)
        gtin_rows = [r for r in ranked if is_gtin(r.get("sku"))]
        listing_rows = [r for r in ranked if is_listing_code(r.get("sku")) or not clean_code(r.get("sku"))]
        if not gtin_rows:
            # Both empty / listing-only: only merge if exactly 2 and subtitle cores equal
            # and at least one listing — still conservative: require curated or embed
            continue
        keep = gtin_rows[0]
        gtin = clean_code(keep.get("sku"))
        for drop in listing_rows:
            if drop["id"] == keep["id"]:
                continue
            dsku = clean_code(drop.get("sku"))
            # Empty-sku drop next to GTIN keep with identical identity key — ok
            if not dsku:
                reason = f"auto: empty-sku near-dupe of GTIN {gtin} under {key[1]} / {key[3]}"
                out.append((keep, drop, reason))
                continue
            if not is_listing_code(dsku):
                continue
            # Require digit-tail embed (HAS359605 ⊂ …359605). Waveish-only is too
            # loose (mis-paired Baylan/Hound, Chaos Magic vs wrong EAN, multipacks).
            embed = listing_embeds_in_gtin(dsku, gtin or "")
            if not embed:
                continue
            reason = (
                f"auto: listing {dsku} embeds in GTIN {gtin} under {key[1]} / {key[3]}"
            )
            out.append((keep, drop, reason))
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    rows = json.loads(ARCHIVE_JSON.read_text())
    by_id = {r["id"]: r for r in rows}
    before = len(rows)
    aliases_doc = load_aliases()
    aliases_doc["policy"] = "gtin-canonical"
    aliases_doc["updatedAt"] = datetime.now(timezone.utc).isoformat()

    planned: list[dict] = []
    flagged: list[dict] = list(CURATED_FLAGS)
    drop_ids: set[str] = set()

    # 1) Curated merges
    for spec in CURATED_MERGES:
        keep = by_id.get(spec["keepId"])
        drop = by_id.get(spec["dropId"])
        if not keep or not drop:
            flagged.append(
                {
                    "ids": [spec["keepId"], spec["dropId"]],
                    "reason": f"curated miss: keep={bool(keep)} drop={bool(drop)} — {spec['reason']}",
                }
            )
            continue
        if drop["id"] in drop_ids:
            continue
        # Ensure keep is the better GTIN bearer when curated order was wrong
        if is_gtin(drop.get("sku")) and not is_gtin(keep.get("sku")):
            keep, drop = drop, keep
        elif keep_rank(drop) > keep_rank(keep) + 50 and is_gtin(drop.get("sku")):
            keep, drop = drop, keep
        rec = apply_merge(keep, drop, aliases_doc, spec["reason"])
        if rec is None:
            flagged.append(
                {
                    "ids": [keep["id"], drop["id"]],
                    "reason": f"curated refused (GTIN conflict?) — {spec['reason']}",
                }
            )
            continue
        planned.append(rec)
        drop_ids.add(drop["id"])

    # 1b) Curated alias attachments (no row drop)
    for spec in CURATED_ALIASES:
        fid = spec["figureId"]
        if fid not in by_id or fid in drop_ids:
            flagged.append(
                {"ids": [fid], "reason": f"curated alias target missing/dropped — {spec['reason']}"}
            )
            continue
        merge_alias_maps(aliases_doc, fid, list(spec["aliases"]))
        # If surviving row still has a listing sku that we now know is alias-only and
        # somehow also has no GTIN, leave sku as-is until bake upgrades.
        print(f"  ALIAS {fid} += {spec['aliases']}")

    # 2) Auto high-confidence (skip already dropped / already planned)
    planned_pairs = {(p["keepId"], p["dropId"]) for p in planned} | {
        (p["dropId"], p["keepId"]) for p in planned
    }
    for keep, drop, reason in auto_candidates(rows):
        if keep["id"] in drop_ids or drop["id"] in drop_ids:
            continue
        if (keep["id"], drop["id"]) in planned_pairs:
            continue
        # Don't auto-touch densify-only conflicts without embed
        if "densify" in str(drop.get("source") or "") and not listing_embeds_in_gtin(
            clean_code(drop.get("sku")) or "", clean_code(keep.get("sku")) or ""
        ):
            flagged.append(
                {
                    "ids": [keep["id"], drop["id"]],
                    "reason": f"skipped densify without embed: {reason}",
                }
            )
            continue
        rec = apply_merge(keep, drop, aliases_doc, reason)
        if rec is None:
            flagged.append({"ids": [keep["id"], drop["id"]], "reason": f"auto refused: {reason}"})
            continue
        planned.append(rec)
        drop_ids.add(drop["id"])
        planned_pairs.add((keep["id"], drop["id"]))

    # Wolverine + any remaining multi-GTIN groups → flags
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        if r["id"] in drop_ids:
            continue
        groups[identity_group_key(r)].append(r)
    for key, group in groups.items():
        if len(group) < 2:
            continue
        gtins = sorted({clean_code(r.get("sku")) for r in group if is_gtin(r.get("sku"))})
        if len(gtins) > 1:
            ids = [r["id"] for r in group]
            if not any(set(ids) <= set(f.get("ids") or []) or set(f.get("ids") or []) <= set(ids) for f in flagged):
                flagged.append(
                    {
                        "ids": ids,
                        "skus": gtins,
                        "reason": f"distinct GTINs under {key[1]} / {key[3]} — left both",
                    }
                )

    # D&W wave report slice
    dw_collapsed = [
        p
        for p in planned
        if any(
            x in p["keepId"] or x in p["dropId"]
            for x in (
                "cassandra-nova",
                "deadpool-wolverine-movie",
                "deadpool-movie",
                "x23-movie",
                "nicepool",
                "wolverine-movie",
            )
        )
    ]

    print(f"before={before} planned_collapses={len(planned)} drop_ids={len(drop_ids)} flagged={len(flagged)}")
    print("D&W-related collapses:", len(dw_collapsed))
    for p in planned[:25]:
        print(
            f"  KEEP {p['keepId']} sku={p['canonicalSku']} "
            f"<- DROP {p['dropId']} aliases={p['aliasesAdded']} | {p['reason'][:80]}"
        )
    if len(planned) > 25:
        print(f"  ... +{len(planned) - 25} more")
    print("flagged samples:")
    for f in flagged[:12]:
        print(f"  FLAG {f.get('ids')} — {f.get('reason')[:100]}")

    if not apply:
        print("dry-run — not writing (pass --apply)")
        # Still write a dry-run stats snapshot? No — keep tree clean.
        return 0

    kept_rows = [r for r in rows if r["id"] not in drop_ids]
    # Re-assert keep mutations from by_id
    kept_rows = [by_id[r["id"]] for r in kept_rows]

    aliases_doc["collapsed"] = planned
    aliases_doc["flagged"] = flagged
    aliases_doc["stats"] = {
        "before": before,
        "removed": len(drop_ids),
        "after": len(kept_rows),
        "dwCollapsed": len(dw_collapsed),
    }

    ARCHIVE_JSON.write_text(json.dumps(kept_rows, indent=2) + "\n")
    ALIASES_JSON.write_text(json.dumps(aliases_doc, indent=2) + "\n")

    # Refresh overlays for survivors only; preserve unrelated map entries then rebuild from rows
    sku_map = {r["id"]: r["sku"] for r in kept_rows if clean_code(r.get("sku"))}
    SKU_MAP_JSON.write_text(json.dumps(sku_map, indent=2, sort_keys=True) + "\n")
    urls = {r["id"]: r["imageUrl"] for r in kept_rows if r.get("imageUrl")}
    URLS_JSON.write_text(json.dumps(urls, indent=2, sort_keys=True) + "\n")

    stats = {
        "collapsedAt": datetime.now(timezone.utc).isoformat(),
        "day": date.today().isoformat(),
        "policy": "gtin-canonical; listing codes are aliases",
        "before": before,
        "removed": len(drop_ids),
        "after": len(kept_rows),
        "dwCollapsed": len(dw_collapsed),
        "dwSamples": dw_collapsed,
        "planned": planned,
        "flagged": flagged,
        "removedBySource": dict(
            Counter(by_id[i].get("source") for i in drop_ids if i in by_id).most_common()
        ),
    }
    STATS_JSON.write_text(json.dumps(stats, indent=2) + "\n")

    if ONESHOT_STATS.exists():
        os_stats = json.loads(ONESHOT_STATS.read_text())
        os_stats["archiveTotal"] = len(kept_rows)
        os_stats["withImageUrl"] = sum(1 for r in kept_rows if r.get("imageUrl"))
        os_stats["identityCollapsed"] = len(drop_ids)
        os_stats["identityCollapsedAt"] = stats["collapsedAt"]
        ONESHOT_STATS.write_text(json.dumps(os_stats, indent=2) + "\n")

    print(f"wrote {ARCHIVE_JSON}")
    print(f"wrote {ALIASES_JSON}")
    print(f"wrote {STATS_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
