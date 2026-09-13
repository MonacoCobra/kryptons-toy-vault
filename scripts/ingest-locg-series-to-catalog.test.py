#!/usr/bin/env python3
"""Fixture proof for the LOCG series → comics.ts importer.

No live League of Comic Geeks traffic. Run:

  python3 scripts/ingest-locg-series-to-catalog.test.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import comic_backlog_common as backlog  # noqa: E402


def _load_ingest():
    path = SCRIPT_DIR / "ingest-locg-series-to-catalog.py"
    spec = importlib.util.spec_from_file_location("ingest_locg_series_to_catalog", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ingest = _load_ingest()

FIXTURE_DIR = SCRIPT_DIR / "fixtures" / "locg-series-ingest"

MINI_COMICS_TS = """\
type Row = [
  id: string,
  series: string,
  issue: string,
  publisher: string,
  coverDate: string,
  writers: string,
  artists: string,
  description: string,
  msrp: number,
  format: ComicFormat,
  demand: number,
  key: number,
  palette: string,
  extra?: { variant?: string; upc?: string; streetDate?: string; cover?: string; locgId?: string },
];

const rows: Row[] = [
  ["im-saga-1", "Saga", "1", "Image Comics", "2012-03-01", "Brian K. Vaughan", "Fiona Staples", "Alana and Marko.", 2.99, "single", 45, 1, "c2410c,1e3a8a,fde68a"],
  ["im-die-1", "DIE", "1", "Image Comics", "2018-12-01", "Kieron Gillen", "Stephanie Hans", "DIE #1.", 3.99, "single", 2.0, 1, "111827,7f1d1d,eab308"],
];

