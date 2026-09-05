#!/usr/bin/env python3
"""Shared helpers for figure-backlog batch generators and inject."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

FLOOR = "1980-01-01"  # nothing older than this release date

ROOT = Path("/workspace/collection-app")
FIGURES_TS = ROOT / "src/data/figures.ts"
BACKLOG = ROOT / "src/data/figure-backlog"

VALID_COMPANIES = {
    "hasbro",
    "toybiz",
    "mattel",
    "mcfarlane",
    "mafex",
    "mezco",
    "bandai",
    "shfiguarts",
    "neca",
    "super7",
    "hottoys",
    "figma",
    "kotobukiya",
    "storm",
    "bossfight",
    "loyalsubjects",
    "premiumdna",
    "hiya",
    "mondo",
    "threezero",
    "dcdirect",
    "kenner",
}
VALID_KINDS = {"figure", "kit"}


def parse_existing_ts():
    src = FIGURES_TS.read_text()
    id_set, key_set = set(), set()
    for m in re.finditer(
        r'\["([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"',
        src,
    ):
        id_set.add(m.group(1))
        key_set.add(f"{m.group(2)}|{m.group(3)}|{m.group(4)}|{m.group(5)}".lower())
    return id_set, key_set


def parse_batch(path: Path):
    data = json.loads(path.read_text())
    id_set, key_set = set(), set()
    for r in data["rows"]:
        id_set.add(r[0])
        key_set.add(f"{r[1]}|{r[2]}|{r[3]}|{r[4]}".lower())
    return id_set, key_set


def load_blocklists(extra_batches=()):
    ids, keys = parse_existing_ts()
    for name in sorted(BACKLOG.glob("batch-*.json")):
        if name.name in extra_batches or True:
            i, k = parse_batch(name)
            ids |= i
            keys |= k
    return ids, keys


def row_key(row):
    return f"{row[1]}|{row[2]}|{row[3]}|{row[4]}".lower()


def ts_literal(row) -> str:
    """Format a backlog row as a figures.ts Row tuple."""
    rid, name, subtitle, line, company, kind, release, msrp, scale, demand, tags = row[:11]
    extra = row[11] if len(row) > 11 else None
    # Prefer single-quoted scale when it contains a double-quote (e.g. 6")
    if '"' in str(scale):
        scale_lit = "'" + str(scale).replace("'", "\\'") + "'"
    else:
        scale_lit = json.dumps(str(scale))
    parts = [
        json.dumps(rid),
        json.dumps(name),
        json.dumps(subtitle),
        json.dumps(line),
        json.dumps(company),
        json.dumps(kind),
        json.dumps(release),
        str(float(msrp) if isinstance(msrp, (int, float)) else msrp),
        scale_lit,
        str(float(demand) if isinstance(demand, (int, float)) else demand),
        json.dumps(tags),
    ]
    if extra and isinstance(extra, dict) and extra:
        bits = []
        if extra.get("sku"):
            bits.append(f'sku: {json.dumps(extra["sku"])}')
        if extra.get("exclusive"):
            bits.append(f'exclusive: {json.dumps(extra["exclusive"])}')
        if bits:
            parts.append("{ " + ", ".join(bits) + " }")
    return "  [" + ", ".join(parts) + "],"


class BatchBuilder:
    def __init__(self, existing_ids, existing_keys, target_min=180, target_max=250):
        self.existing_ids = existing_ids
        self.existing_keys = existing_keys
        self.target_min = target_min
        self.target_max = target_max
        self.rows = []
        self.used_ids = set()
        self.used_keys = set()
        self.skipped = []

    def room(self, n=1):
        return len(self.rows) + n <= self.target_max

    def try_add(
        self,
        rid,
        name,
        subtitle,
        line,
        company,
        release_date,
        msrp,
        scale='6"',
        demand=1.0,
        tags="",
        kind="figure",
        extra=None,
        force=False,
    ):
        if company not in VALID_COMPANIES:
            self.skipped.append({"reason": "company", "id": rid, "company": company})
            return False
        if kind not in VALID_KINDS:
            self.skipped.append({"reason": "kind", "id": rid, "kind": kind})
            return False
        if not force and not self.room():
            self.skipped.append({"reason": "full", "id": rid, "name": name})
            return False
        if rid in self.existing_ids or rid in self.used_ids:
            self.skipped.append({"reason": "id", "id": rid, "name": name})
            return False
        skey = f"{name}|{subtitle}|{line}|{company}".lower()
        if skey in self.existing_keys or skey in self.used_keys:
            self.skipped.append({"reason": "key", "id": rid, "name": name})
            return False
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", release_date):
            self.skipped.append({"reason": "date", "id": rid, "date": release_date})
            return False
        row = [
            rid,
            name,
            subtitle,
            line,
            company,
            kind,
            release_date,
            float(msrp),
            scale,
            float(demand),
            tags,
        ]
        if extra:
            row.append(extra)
        self.rows.append(row)
        self.used_ids.add(rid)
        self.used_keys.add(skey)
        return True

    def finalize(self):
        self.rows.sort(key=lambda r: (r[6], r[4], r[1], r[2]), reverse=True)
        assert len({r[0] for r in self.rows}) == len(self.rows)
        for r in self.rows:
            assert r[0] not in self.existing_ids
            assert r[4] in VALID_COMPANIES
            assert r[5] in VALID_KINDS

    def report(self):
        c = Counter(r[3] for r in self.rows)
        cos = Counter(r[4] for r in self.rows)
        dates = [r[6] for r in self.rows]
        print("FINAL_COUNT", len(self.rows))
        print("DATE_RANGE", max(dates) if dates else None, "→", min(dates) if dates else None)
        print("TOTAL_SKIPPED", len(self.skipped))
        print("BY_LINE")
        for k, v in c.most_common():
            print(f"  {k}: {v}")
        print("BY_COMPANY")
        for k, v in cos.most_common():
            print(f"  {k}: {v}")
        return {
            "count": len(self.rows),
            "date_max": max(dates) if dates else None,
            "date_min": min(dates) if dates else None,
            "total_skipped": len(self.skipped),
            "by_line": c.most_common(),
            "by_company": cos.most_common(),
        }

    def write(self, batch_id, title, focus, created="2026-09-05", status="queued"):
        out = BACKLOG / f"{batch_id}.json"
        batch = {
            "id": batch_id,
            "title": title,
            "created": created,
            "status": status,
            "focus": focus,
            "rows": self.rows,
        }
        out.write_text(json.dumps(batch, indent=2) + "\n")
        return out


def inject_batch(batch_id: str, comment: str | None = None) -> int:
    """Merge a backlog batch into figures.ts rows array. Returns injected count."""
    path = BACKLOG / f"{batch_id}.json"
    batch = json.loads(path.read_text())
    if batch.get("status") == "injected":
        raise SystemExit(f"{batch_id} already injected")

    existing_ids, existing_keys = parse_existing_ts()
    lines = []
    added = 0
    for row in batch["rows"]:
        if row[0] in existing_ids:
            continue
        skey = row_key(row)
        if skey in existing_keys:
            continue
        lines.append(ts_literal(row))
        existing_ids.add(row[0])
        existing_keys.add(skey)
        added += 1

    if not added:
        raise SystemExit("nothing to inject")

    src = FIGURES_TS.read_text()
    marker = "];\n\nexport const FIGURES"
    if marker not in src:
        raise SystemExit("figures.ts marker not found")
    hdr = comment or f"Injected from figure backlog ({batch_id})"
    block = f"\n  // {hdr}\n" + "\n".join(lines) + "\n"
    FIGURES_TS.write_text(src.replace(marker, block + marker, 1))

    batch["status"] = "injected"
    path.write_text(json.dumps(batch, indent=2) + "\n")

    manifest_path = BACKLOG / "manifest.json"
    if manifest_path.exists():
        man = json.loads(manifest_path.read_text())
    else:
        man = {
            "strategy": "inject-one-batch-every-~3-weeks-with-noteworthy-promotion",
            "targetBatchSize": [180, 250],
            "queued": [],
            "injected": [],
        }
    queued = [b for b in man.get("queued", []) if b != batch_id]
    injected = list(man.get("injected", []))
    if batch_id not in injected:
        injected.append(batch_id)
    man["queued"] = queued
    man["injected"] = injected
    man["lastInjectedAt"] = batch.get("created", "2026-09-05")
    man["lastInjectedBatch"] = batch_id
    man["targetBatchSize"] = man.get("targetBatchSize") or [180, 250]
    man["strategy"] = man.get("strategy") or "inject-one-batch-every-~3-weeks-with-noteworthy-promotion"
    manifest_path.write_text(json.dumps(man, indent=2) + "\n")
    return added


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3 and sys.argv[1] == "inject":
        n = inject_batch(sys.argv[2])
        print(f"injected {n} rows from {sys.argv[2]}")
    else:
        ids, keys = parse_existing_ts()
        print(f"figures.ts ids={len(ids)} keys={len(keys)}")
