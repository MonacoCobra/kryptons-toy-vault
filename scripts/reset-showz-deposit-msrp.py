#!/usr/bin/env python3
"""Reset Showzstore rows whose msrp is really a pre-order deposit back to 0 (unknown).

Showzstore pre-order cards show "Dep. $10.00 / Full Unknown". The 2026-09-23 crawl
took that deposit as price_usd and inject-showzstore-3p-official.py stored it as msrp,
so the synthetic market price showed ~$8-10 (or the $4 floor) for $150+ figures.

Rows come from scripts/figure_oneshot/showz-deposit-msrp-reset.json. A row is only
touched if it is still a Showzstore row and its msrp still equals the deposit.
The same items in showzstore_3p_official_catalog.json get msrp 0 too.

  python3 scripts/reset-showz-deposit-msrp.py            # dry run
  python3 scripts/reset-showz-deposit-msrp.py --apply
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
CATALOG = ROOT / "scripts/figure_oneshot/showzstore_3p_official_catalog.json"
LIST = ROOT / "scripts/figure_oneshot/showz-deposit-msrp-reset.json"
STATS = ROOT / "src/data/figure-archive/showz-deposit-msrp-reset-stats.json"
SHOWZ_SOURCES = {"inject-showzstore-3p-official", "inject-showzstore-unbranded"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    dry = not ap.parse_args().apply

    rows = json.loads(ONESHOT.read_text())
    catalog = json.loads(CATALOG.read_text())
    want = json.loads(LIST.read_text())["rows"]
    by_id = {r["id"]: r for r in rows}

    reset, gone, skipped = [], [], []
    for item in want:
        row = by_id.get(item["id"])
        if row is None:
            gone.append(item["id"])  # merged away by dedupe-showzstore-figures.py
            continue
        if row.get("source") not in SHOWZ_SOURCES or abs(float(row.get("msrp") or 0) - float(item["msrpWas"])) > 0.001:
            skipped.append({"id": item["id"], "msrpNow": row.get("msrp"), "source": row.get("source")})
            continue
        row["msrp"] = 0.0
        reset.append({"id": item["id"], "msrpWas": item["msrpWas"]})

    showz_ids = {str(i["showzId"]) for i in want if i.get("showzId")}
    cat_reset = 0
    for it in catalog.get("items") or []:
        if str(it.get("showzId")) in showz_ids and it.get("msrp"):
            it["msrp"] = 0.0
            cat_reset += 1

    stats = {
        "dryRun": dry,
        "at": datetime.now(timezone.utc).isoformat(),
        "listed": len(want),
        "reset": len(reset),
        "alreadyRemovedByDedupe": gone,
        "skipped": skipped,
        "catalogItemsReset": cat_reset,
        "rows": reset,
    }
    if not dry:
        ONESHOT.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
        CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
        STATS.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in stats.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
