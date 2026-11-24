"""Tape S size-up purchase plans rely on the accepted catalog evidence only.

All products are synthetic test fixtures, not additions to the actual catalog.
"""
import unittest
from datetime import datetime, timezone

from src.config import load_categories
from src.purchase import purchase_inputs, purchase_result_html
from src.render import render_comparison, render_diaper_index

NOW = datetime(2026, 11, 22, 0, 0, tzinfo=timezone.utc)


def sku(source_id, price, pieces, *, confidence=.99, shipping='rakuten_postage_filter'):
    return {
        'name': f'赤ちゃん用 テープ Sサイズ {pieces}枚',
        'source_id': source_id,
        'price_yen': price,
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


class TapeSPurchasePlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.categories = load_categories()
        cls.category = cls.categories['diapers']
        cls.segments = {s['id']: s for s in cls.category['segments']}
        cls.offers = [sku('tape-s-74', 2680, 74),
                      sku('tape-s-248', 6920, 248)]

    def page(self, segment='tape-s', products=None):
        return render_comparison(
            self.categories, 'diapers', self.category,
            self.segments[segment],
            self.offers if products is None else products,
            NOW,
        )

    def test_tape_s_purchase_planner_and_search_entry(self):
        html = self.page()
        self.assertIn('id="purchase-planner"', html)
        self.assertIn('data-purchase-entry', html)
        self.assertIn('data-usage="8" aria-pressed="true"', html)
        self.assertIn('data-usage="10"', html)
        self.assertIn('data-purchase-daily type="number" min="1" max="30" step="1" value="8"', html)
        self.assertIn('data-purchase-days type="number" min="1" max="90" step="1" value="14"', html)
        self.assertIn('1日8枚 × 14日 ＝ <strong>必要112枚</strong>', html)
        self.assertIn('テープSをあと14日使う', html)
        self.assertIn('不足は92枚', html)
        self.assertIn('テープSの1日8枚は<strong>計算例</strong>', html)
        self.assertIn('新生児サイズの手持ちをSサイズの在庫に含めない', html)
        self.assertIn('テープSのおむつ何枚必要？', html)
        self.assertIn('content="index,follow"', html)
        self.assertIn('rel="nofollow sponsored noopener"', html)
        self.assertIn('data-size="s"', html)
        self.assertIn('data-product-type="tape"', html)
        self.assertNotIn('新生児テープをあと14日', html)
        self.assertNotIn('パンツMをあと14日', html)
        self.assertNotIn('パンツSをあと14日', html)

    def test_tape_s_initial_calculation_uses_whole_sales_sets(self):
        html = self.page()
        self.assertIn('1日8枚 × 14日：必要112枚', html)
        self.assertIn('¥5,360', html)  # 74枚の商品は2セット必要
        self.assertIn('¥6,920', html)  # 248枚の商品は1セット
        self.assertIn('使用112枚分の費用相当額', html)
        self.assertIn('購入時の支払額（掲載条件）', html)
        self.assertIn('使用後に余る枚数', html)
        self.assertIn('必要150枚', purchase_result_html(self.offers[0]))
        self.assertIn('必要112枚', purchase_result_html(self.offers[0], daily_use=8, days=14))
        self.assertIn('¥5,360', purchase_result_html(self.offers[0], daily_use=8, days=14))
        self.assertEqual(purchase_inputs(self.offers[0])['total'], 74)

    def test_unknown_quantity_shipping_or_single_offer_disables_planner(self):
        for products in (
            [],
            [self.offers[0]],
            [sku('unknown', 2680, 74, shipping='unknown'), self.offers[1]],
            [sku('low-confidence', 2680, 74, confidence=.50), self.offers[1]],
        ):
            with self.subTest(count=len(products)):
                html = self.page(products=products)
                self.assertNotIn('id="purchase-planner"', html)
                self.assertNotIn('data-purchase-product=', html)
                self.assertNotIn('テープSをあと14日', html)
        self.assertIsNone(purchase_inputs(sku('unknown', 2680, 74, shipping='unknown')))
        self.assertIsNone(purchase_inputs(sku('weak', 2680, 74, confidence=.5)))

    def test_does_not_spill_into_tape_m_l_or_other_categories(self):
        for segment in ('tape-l', 'pants-big-plus'):
            with self.subTest(segment=segment):
                html = self.page(segment=segment)
                self.assertIn('id="purchase-planner"', html)
                self.assertNotIn('テープSをあと14日', html)
        newborn = self.page(segment='tape-newborn')
        self.assertIn('id="purchase-planner"', newborn)
        self.assertIn('data-usage="10" aria-pressed="true"', newborn)
        self.assertIn('value="14" inputmode="numeric" aria-describedby="purchase-error"', newborn)
        m = self.page(segment='pants-m')
        self.assertIn('id="purchase-planner"', m)
        self.assertIn('data-usage="5" aria-pressed="true"', m)
        self.assertIn('value="30" inputmode="numeric" aria-describedby="purchase-error"', m)

    def test_hub_link_only_when_two_verified_tape_s_offers(self):
        html = render_diaper_index(
            self.categories, NOW, {'tape-s': {'products': self.offers}}
        )
        self.assertEqual(html.count('data-nav-source="diaper_index_tape_s_planner"'), 1)
        self.assertIn('diapers/tape/s/#purchase-planner', html)
        self.assertIn('S・テープ', html)
        for products in (
            [self.offers[0]],
            [sku('unknown', 2680, 74, shipping='unknown'), self.offers[1]],
        ):
            html = render_diaper_index(
                self.categories, NOW, {'tape-s': {'products': products}}
            )
            self.assertNotIn('data-nav-source="diaper_index_tape_s_planner"', html)
            self.assertIn('diapers/tape/s/', html)


if __name__ == '__main__':
    unittest.main()
