#!/usr/bin/env python3
"""Shared helpers for comic-backlog batch generators and inject."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/collection-app")
COMICS_TS = ROOT / "src/data/comics.ts"
BACKLOG = ROOT / "src/data/comic-backlog"
# Permanent archive release/cover floor — nothing older than this date.
FLOOR = "1980-01-01"

def parse_existing_ts():
    src = COMICS_TS.read_text()
    id_set, key_set = set(), set()
    for m in re.finditer(r'\["([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"', src):
        id_set.add(m.group(1))
        key_set.add(f"{m.group(2)}|{m.group(3)}|{m.group(4)}".lower())
    return id_set, key_set

def parse_batch(path: Path):
    data = json.loads(path.read_text())
    id_set, key_set = set(), set()
    for r in data["rows"]:
        id_set.add(r[0])
        key_set.add(f"{r[1]}|{r[2]}|{r[3]}".lower())
    return id_set, key_set

def load_blocklists(extra_batches=()):
    """Block against comics.ts + all backlog batch-*.json (and any extras)."""
    ids, keys = parse_existing_ts()
    names = {p.name for p in BACKLOG.glob("batch-*.json")}
    names.update(extra_batches)
    for name in sorted(names):
        p = BACKLOG / name
        if p.exists():
            i, k = parse_batch(p)
            ids |= i
            keys |= k
    return ids, keys

def add_months(y, m, n):
    m0 = y * 12 + (m - 1) + n
    return m0 // 12, m0 % 12 + 1

def cover(y, m, day=1):
    return f"{y:04d}-{m:02d}-{day:02d}"

def interp_date(n, n0, y0, m0, n1, y1, m1):
    if n1 == n0:
        return cover(y0, m0)
    t = (n - n0) / (n1 - n0)
    months0 = y0 * 12 + (m0 - 1)
    months1 = y1 * 12 + (m1 - 1)
    mid = int(round(months0 + t * (months1 - months0)))
    return cover(mid // 12, mid % 12 + 1)

def row_key(row):
    return f"{row[1]}|{row[2]}|{row[3]}".lower()

def ts_literal(row) -> str:
    """Format a backlog row as a comics.ts Row tuple."""
    rid, series, issue, pub, cover_date, writers, artists, desc, msrp, fmt, demand, key, palette = row[:13]
    extra = row[13] if len(row) > 13 else None
    parts = [
        json.dumps(rid),
        json.dumps(series),
        json.dumps(str(issue)),
        json.dumps(pub),
        json.dumps(cover_date),
        json.dumps(writers),
        json.dumps(artists),
        json.dumps(desc),
        str(float(msrp)),
        json.dumps(fmt),
        str(float(demand)),
        str(int(key)),
        json.dumps(palette),
    ]
    if extra and isinstance(extra, dict) and extra:
        bits = []
        for k in ("variant", "upc", "streetDate", "cover"):
            if extra.get(k):
                bits.append(f"{k}: {json.dumps(extra[k])}")
        if bits:
            parts.append("{ " + ", ".join(bits) + " }")
    return "  [" + ", ".join(parts) + "],"


class BatchBuilder:
    def __init__(self, pub, palette, existing_ids, existing_keys, target_min=450, target_max=500):
        self.pub = pub
        self.palette = palette
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

    def try_add(self, rid, series, issue, cover_date, writers, artists, desc, msrp,
                fmt="single", demand=0.6, key=0, palette=None, also_block_bare=None,
                force=False):
        issue = str(issue)
        pub = self.pub
        skey = f"{series}|{issue}|{pub}".lower()
        if not force and not self.room():
            self.skipped.append({"reason": "full", "id": rid, "series": series, "issue": issue})
            return False
        if rid in self.existing_ids or rid in self.used_ids:
            self.skipped.append({"reason": "id", "id": rid, "series": series, "issue": issue})
            return False
        if skey in self.existing_keys:
            self.skipped.append({"reason": "archive-key", "id": rid, "series": series, "issue": issue})
            return False
        if also_block_bare:
            bare = f"{also_block_bare}|{issue}|{pub}".lower()
            if bare in self.existing_keys:
                self.skipped.append({"reason": "archive-bare", "id": rid, "series": series, "issue": issue})
                return False
        if skey in self.used_keys:
            self.skipped.append({"reason": "batch-key", "id": rid, "series": series, "issue": issue})
            return False
        if cover_date < FLOOR:
            self.skipped.append({"reason": "pre-floor", "id": rid, "series": series, "issue": issue, "date": cover_date})
            return False
        self.rows.append([
            rid, series, issue, pub, cover_date, writers, artists, desc,
            float(msrp), fmt, float(demand), int(key), palette or self.palette,
        ])
        self.used_ids.add(rid)
        self.used_keys.add(skey)
        return True

    def add_range(self, id_prefix, series, issues, date_fn, writers, artists, desc_fn,
                  msrp_fn=lambda n: 3.99, demand_fn=lambda n: 0.55, key_fn=lambda n: 0,
                  also_block_bare=None, force=False, artist_fn=None, writer_fn=None):
        for n in issues:
            w = writer_fn(n) if writer_fn else writers
            a = artist_fn(n) if artist_fn else artists
            self.try_add(
                f"{id_prefix}-{n}", series, n, date_fn(n), w, a, desc_fn(n),
                msrp_fn(n), demand=demand_fn(n), key=key_fn(n),
                also_block_bare=also_block_bare, force=force,
            )

    def finalize(self, priority_series=None):
        priority_series = priority_series or set()
        while len(self.rows) > self.target_max:
            cands = [i for i, r in enumerate(self.rows)
                     if r[1] not in priority_series and r[11] == 0]
            if not cands:
                cands = [i for i, r in enumerate(self.rows) if r[11] == 0]
            if not cands:
                break
            drop_i = min(cands, key=lambda i: self.rows[i][4])
            self.skipped.append({"reason": "cap", "id": self.rows[drop_i][0],
                                 "series": self.rows[drop_i][1], "issue": self.rows[drop_i][2]})
            self.rows.pop(drop_i)
        self.rows.sort(key=lambda r: (r[4], r[1], int(re.sub(r"\D", "", str(r[2])) or 0)), reverse=True)
        assert len({r[0] for r in self.rows}) == len(self.rows)
        for r in self.rows:
            assert r[0] not in self.existing_ids
            assert re.match(r"^\d{4}-\d{2}-\d{2}$", r[4])
            assert r[4] >= FLOOR, f"pre-floor {r}"
            assert r[9] in ("single", "facsimile", "tpb", "hardcover", "omnibus")
            assert r[3] == self.pub or r[3].startswith(self.pub + " /") or "Comics" in r[3] or "/" in r[3]

    def report(self):
        c = Counter(r[1] for r in self.rows)
        dates = [r[4] for r in self.rows]
        archive_skips = [s for s in self.skipped if s["reason"] in ("id", "archive-key", "archive-known", "archive-bare")]
        print("FINAL_COUNT", len(self.rows))
        print("DATE_RANGE", max(dates) if dates else None, "→", min(dates) if dates else None)
        print("ARCHIVE_SKIPPED", len(archive_skips))
        print("TOTAL_SKIPPED", len(self.skipped))
        print("BREAKDOWN")
        for k, v in c.most_common():
            print(f"  {k}: {v}")
        return {
            "count": len(self.rows),
            "date_max": max(dates) if dates else None,
            "date_min": min(dates) if dates else None,
            "archive_skipped": len(archive_skips),
            "total_skipped": len(self.skipped),
            "breakdown": c.most_common(),
        }

    def write(self, batch_id, title, focus, created="2026-09-05"):
        out = BACKLOG / f"{batch_id}.json"
        batch = {
            "id": batch_id,
            "title": title,
            "created": created,
            "status": "queued",
            "focus": focus,
            "rows": self.rows,
            "conventions": {
                "floor": FLOOR,
                "dates": "Approximate cover dates interpolated between known issue anchors; monthly unless noted.",
                "numbering": "Real published issue numbers; Action Comics skips unpublished 905–956 (New 52 used Vol. 2).",
                "covers": "Palette placeholders only in this batch; Comic Vine covers resolved at runtime when key available.",
            },
        }
        out.write_text(json.dumps(batch, indent=2) + "\n")
        return out


def inject_batch(batch_id: str, comment: str | None = None) -> int:
    """Merge a backlog batch into comics.ts rows array. Returns injected count."""
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

    src = COMICS_TS.read_text()
    marker = "];\n\nfunction pal"
    if marker not in src:
        raise SystemExit("comics.ts marker not found")
    hdr = comment or f"Injected from comic backlog ({batch_id}; floor {FLOOR})"
    block = f"\n  // {hdr}\n" + "\n".join(lines) + "\n"
    COMICS_TS.write_text(src.replace(marker, block + marker, 1))

    batch["status"] = "injected"
    path.write_text(json.dumps(batch, indent=2) + "\n")

    manifest_path = BACKLOG / "manifest.json"
    if manifest_path.exists():
        man = json.loads(manifest_path.read_text())
    else:
        man = {
            "strategy": "mass-inject-allowed; legacy cadence was ~3 weeks",
            "targetBatchSize": [400, 500],
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
    man["floor"] = FLOOR
    man["strategy"] = man.get("strategy") or "mass-inject-allowed; legacy cadence was ~3 weeks"
    manifest_path.write_text(json.dumps(man, indent=2) + "\n")
    return added


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "inject":
        n = inject_batch(sys.argv[2])
        print(f"injected {n} rows from {sys.argv[2]}")
    else:
        ids, keys = parse_existing_ts()
        print(f"comics.ts ids={len(ids)} keys={len(keys)} FLOOR={FLOOR}")
