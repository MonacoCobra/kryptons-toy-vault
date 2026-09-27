#!/usr/bin/env python3
"""Round-trip and no-op proofs for scripts/data_shards.py."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import data_shards as ds

MINI = """\
const rows: Row[] = [
  // keep
  ["im-saga-1", "Saga", "1", "Image Comics", "2012-03-01", "Brian K. Vaughan", "Fiona Staples", "Alana and Marko.", 2.99, "single", 45, 1, "c2410c,1e3a8a,fde68a"],
  ["im-die-1", "DIE", "1", "Image Comics", "2018-12-01", "Kieron Gillen", "Stephanie Hans", "Quote \\"here\\" and P\\u00e9rez.", 3.5, "single", 2.0, 0, "111827,7f1d1d,eab308", { variant: "Cover B", upc: "123", locgId: "9" }],
];

function pal(s: string): [string, string, string] {
  return ["#111827", "#e5e7eb", "#f8fafc"];
}
"""


class ShardTests(unittest.TestCase):
    def test_shard_id_is_lowercase_hex_mod_64(self):
        sid = ds.shard_id("dc-det-n52-488")
        self.assertEqual(len(sid), 2)
        self.assertEqual(sid, f"{int(sid, 16):02x}")
        digest = hashlib.sha256(b"dc-det-n52-488").digest()
        self.assertEqual(sid, f"{int.from_bytes(digest[:4], 'big') % 64:02x}")
        self.assertEqual(ds.shard_id("dc-det-n52-488"), sid)

    def test_parse_and_roundtrip_and_noop(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            comics = root / "src/data/comics.ts"
            comics.parent.mkdir(parents=True)
            comics.write_text(MINI)
            rows = ds.parse_comics_ts(comics)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1][13]["variant"], "Cover B")
            self.assertIn("Pérez", rows[1][7])
            self.assertIn('here', rows[1][7])
            pre = ds.content_hash(rows)
            ds._write_comic_rows(comics, rows)
            loaded = ds.load_comic_rows(comics)
            self.assertEqual(rows, loaded)
            self.assertEqual(pre, ds.content_hash(loaded))
            man = json.loads((root / "src/data/comics/manifest.json").read_text())
            self.assertEqual(man["shardCount"], 64)
            self.assertEqual(man["total"], 2)
            self.assertLessEqual(len(man["shards"]), 2)
            shard_files = list((root / "src/data/comics/shards").glob("*.json"))
            before = {p.name: p.read_bytes() for p in shard_files}
            manifest_before = (root / "src/data/comics/manifest.json").read_bytes()
            added = ds.append_comic_rows(comics, [rows[0]], note="dup")
            self.assertEqual(added, 0)
            after = {p.name: p.read_bytes() for p in (root / "src/data/comics/shards").glob("*.json")}
            self.assertEqual(before, after)
            self.assertEqual(manifest_before, (root / "src/data/comics/manifest.json").read_bytes())
            new_row = ["im-saga-2", "Saga", "2", "Image Comics", "2012-04-01", "BKV", "FS", "Next.", 2.99, "single", 1, 0, "c2410c,1e3a8a,fde68a"]
            added = ds.append_comic_rows(comics, [new_row, rows[0]], note="second")
            self.assertEqual(added, 1)
            ids, keys = ds.comic_id_sets(comics)
            self.assertIn("im-saga-2", ids)
            self.assertIn("saga|2|image comics", keys)
            meta = ds.comics_meta(comics)
            self.assertEqual(meta["im-die-1"]["locgId"], "9")
            self.assertEqual(meta["im-die-1"]["demand"], 2.0)
            self.assertEqual(meta["im-saga-1"]["key"], 1)

    def test_map_merge_locg_wins_and_noop_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "comic-upc-map.json"
            original = {
                "keep": {"upc": "111", "source": "locg", "locgId": "9"},
                "fill": {"source": "gcd", "gcdIssueId": "5"},
            }
            path.write_text(json.dumps(original, indent=2, sort_keys=True) + "\n")
            pre = ds.content_hash(original)

            def merge(disk, local):
                out = dict(disk)
                for cid, ent in local.items():
                    cur = dict(out.get(cid) or {})
                    new = dict(ent or {})
                    if cur.get("upc") and new.get("upc") and cur["upc"] != new["upc"]:
                        cur_src = str(cur.get("source") or "")
                        new_src = str(new.get("source") or "")
                        if any(s in cur_src for s in ("locg", "metron")) and not any(
                            s in new_src for s in ("locg", "metron")
                        ):
                            new["upc"] = cur["upc"]
                            new["source"] = cur_src
                    out[cid] = {**cur, **{k: v for k, v in new.items() if v is not None}}
                return out

            merged = ds.save_map_atomic(
                path,
                {"keep": {"upc": "999", "source": "gcd"}, "fresh": {"upc": "222", "source": "metron"}},
                merge,
            )
            self.assertEqual(merged["keep"]["upc"], "111")
            self.assertEqual(merged["keep"]["source"], "locg")
            self.assertEqual(merged["fresh"]["source"], "metron")
            loaded = ds.load_map(path)
            self.assertEqual(merged, loaded)
            self.assertNotEqual(ds.content_hash(loaded), pre)
            files = {p: p.read_bytes() for p in (path.parent / "comic-upc-map").rglob("*") if p.is_file() and p.name != ".lock"}
            again = ds.save_map_atomic(path, {"keep": {"upc": "111", "source": "locg"}}, merge)
            self.assertEqual(again["keep"]["upc"], "111")
            files_after = {
                p: p.read_bytes() for p in (path.parent / "comic-upc-map").rglob("*") if p.is_file() and p.name != ".lock"
            }
            self.assertEqual(files, files_after)
            self.assertTrue((path.parent / "comic-upc-map" / ".lock").exists())

    def test_array_noop(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "product-sku-index.json"
            rows = [
                {"id": "a:1", "name": "One"},
                {"id": "b:2", "name": "Two"},
            ]
            path.write_text(json.dumps(rows) + "\n")
            ds._write_array(path, rows)
            loaded = ds.load_array(path)
            self.assertEqual(loaded, rows)
            before = {
                p: p.read_bytes()
                for p in (path.parent / "product-sku-index").rglob("*")
                if p.is_file()
            }
            ds.save_array(path, loaded)
            after = {
                p: p.read_bytes()
                for p in (path.parent / "product-sku-index").rglob("*")
                if p.is_file() and p.name != ".lock"
            }
            for p, blob in before.items():
                if p.name == ".lock":
                    continue
                self.assertEqual(after[p], blob)
            self.assertTrue(ds.dataset_exists(path))
            ok, summary = ds.verify_path(path)
            self.assertTrue(ok, summary)

    def test_empty_shard_omitted(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "comic-upc-map.json"
            ds._write_map(path, {"only-one": {"upc": "1"}})
            man = json.loads((path.parent / "comic-upc-map" / "manifest.json").read_text())
            self.assertEqual(man["shardCount"], 64)
            self.assertEqual(len(man["shards"]), 1)
            self.assertEqual(len(list((path.parent / "comic-upc-map" / "shards").glob("*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
