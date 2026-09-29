import subprocess
import sys
import unittest
from pathlib import Path

from scripts.build_site import normalize_products
from src.render import display_product_name, product_card

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
        self.assertLess(text.index("取得対象内の最安単価"), text.index("この順位に入る条件"))

    def test_comparison_has_quick_view_and_quality_copy(self):
        text = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        self.assertIn("上位を早見", text)
        self.assertIn("サイズ選択式やタイプ不明の商品を除外", text)
        self.assertIn("楽天で価格・在庫を見る", text)

    def test_home_explains_quality_and_surfaces_live_price(self):
        text = (ROOT / "site/index.html").read_text(encoding="utf-8")
        self.assertIn("選択式商品は除外", text)
        self.assertIn("取得対象内", text)
        self.assertIn("安さだけでなく、比較条件もそろえます", text)

    def test_display_name_removes_campaign_noise_but_keeps_pack_count(self):
        noisy = "【ポイント10倍！9/30迄】ユニチャーム おむつ BIG 36枚×3個【smtb-s】"
        self.assertEqual(display_product_name(noisy), "ユニチャーム おむつ BIG 36枚×3個")
        pack = "【3個セット】メリーズ パンツ Mサイズ 52枚"
        self.assertEqual(display_product_name(pack), pack)

    def test_product_card_can_show_image_and_gap_from_first(self):
        product = {
            "quantity":{"total":108,"base_unit":"piece","pack_count":3,"evidence":"36枚×3個"},
            "attributes":{},
            "name":"マミーポコ パンツ BIGより大きい 36枚×3個",
            "brand":"マミーポコ",
            "manufacturer":"ユニ・チャーム",
            "shop":"fixture shop",
            "image":"https://example.invalid/item.jpg",
            "unit_price":20.5,
            "unit_metric":"per_piece",
            "price_yen":2214,
            "url":"https://example.invalid/item",
            "source_id":"img-1",
        }
        html = product_card(product, 2, "diapers", {"type":"pants","size":"big_plus"}, best_unit_price=19.5)
        self.assertIn('loading="lazy"', html)
        self.assertIn("1位より +¥1.0 / 1枚", html)
        self.assertIn("fixture shop", html)

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
