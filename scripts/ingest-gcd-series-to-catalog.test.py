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
from pathlib import Path
from unittest.mock import MagicMock

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import comic_backlog_common as backlog  # noqa: E402


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

    def test_429_raises_delay_then_aborts_instead_of_ceiling_retry(self):
        slept: list[float] = []

        class Always429:
            def __init__(self):
                self.calls = 0

            def __call__(self, req, timeout=30):
                self.calls += 1
                raise urllib.error.HTTPError(req.full_url, 429, "Too Many", hdrs=None, fp=None)

        boom = Always429()
        client = ingest.GcdClient(7.0, sleep=slept.append, urlopen=boom)
        with self.assertRaises(ingest.RateLimitAbort):
            client.get_json("https://www.comics.org/api/issue/1/")
        self.assertEqual(boom.calls, ingest.MAX_429_RETRIES + 1)
        self.assertTrue(client.aborted)
        self.assertGreaterEqual(client.session_delay, 30.0)
        self.assertLessEqual(client.session_delay, ingest.SESSION_DELAY_CAP)
        self.assertTrue(slept)
        self.assertLessEqual(max(slept), 90.0)
        self.assertNotIn(600.0, slept)

    def test_429_then_success_raises_session_delay(self):
        class Once429:
            def __init__(self):
                self.n = 0

            def __call__(self, req, timeout=30):
                self.n += 1
                if self.n == 1:
                    raise urllib.error.HTTPError(req.full_url, 429, "Too Many", hdrs=None, fp=None)
                body = json.dumps({"ok": True}).encode()
                resp = MagicMock()
                resp.read.return_value = body
                resp.__enter__.return_value = resp
                resp.__exit__.return_value = False
                return resp

        opener = Once429()
        client = ingest.GcdClient(7.0, sleep=lambda _s: None, urlopen=opener)
        data = client.get_json("https://www.comics.org/api/issue/1/")
        self.assertEqual(data, {"ok": True})
        self.assertGreaterEqual(client.session_delay, 30.0)
        self.assertFalse(client.aborted)


class FixtureIngestTest(unittest.TestCase):
    def tearDown(self):
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
        self.assertIn("variant", skip_reasons)
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
        report = self._run(["900101"], extra=["--max-issues", "1"], root=root)
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


if __name__ == "__main__":
    unittest.main()
