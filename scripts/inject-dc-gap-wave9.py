#!/usr/bin/env python3
"""Inject curated DC gap wave9 into oneshot archive. No Build Publish."""
from __future__ import annotations
import json, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
sys.path.insert(0, str(ROOT / "scripts"))
from figure_oneshot.curated_dc_gap_wave9 import build_dc_gap_wave9

ARCHIVE = ROOT / "src/data/figure-archive/oneshot.json"
STATS = ROOT / "src/data/figure-archive/dc-gap-wave9-inject-stats.json"
SOURCE = "curated-dc-gap-wave9"

def row_key(r: dict) -> str:
    return "|".join([
        (r.get("company") or "").lower(),
        (r.get("line") or "").lower(),
        (r.get("name") or "").lower(),
        (r.get("subtitle") or "").lower(),
    ])

def main() -> None:
    curated = build_dc_gap_wave9()
    rows: list[dict] = json.loads(ARCHIVE.read_text())
    before = len(rows)
    ids = {r["id"] for r in rows}
    keys = {row_key(r) for r in rows}
    added: list[str] = []
    skipped = Counter()
    for r in curated:
        if r["id"] in ids:
            skipped["id"] += 1
            continue
        k = row_key(r)
        if k in keys:
            skipped["key"] += 1
            continue
        r.pop("imageUrl", None)
        r.pop("sku", None)  # never invent GTIN
        rows.append(r)
        ids.add(r["id"])
        keys.add(k)
        added.append(r["id"])
    ARCHIVE.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    added_set = set(added)
    stats = {
        "at": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE,
        "before": before,
        "after": len(rows),
        "raw_curated": len(curated),
        "added": len(added),
        "skipped": dict(skipped),
        "by_line": Counter(r["line"] for r in curated if r["id"] in added_set).most_common(),
        "sample_ids": added[:25],
    }
    STATS.write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
