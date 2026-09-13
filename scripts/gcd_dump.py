#!/usr/bin/env python3
"""Offline Grand Comics Database dump access for catalog ingest.

Official dumps are MySQL (`YYYY-MM-DD.sql` from https://www.comics.org/download/).
This module does **not** talk to comics.org.

Glyph box (LIVE — 2026-09-01 dump):
  zip:    /workspace/gcd-dump/gcd-dump.zip
  sql:    /workspace/gcd-dump/extracted/2026-09-01.sql
  sqlite: /workspace/gcd-dump/gcd.sqlite   (load-gcd-sql-dump.py writes this)

Supported layouts (first match wins):
  * gcd.sqlite / *.sqlite — already-converted working copy
  * gcd_publisher.json + gcd_series.json + gcd_issue.json — table extracts
  * *.sql / *.sql.gz — official or table-sliced MySQL dump (streamed into sqlite)

Only gcd_publisher / gcd_series / gcd_issue are read. Issue rows can be filtered
by series_id while streaming so we never materialize the full ~3.6GB dump.
"""
from __future__ import annotations

import gzip
import json
import re
import sqlite3
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, Iterator

NEEDED_TABLES = ("gcd_publisher", "gcd_series", "gcd_issue")
JSON_ALIASES = {
    "gcd_publisher": ("gcd_publisher.json", "publishers.json", "gcd_publishers.json"),
    "gcd_series": ("gcd_series.json", "series.json"),
    "gcd_issue": ("gcd_issue.json", "issues.json", "gcd_issues.json"),
}

# Shared-box drop from Shelby/Lyra. Cloud Agent VMs may not have these files.
BOX_DUMP_DIR = Path("/workspace/gcd-dump")
BOX_ZIP = Path("/workspace/gcd-dump/gcd-dump.zip")
BOX_SQL_DUMP = Path("/workspace/gcd-dump/extracted/2026-09-01.sql")
BOX_SQLITE = Path("/workspace/gcd-dump/gcd.sqlite")

DEFAULT_DUMP_DIRS = (
    BOX_SQLITE,
    BOX_SQL_DUMP,
    Path("/workspace/gcd-dump/extracted"),
    BOX_DUMP_DIR,
    Path("gcd-dump/extracted"),
    Path("gcd-dump"),
    Path("data/gcd"),
    Path("/data/gcd"),
)

MISSING_DUMP_MESSAGE = (
    "HOLD comics.org — no dump found. Glyph box (LIVE):\n"
    f"  --sql-dump {BOX_SQL_DUMP}\n"
    f"  zip: {BOX_ZIP}\n"
    "Convert once (optional, then reuse --dump-sqlite):\n"
    f"  python3 scripts/load-gcd-sql-dump.py --sql-dump {BOX_SQL_DUMP} "
    f"--sqlite {BOX_SQLITE}\n"
    "Do not loop --use-api during 429 storms."
)


def is_sql_file(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".sql") or name.endswith(".sql.gz")


def is_sqlite_file(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".sqlite") or name.endswith(".db")


def discover_dump_dir(*candidates: Path | str | None, root: Path | None = None) -> Path | None:
    """Return the first dump drop (directory or .sql/.sqlite file)."""
    paths: list[Path] = []
    for c in candidates:
        if c:
            paths.append(Path(c))
    if root:
        paths.extend(root / p if not p.is_absolute() else p for p in DEFAULT_DUMP_DIRS)
    else:
        paths.extend(DEFAULT_DUMP_DIRS)
    seen: set[Path] = set()
    for p in paths:
        p = p.expanduser()
        try:
            p = p.resolve()
        except OSError:
            continue
        if p in seen:
            continue
        seen.add(p)
        if p.is_file() and (is_sql_file(p) or is_sqlite_file(p)):
            return p
        if p.is_dir() and dump_dir_kind(p):
            return p
    return None


def dump_dir_kind(dump_dir: Path) -> str | None:
    if find_sqlite(dump_dir):
        return "sqlite"
    if find_json_tables(dump_dir):
        return "json"
    if list_sql_files(dump_dir):
        return "sql"
    return None


