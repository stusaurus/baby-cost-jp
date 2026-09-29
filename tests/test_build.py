import subprocess
import sys
import unittest
from pathlib import Path

from scripts.build_site import normalize_products

ROOT = Path(__file__).resolve().parents[1]


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, "scripts/build_site.py", "--fixture"], cwd=ROOT, check=True)

    def test_core_pages_exist(self):
        expected = [
            "site/index.html",
            "site/diapers/index.html",
            "site/diapers/pants/m/index.html",
            "site/wipes/index.html",
            "site/formula/index.html",
            "site/diaper-bags/index.html",
            "site/method/index.html",
            "site/sitemap.xml",
            "site/data/latest.json",
            "site/data/quality-audit.json",
        ]
        for path in expected:
            self.assertTrue((ROOT / path).exists(), path)

    def test_wrong_diaper_size_is_filtered(self):
        text = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        self.assertNotIn("bad-l", text)
        self.assertNotIn("パンツ Lサイズ 58枚", text)

    def test_first_answer_is_above_long_explanation(self):
        text = (ROOT / "site/wipes/index.html").read_text(encoding="utf-8")
        self.assertLess(text.index("単価が安い順"), text.index("順位の計算"))

    def test_m_subvariant_has_no_separate_index_url(self):
        sitemap = (ROOT / "site/sitemap.xml").read_text(encoding="utf-8")
        self.assertNotIn("m_haihai", sitemap)
        self.assertFalse((ROOT / "site/diapers/pants/m_haihai/index.html").exists())

    def test_machine_readable_snapshot_has_common_fields(self):
        import json
        payload = json.loads((ROOT / "site/data/latest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["pricing_scope"], "rakuten_postage_included_or_free_shipping")
        product = payload["categories"]["pants-m"]["products"][0]
        for key in ("source", "source_id", "name", "price_yen", "shop", "affiliate_url", "unit_price", "unit_metric", "quantity", "manufacturer", "brand", "attributes"):
            self.assertIn(key, product)

    def test_comparison_shows_quantity_before_calculation_details(self):
        text = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        self.assertIn("取得対象内の最安単価", text)
        self.assertIn("合計 222枚", text)
        self.assertLess(text.index("合計 222枚"), text.index("単価の計算を見る"))

    def test_same_normalized_name_is_deduped_and_cheapest_offer_wins(self):
        raw = [
            {"source":"rakuten","source_id":"dup-expensive","name":"パンパース おむつ パンツ Mサイズ 66枚×3個","price_yen":5200,"url":"https://example.invalid/a","shop":"A","image":"","review_count":10},
            {"source":"rakuten","source_id":"dup-cheap","name":"パンパース おむつ パンツ Mサイズ 66枚×3個","price_yen":4800,"url":"https://example.invalid/b","shop":"B","image":"","review_count":5},
        ]
        audit = []
        rows = normalize_products(raw, "diapers", {"parser":"diapers","metric":"per_piece"}, {"id":"pants-m","type":"pants","size":"m"}, audit=audit)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_id"], "dup-cheap")
        self.assertTrue(any(x["reason"] == "duplicate_equivalent_name" for x in audit))


if __name__ == "__main__":
    unittest.main()
