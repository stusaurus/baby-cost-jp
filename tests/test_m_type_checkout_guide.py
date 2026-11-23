"""M tape/pants purchase comparison uses only accepted SKU evidence and full sets."""
import unittest
import json
import re
from datetime import datetime, timezone

from src.config import load_categories
from src.render import render_comparison, render_diaper_index
from src.type_guide import (
    GUIDE_URL, guide_available, lowest_checkout,
    render_m_diaper_type_guide, verified_offers,
)

NOW = datetime(2026, 11, 23, 22, 0, tzinfo=timezone.utc)


def product(key, pieces, yen, *, confidence=.99, shipping='rakuten_postage_filter'):
    return {
        'source_id': key,
        'name': f'赤ちゃん用 紙おむつ {key} {pieces}枚',
        'price_yen': yen,
        'unit_price': yen / pieces,
        'unit_metric': 'per_piece',
        'quantity': {'total': pieces, 'confidence': confidence,
                     'base_unit': 'piece', 'evidence': f'{pieces}枚',
                     'pack_count': 1},
        'shipping_basis': shipping,
        'url': f'https://hb.afl.rakuten.co.jp/hgc/{key}',
        'image': '', 'manufacturer': 'テスト', 'brand': 'テスト',
        'shop': 'テスト店舗', 'attributes': {},
    }


class MTypeCheckoutGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = {
            'tape-m': {'products': [
                product('tape-74', 74, 2680),
                product('tape-248', 248, 6920),
            ]},
            'pants-m': {'products': [
                product('pants-50', 50, 2100),
                product('pants-180', 180, 6100),
            ]},
        }
        cls.cats = load_categories()
        cls.seg = {s['id']: s for s in cls.cats['diapers']['segments']}

    def test_7_14_30day_real_bundle_checkout_no_fractional_sets(self):
        html = render_m_diaper_type_guide(self.catalog, NOW)
        self.assertTrue(guide_available(self.catalog))
        self.assertIn('content="index,follow"', html)
        self.assertIn(f'rel="canonical" href="{GUIDE_URL}"', html)
        self.assertIn('Mサイズのおむつは、テープとパンツのどちらが安い？', html)
        self.assertIn('6枚/日×7日＝42枚', html)
        self.assertIn('6枚/日×14日＝84枚', html)
        self.assertIn('6枚/日×30日＝180枚', html)
        self.assertEqual(html.count('<tr><th scope="row">'), 3)
        # 7d: 42 needed, tape 74x1 = ¥2680, pants 50x1 = ¥2100.
        self.assertIn('パンツの掲載候補が¥580少ない', html)
        # 14d: 84 needed, tape 74x2 = ¥5360, pants 50x2 = ¥4200.
        self.assertIn('¥5,360', html)
        self.assertIn('¥4,200', html)
        self.assertIn('パンツの掲載候補が¥1,160少ない', html)
        self.assertIn('2販売セット・計148枚購入 ／ 84枚使用後に64枚余る', html)
        self.assertIn('2販売セット・計100枚購入 ／ 84枚使用後に16枚余る', html)
        # 30d: tape 248x1 = ¥6920, pants 180x1 = ¥6100.
        self.assertIn('¥6,920', html)
        self.assertIn('¥6,100', html)
        self.assertIn('パンツの掲載候補が¥820少ない', html)
        self.assertIn('1販売セット・計248枚購入 ／ 180枚使用後に68枚余る', html)
        self.assertIn('1販売セット・計180枚購入 ／ 180枚使用後に0枚余る', html)

    def test_personalized_planner_only_uses_verified_local_snapshot(self):
        html = render_m_diaper_type_guide(self.catalog, NOW)
        self.assertIn('data-m-type-planner', html)
        self.assertIn('data-m-type-input="daily"', html)
        self.assertIn('data-m-type-input="days"', html)
        self.assertIn('data-m-type-input="tape-stock"', html)
        self.assertIn('data-m-type-input="pants-stock"', html)
        self.assertIn('type="number" min="1" max="90"', html)
        self.assertIn('data-m-type-days-choice="30"', html)
        self.assertIn('m_type_planner.js?v=', html)
        match = re.search(
            r'<script type="application/json" data-m-type-snapshot>(.*?)</script>',
            html,
        )
        self.assertIsNotNone(match)
        snapshot = json.loads(match.group(1))
        self.assertEqual([p["price"] for p in snapshot["tape"]], [2680, 6920])
        self.assertEqual([p["total"] for p in snapshot["pants"]], [50, 180])
        self.assertTrue(all(p["verified"] for group in snapshot.values() for p in group))
        self.assertTrue(all("url" not in p for group in snapshot.values() for p in group))
        self.assertIn('入力内容を保存・送信しません', html)
        self.assertIn('異なる商品を混ぜた最適化', html)

    def test_planner_snapshot_escapes_untrusted_product_titles(self):
        changed = dict(self.catalog)
        rows = list(self.catalog['tape-m']['products'])
        rows[0] = dict(rows[0], name='おむつM </script><img src=x onerror=alert(1)>')
        changed['tape-m'] = {'products': rows}
        html = render_m_diaper_type_guide(changed, NOW)
        self.assertNotIn('</script><img', html)
        match = re.search(r'<script type="application/json" data-m-type-snapshot>(.*?)</script>', html)
        self.assertIsNotNone(match)
        parsed = json.loads(match.group(1))
        self.assertEqual(parsed['tape'][0]['name'], 'おむつM </script><img src=x onerror=alert(1)>')
        self.assertEqual(html.count('data-m-type-snapshot'), 1)

    def test_source_and_suitability_cautions_with_clear_outbound_links(self):
        html = render_m_diaper_type_guide(self.catalog, NOW)
        self.assertIn('https://jp.moony.com/ja/tips/baby/childcare/diapers/bm0084.html', html)
        self.assertIn('https://www.pampers.jp/newborn/development/article/diaper-size-up', html)
        self.assertIn('月齢だけでは決められません', html)
        self.assertIn('30日分の表示はまとめ買いを勧めるものではありません', html)
        self.assertIn('地域追加送料', html)
        self.assertIn('手持ち在庫0枚', html)
        self.assertIn('data-nav-source="m_type_tape_planner"', html)
        self.assertIn('data-nav-source="m_type_pants_planner"', html)
        self.assertIn('diapers/tape/m/#purchase-planner', html)
        self.assertIn('diapers/pants/m/#purchase-planner', html)
        self.assertNotIn('1日6枚が標準', html)
        self.assertNotIn('楽天全店最安', html)

    def test_best_checkout_is_not_best_unit_price(self):
        # 84 needed, 1 piece price can be lower for large bundle, but its
        # actual checkout bill can be higher than two small sale sets.
        cheap_small = product('small', 50, 2200)
        cheap_unit = product('large', 180, 7000)
        selected = lowest_checkout([cheap_unit, cheap_small], 84)
        self.assertEqual(selected['product']['source_id'], 'small')
        self.assertEqual(selected['sets'], 2)
        self.assertEqual(selected['payment'], 4400)
        self.assertEqual(selected['surplus'], 16)
        self.assertIsNone(lowest_checkout([], 84))
        self.assertIsNone(lowest_checkout([cheap_small], 0))
        self.assertIsNone(lowest_checkout([cheap_small, product('bad', 50, 2200, shipping='unknown')], 84))

    def test_any_missing_unverified_or_one_offer_disables_comparison_and_indexing(self):
        base = self.catalog
        alternatives = [
            {},
            {'tape-m': base['tape-m']},
            {'tape-m': {'products': base['tape-m']['products'][:1]},
             'pants-m': base['pants-m']},
            {'tape-m': base['tape-m'],
             'pants-m': {'products': [
                 base['pants-m']['products'][0],
                 product('weak', 180, 6100, confidence=.5)]}},
            {'tape-m': {'products': [
                 base['tape-m']['products'][0],
                 product('ship', 248, 6920, shipping='unknown')]},
             'pants-m': base['pants-m']},
        ]
        for snapshots in alternatives:
            with self.subTest(snapshots=list(snapshots)):
                html = render_m_diaper_type_guide(snapshots, NOW)
                self.assertFalse(guide_available(snapshots))
                self.assertIn('content="noindex,follow"', html)
                self.assertIn('購入総額を比較するための商品が不足', html)
                self.assertNotIn('m-type-table', html)
                self.assertNotIn('data-m-type-planner', html)
                self.assertNotIn('data-m-type-snapshot', html)
                self.assertNotIn('パンツの掲載候補が¥', html)
                self.assertIn('diapers/tape/m/"', html)
                self.assertIn('diapers/pants/m/"', html)
                self.assertNotIn('diapers/tape/m/#purchase-planner', html)
                self.assertNotIn('diapers/pants/m/#purchase-planner', html)
                self.assertIn('テープMの比較ページを見る', html)

    def test_hub_and_M_pages_crawlable_related_links(self):
        hub = render_diaper_index(self.cats, NOW, self.catalog)
        self.assertEqual(hub.count('data-nav-source="diaper_index_m_type_guide"'), 1)
        self.assertIn(f'href="{GUIDE_URL}"', hub)
        for key in ('tape-m', 'pants-m'):
            page = render_comparison(
                self.cats, 'diapers', self.cats['diapers'],
                self.seg[key], self.catalog[key]['products'], NOW,
            )
            self.assertIn('data-nav-source="m_type_guide_from_comparison"', page)
            self.assertIn(f'href="{GUIDE_URL}"', page)
        unverified = dict(self.catalog)
        unverified['tape-m'] = {'products': [self.catalog['tape-m']['products'][0]]}
        hub = render_diaper_index(self.cats, NOW, unverified)
        self.assertNotIn('data-nav-source="diaper_index_m_type_guide"', hub)
        self.assertIn('id="diaper-price-by-size"', hub)


if __name__ == '__main__':
    unittest.main()
