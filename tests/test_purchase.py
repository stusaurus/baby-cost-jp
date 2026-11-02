import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from src.purchase import purchase_inputs, purchase_result_html
from src import rakuten
from scripts.build_site import normalize_products, load_categories
from src.render import render_comparison
from datetime import datetime


class PurchaseTests(unittest.TestCase):
    def setUp(self):
        self.product = {'price_yen': 4480, 'shipping_basis': 'rakuten_postage_filter',
                        'quantity': {'total': 192, 'base_unit': 'piece', 'confidence': .99,
                                     'evidence': '64枚×3個', 'pack_count': 3}}

    def test_purchase_uses_total_not_inner_pack_count(self):
        self.assertEqual(purchase_inputs(self.product), {'price': 4480, 'total': 192, 'verified': True})
        html = purchase_result_html(self.product)
        for text in ['¥4,480', '42', '3,500.0', '必要150枚']:
            self.assertIn(text, html)

    def test_invalid_and_unverified_products_never_get_a_payment(self):
        for field, values in [('total', [None, 0, -1, 1.5, float('inf'), float('nan'), True, '192', 20001]),
                              ('confidence', [None, .87, float('nan'), '0.99']),
                              ('base_unit', ['g', None]), ('evidence', ['', None])]:
            for value in values:
                with self.subTest(field=field, value=value):
                    p = copy.deepcopy(self.product); p['quantity'][field] = value
                    self.assertIsNone(purchase_inputs(p))
        for price in [None, 0, -1, 0.5, '4480', True, float('inf'), 1000000000]:
            p = copy.deepcopy(self.product); p['price_yen'] = price
            self.assertIsNone(purchase_inputs(p))
        for basis in [None, '', 'unknown', 'free in title']:
            p = copy.deepcopy(self.product); p['shipping_basis'] = basis
            self.assertIsNone(purchase_inputs(p))
            self.assertNotIn('¥', purchase_result_html(p))

    def test_provenance_is_set_only_by_postage_filtered_api_request(self):
        raw = {'itemName': '紙おむつ パンツ Mサイズ 64枚×3個', 'itemPrice': 4480, 'itemCode': 'shop:id'}
        self.assertNotIn('shipping_basis', rakuten._normalize(raw))
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps({'Items': [raw]}).encode()
        for output_flag, expected in [(None, 'rakuten_postage_filter'), (0, 'rakuten_postage_filter'),
                                       ('0', 'rakuten_postage_filter'), (1, 'unknown'), ('1', 'unknown'), (2, 'unknown')]:
            raw['postageFlag'] = output_flag
            with patch.object(rakuten, 'APP_ID', 'test'), patch.object(rakuten, 'ACCESS_KEY', 'test'), \
                 patch.object(rakuten, '_throttle'), patch.object(rakuten.urllib.request, 'urlopen', return_value=Response()) as request:
                items = rakuten.fetch_items('紙おむつ', pages=1)
                self.assertIn('postageFlag=1', request.call_args.args[0].full_url)
                self.assertEqual(items[0]['shipping_basis'], expected)
                category = load_categories()['diapers']
                segment = next(s for s in category['segments'] if s['id'] == 'pants-m')
                accepted = normalize_products(items, 'diapers', category, segment)
                self.assertEqual(accepted[0]['shipping_basis'], expected)

    def test_pilot_scope_and_empty_catalog(self):
        categories = load_categories(); cat = categories['diapers']
        for seg in cat['segments']:
            page = render_comparison(categories, 'diapers', cat, seg, [], datetime(2026, 11, 2))
            self.assertEqual('data-purchase-planner' in page, seg['id'] == 'pants-m')
            self.assertIn('noindex,follow', page)
            self.assertNotIn('data-purchase-product', page)
        page = Path('site/diapers/pants/m/index.html').read_text()
        self.assertEqual(page.count('data-purchase-planner'), 1)
        self.assertEqual(page.count('data-savings-sim'), 1)
        self.assertEqual(page.count('data-purchase-product='), 2)
        self.assertIn('メーカーの体重目安', page)
        self.assertIn('脚まわり・お腹のフィット', page)
        self.assertIn('月齢からの予測はしません', page)
