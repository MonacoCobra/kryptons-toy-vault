#!/usr/bin/env python3
"""Showzstore follow-up: researched merges, name/code fixes and invented-row deletions.

Reads scripts/figure_oneshot/showz-followup-plan.json (built from the 2026-09-30 review of
the 134 medium/low Showzstore pairs; every action carries a reason and its sources).

Order of operations:
  1. fixes          - field corrections on proper rows (only if the current value == plan "old")
  2. deleteInvented - remove curated rows whose product does not exist (logged in aliases "removed",
                      same shape as the date-audit removals; aliases that pointed at them are dropped)
  3. pairs/merge    - drop the Showzstore row into the proper keeper (keeper msrp/date/sku/name untouched;
                      aliases + id:<dropId> moved; image copied only if keeper has none)
  4. pairs/mergeStub- drop a code-only curated stub into the named Showzstore row; carry the stub's
                      sku/aliases only. Stub msrp/demand are template values and are NOT carried;
                      the keeper msrp is set to 0 (unknown).
  keepBoth / unsure pairs are report-only.

  python3 scripts/showz-followup-fixes.py            # dry run (default)
  python3 scripts/showz-followup-fixes.py --apply
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
BAKED_IMAGES = ROOT / "src/data/figure-image-urls.json"
PLAN = ROOT / "scripts/figure_oneshot/showz-followup-plan.json"
STATS = ROOT / "src/data/figure-archive/showz-followup-stats.json"
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
    return out


def integrity(rows: list[dict], to_fig: dict) -> dict:
    ids = [r["id"] for r in rows]
    idset = set(ids)
    dup = [i for i, c in Counter(ids).items() if c > 1]
    dangling_alias = sorted(k for k, v in to_fig.items() if v not in idset)
    dangling_set = sorted(r["id"] for r in rows if r.get("setId") and r["setId"] not in idset)
    return {"rows": len(rows), "duplicateIds": dup, "danglingAliases": dangling_alias, "danglingSetIds": dangling_set}


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
    removed = aliases.setdefault("removed", [])
    before = integrity(rows, to_fig)

    problems, fixed, deleted, merged = [], [], [], []
    drop_ids: set[str] = set()

    # 1. fixes
    for f in plan["fixes"]:
        r = by_id.get(f["id"])
        if not r:
            problems.append({"fix": f["id"], "problem": "row missing"}); continue
        if r.get(f["field"]) != f["old"]:
            problems.append({"fix": f["id"], "problem": f"{f['field']} is {r.get(f['field'])!r}, plan expects {f['old']!r}"}); continue
        r[f["field"]] = f["new"]
        ensure_tag(r, "fix:showz-followup")
        fixed.append({"id": f["id"], "field": f["field"], "old": f["old"], "new": f["new"]})

    # 2. invented rows
    for dl in plan["deleteInvented"]:
        i = dl["id"]
        r = by_id.get(i)
        if not r:
            problems.append({"delete": i, "problem": "row missing"}); continue
        if r.get("source") in SHOWZ_SOURCES:
            problems.append({"delete": i, "problem": "refusing to delete a Showzstore row as invented"}); continue
        if any(x.get("setId") == i for x in rows):
            problems.append({"delete": i, "problem": "row is a set parent"}); continue
        dropped = list(by_fig.pop(i, []) or [])
        for code, owner in list(to_fig.items()):
            if owner == i:
                if code not in dropped:
                    dropped.append(code)
                del to_fig[code]
        drop_ids.add(i)
        removed.append({"keepId": None, "dropId": i, "canonicalSku": r.get("sku"), "aliasesAdded": [],
                        "aliasesMoved": {}, "aliasesDropped": dropped,
                        "reason": f"Showz follow-up 2026-09-30: {dl['reason']} Sources: {'; '.join(dl['sources'])}"})
        deleted.append({"id": i, "name": r.get("name"), "subtitle": r.get("subtitle"), "aliasesDropped": dropped})

    # 3/4. merges
    def move_aliases(drop_id: str, keep_id: str, extra: list[str]) -> tuple[list, list]:
        codes = list(by_fig.get(drop_id) or [])
        for code, owner in to_fig.items():
            if owner == drop_id and code not in codes:
                codes.append(code)
        for c in extra + [f"id:{drop_id}"]:
            if c not in codes:
                codes.append(c)
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
        return moved, left

    for p in plan["pairs"]:
        if p["action"] not in ("merge", "mergeStub"):
            continue
        drop_id, keep_id = p["dropId"], p["keepId"]
        drop, keep = by_id.get(drop_id), by_id.get(keep_id)
        if not drop or not keep or drop_id in drop_ids or keep_id in drop_ids:
            problems.append({"pair": [drop_id, keep_id], "problem": "row missing or already dropped"}); continue
        if any(x.get("setId") == drop_id for x in rows):
            problems.append({"pair": [drop_id, keep_id], "problem": "drop row is a set parent"}); continue
        if p["action"] == "merge":
            if drop.get("source") not in SHOWZ_SOURCES or keep.get("source") in SHOWZ_SOURCES:
                problems.append({"pair": [drop_id, keep_id], "problem": "merge expects Showz drop -> proper keep"}); continue
            sids = showz_ids(drop)
            for t in ["src:showzstore", *[f"showz:{s}" for s in sids]]:
                ensure_tag(keep, t)
            moved, left = move_aliases(drop_id, keep_id, [f"SHOWZ{s}" for s in sids])
            image_filled = False
            if drop.get("imageUrl") and not keep.get("imageUrl") and not baked.get(keep_id):
                keep["imageUrl"] = drop["imageUrl"]; ensure_tag(keep, "img:showzstore"); image_filled = True
            carried = {}
        else:  # mergeStub: proper stub -> named Showz row
            if drop.get("source") in SHOWZ_SOURCES or keep.get("source") not in SHOWZ_SOURCES:
                problems.append({"pair": [drop_id, keep_id], "problem": "mergeStub expects proper stub -> Showz keep"}); continue
            # Stub msrp/demand are flat template values ($110 every MX, $75 every K) -> not carried
            # (Shelby, 2026-09-30). MSRP stays 0 = unknown until a sourced price exists.
            carried = {}
            if drop.get("sku") not in (None, "") and not keep.get("sku"):
                carried["sku"] = {"from": keep.get("sku"), "to": drop["sku"]}
                keep["sku"] = drop["sku"]
            if keep.get("msrp") not in (0, 0.0, None):
                carried["msrp"] = {"from": keep.get("msrp"), "to": 0.0}
            keep["msrp"] = 0.0
            ensure_tag(keep, f"stub-merged:{drop_id}")
            moved, left = move_aliases(drop_id, keep_id, [])
            image_filled = False
        drop_ids.add(drop_id)
        collapsed.append({"keepId": keep_id, "dropId": drop_id, "canonicalSku": keep.get("sku"), "aliasesAdded": moved,
                          "reason": f"Showz follow-up 2026-09-30 ({p['action']}): {p['reason']}"})
        merged.append({"action": p["action"], "dropId": drop_id, "keepId": keep_id, "dropName": drop.get("name"),
                       "keepName": keep.get("name"), "keepMsrp": keep.get("msrp"), "droppedMsrp": drop.get("msrp"),
                       "carried": carried, "aliasesMoved": moved, "aliasesLeftAlone": left, "imageFilled": image_filled})

    out_rows = [r for r in rows if r["id"] not in drop_ids]
    after = integrity(out_rows, to_fig)
    new_dangling = sorted(set(after["danglingAliases"]) - set(before["danglingAliases"]))
    new_dangling_set = sorted(set(after["danglingSetIds"]) - set(before["danglingSetIds"]))
    report_only = Counter(p["action"] for p in plan["pairs"] if p["action"] in ("keepBoth", "unsure"))
    stats = {
        "dryRun": dry, "at": datetime.now(timezone.utc).isoformat(),
        "rowsBefore": len(rows), "rowsAfter": len(out_rows),
        "fixesApplied": len(fixed), "inventedDeleted": len(deleted),
        "merged": sum(1 for m in merged if m["action"] == "merge"),
        "stubMerged": sum(1 for m in merged if m["action"] == "mergeStub"),
        "reportOnly": dict(report_only),
        "imagesFilled": sum(1 for m in merged if m["imageFilled"]),
        "integrity": {"before": {k: (len(v) if isinstance(v, list) else v) for k, v in before.items()},
                      "after": {k: (len(v) if isinstance(v, list) else v) for k, v in after.items()},
                      "newDanglingAliases": new_dangling, "newDanglingSetIds": new_dangling_set},
        "problems": problems, "fixes": fixed, "deleted": deleted, "merges": merged,
    }
    if new_dangling or new_dangling_set or after["duplicateIds"]:
        problems.append({"integrity": "new dangling references or duplicate ids; not writing"})
    if not dry and not problems:
        aliases["updatedAt"] = stats["at"]
        aliases.setdefault("stats", {})["showzFollowup"] = {"at": stats["at"], "removed": len(drop_ids),
                                                           "fixes": len(fixed), "invented": len(deleted)}
        ONESHOT.write_text(json.dumps(out_rows, indent=2, ensure_ascii=False) + "\n")
        ALIASES.write_text(json.dumps(aliases, indent=2, ensure_ascii=False) + "\n")
        STATS.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
    elif not dry:
        print("NOT WRITTEN: problems present")
    print(json.dumps({k: v for k, v in stats.items() if k not in ("fixes", "deleted", "merges")}, indent=2))
    for f in fixed:
        print(f"FIX    {f['id'][:40]:40} {f['field']}: {f['old']!r} -> {f['new']!r}")
    for dl in deleted:
        print(f"DELETE {dl['id'][:40]:40} {dl['name']} / {dl['subtitle']}")
    for m in merged:
        print(f"{m['action'].upper():9} {m['dropName'][:50]:50} -> {m['keepId'][:52]:52} carried={list(m['carried'])} aliases={len(m['aliasesMoved'])}")


if __name__ == "__main__":
    main()