function pal(s: string): [string, string, string] {
  return ["#111827", "#e5e7eb", "#f8fafc"];
}
"""


class HelpersTest(unittest.TestCase):
    def test_parse_series_ids_file_comments(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ids.txt"
            p.write_text("# header\n148147   # Crossover\n\n139479\nnot-a-id\n")
            self.assertEqual(ingest.parse_series_ids_file(p), ["148147", "139479"])

    def test_parse_series_ids_file_json(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ids.json"
            p.write_text(json.dumps({"seriesIds": [148147, "139479"]}))
            self.assertEqual(ingest.parse_series_ids_file(p), ["148147", "139479"])

    def test_parse_locg_date_real_only(self):
        self.assertEqual(ingest.parse_locg_date("March 2020"), "2020-03-01")
        self.assertEqual(ingest.parse_locg_date("March 11, 2020"), "2020-03-11")
        self.assertEqual(ingest.parse_locg_date("2020-03-11"), "2020-03-11")
        self.assertIsNone(ingest.parse_locg_date("sometime later"))
        self.assertIsNone(ingest.parse_locg_date(""))

    def test_slug_and_prefix(self):
        self.assertEqual(ingest.publisher_prefix("Image Comics"), "im")
        self.assertEqual(ingest.publisher_prefix("Boom! Studios"), "boom")
        self.assertEqual(ingest.publisher_prefix("IDW Publishing"), "idw")
        self.assertEqual(ingest.publisher_prefix("Dark Horse Comics"), "dh")
        self.assertEqual(ingest.slugify_series("The Department of Truth (2020)"), "department-of-truth")

    def test_reuse_existing_prefix(self):
        meta = {
            "im-saga-1": {"series": "Saga", "issue": "1", "publisher": "Image Comics"},
            "im-die-1": {"series": "DIE", "issue": "1", "publisher": "Image Comics"},
        }
        cid = ingest.make_catalog_id(
            series="Saga",
            issue="999",
            publisher="Image Comics",
            cover_date="2024-06-01",
            existing_ids={"im-saga-1", "im-die-1"},
            existing_meta=meta,
        )
        self.assertEqual(cid, "im-saga-999")
        indie = ingest.make_catalog_id(
            series="Fixture Indie",
            issue="2",
            publisher="Image Comics",
            cover_date="2020-04-01",
            existing_ids={"im-saga-1", "im-die-1"},
            existing_meta=meta,
        )
        self.assertEqual(indie, "im-fixture-indie-2")
        self.assertTrue(ingest.series_names_match("The Department of Truth", "Department of Truth"))
        self.assertFalse(ingest.series_names_match("DIE", "Fixture Indie"))

    def test_gate_requires_locg_and_identity(self):
        base = {
            "locgId": "5550001",
            "upc": "84428400999100111",
            "coverUrl": "https://s3.amazonaws.com/comicgeeks/comics/covers/large-5550001.jpg",
            "series": "Fixture Indie",
            "issue": "1",
            "publisher": "Image Comics",
            "coverDate": "2020-03-01",
            "url": "https://leagueofcomicgeeks.com/comic/5550001/fixture-indie-1",
        }
        self.assertIsNone(
            ingest.gate_reason(
                base,
                existing_ids=set(),
                existing_keys=set(),
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-fixture-indie-1",
            )
        )
        no_id = dict(base, locgId="")
        self.assertEqual(
            ingest.gate_reason(
                no_id,
                existing_ids=set(),
                existing_keys=set(),
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-fixture-indie-1",
            ),
            "no-locgId",
        )
        no_code = dict(base, upc=None, coverUrl=None)
        self.assertEqual(
            ingest.gate_reason(
                no_code,
                existing_ids=set(),
                existing_keys=set(),
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-fixture-indie-1",
            ),
            "no-upc-or-cover",
        )
        self.assertEqual(
            ingest.gate_reason(
                base,
                existing_ids=set(),
                existing_keys=set(),
                existing_locg={"5550001"},
                min_year=1980,
                catalog_id="im-fixture-indie-1",
            ),
            "dup-locgId",
        )
        self.assertEqual(
            ingest.gate_reason(
                dict(base, coverDate="1979-12-01"),
                existing_ids=set(),
                existing_keys=set(),
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-fixture-indie-1",
            ),
            "pre-floor",
        )
        self.assertEqual(
            ingest.gate_reason(
                dict(base, title="Fixture Indie Vol. 1 TP"),
                existing_ids=set(),
                existing_keys=set(),
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-fixture-indie-1",
            ),
            "collected-edition",
        )

    def test_merge_upc_does_not_clobber_stronger(self):
        disk = {
            "im-keep-1": {
                "upc": "111111111111",
                "source": "locg",
                "locgId": "1",
            }
        }
        local = {
            "im-keep-1": {
                "upc": None,
                "source": "locg",
                "locgId": "1",
                "coverUrl": "https://s3.amazonaws.com/comicgeeks/comics/covers/large-1.jpg",
            }
        }
        merged = ingest.bf.merge_upc_maps(disk, local)
        self.assertEqual(merged["im-keep-1"]["upc"], "111111111111")
        self.assertEqual(merged["im-keep-1"]["coverUrl"], local["im-keep-1"]["coverUrl"])


class FixtureIngestTest(unittest.TestCase):
    def setUp(self):
        self._orig_fetch = ingest.bf.fetch

    def tearDown(self):
        ingest.bf.fetch = self._orig_fetch
        ingest.bind_paths(ROOT)

    def _run(self, series_ids, extra=None, root=None):
        extra = extra or []
        argv = [
            "--fixture-dir",
            str(FIXTURE_DIR),
            "--dry-run",
            "--delay",
            "0",
            "--report",
            str((root or Path(tempfile.mkdtemp())) / "report.json"),
        ]
        for sid in series_ids:
            argv.extend(["--series-id", sid])
        argv.extend(extra)
        if root:
            argv.extend(["--root", str(root)])
        code = ingest.main(argv)
        self.assertEqual(code, 0)
        report_path = Path(argv[argv.index("--report") + 1])
        return json.loads(report_path.read_text())

    def _mini_root(self, upc_map=None, cover_urls=None):
        td = Path(tempfile.mkdtemp())
        (td / "src/data").mkdir(parents=True)
        (td / "scripts").mkdir(parents=True)
        (td / "src/data/comics.ts").write_text(MINI_COMICS_TS)
        (td / "src/data/comic-upc-map.json").write_text(json.dumps(upc_map or {}, indent=2) + "\n")
        (td / "src/data/comic-cover-urls.json").write_text(json.dumps(cover_urls or {}, indent=2) + "\n")
        (td / "scripts/comic-locg-series-cache.json").write_text("{}\n")
        return td

    def test_fixture_series_adds_gated_rows_only(self):
        root = self._mini_root()
        report = self._run(["900001"], root=root)
        added_ids = {r["id"] for r in report["added"]}
        added_locg = {r["locgId"] for r in report["added"]}
        skip_reasons = {s["reason"] for s in report["skipped"]}
        self.assertIn("im-fixture-indie-1", added_ids)
        self.assertIn("im-fixture-indie-2", added_ids)
        self.assertEqual(added_locg, {"5550001", "5550002"})
        # #1 has UPC+cover; #2 cover only — both allowed
        row1 = next(r for r in report["added"] if r["id"] == "im-fixture-indie-1")
        self.assertEqual(row1["upc"], "84428400999100111")
        row2 = next(r for r in report["added"] if r["id"] == "im-fixture-indie-2")
        self.assertIsNone(row2["upc"])
        # collected / no date / variant skipped
        self.assertTrue({"no-cover-date", "variant"} & skip_reasons or "no-cover-date" in skip_reasons)
        self.assertIn("no-cover-date", skip_reasons)
        self.assertIn("variant", skip_reasons)
        # dry-run did not mutate catalog
        self.assertEqual((root / "src/data/comics.ts").read_text(), MINI_COMICS_TS)
        self.assertNotIn("5550003", added_locg)

    def test_reuses_saga_prefix(self):
        root = self._mini_root()
        report = self._run(["900002"], root=root)
        self.assertEqual(len(report["added"]), 1)
        self.assertEqual(report["added"][0]["id"], "im-saga-999")
        self.assertEqual(report["added"][0]["series"], "Saga")
        self.assertEqual(report["added"][0]["locgId"], "5551001")

    def test_skips_existing_locg_id(self):
        root = self._mini_root(
            upc_map={
                "im-other-1": {"locgId": "5550001", "upc": "84428400999100111", "source": "locg"}
            }
        )
        report = self._run(["900001"], extra=["--max-issues", "1"], root=root)
        self.assertEqual(report["added"], [])
        self.assertTrue(any(s["reason"] == "dup-locgId" for s in report["skipped"]))

    def test_write_merges_maps_and_comics_ts(self):
        root = self._mini_root(
            upc_map={
                "im-keep-1": {
                    "upc": "111111111111",
                    "source": "locg",
                    "locgId": "9",
                    "fetchedAt": "2026-01-01T00:00:00Z",
                }
            }
        )
        argv = [
            "--fixture-dir",
            str(FIXTURE_DIR),
            "--series-id",
            "900001",
            "--max-issues",
            "1",
            "--delay",
            "0",
            "--root",
            str(root),
        ]
        self.assertEqual(ingest.main(argv), 0)
        comics = (root / "src/data/comics.ts").read_text()
        self.assertIn('["im-fixture-indie-1"', comics)
        self.assertIn('locgId: "5550001"', comics)
        self.assertIn('upc: "84428400999100111"', comics)
        upc = json.loads((root / "src/data/comic-upc-map.json").read_text())
        self.assertEqual(upc["im-keep-1"]["upc"], "111111111111")
        self.assertEqual(upc["im-fixture-indie-1"]["locgId"], "5550001")
        self.assertEqual(upc["im-fixture-indie-1"]["upc"], "84428400999100111")
        covers = json.loads((root / "src/data/comic-cover-urls.json").read_text())
        self.assertIn("5550001", covers["im-fixture-indie-1"])
        # row formatting matches backlog helper
        ids, keys = backlog.parse_existing_ts()
        self.assertIn("im-fixture-indie-1", ids)
        self.assertIn("fixture indie|1|image comics", keys)

    def test_example_ids_file_is_numeric_only(self):
        ids = ingest.parse_series_ids_file(SCRIPT_DIR / "locg-series-ids.example.txt")
        self.assertTrue(ids)
        self.assertTrue(all(i.isdigit() for i in ids))
        self.assertIn("148147", ids)


if __name__ == "__main__":
    unittest.main()
