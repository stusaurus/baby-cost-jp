import unittest
from html.parser import HTMLParser
from src.config import load_categories
from src.render import diaper_price_overview, selector

class EntryTests(unittest.TestCase):
    def test_prices_use_same_segment_and_distinguish_unit_from_total(self):
        categories = load_categories()
        key = categories['diapers']['segments'][0]['id']
        data = {key: {'products': [{'price_yen': 2400, 'unit_price': 20}, {'price_yen': 1600, 'unit_price': 25}]}}
        text = diaper_price_overview(categories, data)
        first = text.split('<tbody>')[1].split('</tr>')[0]
        self.assertIn('¥20.0 / 枚', first)
        self.assertIn('¥1,600', first)
        self.assertIn('2商品', first)
        self.assertNotIn('¥2,400', first)

    def test_sparse_and_missing_segments_never_claim_zero_price(self):
        cats = load_categories(); keys=[s['id'] for s in cats['diapers']['segments']]
        text = diaper_price_overview(cats, {keys[0]: {'products': []}, keys[1]: {'products': [{'price_yen':100, 'unit_price':1}]}})
        self.assertIn('0商品', text)
        self.assertIn('1商品', text)
        self.assertIn('比較準備中', text)
        self.assertIn('未確認', text)
        self.assertNotIn('¥0', text)
        self.assertNotIn('¥100', text)

    def test_hub_link_is_available_without_javascript_or_noscript(self):
        text = selector(load_categories())
        self.assertIn('タイプ・サイズ別の価格一覧を見る', text)
        self.assertNotIn('<noscript>', text)
