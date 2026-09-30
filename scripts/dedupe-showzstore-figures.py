#!/usr/bin/env python3
"""Collapse high-confidence Showzstore duplicate figure rows onto the proper vault row.

The 2026-09-23 Showzstore densify (inject-showzstore-3p-official /
inject-showzstore-unbranded) added rows for products that already had a proper
listing (EE / curated MP / small-brand injects). The pairs live in
scripts/figure_oneshot/showz-dupe-merge-plan.json (built by the review report,
high confidence only).

For each pair this:
  * keeps the proper row; never touches its msrp, releaseDate, sku, name, line, company
  * adds tags src:showzstore + showz:<id> to the keeper
  * moves the Showz row's aliases (SHOWZ<id>, listing code, id:<dropId>) to the keeper,
    but only re-points alias codes that currently point at the dropped row
    (id:<dropId> makes figureById(<dropId>) resolve to the keeper; SHOWZ<id> makes the
    Showz inject skip the listing if it is ever re-run)
  * copies the Showz imageUrl only when the keeper has no imageUrl and no baked image,
    and tags it img:showzstore so it can be swapped for a clean photo later
  * logs a "collapsed" entry in figure-sku-aliases.json and removes the Showz row

  python3 scripts/dedupe-showzstore-figures.py            # dry run (default)
  python3 scripts/dedupe-showzstore-figures.py --apply
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
BAKED_IMAGES = ROOT / "src/data/figure-image-urls.json"
PLAN = ROOT / "scripts/figure_oneshot/showz-dupe-merge-plan.json"
STATS = ROOT / "src/data/figure-archive/showz-dupe-merge-stats.json"
SHOWZ_SOURCES = {"inject-showzstore-3p-official", "inject-showzstore-unbranded"}


def ensure_tag(row: dict, tag: str) -> bool:
    tags = row.setdefault("tags", [])
    if tag in tags:
        return False
    tags.append(tag)
    return True


def showz_ids(row: dict) -> list[str]:
    out = []
    for tag in row.get("tags") or []:
        if isinstance(tag, str) and tag.startswith("showz:"):
            out.append(tag.split(":", 1)[1])
        elif isinstance(tag, str) and tag.startswith("code:showzstore:"):
            out.append(tag.split(":", 2)[2])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    dry = not args.apply

    rows: list[dict] = json.loads(ONESHOT.read_text())
    aliases = json.loads(ALIASES.read_text())
    baked = json.loads(BAKED_IMAGES.read_text())
    plan = json.loads(PLAN.read_text())
    by_id = {r["id"]: r for r in rows}
    by_fig = aliases.setdefault("aliasesByFigureId", {})
    to_fig = aliases.setdefault("aliasToFigureId", {})
    collapsed = aliases.setdefault("collapsed", [])

    merged, problems = [], []
    drop_ids: set[str] = set()
    for pair in plan["pairs"]:
        drop_id, keep_id = pair["dropId"], pair["keepId"]
        drop, keep = by_id.get(drop_id), by_id.get(keep_id)
        if not drop or not keep:
            problems.append({"pair": pair, "problem": "row missing"})
            continue
        if drop.get("source") not in SHOWZ_SOURCES:
            problems.append({"pair": pair, "problem": f"drop row source is {drop.get('source')}, not Showzstore"})
            continue
        if keep.get("source") in SHOWZ_SOURCES:
            problems.append({"pair": pair, "problem": "keep row is itself a Showzstore row"})
            continue
        if any(r.get("setId") == drop_id for r in rows):
            problems.append({"pair": pair, "problem": "drop row is a set parent"})
            continue

        sids = showz_ids(drop)
        tags_added = [t for t in ["src:showzstore", *[f"showz:{s}" for s in sids]] if ensure_tag(keep, t)]

        codes = list(by_fig.get(drop_id) or [])
        for code, owner in to_fig.items():
            if owner == drop_id and code not in codes:
                codes.append(code)
        for s in sids:
            if f"SHOWZ{s}" not in codes:
                codes.append(f"SHOWZ{s}")
        if f"id:{drop_id}" not in codes:
            codes.append(f"id:{drop_id}")
        keep_list = list(by_fig.get(keep_id) or [])
        moved, left = [], []
        for code in codes:
            owner = to_fig.get(code)
            if owner not in (None, drop_id):
                left.append({"code": code, "pointsAt": owner})
                continue
            to_fig[code] = keep_id
            if code not in keep_list:
                keep_list.append(code)
            moved.append(code)
        by_fig[keep_id] = keep_list
        by_fig.pop(drop_id, None)

        image_filled = False
        if drop.get("imageUrl") and not keep.get("imageUrl") and not baked.get(keep_id):
            keep["imageUrl"] = drop["imageUrl"]
            ensure_tag(keep, "img:showzstore")
            image_filled = True

        drop_ids.add(drop_id)
        collapsed.append({
            "keepId": keep_id,
            "dropId": drop_id,
            "canonicalSku": keep.get("sku"),
            "aliasesAdded": moved,
            "reason": f"Showzstore duplicate (crawl 2026-09-23): {pair.get('reason', '')}",
        })
        merged.append({
            "dropId": drop_id, "keepId": keep_id, "dropName": drop.get("name"), "keepName": keep.get("name"),
            "keepMsrpUnchanged": keep.get("msrp"), "droppedShowzMsrp": drop.get("msrp"),
            "tagsAdded": tags_added, "aliasesMoved": moved, "aliasesLeftAlone": left, "imageFilled": image_filled,
        })

    out_rows = [r for r in rows if r["id"] not in drop_ids]
    stats = {
        "dryRun": dry,
        "at": datetime.now(timezone.utc).isoformat(),
        "planPairs": len(plan["pairs"]),
        "merged": len(merged),
        "rowsBefore": len(rows),
        "rowsAfter": len(out_rows),
        "imagesFilled": sum(1 for m in merged if m["imageFilled"]),
        "problems": problems,
        "merges": merged,
    }
    if not dry:
        aliases["updatedAt"] = stats["at"]
        aliases.setdefault("stats", {})["showzDupeMerge"] = {
            "at": stats["at"], "removed": len(drop_ids), "imagesFilled": stats["imagesFilled"],
        }
        ONESHOT.write_text(json.dumps(out_rows, indent=2, ensure_ascii=False) + "\n")
        ALIASES.write_text(json.dumps(aliases, indent=2, ensure_ascii=False) + "\n")
        STATS.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in stats.items() if k != "merges"}, indent=2))
    for m in merged:
        print(f"{m['dropName'][:52]:52} -> {m['keepId'][:48]:48} img={int(m['imageFilled'])} aliases={len(m['aliasesMoved'])}")


if __name__ == "__main__":
    main()
