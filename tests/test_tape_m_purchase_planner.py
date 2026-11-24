"""Tape M diaper planning: verifiable full sales-set checkout, not unit-price guesses.

Fixtures are synthetic and must never enter the public product feed.
"""
import unittest
from datetime import datetime, timezone

from src.config import load_categories
from src.purchase import purchase_inputs, purchase_result_html
from src.render import render_comparison, render_diaper_index

NOW = datetime(2026, 11, 22, 0, 0, tzinfo=timezone.utc)


def sku(source_id, price, pieces, *, confidence=.99, shipping='rakuten_postage_filter'):
    return {
        'name': f'赤ちゃん用 テープ Mサイズ {pieces}枚',
        'source_id': source_id, 'price_yen': price,
        'unit_price': price / pieces,
        'unit_metric': 'per_piece',
        'quantity': {'total': pieces, 'base_unit': 'piece',
                     'pack_count': 1, 'confidence': confidence,
                     'evidence': f'{pieces}枚'},
        'shipping_basis': shipping,
        'url': f'https://hb.afl.rakuten.co.jp/hgc/{source_id}',
        'image': '', 'brand': 'テスト用', 'manufacturer': 'テスト用',
        'shop': 'テスト用店舗', 'attributes': {},
    }


class TapeMPurchasePlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.categories = load_categories()
        cls.category = cls.categories['diapers']
        cls.segments = {s['id']: s for s in cls.category['segments']}
        cls.offers = [sku('tape-m-64', 2750, 64, confidence=.89),
                      sku('tape-m-208', 6920, 208)]

    def page(self, segment='tape-m', products=None):
        return render_comparison(
            self.categories, 'diapers', self.category,
            self.segments[segment],
            self.offers if products is None else products, NOW
        )

    def test_planner_entry_and_14day_tape_m_scenario(self):
        html = self.page()
        self.assertIn('id="purchase-planner"', html)
        self.assertIn('data-purchase-entry', html)
        self.assertIn('data-usage="6" aria-pressed="true"', html)
        self.assertIn('data-usage="4"', html)
        self.assertIn('data-usage="8"', html)
        self.assertIn('data-purchase-daily type="number" min="1" max="30" step="1" value="6"', html)
        self.assertIn('data-purchase-days type="number" min="1" max="90" step="1" value="14"', html)
        self.assertIn('1日6枚 × 14日 ＝ <strong>必要84枚</strong>', html)
        self.assertIn('テープMをあと14日使う', html)
        self.assertIn('不足は64枚', html)  # 20 sheets in the illustrative scenario
        self.assertIn('テープMの1日6枚は<strong>計算例</strong>', html)
        self.assertIn('テープSの手持ちをMサイズの在庫に含めない', html)
        self.assertIn('<title>おむつ テープMサイズ｜1枚あたり価格・まとめ買い総額比較</title>', html)
        self.assertIn('content="index,follow"', html)
        self.assertIn('rel="nofollow sponsored noopener"', html)
        self.assertIn('data-size="m"', html)
        self.assertIn('data-product-type="tape"', html)
        self.assertNotIn('新生児テープをあと14日', html)
        self.assertNotIn('テープSをあと14日', html)
        self.assertNotIn('パンツMをあと14日', html)

    def test_initial_static_checkout_uses_whole_sale_sets(self):
        html = self.page()
        self.assertIn('1日6枚 × 14日：必要84枚', html)
        self.assertIn('¥5,500', html)  # 64 sheets per offer: 2 sets
        self.assertIn('¥6,920', html)  # 208 sheets per offer: 1 set
        self.assertIn('使用84枚分の費用相当額', html)
        self.assertIn('購入時の支払額（掲載条件）', html)
        self.assertIn('使用後に余る枚数', html)
        self.assertIn('必要150枚', purchase_result_html(self.offers[0]))
        m = purchase_result_html(self.offers[0], daily_use=6, days=14)
        self.assertIn('必要84枚', m)
        self.assertIn('¥5,500', m)
        self.assertEqual(purchase_inputs(self.offers[0])['total'], 64)

    def test_only_verified_catalog_and_two_offers_enable_planner(self):
        for products in (
            [],
            [self.offers[0]],
            [sku('shipping-unknown', 2750, 64, shipping='unknown'), self.offers[1]],
            [sku('confidence-low', 2750, 64, confidence=.50), self.offers[1]],
        ):
            with self.subTest(count=len(products)):
                html = self.page(products=products)
                self.assertNotIn('id="purchase-planner"', html)
                self.assertNotIn('data-purchase-product=', html)
                self.assertNotIn('テープMをあと14日', html)
        self.assertIsNone(purchase_inputs(sku('unknown', 2750, 64, shipping='unknown')))
        self.assertIsNone(purchase_inputs(sku('low', 2750, 64, confidence=.5)))

    def test_other_unmodified_sizes_stay_isolated(self):
        for segment in ('tape-l', 'pants-big-plus'):
            with self.subTest(segment=segment):
                html = self.page(segment=segment)
                self.assertNotIn('id="purchase-planner"', html)
                self.assertNotIn('テープMをあと14日', html)
        s = self.page(segment='tape-s')
        self.assertIn('id="purchase-planner"', s)
        self.assertIn('data-usage="8" aria-pressed="true"', s)
        newborn = self.page(segment='tape-newborn')
        self.assertIn('data-usage="10" aria-pressed="true"', newborn)
        pants_m = self.page(segment='pants-m')
        self.assertIn('data-usage="5" aria-pressed="true"', pants_m)
        self.assertIn('data-purchase-days type="number" min="1" max="90" step="1" value="30"', pants_m)

    def test_hub_link_only_when_tape_m_offers_are_safe(self):
        html = render_diaper_index(
            self.categories, NOW, {'tape-m': {'products': self.offers}}
        )
        self.assertEqual(html.count('data-nav-source="diaper_index_tape_m_planner"'), 1)
        self.assertIn('diapers/tape/m/#purchase-planner', html)
        self.assertIn('M・テープ', html)
        for products in (
            [self.offers[0]],
            [sku('unknown', 2750, 64, shipping='unknown'), self.offers[1]],
        ):
            html = render_diaper_index(self.categories, NOW,
                {'tape-m': {'products': products}})
            self.assertNotIn('data-nav-source="diaper_index_tape_m_planner"', html)
            self.assertIn('diapers/tape/m/', html)


if __name__ == '__main__':
    unittest.main()
