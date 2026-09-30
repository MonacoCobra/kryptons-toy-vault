#!/usr/bin/env python3
"""Hasbro Studio Series audit: field fixes, duplicate merges and invented-row deletions.

Reads scripts/figure_oneshot/studio-series-audit-plan.json, built 2026-09-30 by checking every
Hasbro "Transformers Studio Series" row (d14ss-*, tfss-*, tfc-*, BBTS wave rows, EE/afmon,
legendsverse), plus the 12 TakaraTomy Showzstore SS rows, against the TFWiki Studio Series list
(https://tfwiki.net/wiki/Studio_Series). UPCs and retailer image filenames count only as
corroborating evidence. Each action records its reason and sources.

Order of operations:
  1. fixFields      - set subtitle / releaseDate / name on the verified row, only when the current
                      value equals the plan's "old" value.
  2. deleteInvented - remove rows for products that do not exist. Each removal is logged in the
                      aliases "removed" list with keepId null, and aliases pointing at the row are dropped.
  3. merge          - fold a duplicate row into the keeper for the same release. The keeper's
                      msrp/sku/date/name are untouched. Aliases plus id:<dropId> move to the keeper;
                      the drop row's image is copied only when the keeper has none.
  correct / unsure / missing / flags entries are report-only and never touched.

  python3 scripts/studio-series-audit.py            # dry run (default; writes nothing)
  python3 scripts/studio-series-audit.py --apply
"""
from __future__ import annotations

import argparse
import re
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
BAKED_IMAGES = ROOT / "src/data/figure-image-urls.json"
PLAN = ROOT / "scripts/figure_oneshot/studio-series-audit-plan.json"
STATS = ROOT / "src/data/figure-archive/studio-series-audit-stats.json"
TAG = "fix:ss-audit"


def ensure_tag(row: dict, tag: str) -> None:
    tags = row.setdefault("tags", [])
    if tag not in tags:
        tags.append(tag)


