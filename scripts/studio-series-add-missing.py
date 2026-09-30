#!/usr/bin/env python3
"""Studio Series: add the TFWiki releases missing from the catalog (2026-09-30).

Reads scripts/figure_oneshot/studio-series-missing-plan.json (built from the audit plan's
"missing" list) and appends its rows to src/data/figure-archive/oneshot.json.

Guards (any hit is a problem and nothing is written):
  - new id already used as a row id, an aliasesByFigureId key, an "id:<x>" alias, or a
    removed/dropped id in figure-sku-aliases.json
  - new sku already on a row or in aliasToFigureId
  - name|subtitle|line|company key already present (figures.ts dedupe key)
  - duplicate ids inside the plan
Multipacks are one row each (no setId members), so no member duplicates an existing single.

  python3 scripts/studio-series-add-missing.py            # dry run (default; writes nothing)
  python3 scripts/studio-series-add-missing.py --apply
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
PLAN = ROOT / "scripts/figure_oneshot/studio-series-missing-plan.json"
STATS = ROOT / "src/data/figure-archive/studio-series-missing-stats.json"
BAKED_FILES = [ROOT / "src/data/figure-image-urls.json", ROOT / "src/data/figure-sku-map.json"]


def norm(s: str | None) -> str:
    return (s or "").strip().lower()


def integrity(rows: list[dict], to_fig: dict) -> dict:
    ids = [r["id"] for r in rows]
    idset = set(ids)
    return {
        "rows": len(rows),
        "duplicateIds": len(ids) - len(idset),
        "danglingAliases": sum(1 for v in to_fig.values() if v not in idset),
        "danglingSetIds": sum(1 for r in rows if r.get("setId") and r["setId"] not in idset),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = json.loads(ONESHOT.read_text())
    aliases = json.loads(ALIASES.read_text())
    plan = json.loads(PLAN.read_text())
    to_fig = aliases["aliasToFigureId"]

    used_ids = {r["id"] for r in rows} | set(aliases["aliasesByFigureId"])
    used_ids |= {k[3:] for k in to_fig if k.startswith("id:")}
    used_ids |= {x for rm in aliases.get("removed", []) for x in (rm.get("dropId"), rm.get("keepId")) if x}
    for f in BAKED_FILES:
        if f.exists():
            try:
                used_ids |= set(json.loads(f.read_text()))
            except Exception:
                pass
    used_skus = {norm(r.get("sku")) for r in rows if r.get("sku")} | {norm(k) for k in to_fig}
    used_keys = {norm(f"{r['name']}|{r['subtitle']}|{r['line']}|{r['company']}") for r in rows}

    before = integrity(rows, to_fig)
    problems, seen = [], set()
    for r in plan["rows"]:
        i = r["id"]
        if i in seen:
            problems.append({"id": i, "problem": "duplicate id in plan"})
        seen.add(i)
        if i in used_ids:
            problems.append({"id": i, "problem": "id collides with an existing/aliased/removed id"})
        if r.get("sku") and norm(r["sku"]) in used_skus:
            problems.append({"id": i, "problem": f"sku {r['sku']} already in catalog"})
        k = norm(f"{r['name']}|{r['subtitle']}|{r['line']}|{r['company']}")
        if k in used_keys:
            problems.append({"id": i, "problem": "name|subtitle|line|company already present"})
        used_keys.add(k)
        if r.get("setId") or r.get("setRole"):
            problems.append({"id": i, "problem": "plan rows must not carry setId/setRole"})

    new_rows = rows + ([] if problems else plan["rows"])
    after = integrity(new_rows, to_fig)
    report = {
        "dryRun": not args.apply,
        "at": datetime.now(timezone.utc).isoformat(),
        "rowsBefore": len(rows),
        "rowsAfter": len(new_rows),
        "added": len(plan["rows"]) if not problems else 0,
        "skippedInPlan": len(plan["skipped"]),
        "withSku": sum(1 for r in plan["rows"] if r.get("sku")),
        "withImage": sum(1 for r in plan["rows"] if r.get("imageUrl")),
        "withMsrp": sum(1 for r in plan["rows"] if r.get("msrp")),
        "integrity": {"before": before, "after": after},
        "problems": problems,
    }
    print(json.dumps(report, indent=2))
    if problems:
        raise SystemExit("problems found; nothing written")
    if after["duplicateIds"] or after["danglingAliases"] > before["danglingAliases"] or after["danglingSetIds"] > before["danglingSetIds"]:
        raise SystemExit("integrity regression; nothing written")
    if args.apply:
        ONESHOT.write_text(json.dumps(new_rows, indent=2, ensure_ascii=False) + "\n")
        STATS.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
