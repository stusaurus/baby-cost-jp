"""Homepage direct shopping paths must reflect the real, verified, indexed catalog."""
import unittest
from datetime import datetime, timezone

from src.config import load_categories, SITE_URL
from src.render import home_diaper_purchase_paths, render_home

NOW = datetime(2026, 11, 23, tzinfo=timezone.utc)
KINDS = (
    ("tape-newborn", "tape", "newborn"),
    ("tape-s", "tape", "s"),
    ("tape-m", "tape", "m"),
    ("pants-s", "pants", "s"),
    ("pants-m", "pants", "m"),
)


def offer(source, pieces=80, price=2800, *, confidence=.99, ship="rakuten_postage_filter"):
    return dict(
        source_id=source, name=f"赤ちゃん用 紙おむつ {pieces}枚",
        price_yen=price, unit_price=price/pieces,
        quantity=dict(total=pieces, base_unit="piece", evidence=f"{pieces}枚",
                      confidence=confidence, pack_count=1),
        shipping_basis=ship,
    )


class HomeDiaperDirectPurchaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.categories = load_categories()
        cls.segments = {
            key: {"products": [offer(key + "-80"), offer(key + "-160", 160, 5200)]}
            for key, _, _ in KINDS
        }

    def test_all_five_safe_diaper_calculators_have_static_direct_links(self):
        html = home_diaper_purchase_paths(self.categories, self.segments)
        self.assertIn('id="diaper-purchase-paths"', html)
        self.assertIn("おむつは何枚・何セット買えばいい？", html)
        self.assertEqual(html.count('data-nav-source="home_diaper_purchase_planner"'), 5)
        for key, kind, size in KINDS:
            with self.subTest(key=key):
                url = f"{SITE_URL}diapers/{kind}/{size}/#purchase-planner"
                self.assertIn(f'href="{url}"', html)
                self.assertIn(f'data-product-type="{kind}" data-size="{size}"', html)
        self.assertEqual(html.count("現在比較できる2商品"), 5)
        self.assertIn(f'href="{SITE_URL}diapers/"', html)
        self.assertNotIn("amazon.co.jp", html)
        self.assertNotIn("楽天全店最安", html)

    def test_partial_or_unverified_catalog_has_no_dead_shortcuts(self):
        bad = dict(self.segments)
        bad["tape-newborn"] = {"products": [offer("only")]}
        bad["tape-s"] = {"products": []}
        bad["tape-m"] = {"products": [
            offer("safe"), offer("unknown", ship="unknown")
        ]}
        bad["pants-s"] = {"products": [
            offer("safe"), offer("unproven", confidence=.40)
        ]}
        html = home_diaper_purchase_paths(self.categories, bad)
        self.assertEqual(html.count('data-nav-source="home_diaper_purchase_planner"'), 1)
        self.assertIn('diapers/pants/m/#purchase-planner', html)
        for kind, size in (("tape","newborn"),("tape","s"),("tape","m"),("pants","s")):
            self.assertNotIn(f'diapers/{kind}/{size}/#purchase-planner', html)
        self.assertNotIn("現在比較できる1商品", html)
        self.assertEqual(home_diaper_purchase_paths(self.categories, {}), "")
        self.assertEqual(home_diaper_purchase_paths(self.categories, None), "")

    def test_page_hero_cta_and_dynamic_shortcuts_keep_existing_entrypoints(self):
        html = render_home(self.categories, {}, [], [], [], NOW,
                           diaper_snapshots=self.segments)
        self.assertIn('class="shop-planner-shortcut" href="#diaper-purchase-paths"', html)
        self.assertIn('data-nav-source="home_diaper_planner_shortcut"', html)
        self.assertIn('data-nav-source="home_category"', html)
        self.assertIn('id="diaper-selector"', html)
        self.assertIn('id="growth-finder"', html)
        self.assertIn('data-nav-source="home_wipes_planner"', html)
        self.assertIn('data-nav-source="home_nursery_planner"', html)
        self.assertLess(html.index('id="diaper-purchase-paths"'), html.index('ONE MONTH / BABY WIPES'))
        empty = render_home(self.categories, {}, [], [], [], NOW, diaper_snapshots={})
        self.assertNotIn('id="diaper-purchase-paths"', empty)
        self.assertNotIn('data-nav-source="home_diaper_planner_shortcut"', empty)
        self.assertIn('id="diaper-selector"', empty)
        self.assertIn('data-nav-source="home_wipes_planner"', empty)


if __name__ == "__main__":
    unittest.main()