def integrity(rows: list[dict], to_fig: dict) -> dict:
    ids = [r["id"] for r in rows]
    idset = set(ids)
    return {
        "rows": len(rows),
        "duplicateIds": [i for i, c in Counter(ids).items() if c > 1],
        "danglingAliases": sorted(k for k, v in to_fig.items() if v not in idset),
        "danglingSetIds": sorted(r["id"] for r in rows if r.get("setId") and r["setId"] not in idset),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    dry = not ap.parse_args().apply

    rows: list[dict] = json.loads(ONESHOT.read_text())
    aliases = json.loads(ALIASES.read_text())
    baked = json.loads(BAKED_IMAGES.read_text()) if BAKED_IMAGES.exists() else {}
    plan = json.loads(PLAN.read_text())
    by_id = {r["id"]: r for r in rows}
    set_parents = {r["setId"] for r in rows if r.get("setId")}
    by_fig = aliases.setdefault("aliasesByFigureId", {})
    to_fig = aliases.setdefault("aliasToFigureId", {})
    collapsed = aliases.setdefault("collapsed", [])
    removed = aliases.setdefault("removed", [])
    before = integrity(rows, to_fig)
    problems, fixed, deleted, merged = [], [], [], []
    drop_ids: set[str] = set()
    untouchable = {e["id"] for e in plan["unsure"]} | {e["id"] for e in plan["correct"]}

    # 1. field fixes
    for f in plan["fixFields"]:
        r = by_id.get(f["id"])
        if not r:
            problems.append({"fix": f["id"], "problem": "row missing"}); continue
        bad = {k: r.get(k) for k, v in f["set"].items() if r.get(k) != v["old"]}
        if bad:
            problems.append({"fix": f["id"], "problem": f"current values differ from plan: {bad}"}); continue
        for k, v in f["set"].items():
            r[k] = v["new"]
            fixed.append({"id": f["id"], "field": k, "old": v["old"], "new": v["new"]})
            if k == "releaseDate" and re.fullmatch(r"\d{4}", str(v["new"])):
                # year-only date: no source gives a month, so none is invented
                ensure_tag(r, "date-precision:year")
        ensure_tag(r, TAG)

    # 2. invented rows
    for dl in plan["deleteInvented"]:
        i = dl["id"]
        r = by_id.get(i)
        if not r:
            problems.append({"delete": i, "problem": "row missing"}); continue
        if i in set_parents:
            problems.append({"delete": i, "problem": "row is a set parent"}); continue
        if i in untouchable:
            problems.append({"delete": i, "problem": "row is listed as correct/unsure"}); continue
        dropped = list(by_fig.pop(i, []) or [])
        for code, owner in list(to_fig.items()):
            if owner == i:
                if code not in dropped:
                    dropped.append(code)
                del to_fig[code]
        drop_ids.add(i)
        removed.append({"keepId": None, "dropId": i, "canonicalSku": r.get("sku"), "aliasesAdded": [],
                        "aliasesMoved": {}, "aliasesDropped": dropped,
                        "reason": f"Studio Series audit 2026-09-30: {dl['reason']} Sources: {'; '.join(dl['sources'])}"})
        deleted.append({"id": i, "name": r.get("name"), "subtitle": r.get("subtitle"), "aliasesDropped": dropped})

    # 3. merges
    def move_aliases(drop_id: str, keep_id: str) -> tuple[list, list]:
        codes = list(by_fig.get(drop_id) or [])
        for code, owner in to_fig.items():
            if owner == drop_id and code not in codes:
                codes.append(code)
        if f"id:{drop_id}" not in codes:
            codes.append(f"id:{drop_id}")
        keep_list = list(by_fig.get(keep_id) or [])
        moved, left = [], []
        for code in codes:
            owner = to_fig.get(code)
            if owner not in (None, drop_id):
                left.append({"code": code, "pointsAt": owner}); continue
            to_fig[code] = keep_id
            if code not in keep_list:
                keep_list.append(code)
            moved.append(code)
        by_fig[keep_id] = keep_list
        by_fig.pop(drop_id, None)
        # redirect any id:<x> aliases that previously pointed at the drop row
        for code, owner in list(to_fig.items()):
            if owner == drop_id:
                to_fig[code] = keep_id
        return moved, left

    for m in plan["merge"]:
        drop_id, keep_id = m["dropId"], m["keepId"]
        drop, keep = by_id.get(drop_id), by_id.get(keep_id)
        if not drop or not keep or drop_id in drop_ids or keep_id in drop_ids:
            problems.append({"merge": [drop_id, keep_id], "problem": "row missing or already dropped"}); continue
        if drop_id in set_parents:
            problems.append({"merge": [drop_id, keep_id], "problem": "drop row is a set parent"}); continue
        if drop_id in untouchable:
            problems.append({"merge": [drop_id, keep_id], "problem": "drop row is listed as correct/unsure"}); continue
        moved, left = move_aliases(drop_id, keep_id)
        image_filled = False
        if drop.get("imageUrl") and not keep.get("imageUrl") and not baked.get(keep_id) and not m.get("noImageFill"):
            keep["imageUrl"] = drop["imageUrl"]; image_filled = True
        ensure_tag(keep, TAG)
        drop_ids.add(drop_id)
        collapsed.append({"keepId": keep_id, "dropId": drop_id, "canonicalSku": keep.get("sku"), "aliasesAdded": moved,
                          "reason": f"Studio Series audit 2026-09-30 (merge): {m['reason']} Sources: {'; '.join(m['sources'])}"})
        merged.append({"dropId": drop_id, "keepId": keep_id, "dropName": drop.get("name"), "dropSubtitle": drop.get("subtitle"),
                       "keepName": keep.get("name"), "ref": m.get("ref"), "aliasesMoved": moved, "aliasesLeftAlone": left,
                       "imageFilled": image_filled})

    out_rows = [r for r in rows if r["id"] not in drop_ids]
    after = integrity(out_rows, to_fig)
    new_dangling = sorted(set(after["danglingAliases"]) - set(before["danglingAliases"]))
    new_dangling_set = sorted(set(after["danglingSetIds"]) - set(before["danglingSetIds"]))
    expected_delta = len(plan["deleteInvented"]) + len(plan["merge"])
    if new_dangling or new_dangling_set or after["duplicateIds"]:
        problems.append({"integrity": "new dangling references or duplicate ids"})
    if len(rows) - len(out_rows) != expected_delta:
        problems.append({"integrity": f"row delta {len(rows) - len(out_rows)} != expected {expected_delta}"})
    stats = {
        "dryRun": dry, "at": datetime.now(timezone.utc).isoformat(),
        "rowsBefore": len(rows), "rowsAfter": len(out_rows), "expectedDelta": expected_delta,
        "fieldChanges": len(fixed), "rowsFixed": len({f["id"] for f in fixed}),
        "inventedDeleted": len(deleted), "merged": len(merged),
        "reportOnly": {"correct": len(plan["correct"]), "unsure": len(plan["unsure"]), "missing": len(plan["missing"]),
                       "flags": len(plan.get("flags", []))},
        "imagesFilled": sum(1 for m in merged if m["imageFilled"]),
        "integrity": {"before": {k: (len(v) if isinstance(v, list) else v) for k, v in before.items()},
                      "after": {k: (len(v) if isinstance(v, list) else v) for k, v in after.items()},
                      "newDanglingAliases": new_dangling, "newDanglingSetIds": new_dangling_set},
        "problems": problems, "fixes": fixed, "deleted": deleted, "merges": merged,
    }
    if not dry and not problems:
        aliases["updatedAt"] = stats["at"]
        aliases.setdefault("stats", {})["studioSeriesAudit"] = {"at": stats["at"], "removed": len(drop_ids),
                                                               "fixes": len(fixed), "invented": len(deleted)}
        ONESHOT.write_text(json.dumps(out_rows, indent=2, ensure_ascii=False) + "\n")
        ALIASES.write_text(json.dumps(aliases, indent=2, ensure_ascii=False) + "\n")
        STATS.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
    elif not dry:
        print("NOT WRITTEN: problems present")
    print(json.dumps({k: v for k, v in stats.items() if k not in ("fixes", "deleted", "merges")}, indent=2))
    for f in fixed:
        print(f"FIX    {f['id'][:40]:40} {f['field']}: {f['old']!r} -> {f['new']!r}")
    for d in deleted:
        print(f"DELETE {d['id'][:40]:40} {d['name']} / {d['subtitle']}")
    for m in merged:
        print(f"MERGE  {m['dropId'][:40]:40} -> {m['keepId'][:40]:40} aliases={len(m['aliasesMoved'])}")


if __name__ == "__main__":
    main()
