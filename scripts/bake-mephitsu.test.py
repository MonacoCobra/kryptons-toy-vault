#!/usr/bin/env python3
"""Photo-fill guards for bake-mephitsu (Kingdom Cheetor / PotP Swoop regressions)."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
_spec = importlib.util.spec_from_file_location("bake_mephitsu", SCRIPT_DIR / "bake-mephitsu.py")
assert _spec and _spec.loader
bm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bm)
import audit_blocklist  # noqa: E402


class PhotoVetoTests(unittest.TestCase):
    def test_blocked_listing_barcode_vetoes_photo(self) -> None:
        # Listing barcode was stripped from this row -> its photo is the other product's.
        blocks = audit_blocklist.load(
            doc={"strippedCodes": [{"figureId": "tfc-kingdom-cheetor", "codes": ["5010996216205"]}]}
        )
        row = {"id": "tfc-kingdom-cheetor", "name": "Cheetor", "scale": "Deluxe"}
        meph = {"title": "Cheetor — Buzzworthy Bumblebee · 2023", "productId": "p1", "sku": None}
        twins = {"p1": {"5010996216205"}}  # barcode only present on the twin line file
        reason = bm.listing_photo_veto(row, meph, blocks, {}, {}, twins)
        self.assertTrue(reason and reason.startswith("listing_code_audit_blocked"), reason)

    def test_listing_gtin_owned_by_other_row_vetoes_photo(self) -> None:
        blocks = audit_blocklist.load(doc={"strippedCodes": []})
        row = {"id": "tfpotp-deluxe-dinobot-swoop", "name": "Dinobot Swoop", "scale": "Deluxe"}
        meph = {"title": "Dinobot Swoop — Wave 15 · 2024", "sku": "5010996367754"}
        owner = {"5010996367754": "tfaotp-selects-g2-dinobot-swoop-g2-dinobot-sludge"}
        reason = bm.listing_photo_veto(row, meph, blocks, owner, {}, {})
        self.assertTrue(reason and reason.startswith("listing_gtin_owned_by"), reason)

    def test_own_gtin_does_not_veto(self) -> None:
        blocks = audit_blocklist.load(doc={"strippedCodes": []})
        row = {"id": "a", "name": "X", "sku": "5010996367754"}
        meph = {"sku": "5010996367754"}
        self.assertIsNone(bm.listing_photo_veto(row, meph, blocks, {"5010996367754": "a"}, {}, {}))

    def test_class_mismatch(self) -> None:
        fig = {"name": "Dinobot Swoop", "scale": "Deluxe", "subtitle": "Power of the Primes Deluxe Class"}
        meph = {"title": "Dinobot Swoop — Wave 15", "name": "Dinobot Swoop", "tags": ["Leader Class"]}
        self.assertEqual(bm.image_fill_blocked(fig, meph, "u", set()), "class_mismatch")
        meph["tags"] = ["Deluxe Class"]
        self.assertIsNone(bm.image_fill_blocked(fig, meph, "u", set()))


if __name__ == "__main__":
    unittest.main()
