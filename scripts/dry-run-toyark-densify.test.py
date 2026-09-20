#!/usr/bin/env python3
"""Apply-path proof for Toyark densify (replay fixture, no live Toyark).

Run: python3 scripts/dry-run-toyark-densify.test.py
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

from figure_identity import is_gtin  # noqa: E402


def _load_mod():
    path = SCRIPT_DIR / "dry-run-toyark-densify.py"
    spec = importlib.util.spec_from_file_location("dry_run_toyark_densify", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_mod()
FIXTURE = SCRIPT_DIR / "fixtures/toyark-densify/posts.json"
COMIC_SENTINEL = ROOT / "src/data/figure-archive/oneshot.json"


def _seed_row() -> dict:
    return {
        "id": "ht-wolverine-seed",
        "name": "Wolverine",
        "subtitle": "Deadpool & Wolverine",
        "line": "Hot Toys MMS",
        "company": "hottoys",
        "kind": "figure",
        "releaseDate": "2026-01-01",
        "msrp": 280.0,
        "scale": "1/6",
        "demand": 1.35,
        "tags": ["seed"],
        "source": "test",
    }


class ToyarkApplyTests(unittest.TestCase):
    def test_apply_refuses_non_list_oneshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            oneshot = td / "oneshot.json"
            oneshot.write_text('{"not": "a list"}\n')
            rc = mod.main(
                [
                    "--apply",
                    "--posts-json",
                    str(FIXTURE),
                    "--after",
                    "2026-09-01",
                    "--oneshot",
                    str(oneshot),
                    "--aliases",
                    str(td / "aliases.json"),
                    "--image-urls",
                    str(td / "urls.json"),
                    "--sku-map",
                    str(td / "sku-map.json"),
                    "--stats",
                    str(td / "stats.json"),
                    "--report",
                    str(td / "report.json"),
                ]
            )
            self.assertEqual(rc, 1)
            self.assertFalse((td / "aliases.json").exists())

    def test_apply_refuses_skip_oneshot(self) -> None:
        rc = mod.main(["--apply", "--skip-oneshot", "--posts-json", str(FIXTURE)])
        self.assertEqual(rc, 2)

    def test_apply_replay_injects_without_inventing_gtin(self) -> None:
        comic_mtime = COMIC_SENTINEL.stat().st_mtime if COMIC_SENTINEL.exists() else None
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            oneshot = td / "oneshot.json"
            aliases = td / "aliases.json"
            urls = td / "urls.json"
            sku_map = td / "sku-map.json"
            stats = td / "stats.json"
            report = td / "report.json"
            oneshot.write_text(json.dumps([_seed_row()], indent=2) + "\n")
            aliases.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "policy": "gtin-canonical",
                        "aliasesByFigureId": {},
                        "aliasToFigureId": {},
                    },
                    indent=2,
                )
                + "\n"
            )
            urls.write_text("{}\n")
            sku_map.write_text("{}\n")

            argv = [
                "--apply",
                "--posts-json",
                str(FIXTURE),
                "--after",
                "2026-09-01",
                "--cap",
                "50",
                "--oneshot",
                str(oneshot),
                "--aliases",
                str(aliases),
                "--image-urls",
                str(urls),
                "--sku-map",
                str(sku_map),
                "--stats",
                str(stats),
                "--report",
                str(report),
            ]
            rc = mod.main(argv)
            self.assertEqual(rc, 0)

            rows = json.loads(oneshot.read_text())
            self.assertIsInstance(rows, list)
            added = [r for r in rows if str(r.get("id") or "").startswith("ta-")]
            self.assertGreaterEqual(len(added), 2, f"expected ta- rows, got {rows}")

            batman = next((r for r in added if "Batman" in str(r.get("name"))), None)
            self.assertIsNotNone(batman, f"Batman missing from {added}")
            assert batman is not None
            self.assertEqual(batman["company"], "hottoys")
            self.assertNotIn("sku", batman)
            self.assertTrue(str(batman.get("imageUrl") or "").startswith("http"))
            self.assertIn("toyark", batman["tags"])
            self.assertIn("toyark-densify", batman["tags"])
            self.assertIn("hottoys", batman["tags"])

            elvira = next((r for r in added if "Elvira" in str(r.get("name"))), None)
            self.assertIsNotNone(elvira)
            assert elvira is not None
            self.assertEqual(elvira.get("sku"), "634482089999")
            self.assertTrue(is_gtin(elvira["sku"]))

            for r in added:
                sku = r.get("sku")
                if sku is not None:
                    self.assertTrue(is_gtin(sku), f"non-GTIN sku invented: {sku}")

            alias_doc = json.loads(aliases.read_text())
            bat_als = alias_doc["aliasesByFigureId"][batman["id"]]
            self.assertIn("MMS897", bat_als)
            self.assertTrue(any(str(a).startswith("https://www.toyark.com/") for a in bat_als))
            self.assertTrue(any(str(a).startswith("toyark:") for a in bat_als))

            url_doc = json.loads(urls.read_text())
            self.assertEqual(url_doc[batman["id"]], batman["imageUrl"])

            sku_doc = json.loads(sku_map.read_text())
            self.assertNotIn(batman["id"], sku_doc)
            self.assertEqual(sku_doc[elvira["id"]], "634482089999")

            rep = json.loads(report.read_text())
            self.assertEqual(rep["mode"], "apply")
            self.assertGreaterEqual(rep["summary"]["applied"], 2)
            skip_reasons = {s.get("reason") for s in rep.get("applySkipped") or []}
            self.assertIn("multipack", skip_reasons)

            st = json.loads(stats.read_text())
            self.assertEqual(st["applied"], rep["summary"]["applied"])
            self.assertEqual(st["comics"], "untouched")

            # Second apply is a no-op (identity already in the copy).
            rc2 = mod.main(argv)
            self.assertEqual(rc2, 0)
            rows2 = json.loads(oneshot.read_text())
            self.assertEqual(len(rows2), len(rows))
            rep2 = json.loads(report.read_text())
            self.assertEqual(rep2["summary"]["applied"], 0)

            if comic_mtime is not None:
                self.assertEqual(COMIC_SENTINEL.stat().st_mtime, comic_mtime)

    def test_wrapper_help(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "toyark_densify_wrapper", SCRIPT_DIR / "toyark-densify.py"
        )
        assert spec and spec.loader
        wrap = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(wrap)
        with self.assertRaises(SystemExit) as cm:
            wrap.main(["--help"])
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    raise SystemExit(unittest.main(verbosity=2))
