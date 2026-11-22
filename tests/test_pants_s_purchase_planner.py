"""Pants-S purchase planning is strictly separated from M and other sizes.

Synthetic SKUs only: tests never add products to the real catalog.
"""
import unittest
from datetime import datetime, timezone

from src.config import load_categories
from src.render import render_comparison


class PantsSPurchasePlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.category = load_categories()["diapers"]
        cls.segments = {seg["id"]: seg for seg in cls.category["segments"]}

    @staticmethod
    def product(name, source_id, price, pieces, *, shipping="rakuten_postage_filter", confidence=.99):
        return {
            "name": name,
            "source_id": source_id,
            "price_yen": price,
            "unit_price": price / pieces,
            "unit_metric": "per_piece",
            "quantity": {"total": pieces, "base_unit": "piece", "pack_count": 1,
                         "confidence": confidence, "evidence": f"{pieces}枚"},
            "shipping_basis": shipping,
            "url": f"https://hb.afl.rakuten.co.jp/hgc/{source_id}",
            "image": "",
            "brand": "テスト用",
            "manufacturer": "テスト用",
            "shop": "テスト用店舗",
            "attributes": {},
        }

    def page(self, segment_id, products):
        return render_comparison(
            {"diapers": self.category}, "diapers", self.category,
            self.segments[segment_id], products,
            datetime(2026, 11, 22, 0, 0, tzinfo=timezone.utc)
        )

    def test_s_only_uses_verified_sets_and_size_correct_language(self):
        products = [
            self.product("赤ちゃん用 パンツ S 156枚", "s-156", 5070, 156),
            self.product("赤ちゃん用 パンツ S 62枚", "s-62", 2840, 62),
        ]
        html = self.page("pants-s", products)
        self.assertIn('id="purchase-planner"', html)
        self.assertIn('data-purchase-entry', html)
        self.assertIn("パンツSをあと14日使う", html)
        self.assertIn('id="14day-example"', html)
        self.assertIn("必要購入セット数", html)
        self.assertIn("支払額（掲載条件）", html)
        self.assertIn("余る枚数", html)
        self.assertIn("パンツSの価格比較｜必要セット数", html)
        self.assertIn("不足は50枚", html)
        self.assertIn("¥2,840", html)
        self.assertIn("¥5,070", html)
        self.assertIn('data-product-type="pants"', html)
        self.assertIn('data-size="s"', html)
        self.assertIn('data-purchase-product=', html)
        self.assertIn('rel="nofollow sponsored noopener"', html)
        self.assertIn('https://hb.afl.rakuten.co.jp/hgc/s-156', html)
        self.assertNotIn("パンツMをあと14日", html)
        self.assertNotIn("pants_m_nursery_planner", html)
        self.assertNotIn("犬用", html)

    def test_s_cannot_show_planner_for_unverified_or_sparse_catalog(self):
        good = self.product("赤ちゃん用 パンツ S 156枚", "s-156", 5070, 156)
        for products in [
            [],
            [good],
            [good, self.product("送料未確認 パンツ S 62枚", "s-unverified", 2840, 62, shipping="unknown")],
            [good, self.product("数量根拠が弱い パンツ S 62枚", "s-weak", 2840, 62, confidence=.5)],
        ]:
            with self.subTest(products=len(products)):
                html = self.page("pants-s", products)
                self.assertNotIn('id="purchase-planner"', html)
                self.assertNotIn('id="14day-example"', html)
                self.assertNotIn("必要枚数分の購入額が安い", html)

    def test_existing_pants_m_and_other_sizes_remain_separate(self):
        m = [
            self.product("赤ちゃん用 パンツ M 160枚", "m-160", 4000, 160),
            self.product("赤ちゃん用 パンツ M 80枚", "m-80", 2500, 80),
        ]
        m_html = self.page("pants-m", m)
        self.assertIn("パンツMをあと14日使う", m_html)
        self.assertIn("14日・30日分の必要セット数と支払額", m_html)
        self.assertIn("pants_m_nursery_planner", m_html)
        self.assertIn('id="purchase-planner"', m_html)
        for segment in ("pants-l", "tape-newborn", "tape-m", "pants-big"):
            html = self.page(segment, m)
            self.assertNotIn('id="purchase-planner"', html)
            self.assertNotIn('id="14day-example"', html)
            self.assertNotIn("必要枚数分の購入額が安い", html)


if __name__ == "__main__":
    unittest.main()