def find_sqlite(dump_dir: Path) -> Path | None:
    named = dump_dir / "gcd.sqlite"
    if named.is_file():
        return named
    if dump_dir.name == "extracted":
        sibling = dump_dir.parent / "gcd.sqlite"
        if sibling.is_file():
            return sibling
    hits = sorted(dump_dir.glob("*.sqlite")) + sorted(dump_dir.glob("*.db"))
    hits = [p for p in hits if p.name != ".gcd-ingest.sqlite"]
    return hits[0] if hits else None


def find_json_tables(dump_dir: Path) -> dict[str, Path] | None:
    out: dict[str, Path] = {}
    for table, names in JSON_ALIASES.items():
        for name in names:
            p = dump_dir / name
            if p.is_file():
                out[table] = p
                break
    return out if len(out) == 3 else None


def list_sql_files(dump_dir: Path) -> list[Path]:
    files: list[Path] = []
    search = [dump_dir]
    extracted = dump_dir / "extracted"
    if extracted.is_dir():
        search.append(extracted)
    for folder in search:
        for pat in ("*.sql", "*.sql.gz"):
            files.extend(sorted(folder.glob(pat)))
    files = [p for p in files if p.is_file()]
    dated = [p for p in files if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.sql(?:\.gz)?", p.name)]
    if dated:
        return [max(dated, key=lambda p: (p.stat().st_size, p.name))]
    return files


def resolve_user_path(raw: str, root: Path | None = None) -> Path:
    p = Path(raw).expanduser()
    if not p.is_absolute() and not p.exists() and root is not None:
        alt = (root / raw).expanduser()
        if alt.exists():
            p = alt
    try:
        return p.resolve()
    except OSError:
        return p


def default_cache_path(source: Path) -> Path:
    """Working sqlite beside a fixture, or gcd.sqlite on the Glyph box drop."""
    try:
        resolved = source.resolve()
    except OSError:
        resolved = source
    if resolved == BOX_SQL_DUMP or resolved == BOX_DUMP_DIR or BOX_DUMP_DIR in resolved.parents:
        return BOX_SQLITE
    if resolved.is_file():
        return resolved.parent / ".gcd-ingest.sqlite"
    return resolved / ".gcd-ingest.sqlite"


def zip_needs_extract_hint(dump_dir: Path) -> str | None:
    zip_path = dump_dir / "gcd-dump.zip" if dump_dir.is_dir() else None
    if dump_dir.is_file() and dump_dir.name.endswith(".zip"):
        zip_path = dump_dir
    if zip_path is None or not zip_path.is_file():
        return None
    if dump_dir.is_dir() and (dump_dir_kind(dump_dir) or list_sql_files(dump_dir)):
        return None
    dest = dump_dir / "extracted" if dump_dir.is_dir() else dump_dir.parent / "extracted"
    return (
        f"Found {zip_path} but no extracted SQL. Unzip, then pass --sql-dump:\n"
        f"  python3 scripts/load-gcd-sql-dump.py --zip {zip_path} --extract-dir {dest}\n"
        f"  python3 scripts/ingest-gcd-series-to-catalog.py --sql-dump {dest / '2026-09-01.sql'} --dry-run"
    )


def extract_dump_zip(zip_path: Path, dest: Path) -> list[Path]:
    """Extract .sql files from Shelby's official zip. Never hits comics.org."""
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            name = Path(info.filename).name
            if not (name.endswith(".sql") or name.endswith(".sql.gz")):
                continue
            target = dest / name
            print(f"extract {info.filename} → {target}", file=sys.stderr)
            with zf.open(info) as src, target.open("wb") as out:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            written.append(target)
    if not written:
        raise FileNotFoundError(f"no .sql inside {zip_path}")
    return written


def open_text(path: Path):
    if path.suffix == ".gz" or path.name.endswith(".sql.gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def parse_create_columns(create_sql: str) -> list[str]:
    """Column names from a MySQL CREATE TABLE body, in dump order."""
    m = re.search(r"\((.*)\)\s*(ENGINE|TYPE|DEFAULT|CHARSET|;|$)", create_sql, re.S | re.I)
    body = m.group(1) if m else create_sql
    cols: list[str] = []
    for raw in _split_create_defs(body):
        item = raw.strip()
        if not item:
            continue
        up = item.split(None, 1)[0].upper()
        if up in {"PRIMARY", "UNIQUE", "KEY", "INDEX", "CONSTRAINT", "FULLTEXT", "SPATIAL", "FOREIGN"}:
            continue
        cm = re.match(r"`([^`]+)`", item)
        if cm:
            cols.append(cm.group(1))
    return cols


def _split_create_defs(body: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    in_quote = False
    i = 0
    while i < len(body):
        ch = body[i]
        if in_quote:
            buf.append(ch)
            if ch == "\\" and i + 1 < len(body):
                buf.append(body[i + 1])
                i += 2
                continue
            if ch == "'":
                in_quote = False
            i += 1
            continue
        if ch == "'":
            in_quote = True
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    if buf:
        parts.append("".join(buf))
    return parts


def parse_mysql_value(raw: str) -> Any:
    s = raw.strip()
    if s.upper() == "NULL":
        return None
    if s.startswith("'") and s.endswith("'"):
        inner = s[1:-1]
        return (
            inner.replace("\\'", "'")
            .replace('\\"', '"')
            .replace("\\n", "\n")
            .replace("\\r", "\r")
            .replace("\\t", "\t")
            .replace("\\\\", "\\")
            .replace("''", "'")
        )
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def iter_mysql_tuples(values_sql: str) -> Iterator[list[Any]]:
    """Yield value tuples from a MySQL INSERT VALUES blob."""
    i = 0
    n = len(values_sql)
    while i < n:
        while i < n and values_sql[i] in " \t\r\n,;":
            i += 1
        if i >= n or values_sql[i] != "(":
            break
        i += 1
        fields: list[str] = []
        buf: list[str] = []
        in_quote = False
        while i < n:
            ch = values_sql[i]
            if in_quote:
                buf.append(ch)
                if ch == "\\" and i + 1 < n:
                    buf.append(values_sql[i + 1])
                    i += 2
                    continue
                if ch == "'":
                    if i + 1 < n and values_sql[i + 1] == "'":
                        buf.append(values_sql[i + 1])
                        i += 2
                        continue
                    in_quote = False
                i += 1
                continue
            if ch == "'":
                in_quote = True
                buf.append(ch)
            elif ch == ",":
                fields.append("".join(buf))
                buf = []
            elif ch == ")":
                fields.append("".join(buf))
                i += 1
                break
            else:
                buf.append(ch)
            i += 1
        yield [parse_mysql_value(f) for f in fields]


def parse_insert_column_list(blob: str) -> list[str] | None:
    """Column names from `INSERT INTO t (`a`,`b`) VALUES` when mysqldump used --complete-insert."""
    m = re.search(
        r"(?:INSERT(?:\s+IGNORE)?|REPLACE)\s+INTO\s+`?(?:gcd_publisher|gcd_series|gcd_issue)`?\s*\((.*?)\)\s*VALUES",
        blob,
        re.I | re.S,
    )
    if not m:
        return None
    cols: list[str] = []
    for raw in m.group(1).split(","):
        cm = re.search(r"`([^`]+)`", raw) or re.search(r"([A-Za-z_][A-Za-z0-9_]*)", raw)
        if cm:
            cols.append(cm.group(1))
    return cols or None


def row_from_tuple(cols: list[str], values: list[Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for idx, col in enumerate(cols):
        out[col] = values[idx] if idx < len(values) else None
    return out


def _truthy_deleted(row: dict) -> bool:
    val = row.get("deleted")
    return val in (1, "1", True)


class GcdDumpStore:
    """Query interface over publisher/series/issue rows."""

    def get_series(self, series_id: str | int) -> dict | None:
        raise NotImplementedError

    def get_publisher(self, publisher_id: str | int) -> dict | None:
        raise NotImplementedError

    def issues_for_series(self, series_id: str | int) -> list[dict]:
        raise NotImplementedError

    def find_publishers(self, needle: str) -> list[dict]:
        raise NotImplementedError

    def series_for_publisher(self, publisher_id: str | int, min_year: int = 0) -> list[dict]:
        raise NotImplementedError

    def close(self) -> None:
        return None


class JsonDumpStore(GcdDumpStore):
    def __init__(self, tables: dict[str, list[dict]]):
        self.publishers = {str(r["id"]): r for r in tables["gcd_publisher"] if not _truthy_deleted(r)}
        self.series = {str(r["id"]): r for r in tables["gcd_series"] if not _truthy_deleted(r)}
        issues: dict[str, list[dict]] = {}
        for r in tables["gcd_issue"]:
            if _truthy_deleted(r):
                continue
            issues.setdefault(str(r["series_id"]), []).append(r)
        for rows in issues.values():
            rows.sort(key=lambda r: (str(r.get("sort_code") or 0), str(r.get("number") or "")))
        self.issues = issues

    def get_series(self, series_id: str | int) -> dict | None:
        return self.series.get(str(series_id))

    def get_publisher(self, publisher_id: str | int) -> dict | None:
        return self.publishers.get(str(publisher_id))

    def issues_for_series(self, series_id: str | int) -> list[dict]:
        return list(self.issues.get(str(series_id)) or [])

    def find_publishers(self, needle: str) -> list[dict]:
        n = re.sub(r"[^a-z0-9]+", " ", (needle or "").lower()).strip()
        if n.isdigit():
            hit = self.publishers.get(n)
            return [hit] if hit else []
        out = []
        for row in self.publishers.values():
            name = re.sub(r"[^a-z0-9]+", " ", str(row.get("name") or "").lower()).strip()
            if n and (n in name or name in n):
                out.append(row)
        return out

    def series_for_publisher(self, publisher_id: str | int, min_year: int = 0) -> list[dict]:
        pid = str(publisher_id)
        out = []
        for row in self.series.values():
            if str(row.get("publisher_id")) != pid:
                continue
            year = row.get("year_began")
            if min_year and isinstance(year, int) and year < min_year:
                continue
            out.append(row)
        out.sort(key=lambda r: (r.get("year_began") or 0, r.get("name") or ""))
        return out


class SqliteDumpStore(GcdDumpStore):
    def __init__(self, path: Path):
        self.path = path
        self.con = sqlite3.connect(str(path))
        self.con.row_factory = sqlite3.Row

    def _row(self, table: str, ident: str | int) -> dict | None:
        cur = self.con.execute(
            f"SELECT * FROM {table} WHERE id = ? AND COALESCE(deleted, 0) = 0",
            (int(ident),),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def get_series(self, series_id: str | int) -> dict | None:
        return self._row("gcd_series", series_id)

    def get_publisher(self, publisher_id: str | int) -> dict | None:
        return self._row("gcd_publisher", publisher_id)

    def issues_for_series(self, series_id: str | int) -> list[dict]:
        cur = self.con.execute(
            "SELECT * FROM gcd_issue WHERE series_id = ? AND COALESCE(deleted, 0) = 0 "
            "ORDER BY COALESCE(sort_code, 0), number",
            (int(series_id),),
        )
        return [dict(r) for r in cur.fetchall()]

    def find_publishers(self, needle: str) -> list[dict]:
        n = (needle or "").strip()
        if n.isdigit():
            hit = self.get_publisher(n)
            return [hit] if hit else []
        cur = self.con.execute(
            "SELECT * FROM gcd_publisher WHERE COALESCE(deleted, 0) = 0 "
            "AND lower(name) LIKE ?",
            (f"%{n.lower()}%",),
        )
        return [dict(r) for r in cur.fetchall()]

    def series_for_publisher(self, publisher_id: str | int, min_year: int = 0) -> list[dict]:
        if min_year:
            cur = self.con.execute(
                "SELECT * FROM gcd_series WHERE publisher_id = ? AND COALESCE(deleted, 0) = 0 "
                "AND (year_began IS NULL OR year_began >= ?) ORDER BY year_began, name",
                (int(publisher_id), min_year),
            )
        else:
            cur = self.con.execute(
                "SELECT * FROM gcd_series WHERE publisher_id = ? AND COALESCE(deleted, 0) = 0 "
                "ORDER BY year_began, name",
                (int(publisher_id),),
            )
        return [dict(r) for r in cur.fetchall()]

    def close(self) -> None:
        self.con.close()


def _ensure_sqlite_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS gcd_publisher (
          id INTEGER PRIMARY KEY,
          name TEXT,
          deleted INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS gcd_series (
          id INTEGER PRIMARY KEY,
          name TEXT,
          year_began INTEGER,
          publisher_id INTEGER,
          deleted INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS gcd_issue (
          id INTEGER PRIMARY KEY,
          number TEXT,
          series_id INTEGER,
          publication_date TEXT,
          key_date TEXT,
          on_sale_date TEXT,
          price TEXT,
          barcode TEXT,
          isbn TEXT,
          valid_isbn TEXT,
          variant_of_id INTEGER,
          variant_name TEXT,
          title TEXT,
          sort_code INTEGER,
          deleted INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_gcd_issue_series ON gcd_issue(series_id);
        CREATE INDEX IF NOT EXISTS idx_gcd_series_pub ON gcd_series(publisher_id);
        """
    )


KEEP_ISSUE_COLS = {
    "id",
    "number",
    "series_id",
    "publication_date",
    "key_date",
    "on_sale_date",
    "price",
    "barcode",
    "isbn",
    "valid_isbn",
    "variant_of_id",
    "variant_name",
    "title",
    "sort_code",
    "deleted",
}
KEEP_SERIES_COLS = {"id", "name", "year_began", "publisher_id", "deleted"}
KEEP_PUB_COLS = {"id", "name", "deleted"}
KEEP_COLS = {
    "gcd_publisher": KEEP_PUB_COLS,
    "gcd_series": KEEP_SERIES_COLS,
    "gcd_issue": KEEP_ISSUE_COLS,
}


def _insert_filtered(con: sqlite3.Connection, table: str, row: dict, series_ids: set[int] | None) -> None:
    if table == "gcd_issue" and series_ids is not None:
        try:
            sid = int(row.get("series_id"))
        except (TypeError, ValueError):
            return
        if sid not in series_ids:
            return
    keep = KEEP_COLS[table]
    cols = [c for c in keep if c in row]
    if "id" not in cols:
        return
    placeholders = ",".join("?" for _ in cols)
    colsql = ",".join(cols)
    con.execute(
        f"INSERT OR REPLACE INTO {table} ({colsql}) VALUES ({placeholders})",
        [row.get(c) for c in cols],
    )


def _write_cache_meta(con: sqlite3.Connection, series_ids: Iterable[str | int] | None) -> None:
    con.execute("CREATE TABLE IF NOT EXISTS _gcd_ingest_meta (k TEXT PRIMARY KEY, v TEXT)")
    if series_ids is None:
        filt = "*"
    else:
        filt = ",".join(str(int(s)) for s in sorted({int(x) for x in series_ids}))
    con.execute("INSERT OR REPLACE INTO _gcd_ingest_meta (k, v) VALUES ('issue_filter', ?)", (filt,))


def sqlite_cache_covers(path: Path, series_ids: Iterable[str | int] | None) -> bool:
    """True when an existing .gcd-ingest.sqlite can serve this issue filter."""
    if not path.is_file():
        return False
    try:
        con = sqlite3.connect(str(path))
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not set(NEEDED_TABLES).issubset(tables):
            con.close()
            return False
        filt = None
        if "_gcd_ingest_meta" in tables:
            row = con.execute("SELECT v FROM _gcd_ingest_meta WHERE k = 'issue_filter'").fetchone()
            filt = row[0] if row else None
        con.close()
    except sqlite3.Error:
        return False
    if filt == "*":
        return True
    if series_ids is None:
        return False
    wanted = {int(s) for s in series_ids}
    if not wanted:
        # Publisher / series listing only — pubs + series tables are enough.
        return True
    if not filt:
        return False
    have = {int(x) for x in filt.split(",") if x.strip()}
    return wanted.issubset(have)


def load_sql_files_into_sqlite(
    sql_files: list[Path],
    sqlite_path: Path,
    *,
    series_ids: Iterable[str | int] | None = None,
    progress: bool = True,
) -> Path:
    """Stream official/sliced MySQL dumps into a small working sqlite file."""
    materialized = list(series_ids) if series_ids is not None else None
    wanted = {int(s) for s in materialized} if materialized is not None else None
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()
    con = sqlite3.connect(str(sqlite_path))
    _ensure_sqlite_schema(con)
    columns: dict[str, list[str]] = {}
    current_table: str | None = None
    create_buf = ""
    insert_buf = ""
    in_create = False
    in_insert = False
    inserted = 0

    def flush_insert() -> None:
        nonlocal insert_buf, in_insert, current_table, inserted
        if not in_insert or not current_table:
            insert_buf = ""
            in_insert = False
            return
        table = current_table
        blob = insert_buf
        insert_buf = ""
        in_insert = False
        current_table = None
        cols = parse_insert_column_list(blob) or columns.get(table)
        if not cols:
            return
        m = re.search(r"VALUES\s*", blob, re.I)
        values = blob[m.end() :] if m else blob
        before = inserted
        for tup in iter_mysql_tuples(values):
            row = row_from_tuple(cols, tup)
            _insert_filtered(con, table, row, wanted)
            inserted += 1
        if progress and inserted - before >= 5000:
            print(f"  {table}: streamed {inserted} row(s)…", file=sys.stderr)

    for path in sql_files:
        size = path.stat().st_size if path.is_file() else 0
        if progress:
            print(f"streaming {path} ({size / 1e9:.2f} GB) → {sqlite_path}", file=sys.stderr)
        last_report = 0
        with open_text(path) as fh:
            for line in fh:
                if in_create:
                    create_buf += line
                    if ";" in line:
                        in_create = False
                        if current_table:
                            columns[current_table] = parse_create_columns(create_buf)
                            if progress:
                                print(f"  CREATE {current_table} ({len(columns[current_table])} cols)", file=sys.stderr)
                        create_buf = ""
                        current_table = None
                    continue
                if in_insert:
                    insert_buf += line
                    # A dump INSERT ends at `;\n` outside of quotes — `;` at EOL is the usual form.
                    if re.search(r";\s*$", line):
                        flush_insert()
                    continue
                if progress and size and hasattr(fh, "tell"):
                    try:
                        pos = fh.tell()
                    except OSError:
                        pos = 0
                    if pos and pos - last_report >= 80 * 1024 * 1024:
                        print(f"  read {pos / 1e9:.2f}/{size / 1e9:.2f} GB", file=sys.stderr)
                        last_report = pos
                cm = re.match(
                    r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+`?(gcd_publisher|gcd_series|gcd_issue)`?",
                    line,
                    re.I,
                )
                if cm:
                    current_table = cm.group(1).lower()
                    in_create = True
                    create_buf = line
                    if ";" in line:
                        in_create = False
                        columns[current_table] = parse_create_columns(create_buf)
                        if progress:
                            print(f"  CREATE {current_table} ({len(columns[current_table])} cols)", file=sys.stderr)
                        create_buf = ""
                        current_table = None
                    continue
                im = re.match(
                    r"(?:INSERT(?:\s+IGNORE)?|REPLACE)\s+INTO\s+`?(gcd_publisher|gcd_series|gcd_issue)`?",
                    line,
                    re.I,
                )
                if im:
                    current_table = im.group(1).lower()
                    in_insert = True
                    insert_buf = line
                    if re.search(r";\s*$", line):
                        flush_insert()
                    continue
        if in_insert:
            flush_insert()
    _write_cache_meta(con, materialized)
    con.commit()
    con.close()
    if progress:
        print(f"wrote {sqlite_path} ({inserted} streamed row(s))", file=sys.stderr)
    return sqlite_path


def load_json_tables(paths: dict[str, Path]) -> dict[str, list[dict]]:
    tables: dict[str, list[dict]] = {}
    for table, path in paths.items():
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            data = data.get("rows") or data.get(table) or []
        if not isinstance(data, list):
            raise ValueError(f"{path} is not a JSON list of {table} rows")
        tables[table] = [r for r in data if isinstance(r, dict)]
    return tables


def _open_sql_cache(
    sql_files: list[Path],
    cache: Path,
    series_ids: Iterable[str | int] | None,
    rebuild_cache: bool,
) -> GcdDumpStore:
    if not rebuild_cache and sqlite_cache_covers(cache, series_ids):
        print(f"reusing sqlite cache {cache}", file=sys.stderr)
        return SqliteDumpStore(cache)
    load_sql_files_into_sqlite(sql_files, cache, series_ids=series_ids)
    return SqliteDumpStore(cache)


def open_dump(
    *,
    dump_dir: Path | None = None,
    dump_sqlite: Path | None = None,
    sql_dump: Path | None = None,
    cache_sqlite: Path | None = None,
    series_ids: Iterable[str | int] | None = None,
    rebuild_cache: bool = False,
) -> GcdDumpStore:
    """Open a local dump. Never touches comics.org.

    `sql_dump` / `dump_dir` may be a directory drop *or* a single `.sql` /
    `.sqlite` file. MySQL dumps stream into gcd.sqlite (box) or
    `.gcd-ingest.sqlite` (fixtures) and are reused when the cache covers
    the requested series.
    """
    if dump_sqlite:
        path = Path(dump_sqlite)
        if not path.is_file():
            raise FileNotFoundError(f"dump sqlite not found: {path}")
        return SqliteDumpStore(path)
    source = Path(sql_dump) if sql_dump else (Path(dump_dir) if dump_dir else None)
    if source is None:
        raise FileNotFoundError(MISSING_DUMP_MESSAGE)
    if source.is_file():
        if is_sqlite_file(source):
            return SqliteDumpStore(source)
        if is_sql_file(source):
            cache = Path(cache_sqlite) if cache_sqlite else default_cache_path(source)
            return _open_sql_cache([source], cache, series_ids, rebuild_cache)
        raise FileNotFoundError(f"dump file is not a GCD SQL/sqlite dump: {source}")
    if source.is_dir():
        hint = zip_needs_extract_hint(source)
        sqlite_hit = find_sqlite(source)
        if sqlite_hit:
            return SqliteDumpStore(sqlite_hit)
        json_hit = find_json_tables(source)
        if json_hit:
            return JsonDumpStore(load_json_tables(json_hit))
        sql_files = list_sql_files(source)
        if sql_files:
            cache = Path(cache_sqlite) if cache_sqlite else default_cache_path(sql_files[0])
            return _open_sql_cache(sql_files, cache, series_ids, rebuild_cache)
        if hint:
            raise FileNotFoundError(hint)
        raise FileNotFoundError(
            f"no GCD dump in {source} — pass --sql-dump {BOX_SQL_DUMP} "
            f"(or unzip {BOX_ZIP} first)"
        )
    raise FileNotFoundError(f"dump path not found: {source}\n{MISSING_DUMP_MESSAGE}")


def dump_issue_descriptor(issue: dict) -> str:
    number = str(issue.get("number") or "").strip()
    variant = str(issue.get("variant_name") or "").strip()
    if variant:
        return f"{number} [{variant}]" if number else f"[{variant}]"
    return number
