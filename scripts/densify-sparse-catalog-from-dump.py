#!/usr/bin/env python3
"""Find catalog series that are missing dump issues (sparse) and print GCD series ids.

Used with ingest-gcd-series-to-catalog.py --series-ids-file.

Linkage is via catalog gcdIssueId → dump gcd_issue.series_id (not publisher-name
matching). Cover A (even with artist text) counts as a dump main. Default focus:
2020+ families with at most 2 catalog Cover-A mains (1–2 issue sparse series).
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
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


def load_upc_gcd_map(path: Path) -> dict[str, str]:
    """catalog id → gcdIssueId from comic-upc-map.json (fallback)."""
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text())
    out: dict[str, str] = {}
    if not isinstance(raw, dict):
        return out
    for cid, ent in raw.items():
        if not isinstance(ent, dict):
            continue
        gid = ent.get("gcdIssueId") or ent.get("sourceId")
        if gid is not None and str(gid).isdigit():
            out[str(cid)] = str(gid)
    return out


def parse_catalog(path: Path, upc_gid: dict[str, str]):
    text = path.read_text()
    pat = re.compile(
        r'\["([^"]+)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*'
        r'"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*([0-9.]+),\s*"([^"]+)",\s*'
        r'([0-9.]+),\s*([0-9]+),\s*"([^"]*)"',
        re.M,
    )
    rows = []
    for m in pat.finditer(text):
        cid, series, issue, publisher, cover_date = (
            m.group(1),
            m.group(2),
            m.group(3),
            m.group(4),
            m.group(5),
        )
        rest = text[m.end() : m.end() + 500]
        variant = None
        gid = None
        em = re.search(r"\{([^}]*)\}\s*\]", rest)
        if em:
            body = em.group(1)
            vm = re.search(r'variant:\s*"([^"]+)"', body)
            if vm:
                variant = vm.group(1)
            gm = re.search(r'gcdIssueId:\s*"(\d+)"', body)
            if gm:
                gid = gm.group(1)
        if not gid:
            gid = upc_gid.get(cid)
        rows.append(
            {
                "id": cid,
                "series": series,
                "issue": issue,
                "publisher": publisher,
                "coverDate": cover_date,
                "variant": variant,
                "gcdIssueId": gid,
            }
        )
    return rows


def year_of(row) -> int:
    cd = str(row.get("coverDate") or "")
    if len(cd) >= 4 and cd[:4].isdigit():
        return int(cd[:4])
    return 0


def resolve_gid_to_series(conn: sqlite3.Connection, gids: list[str]) -> dict[str, str]:
    """gcdIssueId → dump series_id."""
    out: dict[str, str] = {}
    uniq = sorted({g for g in gids if g and str(g).isdigit()})
    for i in range(0, len(uniq), 900):
        batch = uniq[i : i + 900]
        q = (
            f"select id, series_id from gcd_issue "
            f"where id in ({','.join('?' * len(batch))}) and coalesce(deleted,0)=0"
        )
        for row in conn.execute(q, batch):
            out[str(row["id"])] = str(row["series_id"])
    return out


def dump_cover_a_mains(conn: sqlite3.Connection, ingest, series_id: str, cache: dict):
    if series_id in cache:
        return cache[series_id]
    dump_issues = conn.execute(
        """
        select id, number, variant_of_id, variant_name
        from gcd_issue
        where series_id=? and coalesce(deleted,0)=0
        """,
        (series_id,),
    ).fetchall()
    mains = [
        i
        for i in dump_issues
        if ingest.variant_of_id({"variant_of_id": i["variant_of_id"]}) is None
        and ingest.is_cover_a_name(i["variant_name"])
    ]
    cache[series_id] = mains
    return mains


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump-sqlite", default="/workspace/gcd-dump/gcd.sqlite")
    ap.add_argument("--min-year", type=int, default=2020)
    ap.add_argument(
        "--max-catalog-mains",
        type=int,
        default=2,
        help="Treat as sparse if catalog Cover-A mains <= this (default 2)",
    )
    ap.add_argument("--out", default="/tmp/sparse-series-ids.txt")
    ap.add_argument("--report", default="/tmp/sparse-series-report.json")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument(
        "--comics-ts",
        default=str(ROOT / "src/data/comics.ts"),
    )
    ap.add_argument(
        "--upc-map",
        default=str(ROOT / "src/data/comic-upc-map.json"),
    )
    args = ap.parse_args()

    ingest = load_ingest()
    upc_gid = load_upc_gcd_map(Path(args.upc_map))
    rows = parse_catalog(Path(args.comics_ts), upc_gid)

    families: dict[tuple[str, str], list] = defaultdict(list)
    for r in rows:
        y = year_of(r)
        if y and y < args.min_year:
            continue
        families[(r["series"], r["publisher"])].append(r)

    candidates = []
    all_gids: set[str] = set()
    for key, members in families.items():
        mains = [m for m in members if not (m.get("variant") or "").strip()]
        if len(mains) > args.max_catalog_mains:
            continue
        gids = [m["gcdIssueId"] for m in members if m.get("gcdIssueId")]
        if not gids:
            continue
        candidates.append((key, members, mains, gids))
        all_gids.update(gids)

    conn = sqlite3.connect(args.dump_sqlite)
    conn.row_factory = sqlite3.Row
    gid_to_sid = resolve_gid_to_series(conn, list(all_gids))

    dump_cache: dict = {}
    by_sid: dict[str, dict] = {}
    multi_sid_families = 0
    for (series, publisher), members, mains, gids in candidates:
        linked = [gid_to_sid[g] for g in gids if g in gid_to_sid]
        if not linked:
            continue
        sids = set(linked)
        if len(sids) > 1:
            multi_sid_families += 1
        catalog_issues = {str(m["issue"]).lstrip("#") for m in mains}
        for sid in sids:
            dump_mains = dump_cover_a_mains(conn, ingest, sid, dump_cache)
            dump_issue_nums = {str(i["number"] or "").lstrip("#") for i in dump_mains}
            # Dump Cover-A mains have more issue numbers than catalog Cover-A
            if len(dump_issue_nums) <= len(catalog_issues):
                continue
            missing = sorted(dump_issue_nums - catalog_issues, key=lambda x: (len(x), x))
            if not missing:
                continue
            score = (len(missing), len(dump_issue_nums), -len(catalog_issues))
            prev = by_sid.get(sid)
            if prev and prev.get("_score", ()) >= score:
                continue
            # Prefer the catalog family that contributed the most links to this sid
            link_count = sum(1 for s in linked if s == sid)
            by_sid[sid] = {
                "series": series,
                "publisher": publisher,
                "gcdSeriesId": sid,
                "catalogMains": len(mains),
                "dumpMains": len(dump_mains),
                "dumpIssueNumbers": len(dump_issue_nums),
                "catalogIssues": sorted(catalog_issues, key=lambda x: (len(x), x)),
                "missingIssues": missing[:20],
                "linkedGcdIssueIds": link_count,
                "dumpYear": conn.execute(
                    "select year_began from gcd_series where id=?", (sid,)
                ).fetchone()["year_began"],
                "_score": score,
            }

    sparse = list(by_sid.values())
    for r in sparse:
        r.pop("_score", None)
    sparse.sort(key=lambda r: (r["publisher"], r["series"], r["gcdSeriesId"]))
    if args.limit > 0:
        sparse = sparse[: args.limit]

    ids = [r["gcdSeriesId"] for r in sparse]
    Path(args.out).write_text("\n".join(ids) + ("\n" if ids else ""))
    report = {
        "count": len(sparse),
        "minYear": args.min_year,
        "maxCatalogMains": args.max_catalog_mains,
        "candidateFamilies": len(candidates),
        "resolvedGcdIssueIds": len(gid_to_sid),
        "multiSidFamilies": multi_sid_families,
        "linkage": "gcdIssueId→dump.series_id",
        "series": sparse,
    }
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
    print(f"sparse series {len(sparse)} → {args.out}")
    for r in sparse[:15]:
        print(
            f"  {r['gcdSeriesId']}  {r['series']} ({r['publisher']})  "
            f"catalog {r['catalogMains']} dumpNums {r['dumpIssueNumbers']} "
            f"missing {r['missingIssues'][:8]}"
        )
    if len(sparse) > 15:
        print(f"  … {len(sparse) - 15} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
