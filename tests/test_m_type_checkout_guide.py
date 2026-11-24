"""M tape/pants purchase comparison uses only accepted SKU evidence and full sets."""
import unittest
import json
import re
from datetime import datetime, timezone

from src.config import load_categories
from src.render import render_comparison, render_diaper_index, render_home
from src.type_guide import (
    GUIDE_URL, guide_available, lowest_checkout, verified_retail_link,
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
        self.assertTrue(all(p["url"] == "" for group in snapshot.values() for p in group))
        self.assertEqual(html.count('data-m-type-buy'), 2)
        self.assertEqual(html.count('data-affiliate="rakuten"'), 2)
        self.assertIn('nofollow sponsored noopener', html)
        self.assertIn('data-click-position="m_type_personal_result"', html)
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

    def test_exact_rakuten_product_id_is_required_for_direct_checkout_link(self):
        original = product('store:123456', 64, 2750)
        url = (
            'https://hb.afl.rakuten.co.jp/hgc/safe.example/?'
            'pc=https%3A%2F%2Fitem.rakuten.co.jp%2Fstore%2Fdiapers-m%2F'
            '&m=http%3A%2F%2Fm.rakuten.co.jp%2Fstore%2Fi%2F123456%2F'
        )
        original['url'] = url
        self.assertEqual(verified_retail_link(original), url)
        catalog = dict(self.catalog)
        rows = [original, self.catalog['tape-m']['products'][1]]
        catalog['tape-m'] = {'products': rows}
        html = render_m_diaper_type_guide(catalog, NOW)
        match = re.search(
            r'<script type="application/json" data-m-type-snapshot>(.*?)</script>',
            html,
        )
        self.assertIsNotNone(match)
        snapshot = json.loads(match.group(1))
        self.assertEqual(snapshot['tape'][0]['id'], 'store:123456')
        self.assertEqual(snapshot['tape'][0]['url'], url)
        self.assertEqual(snapshot['tape'][1]['url'], '')
        self.assertIn('data-m-type-fallback', html)

        wrong = dict(original)
        for changed in (
            'javascript:alert(1)',
            'https://hb.afl.rakuten.co.jp.evil.example/hgc/abc',
            'https://hb.afl.rakuten.co.jp/hgc/abc?'
                'pc=https%3A%2F%2Fitem.rakuten.co.jp%2Fstore%2Fdiapers-m%2F'
                '&m=http%3A%2F%2Fm.rakuten.co.jp%2Fstore%2Fi%2F999999%2F',
            url.replace('item.rakuten.co.jp%2Fstore', 'item.rakuten.co.jp%2Fother'),
            url.replace('m.rakuten.co.jp%2Fstore', 'm.rakuten.co.jp%2Fother'),
            url.replace('https://hb', 'http://hb'),
            url + '&m=https%3A%2F%2Fm.rakuten.co.jp%2Fstore%2Fi%2F123456%2F',
        ):
            with self.subTest(changed=changed[:60]):
                wrong['url'] = changed
                self.assertEqual(verified_retail_link(wrong), '')
        wrong['url'] = url
        wrong['source_id'] = 'store:999999'
        self.assertEqual(verified_retail_link(wrong), '')
        wrong['source_id'] = 'no-store-item-id'
        self.assertEqual(verified_retail_link(wrong), '')

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
                self.assertNotIn('data-m-type-buy', html)
                self.assertNotIn('パンツの掲載候補が¥', html)
                self.assertIn('diapers/tape/m/"', html)
                self.assertIn('diapers/pants/m/"', html)
                self.assertNotIn('diapers/tape/m/#purchase-planner', html)
                self.assertNotIn('diapers/pants/m/#purchase-planner', html)
                self.assertIn('テープMの比較ページを見る', html)

    def test_m_purchase_search_metadata_matches_verified_page(self):
        for key, title in (
            ('tape-m', 'おむつ テープMサイズ｜1枚あたり価格・まとめ買い総額比較'),
            ('pants-m', 'おむつ パンツMサイズ｜1枚あたり価格・まとめ買い総額比較'),
        ):
            with self.subTest(key=key):
                page = render_comparison(
                    self.cats, 'diapers', self.cats['diapers'], self.seg[key],
                    self.catalog[key]['products'], NOW,
                )
                self.assertIn(f'<title>{title}</title>', page)
                self.assertIn('購入総額、余る枚数を計算できます', page)
                self.assertIn('ポイント・クーポンは含めません', page)
                self.assertIn('id="purchase-planner"', page)
                self.assertIn('content="index,follow"', page)
                self.assertIn(f'{title}', page)
                one = render_comparison(
                    self.cats, 'diapers', self.cats['diapers'], self.seg[key],
                    self.catalog[key]['products'][:1], NOW,
                )
                self.assertNotIn(f'<title>{title}</title>', one)
                self.assertIn('content="noindex,follow"', one)

    def test_wipes_search_metadata_requires_verified_purchase_comparison(self):
        category = self.cats['wipes']
        segment = category['segments'][0]
        rows = [dict(product('wipes-a', 640, 1417), name='おしりふき 640枚'),
                dict(product('wipes-b', 1200, 3000), name='おしりふき 1200枚')]
        page = render_comparison(self.cats, 'wipes', category, segment, rows, NOW)
        title = 'おしりふき 1枚あたり価格比較｜まとめ買い・1か月の購入総額'
        self.assertIn(f'<title>{title}</title>', page)
        self.assertIn('必要セット数・購入総額・余る枚数を計算できます', page)
        self.assertIn('id="wipes-plan"', page)
        one = render_comparison(self.cats, 'wipes', category, segment, rows[:1], NOW)
        self.assertNotIn(f'<title>{title}</title>', one)
        self.assertIn('<title>おしりふきの価格・必要枚数｜1か月の買い足し計算</title>', one)
        self.assertIn('content="noindex,follow"', one)

    def test_home_has_one_evidence_gated_crawlable_m_purchase_guide_link(self):
        home = render_home(self.cats, {}, [], [], [], NOW, diaper_snapshots=self.catalog)
        self.assertEqual(home.count('data-nav-source="home_m_type_guide"'), 1)
        self.assertIn(f'href="{GUIDE_URL}"', home)
        self.assertIn('Mサイズのおむつはテープとパンツ、どっちが安い？', home)
        self.assertIn('実支払額・販売セット数・余り', home)
        self.assertIn('data-product-type="both" data-size="m"', home)
        self.assertNotIn('楽天全店の最安', home)
        # A missing type or even one unverified SKU must suppress promotion.
        for invalid in (
            None, {},
            {'tape-m': self.catalog['tape-m']},
            {
                'tape-m': {'products': [
                    self.catalog['tape-m']['products'][0],
                    product('unverified', 64, 2500, shipping='unknown'),
                ]},
                'pants-m': self.catalog['pants-m'],
            },
        ):
            with self.subTest(invalid=str(invalid)[:50]):
                rendered = render_home(self.cats, {}, [], [], [], NOW, diaper_snapshots=invalid)
                self.assertNotIn('data-nav-source="home_m_type_guide"', rendered)

    def test_diaper_hub_high_intent_guide_precedes_large_price_table(self):
        html = render_diaper_index(self.cats, NOW, self.catalog)
        self.assertEqual(html.count('data-nav-source="diaper_index_m_type_guide"'), 1)
        self.assertLess(html.index('data-nav-source="diaper_index_m_type_guide"'),
                        html.index('id="diaper-price-by-size"'))
        self.assertIn(f'href="{GUIDE_URL}"', html)

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
