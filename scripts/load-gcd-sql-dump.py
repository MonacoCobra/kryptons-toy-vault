#!/usr/bin/env python3
"""Load official GCD MySQL dump → working sqlite (OFFLINE, no comics.org).

Does not start MySQL/MariaDB. sqlite is the in-repo working copy the catalog
importer reads. If you already imported the dump into MySQL, export
gcd_publisher / gcd_series / gcd_issue or convert with this helper.

Glyph box (LIVE — 2026-09-01):
  zip:    /workspace/gcd-dump/gcd-dump.zip
  sql:    /workspace/gcd-dump/extracted/2026-09-01.sql
  sqlite: /workspace/gcd-dump/gcd.sqlite

  python3 scripts/load-gcd-sql-dump.py \\
      --sql-dump /workspace/gcd-dump/extracted/2026-09-01.sql \\
      --sqlite /workspace/gcd-dump/gcd.sqlite

  # Smaller cache: only series Glyph will ingest
  python3 scripts/load-gcd-sql-dump.py \\
      --sql-dump /workspace/gcd-dump/extracted/2026-09-01.sql \\
      --series-ids-file scripts/gcd-series-ids.example.txt

  # Zip still packed
  python3 scripts/load-gcd-sql-dump.py \\
      --zip /workspace/gcd-dump/gcd-dump.zip \\
      --extract-dir /workspace/gcd-dump/extracted

Then ingest (still no API):

  python3 scripts/ingest-gcd-series-to-catalog.py \\
      --dump-sqlite /workspace/gcd-dump/gcd.sqlite \\
      --series-ids-file scripts/gcd-series-ids.example.txt --dry-run

  python3 scripts/ingest-gcd-series-to-catalog.py \\
      --sql-dump /workspace/gcd-dump/extracted/2026-09-01.sql \\
      --series-id 122674 --dry-run
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent


def _load_ingest():
    path = SCRIPT_DIR / "ingest-gcd-series-to-catalog.py"
    spec = importlib.util.spec_from_file_location("ingest_gcd_series_to_catalog", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv: list[str] | None = None) -> int:
    import gcd_dump

    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--sql-dump",
        default="",
        help=f"Official YYYY-MM-DD.sql (default on the box: {gcd_dump.BOX_SQL_DUMP})",
    )
    ap.add_argument(
        "--zip",
        default="",
        help=f"Official zip to extract first (box: {gcd_dump.BOX_ZIP})",
    )
    ap.add_argument(
        "--extract-dir",
        default="",
        help="Where to unzip .sql files (box: /workspace/gcd-dump/extracted)",
    )
    ap.add_argument(
        "--sqlite",
        default="",
        help=f"Working sqlite to write (default {gcd_dump.BOX_SQLITE} on the box)",
    )
    ap.add_argument("--series-id", action="append", default=[], help="Only keep issues for these series ids")
    ap.add_argument("--series-ids-file", default="", help="File of GCD series ids")
    ap.add_argument("--rebuild", action="store_true", help="Overwrite existing sqlite")
    args = ap.parse_args(argv)

    sql_path: Path | None = None
    if args.zip:
        zip_path = gcd_dump.resolve_user_path(args.zip, ROOT)
        if not zip_path.is_file():
            raise SystemExit(f"zip not found: {zip_path}")
        dest = (
            gcd_dump.resolve_user_path(args.extract_dir, ROOT)
            if args.extract_dir
            else gcd_dump.BOX_DUMP_DIR / "extracted"
        )
        extracted = gcd_dump.extract_dump_zip(zip_path, dest)
        sql_path = extracted[0]
        print(f"extracted {len(extracted)} sql file(s)", file=sys.stderr)

    if args.sql_dump:
        sql_path = gcd_dump.resolve_user_path(args.sql_dump, ROOT)
    elif sql_path is None:
        if gcd_dump.BOX_SQL_DUMP.is_file():
            sql_path = gcd_dump.BOX_SQL_DUMP
        else:
            raise SystemExit(gcd_dump.MISSING_DUMP_MESSAGE)

    if not sql_path.is_file():
        raise SystemExit(f"sql-dump not found: {sql_path}\n{gcd_dump.MISSING_DUMP_MESSAGE}")
    if not gcd_dump.is_sql_file(sql_path):
        raise SystemExit(f"not a .sql / .sql.gz file: {sql_path}")

    sqlite_path = (
        gcd_dump.resolve_user_path(args.sqlite, ROOT)
        if args.sqlite
        else gcd_dump.default_cache_path(sql_path)
    )

    series_ids: list[str] = [s.strip() for s in args.series_id if str(s).strip().isdigit()]
    if args.series_ids_file:
        ingest = _load_ingest()
        series_ids.extend(ingest.parse_series_ids_file(Path(args.series_ids_file)))

    if sqlite_path.exists() and not args.rebuild and gcd_dump.sqlite_cache_covers(sqlite_path, series_ids or None):
        print(f"already covers requested series: {sqlite_path}", file=sys.stderr)
        print(sqlite_path)
        return 0

    gcd_dump.load_sql_files_into_sqlite(
        [sql_path],
        sqlite_path,
        series_ids=series_ids or None,
        progress=True,
    )
    print(sqlite_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
