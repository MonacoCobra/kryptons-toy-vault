"""Tests for scripts/audit_blocklist.py (run: python3 scripts/audit_blocklist.test.py)."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_blocklist as ab  # noqa: E402

DOC = {
    "aliasesByFigureId": {"fig-a": ["KEEP1", "787926174090"], "gone-1": ["X1"]},
    "aliasToFigureId": {"KEEP1": "fig-a", "787926174090": "fig-a", "X1": "gone-1"},
    "strippedCodes": [
        {"figureId": "fig-a", "codes": ["787926174090", "5010996361400"],
         "imageUrls": ["https://cdn.shopify.com/s/files/1/x/files/wrong-photo_600x600.jpg?v=1"],
         "imageDropped": True, "reason": "t"},
    ],
    "removed": [{"keepId": None, "dropId": "gone-1", "reason": "t"}],
}


class AuditBlocklistTest(unittest.TestCase):
    def test_blocks_per_figure_only(self):
        b = ab.load(doc=DOC)
        self.assertTrue(b.code_blocked("fig-a", "787926174090"))
        self.assertTrue(b.code_blocked("fig-a", "787926174090dmg"))
        self.assertTrue(b.code_blocked("fig-a", "HAS361400"))  # same Hasbro item as the stripped EAN
        self.assertFalse(b.code_blocked("fig-b", "787926174090"))  # other rows may carry it
        self.assertFalse(b.code_blocked("fig-a", "KEEP1"))
        self.assertTrue(b.image_blocked("fig-a", "https://cdn.shopify.com/s/files/1/x/files/wrong-photo.jpg?v=9"))
        self.assertFalse(b.image_blocked("fig-a", "https://cdn.shopify.com/s/files/1/x/files/right.jpg"))
        self.assertTrue(b.id_removed("gone-1"))

    def test_enforce_undoes_reattachment_and_recreation(self):
        doc = json.loads(json.dumps(DOC))
        rows = [
            {"id": "fig-a", "sku": "787926174090",
             "imageUrl": "https://cdn.shopify.com/s/files/1/x/files/wrong-photo_600x600.jpg?v=2"},
            {"id": "fig-b", "sku": "787926174090", "imageUrl": "https://x/wrong-photo.jpg"},
            {"id": "gone-1", "name": "recreated"},
        ]
        urls = {"fig-a": "https://cdn.shopify.com/s/files/1/x/files/wrong-photo.jpg", "gone-1": "https://x/y.jpg"}
        sku_map = {"fig-a": "787926174090", "gone-1": "X1"}
        n = ab.enforce(rows, alias_doc=doc, image_urls=urls, sku_map=sku_map)
        self.assertEqual([r["id"] for r in rows], ["fig-a", "fig-b"])
        self.assertNotIn("sku", rows[0])
        self.assertIsNone(rows[0]["imageUrl"])
        self.assertEqual(rows[1]["sku"], "787926174090")  # untouched: not stripped from fig-b
        self.assertEqual(doc["aliasesByFigureId"], {"fig-a": ["KEEP1"]})
        self.assertEqual(doc["aliasToFigureId"], {"KEEP1": "fig-a"})
        self.assertEqual(urls, {})
        self.assertEqual(sku_map, {})
        self.assertGreater(ab.total(n), 0)
        # idempotent: a clean catalog reports zero re-attachments
        self.assertEqual(ab.total(ab.enforce(rows, alias_doc=doc, image_urls=urls, sku_map=sku_map)), 0)

    def test_live_catalog_is_clean(self):
        root = Path(__file__).resolve().parents[1] / "src/data"
        doc = json.loads((root / "figure-sku-aliases.json").read_text())
        rows = json.loads((root / "figure-archive/oneshot.json").read_text())
        urls = json.loads((root / "figure-image-urls.json").read_text())
        sku_map = json.loads((root / "figure-sku-map.json").read_text())
        n = ab.enforce(rows, alias_doc=doc, image_urls=urls, sku_map=sku_map)
        self.assertEqual(ab.total(n), 0, n)


if __name__ == "__main__":
    unittest.main()
