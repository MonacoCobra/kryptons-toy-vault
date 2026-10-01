"""Confidence rules for scripts/ml_verified_photos.py."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ml_verified_photos as m  # noqa: E402


def fig(name, subtitle, year, *, line="Marvel Legends", company="hasbro", fid="f"):
    return {
        "id": fid,
        "name": name,
        "subtitle": subtitle,
        "line": line,
        "company": company,
        "releaseDate": f"{year}-01-01",
    }


def row(name, wave, year, *, line="Hasbro"):
    return {"name": name, "wave": wave, "year": str(year), "line": line}


class MatchRules(unittest.TestCase):
    def test_xmen97_cyclops_matches_named_wave(self):
        info = m.pair_ok(
            row("Cyclops", "X-Men '97 Wave 2", 2024),
            fig("Cyclops X-Men '97 (2024)", "X-Men '97 Legends", 2024),
        )
        self.assertIsNotNone(info)
        self.assertEqual(info["relation"], "agree")
        self.assertEqual(info["how"], "prefix")

    def test_deluxe_beast_does_not_claim_xmen97_beast(self):
        info = m.pair_ok(
            row("Beast", "Deluxe", 2026),
            fig("Beast X-Men '97 (2026)", "X-Men '97 Legends", 2026),
        )
        self.assertIsNone(info)

    def test_xmen97_beast_matches(self):
        info = m.pair_ok(
            row("Beast", "X-Men '97 Wave 1", 2026),
            fig("Beast X-Men '97 (2026)", "X-Men '97 Legends", 2026),
        )
        self.assertIsNotNone(info)
        self.assertEqual(info["relation"], "agree")

    def test_series_number_conflict(self):
        info = m.pair_ok(
            row("Iron Man", "Series 8", 2006, line="Toy Biz"),
            fig(
                "Iron Man (2006)",
                "Series 7",
                2006,
                line="Marvel Legends (Toy Biz)",
                company="toybiz",
            ),
        )
        self.assertIsNone(info)

    def test_roman_series_agrees(self):
        info = m.pair_ok(
            row("Deadpool", "Series VI", 2004, line="Toy Biz"),
            fig(
                "Deadpool (2004)",
                "Series VI",
                2004,
                line="Marvel Legends (Toy Biz)",
                company="toybiz",
            ),
        )
        self.assertIsNotNone(info)

    def test_wave_index_conflict(self):
        info = m.pair_ok(
            row("Nebula", "Guardians of the Galaxy Vol. 3 Wave 2", 2023),
            fig("Nebula Guardians of the Galaxy Vol. 3 (2023)", "Vol. 3 Wave6", 2023),
        )
        self.assertIsNone(info)

    def test_red_hulk_does_not_match_plain_hulk(self):
        info = m.pair_ok(
            row("Red Hulk", "Red Hulk BAF Wave", 2020),
            fig("Hulk (2020)", "Avengers", 2020),
        )
        self.assertIsNone(info)

    def test_variant_in_subtitle_matches(self):
        info = m.pair_ok(
            row("Totally Awesome Hulk", "Totally Awesome Hulk BAF Wave", 2023),
            fig("Hulk (2023)", "Totally Awesome Hulk BAF", 2023),
        )
        self.assertIsNotNone(info)
        self.assertEqual(info["how"], "suffix")

    def test_two_pack_does_not_match_single(self):
        info = m.pair_ok(
            row("Captain Marvel", "Endgame", 2021),
            fig("Captain Marvel & Rescue (2021)", "Infinity Saga 2-Pack", 2021),
        )
        self.assertIsNone(info)

    def test_weak_deluxe_does_not_bridge_a_named_line(self):
        info = m.pair_ok(
            row("Apocalypse", "Deluxe", 2022),
            fig("Apocalypse (2022)", "Age of Apocalypse Deluxe", 2022),
        )
        self.assertIsNone(info)

    def test_vhs_does_not_match_xmen97(self):
        info = m.pair_ok(
            row("Storm", "X-Men Animated VHS Series", 2022),
            fig("Storm (2022)", "Marvel Legends X-Men 97", 2022),
        )
        self.assertIsNone(info)

    def test_same_volume_matches_across_wave_number(self):
        info = m.pair_ok(
            row("Drax", "GOTG Vol. 3 Cosmo BAF Wave", 2023),
            fig("Drax (2023)", "Vol. 3 Wave6", 2023),
        )
        self.assertIsNotNone(info)
        self.assertEqual(info["relation"], "agree")

    def test_retro_card_matches_retro_wave(self):
        info = m.pair_ok(
            row("Cyclops", "Retro 2019", 2019),
            fig("Cyclops (2019)", "Retro Card", 2019),
        )
        self.assertIsNotNone(info)

    def test_retailer_does_not_match_classic(self):
        info = m.pair_ok(
            row("Black Panther", "Walmart", 2018),
            fig("Black Panther (2018)", "Classic", 2018),
        )
        self.assertIsNone(info)

    def test_variant_in_both_names_matches_without_a_wave(self):
        info = m.pair_ok(
            row("Spider-Man, Stealth Suit", "UK Wave", 2019),
            fig("Spider-Man Stealth Suit (2019)", "Stealth Suit", 2019),
        )
        self.assertIsNotNone(info)

    def test_retailer_wave_does_not_match_a_named_subtitle(self):
        info = m.pair_ok(
            row("Thor", "Fan Channel", 2026),
            fig("Thor (2026)", "Ragnarok", 2026),
        )
        self.assertIsNone(info)

    def test_unlabeled_listing_can_take_a_specific_photo(self):
        info = m.pair_ok(
            row("Wendigo", "Wendigo BAF Wave", 2019),
            fig("Wendigo (2019)", "BAF", 2019),
        )
        self.assertIsNotNone(info)
        self.assertEqual(info["relation"], "agree")

    def test_dirty_year_requires_wave_agreement(self):
        # release 2025, parenthetical 2026. Generic wave must not attach.
        catalog = fig("Scarlet Witch (2026)", "Classic", 2025)
        self.assertIsNone(m.pair_ok(row("Scarlet Witch", "Deluxe", 2026), catalog))
        agreed = m.pair_ok(row("Scarlet Witch", "Chaos Magic", 2026), fig("Scarlet Witch (2026)", "Chaos Magic", 2025))
        self.assertIsNotNone(agreed)
        self.assertEqual(agreed["yearBasis"], "paren")

    def test_unique_resolution_drops_two_photos(self):
        pairs = [
            {"rowIndex": 0, "figureId": "a", "sha": "1", "relation": "agree"},
            {"rowIndex": 1, "figureId": "a", "sha": "2", "relation": "agree"},
        ]
        final, row_ambig, fig_ambig = m.resolve_unique(pairs)
        self.assertEqual(final, [])
        self.assertIn("a", fig_ambig)
        self.assertEqual(row_ambig, {})

    def test_agree_beats_generic(self):
        pairs = [
            {"rowIndex": 0, "figureId": "a", "sha": "1", "relation": "agree"},
            {"rowIndex": 1, "figureId": "a", "sha": "2", "relation": "generic"},
        ]
        final, _, fig_ambig = m.resolve_unique(pairs)
        self.assertEqual([p["rowIndex"] for p in final], [0])
        self.assertEqual(fig_ambig, {})

    def test_wix_renditions_share_a_canon(self):
        a = "https://static.wixstatic.com/media/adc447_abc123abc123abc123abc123abc123ab~mv2.jpg/v1/fill/w_800,h_800/adc447_abc123abc123abc123abc123abc123ab~mv2.jpg"
        b = "https://static.wixstatic.com/media/adc447_abc123abc123abc123abc123abc123ab~mv2.jpg/v1/fill/w_1200,h_1200,al_c,q_90/adc447_abc123abc123abc123abc123abc123ab~mv2.jpg"
        self.assertEqual(m.canon_url(a), m.canon_url(b))
        self.assertNotEqual(m.canon_url(a), m.canon_url(a.replace("abc123abc123abc123abc123abc123ab", "fff123fff123fff123fff123fff123ff")))


if __name__ == "__main__":
    unittest.main()
