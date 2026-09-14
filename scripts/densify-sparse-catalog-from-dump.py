#!/usr/bin/env python3
"""Find catalog series that are missing dump issues (sparse) and print GCD series ids.

Used with ingest-gcd-series-to-catalog.py --series-ids-file.
Cover A (even with artist text) counts as a main. 2020+ first.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("/workspace/collection-app")
sys.path.insert(0, str(ROOT / "scripts"))
import importlib.util


def load_ingest():
    spec = importlib.util.spec_from_file_location(
        "ingest_gcd_series_to_catalog", ROOT / "scripts/ingest-gcd-series-to-catalog.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_catalog(path: Path):
    text = path.read_text()
    pat = re.compile(
        r'\["([^"]+)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*'
        r'"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*([0-9.]+),\s*"([^"]+)",\s*'
        r'([0-9.]+),\s*([0-9]+),\s*"([^"]*)"',
        re.M,
    )
    rows = []
    for m in pat.finditer(text):
        cid, series, issue, publisher, cover_date = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        rest = text[m.end() : m.end() + 400]
        variant = None
        em = re.search(r"\{([^}]*)\}\s*\]", rest)
        if em and "variant" in em.group(1):
            vm = re.search(r'variant:\s*"([^"]+)"', em.group(1))
            if vm:
                variant = vm.group(1)
        rows.append(
            {
                "id": cid,
                "series": series,
                "issue": issue,
                "publisher": publisher,
                "coverDate": cover_date,
                "variant": variant,
            }
        )
    return rows


def pub_norm(p: str) -> str:
    p = re.sub(r"\s+", " ", (p or "").strip().lower())
    p = p.replace("dc comics", "dc").replace("marvel comics", "marvel")
    p = p.replace("image comics", "image").replace("boom! studios", "boom")
    p = p.replace("boom studios", "boom")
    if p.startswith("dc "):
        p = "dc"
    return p


def year_of(row) -> int:
    cd = str(row.get("coverDate") or "")
    if len(cd) >= 4 and cd[:4].isdigit():
        return int(cd[:4])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump-sqlite", default="/workspace/gcd-dump/gcd.sqlite")
    ap.add_argument("--min-year", type=int, default=2020)
    ap.add_argument("--max-catalog-mains", type=int, default=3, help="Treat as sparse if catalog mains <= this")
    ap.add_argument("--out", default="/tmp/sparse-series-ids.txt")
    ap.add_argument("--report", default="/tmp/sparse-series-report.json")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    ingest = load_ingest()
    rows = parse_catalog(ROOT / "src/data/comics.ts")
    families = defaultdict(list)
    for r in rows:
        if year_of(r) and year_of(r) < args.min_year:
            continue
        families[(r["series"], r["publisher"])].append(r)

    conn = sqlite3.connect(args.dump_sqlite)
    conn.row_factory = sqlite3.Row
    dump_series = conn.execute(
        """
        select s.id, s.name, s.year_began, p.name as pub
        from gcd_series s
        join gcd_publisher p on p.id = s.publisher_id
        where coalesce(s.deleted,0)=0 and coalesce(s.year_began,0) >= ?
        """,
        (args.min_year,),
    ).fetchall()
    by_key = defaultdict(list)
    for s in dump_series:
        by_key[(s["name"].strip().lower(), pub_norm(s["pub"]))].append(s)

    sparse = []
    for (series, publisher), members in families.items():
        mains = [m for m in members if not (m.get("variant") or "").strip()]
        if len(mains) > args.max_catalog_mains:
            continue
        hits = by_key.get((series.strip().lower(), pub_norm(publisher))) or []
        if not hits:
            continue
        # prefer year closest to catalog
        cy = max(year_of(m) for m in members)
        hits = sorted(hits, key=lambda s: abs((s["year_began"] or 0) - cy))
        sid = str(hits[0]["id"])
        dump_issues = conn.execute(
            """
            select id, number, variant_of_id, variant_name
            from gcd_issue
            where series_id=? and coalesce(deleted,0)=0
            """,
            (sid,),
        ).fetchall()
        dump_mains = [
            i
            for i in dump_issues
            if ingest.variant_of_id({"variant_of_id": i["variant_of_id"]}) is None
            and ingest.is_cover_a_name(i["variant_name"])
        ]
        if len(dump_mains) <= len(mains):
            continue
        catalog_issues = {str(m["issue"]).lstrip("#") for m in mains}
        dump_issue_nums = {str(i["number"] or "").lstrip("#") for i in dump_mains}
        missing = sorted(dump_issue_nums - catalog_issues, key=lambda x: (len(x), x))
        if not missing:
            continue
        sparse.append(
            {
                "series": series,
                "publisher": publisher,
                "gcdSeriesId": sid,
                "catalogMains": len(mains),
                "dumpMains": len(dump_mains),
                "catalogIssues": sorted(catalog_issues, key=lambda x: (len(x), x)),
                "missingIssues": missing[:20],
                "dumpYear": hits[0]["year_began"],
            }
        )

    sparse.sort(key=lambda r: (r["publisher"], r["series"]))
    if args.limit > 0:
        sparse = sparse[: args.limit]
    ids = [r["gcdSeriesId"] for r in sparse]
    Path(args.out).write_text("\n".join(ids) + ("\n" if ids else ""))
    Path(args.report).write_text(json.dumps({"count": len(sparse), "series": sparse}, indent=2) + "\n")
    print(f"sparse series {len(sparse)} → {args.out}")
    for r in sparse[:15]:
        print(
            f"  {r['gcdSeriesId']}  {r['series']} ({r['publisher']})  "
            f"catalog {r['catalogMains']} dump {r['dumpMains']} missing {r['missingIssues'][:8]}"
        )
    if len(sparse) > 15:
        print(f"  … {len(sparse) - 15} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
