#!/usr/bin/env python3
"""Fixture proof for LOCG UPC / missing-cover backfill selection.

No live League of Comic Geeks traffic. Run:

  python3 scripts/backfill-comic-upcs.test.py
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))


def _load_backfill():
    path = SCRIPT_DIR / "backfill-comic-upcs.py"
    spec = importlib.util.spec_from_file_location("backfill_comic_upcs", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bf = _load_backfill()


def _row(
    *,
    series="Creepshow",
    issue="1",
    publisher="Image",
    cover_date="2022-09-21",
    variant=None,
    upc=None,
    cover=None,
    fmt="single",
    demand=0.8,
    key=0,
) -> dict:
    return {
        "series": series,
        "issue": issue,
        "publisher": publisher,
        "coverDate": cover_date,
        "variant": variant,
        "upc": upc,
        "cover": cover,
        "format": fmt,
        "demand": demand,
        "key": key,
    }


MAIN_UPC = "70985303557200111"
VANCE_UPC = "70985303557200131"
SHALVEY_UPC = "70985303557200121"
MAIN_COVER = "https://s3.amazonaws.com/comicgeeks/comics/covers/large-111.jpg"
VANCE_COVER = "https://s3.amazonaws.com/comicgeeks/comics/covers/large-222.jpg"
SHALVEY_COVER = "https://s3.amazonaws.com/comicgeeks/comics/covers/large-333.jpg"

CREEPSHOW_META = {
    "im-creepshow-1": _row(upc=MAIN_UPC),
    "im-creepshow-1-vance-kelly-cover": _row(variant="Vance Kelly Cover", upc=VANCE_UPC),
    "im-creepshow-1-declan-shalvey-cover": _row(variant="Declan Shalvey Cover", upc=SHALVEY_UPC),
    "im-creepshow-omnibus": _row(series="Creepshow", issue="1", fmt="omnibus", upc="9781534320000"),
}

CREEPSHOW_UPC_MAP = {
    "im-creepshow-1": {"upc": MAIN_UPC, "gcdIssueId": "2434621", "source": "gcd"},
    "im-creepshow-1-vance-kelly-cover": {
        "upc": VANCE_UPC,
        "gcdIssueId": "2436703",
        "source": "gcd",
    },
    "im-creepshow-1-declan-shalvey-cover": {
        "upc": SHALVEY_UPC,
        "gcdIssueId": "2436947",
        "source": "gcd",
    },
}

SERIES_ISSUE = {
    "locgId": "111",
    "slug": "creepshow-1",
    "title": "Creepshow #1",
    "main": True,
    "coverUrl": MAIN_COVER,
    "variants": [
        {
            "locgId": "222",
            "slug": "creepshow-1-vance-kelly-variant",
            "title": "Creepshow #1 Vance Kelly Cover",
            "main": False,
            "coverUrl": VANCE_COVER,
        },
        {
            "locgId": "333",
            "slug": "creepshow-1-declan-shalvey-variant",
            "title": "Creepshow #1 Declan Shalvey Cover",
            "main": False,
            "coverUrl": SHALVEY_COVER,
        },
    ],
}


class MissingCoverCandidatesTest(unittest.TestCase):
    def test_upc_row_without_cover_is_a_cover_candidate(self):
        default_ids = bf.build_catalog_candidates(
            CREEPSHOW_META, CREEPSHOW_UPC_MAP, min_year=2005, limit=50
        )
        self.assertNotIn("im-creepshow-1", default_ids)
        self.assertNotIn("im-creepshow-1-vance-kelly-cover", default_ids)

        fill_ids = bf.build_catalog_candidates(
            CREEPSHOW_META,
            CREEPSHOW_UPC_MAP,
            min_year=2005,
            limit=50,
            missing_covers=True,
            cover_urls={},
        )
        self.assertIn("im-creepshow-1", fill_ids)
        self.assertIn("im-creepshow-1-vance-kelly-cover", fill_ids)
        self.assertIn("im-creepshow-1-declan-shalvey-cover", fill_ids)
        self.assertNotIn("im-creepshow-omnibus", fill_ids)
        self.assertIsNone(
            bf.should_skip_catalog_row(
                "im-creepshow-1",
                meta=CREEPSHOW_META,
                upc_map=CREEPSHOW_UPC_MAP,
                cover_urls={},
                missing_covers=True,
            )
        )
        self.assertEqual(
            bf.should_skip_catalog_row(
                "im-creepshow-1",
                meta=CREEPSHOW_META,
                upc_map=CREEPSHOW_UPC_MAP,
                cover_urls={},
                missing_covers=False,
            ),
            "has_upc",
        )

    def test_has_cover_rows_are_not_re_crawled(self):
        cover_urls = {"im-creepshow-1": MAIN_COVER}
        fill_ids = bf.build_catalog_candidates(
            CREEPSHOW_META,
            CREEPSHOW_UPC_MAP,
            min_year=2005,
            limit=50,
            missing_covers=True,
            cover_urls=cover_urls,
        )
        self.assertNotIn("im-creepshow-1", fill_ids)
        self.assertIn("im-creepshow-1-vance-kelly-cover", fill_ids)
        self.assertEqual(
            bf.should_skip_catalog_row(
                "im-creepshow-1",
                meta=CREEPSHOW_META,
                upc_map=CREEPSHOW_UPC_MAP,
                cover_urls=cover_urls,
                missing_covers=True,
            ),
            "has_cover",
        )

        via_map = dict(CREEPSHOW_UPC_MAP)
        via_map["im-creepshow-1-vance-kelly-cover"] = {
            **via_map["im-creepshow-1-vance-kelly-cover"],
            "coverUrl": VANCE_COVER,
        }
        fill_via_map = bf.build_catalog_candidates(
            CREEPSHOW_META,
            via_map,
            min_year=2005,
            limit=50,
            missing_covers=True,
            cover_urls={},
        )
        self.assertNotIn("im-creepshow-1-vance-kelly-cover", fill_via_map)
        self.assertEqual(
            bf.should_skip_catalog_row(
                "im-creepshow-1-vance-kelly-cover",
                meta=CREEPSHOW_META,
                upc_map=via_map,
                cover_urls={},
                missing_covers=True,
            ),
            "has_cover",
        )
        pending = bf.retain_pending_ids(
            ["im-creepshow-1", "im-creepshow-1-vance-kelly-cover"],
            via_map,
            cover_urls,
            missing_covers=True,
            meta=CREEPSHOW_META,
        )
        self.assertEqual(pending, [])

    def test_default_mode_still_drops_upc_and_variants(self):
        no_upc = {
            "im-new-1": _row(series="New Book", issue="1", upc=None),
            "im-new-1-cover-b": _row(series="New Book", issue="1", variant="Cover B", upc=None),
        }
        ids = bf.build_catalog_candidates(no_upc, {}, min_year=2005, limit=20)
        self.assertEqual(ids, ["im-new-1"])


class VariantCoverIdentityTest(unittest.TestCase):
    def test_variant_sibling_does_not_take_the_main_cover(self):
        main = bf.pick_locg_issue_for_row(SERIES_ISSUE, None)
        self.assertIsNotNone(main)
        assert main is not None
        self.assertEqual(main["locgId"], "111")
        self.assertEqual(main["coverUrl"], MAIN_COVER)

        vance = bf.pick_locg_issue_for_row(SERIES_ISSUE, "Vance Kelly Cover")
        self.assertIsNotNone(vance)
        assert vance is not None
        self.assertEqual(vance["locgId"], "222")
        self.assertEqual(vance["coverUrl"], VANCE_COVER)
        self.assertNotEqual(vance["coverUrl"], main["coverUrl"])
        self.assertNotEqual(vance["locgId"], main["locgId"])

        shalvey = bf.pick_locg_issue_for_row(SERIES_ISSUE, "Declan Shalvey Cover")
        self.assertIsNotNone(shalvey)
        assert shalvey is not None
        self.assertEqual(shalvey["locgId"], "333")
        self.assertEqual(shalvey["coverUrl"], SHALVEY_COVER)
        self.assertNotEqual(shalvey["coverUrl"], main["coverUrl"])
        self.assertNotEqual(shalvey["coverUrl"], vance["coverUrl"])

        # No name match → do not fall back to the main (would steal Cover A art)
        self.assertIsNone(bf.pick_locg_issue_for_row(SERIES_ISSUE, "Memphis Comic Expo"))

        main_hit = {
            "upc": MAIN_UPC,
            "title": "Creepshow #1",
            "issue": "1",
            "publisher": "Image",
            "series": "Creepshow",
            "coverUrl": MAIN_COVER,
        }
        self.assertEqual(
            bf.locg_hit_identity_reason(
                main_hit,
                CREEPSHOW_META["im-creepshow-1-vance-kelly-cover"],
                existing_upc=VANCE_UPC,
            ),
            "upc_mismatch",
        )
        self.assertIsNone(
            bf.locg_hit_identity_reason(
                {**main_hit, "upc": VANCE_UPC, "title": "Creepshow #1 Vance Kelly Cover"},
                CREEPSHOW_META["im-creepshow-1-vance-kelly-cover"],
                existing_upc=VANCE_UPC,
            )
        )
        self.assertEqual(
            bf.locg_hit_identity_reason(
                {
                    "title": "Creepshow #1 Vance Kelly Cover",
                    "issue": "1",
                    "publisher": "Image",
                    "series": "Creepshow",
                    "slug": "creepshow-1-vance-kelly-variant",
                },
                CREEPSHOW_META["im-creepshow-1"],
                existing_upc=MAIN_UPC,
            ),
            "variant_mismatch",
        )

    def test_keep_catalog_ids_drops_ghosts(self):
        kept = bf.keep_catalog_ids(
            ["im-creepshow-1", "ghost-pruned-id"],
            CREEPSHOW_META,
            label="test",
        )
        self.assertEqual(kept, ["im-creepshow-1"])


class CatalogParseTest(unittest.TestCase):
    def test_parse_sees_dump_variant_upc_without_cover(self):
        meta = bf.parse_comics_meta()
        row = meta.get("im-creepshow-1-vance-kelly-cover")
        if not row:
            self.skipTest("Creepshow dump row not in comics.ts")
        self.assertEqual(row.get("variant"), "Vance Kelly Cover")
        self.assertTrue(row.get("upc"))
        self.assertFalse(row.get("cover"))
        main = meta.get("im-creepshow-1")
        self.assertTrue(main and main.get("upc"))
        self.assertNotEqual(row.get("upc"), main.get("upc"))


if __name__ == "__main__":
    raise SystemExit(unittest.main())
