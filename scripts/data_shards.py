#!/usr/bin/env python3
"""Shard catalog datasets so GitHub never sees a file over 100 MB.

64 shards, ids ``00``–``3f``. Assignment is sha256(utf-8 key), first 4 bytes
as a big-endian int, mod 64. Empty shards are omitted. ``shardCount`` stays
64 unless every row is re-sharded.

Callers keep passing the legacy paths:

  src/data/comics.ts
  src/data/comic-upc-map.json
  src/data/figure-archive/product-sku-index.json

See src/data/SHARDING.md.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
from pathlib import Path

SHARD_COUNT = 64
MAX_FILE_BYTES = 50 * 1024 * 1024

COMICS_DATASET = "comics"
MAP_DATASET = "comic-upc-map"
ARRAY_DATASET = "product-sku-index"


def shard_id(key: str) -> str:
    """Stable bucket for a catalog id, UPC-map key, or SKU record id."""
    digest = hashlib.sha256(str(key).encode("utf-8")).digest()
    n = int.from_bytes(digest[:4], "big")
    return f"{n % SHARD_COUNT:02x}"


def content_hash(value) -> str:
    """sha256 of canonical JSON (sorted keys, compact separators, UTF-8)."""
    blob = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def dataset_kind(path: Path | str) -> str | None:
    name = Path(path).name
    if name in {"comics.ts", "comics"}:
        return "comics"
    if name in {"comic-upc-map.json", "comic-upc-map"}:
        return "map"
    if name in {"product-sku-index.json", "product-sku-index"}:
        return "array"
    return None


def dataset_dir(path: Path | str) -> Path:
    path = Path(path)
    kind = dataset_kind(path)
    if kind is None:
        raise ValueError(f"not a sharded dataset path: {path}")
    if path.name in {"comics", "comic-upc-map", "product-sku-index"}:
        return path
    if kind == "comics":
        return path.parent / "comics"
    if kind == "map":
        return path.parent / "comic-upc-map"
    return path.parent / "product-sku-index"


def legacy_file(path: Path | str) -> Path:
    path = Path(path)
    kind = dataset_kind(path)
    if kind is None:
        return path
    if path.name == "comics":
        return path.parent / "comics.ts"
    if path.name == "comic-upc-map":
        return path.parent / "comic-upc-map.json"
    if path.name == "product-sku-index":
        return path.parent / "product-sku-index.json"
    return path


def manifest_path(path: Path | str) -> Path:
    return dataset_dir(path) / "manifest.json"


def shards_present(path: Path | str) -> bool:
    return manifest_path(path).is_file()


def is_legacy_comics(path: Path) -> bool:
    if not path.is_file():
        return False
    with path.open("r", encoding="utf-8") as fh:
        head = fh.read(12000)
    return "const rows:" in head


def dataset_exists(path: Path | str) -> bool:
    kind = dataset_kind(path)
    if kind is None:
        return Path(path).exists()
    if shards_present(path):
        return True
    legacy = legacy_file(path)
    if kind == "comics":
        return is_legacy_comics(legacy)
    return legacy.is_file()


def _dump(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _write_if_changed(path: Path, text: str) -> bool:
    if path.is_file():
        current = path.read_text(encoding="utf-8")
        if current == text:
            return False
    _atomic_write(path, text)
    return True


class _Parser:
    """Subset of JS literal syntax used by the comics.ts rows array."""

    def __init__(self, text: str, i: int) -> None:
        self.s = text
        self.i = i
        self.n = len(text)

    def skip(self) -> None:
        s = self.s
        i = self.i
        n = self.n
        while i < n:
            c = s[i]
            if c in " \t\r\n":
                i += 1
                continue
            if c == "/" and i + 1 < n and s[i + 1] == "/":
                nl = s.find("\n", i)
                i = n if nl < 0 else nl + 1
                continue
            break
        self.i = i

    def parse_value(self):
        self.skip()
        if self.i >= self.n:
            raise ValueError("unexpected end of comics.ts rows")
        c = self.s[self.i]
        if c == '"':
            return self.parse_string()
        if c == "[":
            return self.parse_array()
        if c == "{":
            return self.parse_object()
        if c == "-" or c.isdigit():
            return self.parse_number()
        if self.s.startswith("true", self.i):
            self.i += 4
            return True
        if self.s.startswith("false", self.i):
            self.i += 5
            return False
        if self.s.startswith("null", self.i):
            self.i += 4
            return None
        raise ValueError(f"bad token at {self.i}: {self.s[self.i:self.i+24]!r}")

    def parse_string(self) -> str:
        s = self.s
        i = self.i + 1
        n = self.n
        out: list[str] = []
        while i < n:
            c = s[i]
            if c == '"':
                self.i = i + 1
                return "".join(out)
            if c == "\\":
                i += 1
                if i >= n:
                    break
                esc = s[i]
                if esc == "u":
                    hexes = s[i + 1 : i + 5]
                    out.append(chr(int(hexes, 16)))
                    i += 5
                    continue
                mapping = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", '"': '"', "\\": "\\", "/": "/"}
                out.append(mapping.get(esc, esc))
                i += 1
                continue
            out.append(c)
            i += 1
        raise ValueError("unterminated string in comics.ts")

    def parse_number(self):
        s = self.s
        i = self.i
        n = self.n
        j = i
        if s[j] == "-":
            j += 1
        while j < n and s[j].isdigit():
            j += 1
        is_float = False
        if j < n and s[j] == ".":
            is_float = True
            j += 1
            while j < n and s[j].isdigit():
                j += 1
        if j < n and s[j] in "eE":
            is_float = True
            j += 1
            if j < n and s[j] in "+-":
                j += 1
            while j < n and s[j].isdigit():
                j += 1
        token = s[i:j]
        self.i = j
        return float(token) if is_float else int(token)

    def parse_array(self) -> list:
        self.i += 1
        out: list = []
        while True:
            self.skip()
            if self.i < self.n and self.s[self.i] == "]":
                self.i += 1
                return out
            out.append(self.parse_value())
            self.skip()
            if self.i < self.n and self.s[self.i] == ",":
                self.i += 1

    def parse_object(self) -> dict:
        self.i += 1
        out: dict = {}
        while True:
            self.skip()
            if self.i < self.n and self.s[self.i] == "}":
                self.i += 1
                return out
            key = self.parse_key()
            self.skip()
            if self.i >= self.n or self.s[self.i] != ":":
                raise ValueError(f"expected ':' after key {key!r} at {self.i}")
            self.i += 1
            out[key] = self.parse_value()
            self.skip()
            if self.i < self.n and self.s[self.i] == ",":
                self.i += 1

    def parse_key(self) -> str:
        self.skip()
        if self.s[self.i] == '"':
            return self.parse_string()
        s = self.s
        i = self.i
        n = self.n
        j = i
        while j < n and (s[j].isalnum() or s[j] in "_$"):
            j += 1
        if j == i:
            raise ValueError(f"bad object key at {i}: {s[i:i+16]!r}")
        self.i = j
        return s[i:j]


def parse_comics_ts(path: Path) -> list:
    text = path.read_text(encoding="utf-8")
    marker = text.find("const rows:")
    if marker < 0:
        raise ValueError(f"const rows not found in {path}")
    eq = text.find("=", marker)
    if eq < 0:
        raise ValueError(f"rows assignment not found in {path}")
    start = text.find("[", eq)
    if start < 0:
        raise ValueError(f"rows array not found in {path}")
    parser = _Parser(text, start)
    rows = parser.parse_value()
    if not isinstance(rows, list):
        raise ValueError(f"rows did not parse to a list in {path}")
    return rows


def _read_manifest(path: Path | str) -> dict:
    return json.loads(manifest_path(path).read_text(encoding="utf-8"))


def _iter_shard_docs(path: Path | str):
    man = _read_manifest(path)
    directory = dataset_dir(path)
    for entry in man.get("shards") or []:
        sid = entry["id"]
        doc = json.loads((directory / "shards" / f"{sid}.json").read_text(encoding="utf-8"))
        yield sid, entry, doc


def load_comic_rows(path: Path | str) -> list:
    path = Path(path)
    if shards_present(path):
        packed: list[tuple[int, list]] = []
        for _sid, _meta, doc in _iter_shard_docs(path):
            for ent in doc.get("entries") or []:
                packed.append((int(ent["seq"]), ent["row"]))
        packed.sort(key=lambda item: item[0])
        return [row for _seq, row in packed]
    legacy = legacy_file(path)
    if is_legacy_comics(legacy):
        return parse_comics_ts(legacy)
    raise FileNotFoundError(
        f"comic catalog not found at {legacy} (no shards in {dataset_dir(path)})"
    )


def ids_from_comic_rows(rows) -> set[str]:
    return {str(row[0]) for row in rows if row}


def comic_id_sets(path: Path | str) -> tuple[set[str], set[str]]:
    """(catalog ids, ``series|issue|publisher`` keys lowercased)."""
    ids: set[str] = set()
    keys: set[str] = set()
    for row in load_comic_rows(path):
        ids.add(str(row[0]))
        series = "" if len(row) < 2 or row[1] is None else str(row[1])
        issue = "" if len(row) < 3 or row[2] is None else str(row[2])
        publisher = "" if len(row) < 4 or row[3] is None else str(row[3])
        keys.add(f"{series}|{issue}|{publisher}".lower())
    return ids, keys


def _extra(row) -> dict:
    if len(row) > 13 and isinstance(row[13], dict):
        return row[13]
    return {}


def comics_meta(path: Path | str | None = None) -> dict[str, dict]:
    """id → catalog fields. Same shape the UPC backfill regex used to build."""
    if path is None:
        root = Path(__file__).resolve().parents[1]
        path = root / "src/data/comics.ts"
    out: dict[str, dict] = {}
    for row in load_comic_rows(path):
        extra = _extra(row)
        demand = row[10] if len(row) > 10 else 0
        key = row[11] if len(row) > 11 else 0
        out[str(row[0])] = {
            "series": row[1] if len(row) > 1 else "",
            "issue": "" if len(row) < 3 or row[2] is None else str(row[2]),
            "publisher": row[3] if len(row) > 3 else "",
            "coverDate": row[4] if len(row) > 4 else "",
            "variant": extra.get("variant"),
            "upc": extra.get("upc"),
            "cover": extra.get("cover"),
            "format": row[9] if len(row) > 9 else "",
            "demand": float(demand) if demand is not None else 0.0,
            "key": int(key) if key is not None else 0,
            "gcdIssueId": None if extra.get("gcdIssueId") is None else str(extra.get("gcdIssueId")),
            "locgId": None if extra.get("locgId") is None else str(extra.get("locgId")),
            "streetDate": extra.get("streetDate"),
        }
    return out


def load_map(path: Path | str) -> dict:
    path = Path(path)
    if shards_present(path):
        merged: dict = {}
        for _sid, _meta, doc in _iter_shard_docs(path):
            entries = doc.get("entries") or {}
            if not isinstance(entries, dict):
                raise ValueError(f"map shard entries must be an object ({path})")
            merged.update(entries)
        return merged
    legacy = legacy_file(path)
    if legacy.is_file():
        data = json.loads(legacy.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{legacy} is not a JSON object")
        return data
    return {}


def load_array(path: Path | str) -> list:
    path = Path(path)
    if shards_present(path):
        packed: list[tuple[int, dict]] = []
        for _sid, _meta, doc in _iter_shard_docs(path):
            for ent in doc.get("entries") or []:
                packed.append((int(ent["seq"]), ent["record"]))
        packed.sort(key=lambda item: item[0])
        return [rec for _seq, rec in packed]
    legacy = legacy_file(path)
    if legacy.is_file():
        data = json.loads(legacy.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{legacy} is not a JSON array")
        return data
    return []


def load_document(path: Path | str, default=None):
    kind = dataset_kind(path)
    if kind == "comics":
        return load_comic_rows(path)
    if kind == "map":
        if dataset_exists(path):
            return load_map(path)
        return {} if default is None else default
    if kind == "array":
        if dataset_exists(path):
            return load_array(path)
        return [] if default is None else default
    path = Path(path)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def _sync_shard_list(directory: Path, kind: str) -> None:
    man = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    ids = [entry["id"] for entry in man.get("shards") or []]
    # `?raw` keeps tsc from inferring a union of every catalog literal (that
    # union exceeds V8's Map limit). Vite and the node test loader parse it.
    lines = ["// Generated by scripts/data_shards.py — do not edit.", ""]
    for sid in ids:
        lines.append(f'import s{sid} from "./shards/{sid}.json?raw";')
    lines.append("")
    if kind == "comics":
        cast = "{ entries: { seq: number; row: unknown[] }[] }"
    else:
        cast = "{ entries: Record<string, Record<string, unknown>> }"
    lines.append("export const SHARDS = [")
    for sid in ids:
        lines.append(f"  JSON.parse(s{sid}),")
    lines.append(f"] as {cast}[];")
    lines.append("")
    _write_if_changed(directory / "shard-list.ts", "\n".join(lines))


def _write_manifest(directory: Path, *, dataset: str, total: int, value, shards: list[dict], note: str | None) -> None:
    manifest = {
        "contentHash": content_hash(value),
        "dataset": dataset,
        "shardCount": SHARD_COUNT,
        "shards": shards,
        "total": total,
    }
    if note:
        manifest["lastNote"] = note
    _write_if_changed(directory / "manifest.json", _dump(manifest))


def _write_buckets(directory: Path, buckets: dict[str, list], wrapper_key: str) -> list[dict]:
    shard_dir = directory / "shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    listed: list[dict] = []
    keep: set[str] = set()
    for index in range(SHARD_COUNT):
        sid = f"{index:02x}"
        entries = buckets.get(sid) or []
        path = shard_dir / f"{sid}.json"
        if not entries:
            if path.exists():
                path.unlink()
            continue
        keep.add(sid)
        payload = _dump({"entries": entries})
        _write_if_changed(path, payload)
        listed.append({"count": len(entries), "id": sid})
    for path in shard_dir.glob("*.json"):
        if path.stem not in keep:
            path.unlink()
    listed.sort(key=lambda item: item["id"])
    return listed


def _write_comic_rows(path: Path | str, rows: list, note: str | None = None) -> None:
    buckets: dict[str, list] = {}
    for seq, row in enumerate(rows):
        sid = shard_id(str(row[0]))
        buckets.setdefault(sid, []).append({"row": row, "seq": seq})
    directory = dataset_dir(path)
    directory.mkdir(parents=True, exist_ok=True)
    listed = _write_buckets(directory, buckets, "row")
    _write_manifest(directory, dataset="comics", total=len(rows), value=rows, shards=listed, note=note)
    _sync_shard_list(directory, "comics")


def _write_map(path: Path | str, data: dict) -> None:
    buckets: dict[str, dict] = {}
    for key in sorted(data):
        sid = shard_id(str(key))
        buckets.setdefault(sid, {})[str(key)] = data[key]
    directory = dataset_dir(path)
    directory.mkdir(parents=True, exist_ok=True)
    # Map shards store an object, not a seq list. Reuse the writer shape via a dedicated path.
    shard_dir = directory / "shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    listed: list[dict] = []
    keep: set[str] = set()
    for index in range(SHARD_COUNT):
        sid = f"{index:02x}"
        entries = buckets.get(sid) or {}
        file_path = shard_dir / f"{sid}.json"
        if not entries:
            if file_path.exists():
                file_path.unlink()
            continue
        keep.add(sid)
        _write_if_changed(file_path, _dump({"entries": entries}))
        listed.append({"count": len(entries), "id": sid})
    for file_path in shard_dir.glob("*.json"):
        if file_path.stem not in keep:
            file_path.unlink()
    listed.sort(key=lambda item: item["id"])
    _write_manifest(directory, dataset="comic-upc-map", total=len(data), value=data, shards=listed, note=None)
    _sync_shard_list(directory, "map")


def _record_key(record: dict, seq: int) -> str:
    if isinstance(record, dict) and record.get("id") not in (None, ""):
        return str(record["id"])
    return f"__missing_id_{seq}"


def _write_array(path: Path | str, rows: list) -> None:
    buckets: dict[str, list] = {}
    for seq, record in enumerate(rows):
        sid = shard_id(_record_key(record, seq))
        buckets.setdefault(sid, []).append({"record": record, "seq": seq})
    directory = dataset_dir(path)
    directory.mkdir(parents=True, exist_ok=True)
    listed = _write_buckets(directory, buckets, "record")
    _write_manifest(
        directory,
        dataset="product-sku-index",
        total=len(rows),
        value=rows,
        shards=listed,
        note=None,
    )


def _lock(path: Path | str):
    directory = dataset_dir(path)
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / ".lock"
    fh = lock_path.open("a+", encoding="utf-8")
    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    return fh


def append_comic_rows(path: Path | str, rows: list, note: str | None = None) -> int:
    """Append catalog rows. Skips ids already present. No-op does not rewrite shards."""
    path = Path(path)
    if not rows:
        return 0
    lock = _lock(path)
    try:
        current = load_comic_rows(path)
        have = ids_from_comic_rows(current)
        fresh: list = []
        for row in rows:
            rid = str(row[0])
            if rid in have:
                continue
            have.add(rid)
            fresh.append(row)
        if not fresh:
            return 0
        _write_comic_rows(path, [*current, *fresh], note=note)
        return len(fresh)
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()


def save_map_atomic(path: Path | str, local: dict, merge_fn) -> dict:
    """Lock, merge ``local`` into the on-disk map, write changed shards only.

    The lock file is ``<dataset>/.lock`` (``src/data/comic-upc-map/.lock`` when
    ``path`` is the legacy UPC map). A no-op merge leaves shard bytes unchanged.
    """
    path = Path(path)
    lock = _lock(path)
    try:
        disk = load_map(path)
        had_shards = shards_present(path)
        before = content_hash(disk) if had_shards else None
        merged = merge_fn(disk, local)
        if not isinstance(merged, dict):
            raise TypeError("merge_fn must return a dict")
        if had_shards and content_hash(merged) == before:
            return merged
        _write_map(path, merged)
        return merged
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()


def save_array(path: Path | str, rows: list) -> None:
    """Replace the SKU index. Identical lists do not rewrite shard bytes."""
    path = Path(path)
    lock = _lock(path)
    try:
        if shards_present(path):
            current = load_array(path)
            if current == list(rows):
                return
        _write_array(path, list(rows))
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()


def save_document(path: Path | str, data) -> None:
    kind = dataset_kind(path)
    if kind == "map":
        save_map_atomic(path, data if isinstance(data, dict) else {}, lambda _disk, local: local)
        return
    if kind == "array":
        save_array(path, data if isinstance(data, list) else [])
        return
    if kind == "comics":
        raise TypeError("use append_comic_rows for the comic catalog")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _check_assignment_comics(directory: Path, rows: list) -> list[str]:
    errors: list[str] = []
    seen_seq: set[int] = set()
    for sid, meta, doc in _iter_shard_docs(directory):
        entries = doc.get("entries") or []
        if meta.get("count") != len(entries):
            errors.append(f"comics shard {sid} count {meta.get('count')} != {len(entries)}")
        if not entries:
            errors.append(f"comics shard {sid} is empty but listed")
        for ent in entries:
            seq = int(ent["seq"])
            if seq in seen_seq:
                errors.append(f"duplicate comic seq {seq}")
            seen_seq.add(seq)
            row = ent["row"]
            expect = shard_id(str(row[0]))
            if expect != sid:
                errors.append(f"comic {row[0]} in shard {sid}, expected {expect}")
    if seen_seq != set(range(len(rows))):
        errors.append(f"comic seqs are not 0..{len(rows) - 1}")
    return errors


def _check_assignment_map(directory: Path, data: dict) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for sid, meta, doc in _iter_shard_docs(directory):
        entries = doc.get("entries") or {}
        if meta.get("count") != len(entries):
            errors.append(f"map shard {sid} count {meta.get('count')} != {len(entries)}")
        if not entries:
            errors.append(f"map shard {sid} is empty but listed")
        for key in entries:
            if key in seen:
                errors.append(f"duplicate map key {key}")
            seen.add(key)
            expect = shard_id(str(key))
            if expect != sid:
                errors.append(f"map key {key} in shard {sid}, expected {expect}")
    if seen != set(data):
        errors.append(f"map keys {len(seen)} != merged {len(data)}")
    return errors


def _check_assignment_array(directory: Path, rows: list) -> list[str]:
    errors: list[str] = []
    seen_seq: set[int] = set()
    for sid, meta, doc in _iter_shard_docs(directory):
        entries = doc.get("entries") or []
        if meta.get("count") != len(entries):
            errors.append(f"sku shard {sid} count {meta.get('count')} != {len(entries)}")
        if not entries:
            errors.append(f"sku shard {sid} is empty but listed")
        for ent in entries:
            seq = int(ent["seq"])
            if seq in seen_seq:
                errors.append(f"duplicate sku seq {seq}")
            seen_seq.add(seq)
            record = ent["record"]
            expect = shard_id(_record_key(record, seq))
            if expect != sid:
                errors.append(f"sku seq {seq} in shard {sid}, expected {expect}")
    if seen_seq != set(range(len(rows))):
        errors.append(f"sku seqs are not 0..{len(rows) - 1}")
    return errors


def verify_path(path: Path | str) -> tuple[bool, str]:
    path = Path(path)
    kind = dataset_kind(path)
    if kind is None:
        return False, f"{path} is not a sharded dataset"
    if not shards_present(path):
        return False, f"{path} has no manifest"
    man = _read_manifest(path)
    errors: list[str] = []
    if man.get("shardCount") != SHARD_COUNT:
        errors.append(f"shardCount {man.get('shardCount')} != {SHARD_COUNT}")
    ids = []
    for entry in man.get("shards") or []:
        sid = str(entry.get("id"))
        ids.append(sid)
        if len(sid) != 2 or any(c not in "0123456789abcdef" for c in sid) or int(sid, 16) >= SHARD_COUNT:
            errors.append(f"bad shard id {sid}")
        shard_file = dataset_dir(path) / "shards" / f"{sid}.json"
        if not shard_file.is_file():
            errors.append(f"missing shard file {sid}")
        elif shard_file.stat().st_size > MAX_FILE_BYTES:
            errors.append(f"shard {sid} exceeds 50 MB")
    extra = []
    shard_dir = dataset_dir(path) / "shards"
    if shard_dir.is_dir():
        for file_path in shard_dir.glob("*.json"):
            if file_path.stem not in ids:
                extra.append(file_path.name)
    if extra:
        errors.append(f"shard files not in manifest: {extra}")
    if kind == "comics":
        rows = load_comic_rows(path)
        digest = content_hash(rows)
        if man.get("total") != len(rows):
            errors.append(f"comics total {man.get('total')} != {len(rows)}")
        if man.get("contentHash") != digest:
            errors.append("comics contentHash mismatch")
        errors.extend(_check_assignment_comics(dataset_dir(path), rows))
        summary = f"comics total={len(rows)} hash={digest}"
    elif kind == "map":
        data = load_map(path)
        digest = content_hash(data)
        if man.get("total") != len(data):
            errors.append(f"map total {man.get('total')} != {len(data)}")
        if man.get("contentHash") != digest:
            errors.append("map contentHash mismatch")
        errors.extend(_check_assignment_map(dataset_dir(path), data))
        summary = f"upc-map total={len(data)} hash={digest}"
    else:
        rows = load_array(path)
        digest = content_hash(rows)
        if man.get("total") != len(rows):
            errors.append(f"sku total {man.get('total')} != {len(rows)}")
        if man.get("contentHash") != digest:
            errors.append("sku contentHash mismatch")
        errors.extend(_check_assignment_array(dataset_dir(path), rows))
        summary = f"sku-index total={len(rows)} hash={digest}"
    if errors:
        return False, summary + "\n  " + "\n  ".join(errors)
    return True, summary + " match=yes"


def verify(root: Path | None = None) -> int:
    root = root or Path(__file__).resolve().parents[1]
    targets = [
        root / "src/data/comics.ts",
        root / "src/data/comic-upc-map.json",
        root / "src/data/figure-archive/product-sku-index.json",
    ]
    ok = True
    for target in targets:
        passed, summary = verify_path(target)
        print(summary)
        ok = ok and passed
    data_root = root / "src/data"
    if data_root.is_dir():
        for file_path in data_root.rglob("*"):
            if not file_path.is_file() or file_path.name.endswith(".tmp"):
                continue
            size = file_path.stat().st_size
            if size > MAX_FILE_BYTES:
                print(f"OVERSIZE {file_path} {size}")
                ok = False
    if ok:
        print("OK")
        return 0
    print("FAIL")
    return 1


def _migrate_comics(root: Path) -> str:
    legacy = root / "src/data/comics.ts"
    if not is_legacy_comics(legacy):
        if shards_present(legacy):
            print("comics already sharded")
            return json.loads(manifest_path(legacy).read_text(encoding="utf-8"))["contentHash"]
        raise SystemExit(f"no legacy comics.ts at {legacy}")
    print("parsing comics.ts …", flush=True)
    rows = parse_comics_ts(legacy)
    pre = content_hash(rows)
    print(f"comics parsed {len(rows)} hash={pre}", flush=True)
    _write_comic_rows(legacy, rows, note=None)
    loaded = load_comic_rows(legacy)
    post = content_hash(loaded)
    if rows != loaded or pre != post:
        raise SystemExit(f"comics shard mismatch pre={pre} post={post} eq={rows == loaded}")
    print(f"comics shards match hash={post}", flush=True)
    return post


def _migrate_map(root: Path) -> str:
    legacy = root / "src/data/comic-upc-map.json"
    if not legacy.is_file():
        if shards_present(legacy):
            print("upc map already sharded")
            return json.loads(manifest_path(legacy).read_text(encoding="utf-8"))["contentHash"]
        raise SystemExit(f"no legacy comic-upc-map.json at {legacy}")
    print("parsing comic-upc-map.json …", flush=True)
    data = json.loads(legacy.read_text(encoding="utf-8"))
    pre = content_hash(data)
    print(f"upc map parsed {len(data)} hash={pre}", flush=True)
    _write_map(legacy, data)
    loaded = load_map(legacy)
    post = content_hash(loaded)
    if data != loaded or pre != post:
        raise SystemExit(f"upc map shard mismatch pre={pre} post={post}")
    legacy.unlink()
    print(f"upc map shards match hash={post}; removed legacy file", flush=True)
    return post


def _migrate_array(root: Path) -> str:
    legacy = root / "src/data/figure-archive/product-sku-index.json"
    if not legacy.is_file():
        if shards_present(legacy):
            print("sku index already sharded")
            return json.loads(manifest_path(legacy).read_text(encoding="utf-8"))["contentHash"]
        raise SystemExit(f"no legacy product-sku-index.json at {legacy}")
    print("parsing product-sku-index.json …", flush=True)
    rows = json.loads(legacy.read_text(encoding="utf-8"))
    pre = content_hash(rows)
    print(f"sku index parsed {len(rows)} hash={pre}", flush=True)
    _write_array(legacy, rows)
    loaded = load_array(legacy)
    post = content_hash(loaded)
    if rows != loaded or pre != post:
        raise SystemExit(f"sku index shard mismatch pre={pre} post={post}")
    legacy.unlink()
    print(f"sku index shards match hash={post}; removed legacy file", flush=True)
    return post


def migrate(root: Path | None = None) -> int:
    root = root or Path(__file__).resolve().parents[1]
    _migrate_comics(root)
    _migrate_map(root)
    _migrate_array(root)
    print("migrate hashes matched legacy files")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description="Shard or verify catalog datasets")
    parser.add_argument("command", choices=("verify", "migrate", "shard-id"))
    parser.add_argument("key", nargs="?", help="key for shard-id")
    parser.add_argument("--root", default="")
    args = parser.parse_args(argv)
    if args.command == "shard-id":
        if not args.key:
            raise SystemExit("shard-id requires a key")
        print(shard_id(args.key))
        return 0
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    if args.command == "migrate":
        return migrate(root)
    return verify(root)


if __name__ == "__main__":
    raise SystemExit(main())
