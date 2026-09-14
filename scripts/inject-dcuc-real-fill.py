#!/usr/bin/env python3
"""Inject Wikipedia-sourced DCUC real-fill rows into oneshot archive.

Dedupes by id and company|line|name|subtitle. Floor 1980. No AI art.
Does NOT Build Publish Live.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_oneshot.curated_dcuc_real_fill import build_dcuc_real_fill  # noqa: E402

ARCHIVE = ROOT / "src/data/figure-archive/oneshot.json"
STATS = ROOT / "src/data/figure-archive/dcuc-real-fill-inject-stats.json"
SOURCE = "curated-dcuc-real-fill"


def row_key(r: dict) -> str:
    return "|".join(
        [
            (r.get("company") or "").lower(),
            (r.get("line") or "").lower(),
            (r.get("name") or "").lower(),
            (r.get("subtitle") or "").lower(),
        ]
    )


def main() -> None:
    curated = build_dcuc_real_fill()
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
        # never invent imageUrl
        r.pop("imageUrl", None)
        rows.append(r)
        ids.add(r["id"])
        keys.add(k)
        added.append(r["id"])

    ARCHIVE.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    stats = {
        "at": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE,
        "before": before,
        "after": len(rows),
        "raw_curated": len(curated),
        "added": len(added),
        "skipped": dict(skipped),
        "by_line": Counter(r["line"] for r in curated if r["id"] in set(added)).most_common(),
        "sample_ids": added[:20],
    }
    STATS.write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
