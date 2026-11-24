"""Newborn tape diaper purchasing uses verified SKU totals and a short stock horizon.

Fixtures are synthetic and never enter the published catalog.
"""
import unittest
from datetime import datetime, timezone

from src.config import load_categories
from src.purchase import purchase_inputs, purchase_result_html
from src.render import render_comparison, render_diaper_index

NOW = datetime(2026, 11, 22, 0, 0, tzinfo=timezone.utc)


def sku(source_id, price, pieces, shipping='rakuten_postage_filter', confidence=.99):
    return {
        'name': f'赤ちゃん用 新生児 テープ {pieces}枚',
        'source_id': source_id,
        'price_yen': price, 'unit_price': price / pieces,
        'unit_metric': 'per_piece',
        'quantity': {'total': pieces, 'base_unit': 'piece', 'pack_count': 1,
                     'confidence': confidence, 'evidence': f'{pieces}枚'},
        'shipping_basis': shipping,
        'url': f'https://hb.afl.rakuten.co.jp/hgc/{source_id}',
        'brand': 'テスト用', 'manufacturer': 'テスト用',
        'shop': 'テスト店舗', 'image': '', 'attributes': {},
    }


class NewbornTapePurchasePlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.categories = load_categories()
        cls.diapers = cls.categories['diapers']
        cls.segments = {s['id']: s for s in cls.diapers['segments']}
        cls.offers = [sku('newborn-82', 2600, 82),
                      sku('newborn-272', 6920, 272)]

    def page(self, segment='tape-newborn', products=None):
        return render_comparison(
            self.categories, 'diapers', self.diapers,
            self.segments[segment],
            self.offers if products is None else products, NOW,
        )

    def test_verified_newborn_calculator_has_appropriate_usage_and_defaults(self):
        html = self.page()
        self.assertIn('id="purchase-planner"', html)
        self.assertIn('data-usage="10" aria-pressed="true"', html)
        self.assertIn('data-usage="12"', html)
        self.assertIn('data-purchase-daily type="number" min="1" max="30" step="1" value="10"', html)
        self.assertIn('data-purchase-days type="number" min="1" max="90" step="1" value="14"', html)
        self.assertIn("1日10枚 × 14日 ＝ <strong>必要140枚</strong>", html)
        self.assertIn("新生児テープをあと14日使う", html)
        self.assertIn("不足は120枚", html)
        self.assertIn("1日10枚は<strong>計算例</strong>", html)
        self.assertIn("https://jp.moony.com/ja/tips/baby/childcare/diapers/bm0088.html", html)
        self.assertIn("新生児のおむつは何枚必要？", html)
        self.assertIn('content="index,follow"', html)
        self.assertIn('rel="nofollow sponsored noopener"', html)
        self.assertNotIn("パンツMをあと14日", html)
        self.assertNotIn("パンツSをあと14日", html)

    def test_initial_static_checkout_matches_planner_for_newborn(self):
        html = self.page()
        self.assertIn("1日10枚 × 14日：必要140枚", html)
        # 82 sheets per real sales set needs two sets, not two inner bags.
        self.assertIn("¥5,200", html)
        self.assertIn("¥6,920", html)
        self.assertIn("使用140枚分の費用相当額", html)
        self.assertIn("購入時の支払額（掲載条件）", html)
        self.assertIn("使用後に余る枚数", html)
        default = purchase_result_html(self.offers[0])
        newborn = purchase_result_html(self.offers[0], daily_use=10, days=14)
        self.assertIn("必要150枚", default)
        self.assertIn("必要140枚", newborn)
        self.assertIn("¥5,200", newborn)

    def test_no_invented_checkout_when_any_offer_unverified(self):
        cases = [
            [],
            [self.offers[0]],
            [sku('unknown-shipping', 2600, 82, shipping='unknown'), self.offers[1]],
            [sku('weak-quantity', 2600, 82, confidence=.5), self.offers[1]],
        ]
        for products in cases:
            with self.subTest(count=len(products)):
                html = self.page(products=products)
                self.assertNotIn('id="purchase-planner"', html)
                self.assertNotIn('data-purchase-product=', html)
                self.assertNotIn("新生児テープをあと14日", html)
        self.assertIsNone(purchase_inputs(sku('weak', 2600, 82, confidence=.5)))
        self.assertIsNone(purchase_inputs(sku('unknown', 2600, 82, shipping='unknown')))

    def test_other_diaper_sizes_cannot_inherit_newborn_planner(self):
        html = self.page(segment='tape-l')
        self.assertIn('id="purchase-planner"', html)
        self.assertIn('テープLをあと14日使う予定なら？', html)
        self.assertIn('data-usage="5" aria-pressed="true"', html)
        self.assertNotIn("新生児テープをあと14日", html)
        m = self.page(segment='pants-m')
        self.assertIn('id="purchase-planner"', m)
        self.assertIn('data-usage="5" aria-pressed="true"', m)
        self.assertIn('data-purchase-daily type="number" min="1" max="30" step="1" value="5"', m)
        self.assertIn('data-purchase-days type="number" min="1" max="90" step="1" value="30"', m)

    def test_hub_link_is_only_added_for_verified_newborn_catalog(self):
        offers = {'tape-newborn': {'products': self.offers}}
        html = render_diaper_index(self.categories, NOW, offers)
        self.assertEqual(html.count('data-nav-source="diaper_index_newborn_planner"'), 1)
        self.assertIn('diapers/tape/newborn/#purchase-planner', html)
        self.assertIn("新生児・テープ", html)
        html = render_diaper_index(self.categories, NOW,
                                   {'tape-newborn': {'products': [self.offers[0]]}})
        self.assertNotIn('data-nav-source="diaper_index_newborn_planner"', html)
        self.assertIn('href="https://stusaurus.github.io/baby-cost-jp/diapers/tape/newborn/"', html)


if __name__ == '__main__':
    unittest.main()
