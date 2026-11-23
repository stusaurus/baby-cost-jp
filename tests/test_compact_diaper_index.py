"""The diaper hub stays useful with or without valid purchase-planner offers."""
import unittest
from datetime import datetime, timezone

from src.config import SITE_URL, load_categories
from src.render import render_diaper_index
from tests.test_home_diaper_purchase_paths import KINDS, offer

NOW = datetime(2026, 11, 23, tzinfo=timezone.utc)


class CompactDiaperIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.categories = load_categories()
        cls.snapshots = {
            key: {"products": [offer(key + "-80"), offer(key + "-160", 160, 5200)]}
            for key, _, _ in KINDS
        }
        # Every type-size in the price overview is retained independently of
        # whether its purchase calculator has verified offers.
        for seg in cls.categories["diapers"]["segments"]:
            cls.snapshots.setdefault(seg["id"], {"products": []})

    def test_compact_hub_contains_one_purchase_section_and_five_buy_paths(self):
        html = render_diaper_index(self.categories, NOW, self.snapshots)
        self.assertEqual(html.count('id="diaper-purchase-paths"'), 1)
        self.assertEqual(html.count('data-nav-source="diaper_index_compact_planner"'), 5)
        self.assertEqual(html.count('class="home-purchase-path"'), 5)
        self.assertEqual(html.count('data-nav-source="diaper_index_purchase_jump"'), 1)
        self.assertEqual(html.count('data-nav-source="diaper_index_type_size_jump"'), 1)
        self.assertEqual(html.count('data-nav-source="diaper_index_price_jump"'), 1)
        self.assertIn('href="#diaper-purchase-paths"', html)
        self.assertIn('href="#diaper-selector"', html)
        self.assertIn('href="#diaper-price-by-size"', html)
        self.assertIn('id="diaper-price-by-size"', html)
        self.assertIn('id="diaper-selector"', html)
        self.assertIn("現在比較できる2商品", html)
        self.assertIn("今使っているタイプ", html)
        self.assertIn('data-nav-source="diaper_index_nursery_planner"', html)
        self.assertIn("保育園用もまとめて必要？", html)
        self.assertNotIn('data-nav-source="home_diaper_size_list"', html)
        self.assertNotIn('<h2>すべての比較条件</h2>', html)
        self.assertNotIn('class="choices"', html)
        self.assertNotIn('class="home-section diaper-planner-entry"', html)
        self.assertNotIn('class="home-section diaper-planner-entry newborn-planner-entry"', html)
        self.assertNotIn('class="home-section diaper-planner-entry tape-s-planner-entry"', html)
        self.assertNotIn('class="home-section diaper-planner-entry tape-m-planner-entry"', html)

    def test_all_nine_direct_index_links_survive_in_static_price_table(self):
        html = render_diaper_index(self.categories, NOW, self.snapshots)
        self.assertEqual(html.count('<th scope="row"><a href="'), len(self.categories['diapers']['segments']))
        for seg in self.categories["diapers"]["segments"]:
            url = f"{SITE_URL}diapers/{seg['type']}/{seg['size']}/"
            self.assertIn(f'<th scope="row"><a href="{url}"', html)
        self.assertIn("1枚単価と支払総額は、別の商品になる場合があります。", html)

    def test_unverified_size_has_no_dead_purchase_link_but_keeps_price_link(self):
        altered = dict(self.snapshots)
        altered["tape-s"] = {"products": [offer("only")]}
        altered["pants-s"] = {"products": [
            offer("ok"), offer("unverified", ship="unknown")
        ]}
        html = render_diaper_index(self.categories, NOW, altered)
        self.assertEqual(html.count('data-nav-source="diaper_index_compact_planner"'), 3)
        self.assertNotIn('diapers/tape/s/#purchase-planner', html)
        self.assertNotIn('diapers/pants/s/#purchase-planner', html)
        self.assertIn(f'href="{SITE_URL}diapers/tape/s/"', html)
        self.assertIn(f'href="{SITE_URL}diapers/pants/s/"', html)
        self.assertIn("比較準備中", html)

    def test_zero_verified_calculators_has_no_empty_section_or_broken_jump(self):
        html = render_diaper_index(self.categories, NOW, {})
        self.assertNotIn('id="diaper-purchase-paths"', html)
        self.assertNotIn('href="#diaper-purchase-paths"', html)
        self.assertNotIn('data-nav-source="diaper_index_compact_planner"', html)
        self.assertIn('href="#diaper-selector"', html)
        self.assertIn('href="#diaper-price-by-size"', html)
        self.assertIn('id="diaper-price-by-size"', html)
        self.assertIn('data-nav-source="diaper_index_nursery_planner"', html)
        self.assertIn("未確認", html)


if __name__ == "__main__":
    unittest.main()
