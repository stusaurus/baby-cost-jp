import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from src.nursery_guide import render_nursery_diaper_guide

ROOT = Path(__file__).resolve().parents[1]

class NurseryDiaperGuideTests(unittest.TestCase):
    def test_guide_is_indexable_and_has_independent_purchase_math(self):
        doc = (ROOT / "site/guides/nursery-diapers/index.html").read_text(encoding="utf-8")
        self.assertIn("保育園のおむつ、", doc)
        self.assertIn('name="robots" content="index,follow"', doc)
        self.assertIn('href="https://stusaurus.github.io/baby-cost-jp/guides/nursery-diapers/"', doc)
        self.assertIn("10日×3枚＋4日×6枚＝54枚", doc)
        self.assertIn("追加で89枚", doc)
        self.assertIn('id="nursery-catalog"', doc)
        self.assertIn('data-nursery-form', doc)
        self.assertIn('data-nursery-output', doc)
        self.assertIn('data-nav-source="nursery_to_pants_m"', doc)
        self.assertIn('https://www.city.koto.lg.jp/280306/omutusabusuku240131.html', doc)
        self.assertIn("guides/nursery-diapers/", (ROOT / "site/sitemap.xml").read_text(encoding="utf-8"))

    def test_nursery_guide_is_linked_from_home_and_diaper_hub(self):
        for page in ("site/index.html","site/diapers/index.html","site/diapers/pants/m/index.html"):
            body = (ROOT/page).read_text(encoding="utf-8")
            self.assertIn("guides/nursery-diapers/", body, page)

    def test_catalog_has_only_verified_pants_m_offers(self):
        import html, json, re
        valid = {
            "name": '</script><img src=x onerror=alert(1)> パンツ Mサイズ 52枚',
            "source_id": "good-52", "url": "https://hb.afl.rakuten.co.jp/hgc/example",
            "price_yen": 2080, "shipping_basis":"rakuten_postage_filter",
            "quantity":{"total":52, "base_unit":"piece", "confidence":0.99, "evidence":"52枚"}
        }
        invalid = dict(valid, source_id="bad-price", price_yen=0)
        not_affiliate = dict(valid, source_id="bad-link", url="https://example.com/bad")
        no_shipping = dict(valid, source_id="bad-shipping", shipping_basis="unknown")
        doc = render_nursery_diaper_guide([valid,invalid,not_affiliate,no_shipping])
        script = re.search(r'<script type="application/json" id="nursery-catalog">(.*?)</script>',doc)
        self.assertIsNotNone(script)
        self.assertNotIn("</script>",script.group(1))
        offers=json.loads(script.group(1))
        self.assertEqual(len(offers),1)
        self.assertEqual(offers[0]["id"],"good-52")
        self.assertEqual(offers[0]["pieces"],52)
        self.assertEqual(offers[0]["price"],2080)

    def test_guide_works_without_product_offers(self):
        doc=render_nursery_diaper_guide([])
        self.assertIn('id="nursery-catalog">[]</script>',doc)
        self.assertIn('data-nursery-form',doc)

if __name__ == "__main__":
    unittest.main()
