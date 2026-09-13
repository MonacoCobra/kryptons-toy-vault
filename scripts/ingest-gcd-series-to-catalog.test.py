#!/usr/bin/env python3
"""Fixture proof for the GCD series → comics.ts importer.

No live comics.org traffic. Run:

  python3 scripts/ingest-gcd-series-to-catalog.test.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import comic_backlog_common as backlog  # noqa: E402
import gcd_dump  # noqa: E402


def _load_ingest():
    path = SCRIPT_DIR / "ingest-gcd-series-to-catalog.py"
    spec = importlib.util.spec_from_file_location("ingest_gcd_series_to_catalog", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ingest = _load_ingest()

FIXTURE_DIR = SCRIPT_DIR / "fixtures" / "gcd-series-ingest"
DUMP_DIR = SCRIPT_DIR / "fixtures" / "gcd-dump-ingest"
DUMP_SQL_DIR = SCRIPT_DIR / "fixtures" / "gcd-dump-sql"

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
  extra?: { variant?: string; upc?: string; streetDate?: string; cover?: string; locgId?: string; gcdIssueId?: string },
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
            p.write_text("# header\n122674   # X-O Manowar\n\n131922\nnot-a-id\n")
            self.assertEqual(ingest.parse_series_ids_file(p), ["122674", "131922"])

    def test_normalize_upc_never_invents(self):
        self.assertEqual(ingest.normalize_upc("84428400999100111"), "84428400999100111")
        self.assertEqual(ingest.normalize_upc("978-1-5343-2123-4"), "9781534321234")
        self.assertIsNone(ingest.normalize_upc("111111111111"))
        self.assertIsNone(ingest.normalize_upc("short"))
        self.assertIsNone(ingest.normalize_upc(""))
        self.assertIsNone(ingest.normalize_upc(None))

    def test_parse_gcd_date_real_only(self):
        self.assertEqual(ingest.parse_gcd_date("2020-03-00"), "2020-03-01")
        self.assertEqual(ingest.parse_gcd_date("2020-03-11"), "2020-03-11")
        self.assertEqual(ingest.parse_gcd_date("March 2020"), "2020-03-01")
        self.assertEqual(ingest.parse_gcd_date("", "April 8, 2020"), "2020-04-08")
        self.assertIsNone(ingest.parse_gcd_date("sometime later"))
        self.assertIsNone(ingest.parse_gcd_date("", None))

    def test_gate_accepts_gcd_id_without_barcode(self):
        base = {
            "gcdIssueId": "8000002",
            "upc": None,
            "isbn": None,
            "series": "GCD Fixture Indie",
            "issue": "2",
            "publisher": "Image Comics",
            "coverDate": "2020-04-01",
        }
        self.assertIsNone(
            ingest.gate_reason(
                base,
                existing_ids=set(),
                existing_keys=set(),
                existing_gcd=set(),
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-gcd-fixture-indie-2",
            )
        )

    def test_gate_accepts_isbn_or_upc_without_repeating_id_requirement(self):
        isbn_only = {
            "gcdIssueId": "",
            "upc": None,
            "isbn": "9781534321234",
            "series": "GCD Fixture Indie",
            "issue": "6",
            "publisher": "Image Comics",
            "coverDate": "2020-08-01",
        }
        self.assertIsNone(
            ingest.gate_reason(
                isbn_only,
                existing_ids=set(),
                existing_keys=set(),
                existing_gcd=set(),
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-gcd-fixture-indie-6",
            )
        )

    def test_gate_rejects_missing_id_and_codes(self):
        bare = {
            "gcdIssueId": "",
            "upc": None,
            "isbn": None,
            "series": "GCD Fixture Indie",
            "issue": "9",
            "publisher": "Image Comics",
            "coverDate": "2020-09-01",
        }
        self.assertEqual(
            ingest.gate_reason(
                bare,
                existing_ids=set(),
                existing_keys=set(),
                existing_gcd=set(),
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-gcd-fixture-indie-9",
            ),
            "no-gcdIssueId-or-upc-or-isbn",
        )

    def test_gate_requires_real_identity_and_skips_dups(self):
        base = {
            "gcdIssueId": "8000001",
            "upc": "84428400999100111",
            "series": "GCD Fixture Indie",
            "issue": "1",
            "publisher": "Image Comics",
            "coverDate": "2020-03-01",
        }
        self.assertEqual(
            ingest.gate_reason(
                dict(base, series=""),
                existing_ids=set(),
                existing_keys=set(),
                existing_gcd=set(),
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-x-1",
            ),
            "incomplete-identity",
        )
        self.assertEqual(
            ingest.gate_reason(
                base,
                existing_ids=set(),
                existing_keys=set(),
                existing_gcd={"8000001"},
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-x-1",
            ),
            "dup-gcdIssueId",
        )
        self.assertEqual(
            ingest.gate_reason(
                dict(base, coverDate="1979-12-01"),
                existing_ids=set(),
                existing_keys=set(),
                existing_gcd=set(),
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-x-1",
            ),
            "pre-floor",
        )

    def test_viewer_family_copies_parent_sibling_or_skips(self):
        parent = {"id": 8000001, "number": "1"}
        added = [[
            "im-gcd-fixture-indie-1",
            "GCD Fixture Indie",
            "1",
            "Image Comics",
            "2020-03-01",
            "",
            "",
            "",
            3.99,
            "single",
            0.8,
            0,
            "c2410c,1e3a8a,fde68a",
            {"gcdIssueId": "8000001"},
        ]]
        self.assertEqual(
            ingest.viewer_family_from_parent(
                parent,
                series_name="GCD Fixture Indie",
                publisher="Image Comics",
                existing_meta={},
                added_rows=added,
            ),
            ("GCD Fixture Indie", "1", "Image Comics", "single"),
        )
        self.assertEqual(
            ingest.viewer_family_from_parent(
                {"id": 99, "number": "1"},
                series_name="Saga",
                publisher="Image Comics",
                existing_meta={
                    "im-saga-1": {
                        "series": "Saga",
                        "issue": "1",
                        "publisher": "Image Comics",
                        "format": "single",
                    }
                },
                added_rows=[],
            ),
            ("Saga", "1", "Image Comics", "single"),
        )
        self.assertIsNone(
            ingest.viewer_family_from_parent(
                {"id": 8000005, "number": "5"},
                series_name="GCD Fixture Indie",
                publisher="Image Comics",
                existing_meta={},
                added_rows=[],
            )
        )

    def test_gate_identity_includes_variant(self):
        main = {
            "gcdIssueId": "8000001",
            "upc": "84428400999100111",
            "series": "GCD Fixture Indie",
            "issue": "1",
            "publisher": "Image Comics",
            "coverDate": "2020-03-01",
            "variantName": "",
        }
        variant = dict(main, gcdIssueId="8000004", upc="84428400999100121", variantName="Cover B")
        keys = {
            ingest.identity_key("GCD Fixture Indie", "1", "Image Comics"),
        }
        self.assertIsNone(
            ingest.gate_reason(
                variant,
                existing_ids={"im-gcd-fixture-indie-1"},
                existing_keys=keys,
                existing_gcd={"8000001"},
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-gcd-fixture-indie-1-cover-b",
            )
        )
        keys.add(ingest.identity_key("GCD Fixture Indie", "1", "Image Comics", "Cover B"))
        self.assertEqual(
            ingest.gate_reason(
                variant,
                existing_ids={"im-gcd-fixture-indie-1", "im-gcd-fixture-indie-1-cover-b"},
                existing_keys=keys,
                existing_gcd={"8000001", "8000004"},
                existing_locg=set(),
                min_year=1980,
                catalog_id="im-gcd-fixture-indie-1-cover-b-2",
            ),
            "dup-gcdIssueId",
        )

    def test_merge_upc_does_not_clobber_locg_or_metron(self):
        disk = {
            "im-keep-locg": {"upc": "111111111111", "source": "locg", "locgId": "1"},
            "im-keep-metron": {"upc": "222222222222", "source": "metron", "sourceId": "99"},
        }
        local = {
            "im-keep-locg": {
                "upc": "999999999999",
                "source": "gcd",
                "gcdIssueId": "8000001",
            },
            "im-keep-metron": {
                "upc": "888888888888",
                "source": "gcd",
                "gcdIssueId": "8000002",
            },
            "im-new-1": {"gcdIssueId": "8000099", "source": "gcd", "sourceId": "8000099"},
        }
        merged = ingest.bf.merge_upc_maps(disk, local)
        self.assertEqual(merged["im-keep-locg"]["upc"], "111111111111")
        self.assertEqual(merged["im-keep-locg"]["source"], "locg")
        self.assertEqual(merged["im-keep-locg"]["gcdIssueId"], "8000001")
        self.assertEqual(merged["im-keep-metron"]["upc"], "222222222222")
        self.assertEqual(merged["im-keep-metron"]["source"], "metron")
        self.assertEqual(merged["im-new-1"]["gcdIssueId"], "8000099")

    def test_parse_retry_after_seconds_and_http_date(self):
        self.assertEqual(ingest.parse_retry_after({"Retry-After": "120"}), 120.0)
        when = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 13, 11, 55, tzinfo=timezone.utc)
        headers = {"Retry-After": "Sun, 13 Sep 2026 12:00:00 GMT"}
        self.assertEqual(ingest.parse_retry_after(headers, now=now), 300.0)
        self.assertIsNone(ingest.parse_retry_after({}))
        self.assertEqual(ingest.pullback_cooldown({"Retry-After": "99999"}), ingest.COOLDOWN_CAP_SEC)

    def test_429_stops_after_one_cooldown_no_retry(self):
        slept: list[float] = []

        class Always429:
            def __init__(self):
                self.calls = 0

            def __call__(self, req, timeout=30):
                self.calls += 1
                raise urllib.error.HTTPError(req.full_url, 429, "Too Many", hdrs={"Retry-After": "180"}, fp=None)

        boom = Always429()
        client = ingest.GcdClient(7.0, sleep=slept.append, urlopen=boom)
        with self.assertRaises(ingest.RateLimitAbort):
            client.get_json("https://www.comics.org/api/issue/1/")
        self.assertEqual(boom.calls, 1)
        self.assertTrue(client.aborted)
        self.assertGreaterEqual(client.session_delay, ingest.SESSION_DELAY_FLOOR_ON_PULLBACK)
        self.assertEqual(client.last_cooldown, 180.0)
        self.assertIn(180.0, slept)
        with self.assertRaises(ingest.RateLimitAbort):
            client.get_json("https://www.comics.org/api/issue/2/")
        self.assertEqual(boom.calls, 1)

    def test_403_hard_block_also_pulls_back(self):
        class Boom403:
            def __call__(self, req, timeout=30):
                raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", hdrs=None, fp=None)

        client = ingest.GcdClient(7.0, sleep=lambda _s: None, urlopen=Boom403())
        with self.assertRaises(ingest.RateLimitAbort):
            client.get_json("https://www.comics.org/api/issue/1/")
        self.assertTrue(client.aborted)
        self.assertEqual(client.last_cooldown, ingest.LONG_COOLDOWN_SEC)


class FixtureIngestTest(unittest.TestCase):
    def tearDown(self):
        ingest.bind_paths(ROOT)

    def _run(self, series_ids, extra=None, root=None):
        extra = extra or []
        argv = [
            "--use-api",
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
        (td / "scripts/comic-gcd-series-cache.json").write_text("{}\n")
        return td

    def test_fixture_series_keeps_gcd_id_without_barcode(self):
        root = self._mini_root()
        report = self._run(["900101"], root=root)
        added = {r["id"]: r for r in report["added"]}
        skip_reasons = {s["reason"] for s in report["skipped"]}
        self.assertIn("im-gcd-fixture-indie-1", added)
        self.assertIn("im-gcd-fixture-indie-2", added)
        self.assertIn("im-gcd-fixture-indie-6", added)
        self.assertEqual(added["im-gcd-fixture-indie-1"]["upc"], "84428400999100111")
        self.assertEqual(added["im-gcd-fixture-indie-1"]["gcdIssueId"], "8000001")
        # Shelby/Lyra: real gcdIssueId is enough — no barcode required
        self.assertEqual(added["im-gcd-fixture-indie-2"]["gcdIssueId"], "8000002")
        self.assertIsNone(added["im-gcd-fixture-indie-2"]["upc"])
        self.assertEqual(added["im-gcd-fixture-indie-6"]["gcdIssueId"], "8000006")
        self.assertEqual(added["im-gcd-fixture-indie-6"]["upc"], "9781534321234")
        self.assertIn("im-gcd-fixture-indie-1-cover-b", added)
        self.assertEqual(added["im-gcd-fixture-indie-1-cover-b"]["issue"], "1")
        self.assertEqual(added["im-gcd-fixture-indie-1-cover-b"]["variant"], "Cover B")
        self.assertEqual(added["im-gcd-fixture-indie-1-cover-b"]["gcdIssueId"], "8000004")
        self.assertIn("no-cover-date", skip_reasons)
        self.assertIn("collected-edition", skip_reasons)
        self.assertEqual((root / "src/data/comics.ts").read_text(), MINI_COMICS_TS)

    def test_reuses_saga_prefix(self):
        root = self._mini_root()
        report = self._run(["900102"], root=root)
        self.assertEqual(len(report["added"]), 1)
        self.assertEqual(report["added"][0]["id"], "im-saga-999")
        self.assertEqual(report["added"][0]["series"], "Saga")
        self.assertEqual(report["added"][0]["gcdIssueId"], "8001001")

    def test_skips_existing_gcd_issue_id(self):
        root = self._mini_root(
            upc_map={
                "im-other-1": {
                    "gcdIssueId": "8000001",
                    "source": "gcd",
                    "sourceId": "8000001",
                    "upc": "84428400999100111",
                }
            }
        )
        report = self._run(["900101"], extra=["--max-issues", "1", "--mains-only"], root=root)
        self.assertEqual(report["added"], [])
        self.assertTrue(any(s["reason"] == "dup-gcdIssueId" for s in report["skipped"]))

    def test_publisher_filter_skips_mismatch(self):
        root = self._mini_root()
        report = self._run(["900101"], extra=["--publisher", "Dark Horse"], root=root)
        self.assertEqual(report["added"], [])
        self.assertTrue(any(s["reason"] == "publisher-filter" for s in report["skipped"]))

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
            "--use-api",
            "--fixture-dir",
            str(FIXTURE_DIR),
            "--series-id",
            "900101",
            "--max-issues",
            "1",
            "--delay",
            "0",
            "--root",
            str(root),
        ]
        self.assertEqual(ingest.main(argv), 0)
        comics = (root / "src/data/comics.ts").read_text()
        self.assertIn('["im-gcd-fixture-indie-1"', comics)
        self.assertIn('gcdIssueId: "8000001"', comics)
        self.assertIn('upc: "84428400999100111"', comics)
        upc = json.loads((root / "src/data/comic-upc-map.json").read_text())
        self.assertEqual(upc["im-keep-1"]["upc"], "111111111111")
        self.assertEqual(upc["im-gcd-fixture-indie-1"]["gcdIssueId"], "8000001")
        self.assertEqual(upc["im-gcd-fixture-indie-1"]["sourceId"], "8000001")
        self.assertEqual(upc["im-gcd-fixture-indie-1"]["source"], "gcd")
        self.assertEqual(upc["im-gcd-fixture-indie-1"]["upc"], "84428400999100111")
        self.assertIn("/issue/8000001", upc["im-gcd-fixture-indie-1"]["url"])
        covers = json.loads((root / "src/data/comic-cover-urls.json").read_text())
        self.assertIn("8000001", covers["im-gcd-fixture-indie-1"])
        ids, keys = backlog.parse_existing_ts()
        self.assertIn("im-gcd-fixture-indie-1", ids)
        self.assertIn("gcd fixture indie|1|image comics", keys)

    def test_example_ids_file_is_numeric_only(self):
        ids = ingest.parse_series_ids_file(SCRIPT_DIR / "gcd-series-ids.example.txt")
        self.assertTrue(ids)
        self.assertTrue(all(i.isdigit() for i in ids))
        self.assertIn("122674", ids)


class DumpIngestTest(unittest.TestCase):
    """Primary path: local dump, no comics.org."""

    def tearDown(self):
        ingest.bind_paths(ROOT)

    def _run(self, series_ids, extra=None, root=None, dump_dir=None):
        extra = extra or []
        argv = [
            "--dump-dir",
            str(dump_dir or DUMP_DIR),
            "--dry-run",
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
        (td / "scripts/comic-gcd-series-cache.json").write_text("{}\n")
        return td

    def test_dump_keeps_gcd_id_without_barcode(self):
        root = self._mini_root()
        report = self._run(["900101"], root=root)
        self.assertEqual(report["source"], "dump")
        added = {r["id"]: r for r in report["added"]}
        skip_reasons = {s["reason"] for s in report["skipped"]}
        self.assertIn("im-gcd-fixture-indie-1", added)
        self.assertIn("im-gcd-fixture-indie-2", added)
        self.assertIn("im-gcd-fixture-indie-6", added)
        self.assertEqual(added["im-gcd-fixture-indie-1"]["upc"], "84428400999100111")
        self.assertEqual(added["im-gcd-fixture-indie-2"]["gcdIssueId"], "8000002")
        self.assertIsNone(added["im-gcd-fixture-indie-2"]["upc"])
        self.assertEqual(added["im-gcd-fixture-indie-6"]["upc"], "9781534321234")
        self.assertTrue({"variant-orphan", "no-cover-date", "collected-edition"} <= skip_reasons)
        cover_b = next((r for r in report["added"] if r.get("gcdIssueId") == "8000004"), None)
        self.assertIsNotNone(cover_b)
        assert cover_b is not None
        self.assertEqual(cover_b["issue"], "1")
        self.assertEqual(cover_b["variant"], "Cover B")
        self.assertEqual(cover_b["id"], "im-gcd-fixture-indie-1-cover-b")
        self.assertNotEqual(cover_b["id"], added["im-gcd-fixture-indie-1"]["id"])
        self.assertFalse(any(r.get("gcdIssueId") in {"8000007", "8000008", "8000009", "8000010"} for r in report["added"]))
        self.assertEqual((root / "src/data/comics.ts").read_text(), MINI_COMICS_TS)

    def test_dump_publisher_discovery(self):
        root = self._mini_root()
        report = self._run([], extra=["--publisher", "Image", "--max-issues", "1"], root=root)
        ids = {r["id"] for r in report["added"]}
        self.assertTrue(ids)
        self.assertTrue(any(i.startswith("im-") for i in ids))

    def test_dump_sql_slice(self):
        root = self._mini_root()
        report = self._run(["900101"], root=root, dump_dir=DUMP_SQL_DIR)
        added = {r["gcdIssueId"]: r for r in report["added"]}
        self.assertIn("8000001", added)
        self.assertIn("8000002", added)
        self.assertEqual(added["8000001"]["upc"], "84428400999100111")
        self.assertIsNone(added["8000002"]["upc"])

    def test_dump_dir_accepts_sql_file(self):
        root = self._mini_root()
        sql = DUMP_SQL_DIR / "slice.sql"
        report = self._run(["900101"], root=root, dump_dir=sql)
        added = {r["gcdIssueId"]: r for r in report["added"]}
        self.assertIn("8000001", added)
        self.assertIn("8000002", added)

    def test_sql_dump_flag(self):
        root = self._mini_root()
        report_path = root / "report.json"
        argv = [
            "--sql-dump",
            str(DUMP_SQL_DIR / "slice.sql"),
            "--series-id",
            "900101",
            "--dry-run",
            "--report",
            str(report_path),
            "--root",
            str(root),
        ]
        self.assertEqual(ingest.main(argv), 0)
        report = json.loads(report_path.read_text())
        self.assertEqual(report["source"], "dump")
        self.assertIn("8000001", {r["gcdIssueId"] for r in report["added"]})

    def test_load_helper_writes_sqlite(self):
        spec = importlib.util.spec_from_file_location(
            "load_gcd_sql_dump", SCRIPT_DIR / "load-gcd-sql-dump.py"
        )
        self.assertIsNotNone(spec)
        assert spec is not None and spec.loader is not None
        load = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(load)
        td = Path(tempfile.mkdtemp())
        sqlite = td / "gcd.sqlite"
        self.assertEqual(
            load.main(
                [
                    "--sql-dump",
                    str(DUMP_SQL_DIR / "slice.sql"),
                    "--sqlite",
                    str(sqlite),
                    "--series-id",
                    "900101",
                ]
            ),
            0,
        )
        self.assertTrue(sqlite.is_file())
        store = gcd_dump.SqliteDumpStore(sqlite)
        self.assertIsNotNone(store.get_series(900101))
        self.assertTrue(store.issues_for_series(900101))
        store.close()
        root = self._mini_root()
        report_path = root / "report.json"
        self.assertEqual(
            ingest.main(
                [
                    "--dump-sqlite",
                    str(sqlite),
                    "--series-id",
                    "900101",
                    "--dry-run",
                    "--report",
                    str(report_path),
                    "--root",
                    str(root),
                ]
            ),
            0,
        )
        report = json.loads(report_path.read_text())
        self.assertIn("8000001", {r["gcdIssueId"] for r in report["added"]})

    def test_complete_insert_column_list(self):
        blob = (
            "INSERT INTO `gcd_issue` (`id`,`number`,`series_id`,`barcode`,`deleted`) "
            "VALUES (9,'1',900101,'84428400999100111',0);"
        )
        cols = gcd_dump.parse_insert_column_list(blob)
        self.assertEqual(cols, ["id", "number", "series_id", "barcode", "deleted"])

    def test_dump_write_does_not_clobber_locg(self):
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
            "--dump-dir",
            str(DUMP_DIR),
            "--series-id",
            "900101",
            "--max-issues",
            "1",
            "--mains-only",
            "--root",
            str(root),
        ]
        self.assertEqual(ingest.main(argv), 0)
        comics = (root / "src/data/comics.ts").read_text()
        self.assertIn('gcdIssueId: "8000001"', comics)
        upc = json.loads((root / "src/data/comic-upc-map.json").read_text())
        self.assertEqual(upc["im-keep-1"]["upc"], "111111111111")
        self.assertEqual(upc["im-gcd-fixture-indie-1"]["gcdIssueId"], "8000001")

    def test_dump_keeps_linked_variant_on_parent_issue(self):
        root = self._mini_root()
        report = self._run(["900101"], root=root)
        added = {r["gcdIssueId"]: r for r in report["added"]}
        self.assertEqual(added["8000001"]["issue"], "1")
        self.assertIsNone(added["8000001"].get("variant"))
        self.assertEqual(added["8000004"]["issue"], "1")
        self.assertEqual(added["8000004"]["variant"], "Cover B")
        self.assertEqual(added["8000004"]["id"], "im-gcd-fixture-indie-1-cover-b")
        self.assertNotEqual(added["8000004"]["id"], added["8000001"]["id"])
        # Live viewer: comicFamilyKey = series|issue|publisher (no variant).
        self.assertEqual(
            ingest.comic_family_key(
                added["8000004"]["series"],
                added["8000004"]["issue"],
                added["8000004"]["publisher"],
            ),
            ingest.comic_family_key(
                added["8000001"]["series"],
                added["8000001"]["issue"],
                added["8000001"]["publisher"],
            ),
        )
        self.assertEqual(added["8000004"]["format"], added["8000001"]["format"])
        self.assertEqual(added["8000004"]["upc"], "84428400999100121")

    def test_comic_family_key_matches_viewer_normalize(self):
        self.assertEqual(
            ingest.comic_family_key("GCD Fixture Indie", "1", "Image Comics"),
            "gcd fixture indie|1|image comics",
        )
        self.assertEqual(
            ingest.comic_family_key("  Saga  ", " 1 ", "IMAGE   Comics"),
            "saga|1|image comics",
        )

    def test_dump_skips_orphan_variants(self):
        root = self._mini_root()
        report = self._run(["900101"], root=root)
        orphan_ids = {
            str(s.get("gcdIssueId"))
            for s in report["skipped"]
            if s.get("reason") == "variant-orphan"
        }
        self.assertTrue({"8000007", "8000008", "8000009", "8000010"} <= orphan_ids)
        added_ids = {r["gcdIssueId"] for r in report["added"]}
        self.assertFalse(added_ids & {"8000007", "8000008", "8000009", "8000010"})

    def test_dump_mains_only_skips_linked_variants(self):
        root = self._mini_root()
        report = self._run(["900101"], extra=["--mains-only"], root=root)
        added_ids = {r["gcdIssueId"] for r in report["added"]}
        self.assertIn("8000001", added_ids)
        self.assertNotIn("8000004", added_ids)
        self.assertTrue(any(s.get("gcdIssueId") == 8000004 or s.get("gcdIssueId") == "8000004" for s in report["skipped"]))

    def test_dump_max_issues_counts_mains_and_brings_their_variants(self):
        root = self._mini_root()
        report = self._run(["900101"], extra=["--max-issues", "1"], root=root)
        added = {r["gcdIssueId"]: r for r in report["added"]}
        self.assertIn("8000001", added)
        self.assertIn("8000004", added)
        self.assertNotIn("8000002", added)
        self.assertEqual(added["8000004"]["issue"], "1")

    def test_dump_write_variant_extra_and_own_gcd_id(self):
        root = self._mini_root()
        argv = [
            "--dump-dir",
            str(DUMP_DIR),
            "--series-id",
            "900101",
            "--max-issues",
            "1",
            "--root",
            str(root),
        ]
        self.assertEqual(ingest.main(argv), 0)
        comics = (root / "src/data/comics.ts").read_text()
        self.assertIn('gcdIssueId: "8000001"', comics)
        self.assertIn('gcdIssueId: "8000004"', comics)
        self.assertIn('variant: "Cover B"', comics)
        self.assertIn("im-gcd-fixture-indie-1-cover-b", comics)

    def test_refuses_api_without_use_api_flag(self):
        root = self._mini_root()
        with self.assertRaises(SystemExit):
            ingest.main(["--root", str(root), "--series-id", "900101", "--dry-run"])


if __name__ == "__main__":
    unittest.main()
