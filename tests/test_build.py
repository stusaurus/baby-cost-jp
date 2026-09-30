import subprocess
import sys
import unittest
from pathlib import Path

from scripts.build_site import normalize_products
from src.render import display_product_name, product_card, product_strength_tags

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
        self.assertIn("「安いけど条件が違う」を入れません", text)

    def test_display_name_removes_campaign_noise_but_keeps_pack_count(self):
        noisy = "【ポイント10倍！9/30迄】ユニチャーム おむつ BIG 36枚×3個【smtb-s】"
        self.assertEqual(display_product_name(noisy), "ユニチャーム おむつ BIG 36枚×3個")
        pack = "【3個セット】メリーズ パンツ Mサイズ 52枚"
        self.assertEqual(display_product_name(pack), pack)

    def test_home_has_original_visual_illustrations(self):
        text = (ROOT / "site/index.html").read_text(encoding="utf-8")
        self.assertIn("hero-art", text)
        self.assertIn("cat-icon", text)
        self.assertIn("<svg", text)
        self.assertIn("DIAPER FINDER", text)

    def test_diaper_selector_uses_visual_chips(self):
        text = (ROOT / "site/diapers/index.html").read_text(encoding="utf-8")
        self.assertIn("type-chip", text)
        self.assertIn("size-chips", text)
        self.assertNotIn('id="diaper-type"', text)

    def test_brand_mascot_and_three_step_flow_render(self):
        text = (ROOT / "site/index.html").read_text(encoding="utf-8")
        self.assertIn("brand-mark", text)
        self.assertIn("hero-mascot", text)
        self.assertIn("3ステップで、すぐ比較", text)
        self.assertIn("HOW TO USE", text)

    def test_comparison_pages_have_category_visuals_and_mascot_tip(self):
        text = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        self.assertIn("comparison-head-art--diapers", text)
        self.assertIn("result-mascot-tip", text)
        self.assertIn("quick-image", text)
        self.assertIn("ランキング", text)

    def test_method_page_uses_visual_cards_and_principle(self):
        text = (ROOT / "site/method/index.html").read_text(encoding="utf-8")
        self.assertIn("method-grid", text)
        self.assertIn("method-principle", text)
        self.assertIn("商品数を増やすために、曖昧な商品を載せません", text)
        self.assertIn("footer-brand", text)

    def test_price_snapshot_and_diaper_savings_simulator_render(self):
        diaper = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        wipes = (ROOT / "site/wipes/index.html").read_text(encoding="utf-8")
        self.assertIn("PRICE SNAPSHOT", diaper)
        self.assertIn("中央値", diaper)
        self.assertIn("SAVINGS SIMULATOR", diaper)
        self.assertIn('data-savings-sim', diaper)
        self.assertIn("PRICE SNAPSHOT", wipes)
        self.assertNotIn("SAVINGS SIMULATOR", wipes)

    def test_product_compare_ui_is_rendered(self):
        text = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        self.assertIn("比較に追加", text)
        self.assertIn("data-compare-add", text)
        self.assertIn("data-compare-dock", text)
        self.assertIn("data-compare-modal", text)
        self.assertIn("選んだ商品を比較", text)

    def test_home_has_dynamic_featured_deals(self):
        import json
        text = (ROOT / "site/index.html").read_text(encoding="utf-8")
        latest = json.loads((ROOT / "site/data/latest.json").read_text(encoding="utf-8"))
        self.assertIn("今日の買い候補", text)
        self.assertIn("TODAY'S PICKS", text)
        self.assertIn("中央値より", text)
        self.assertIn("featured_deals", latest)
        self.assertGreaterEqual(len(latest["featured_deals"]), 1)
        self.assertIn("gap_percent", latest["featured_deals"][0])

    def test_purpose_sort_controls_are_rendered(self):
        text = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        self.assertIn("比べ方を切り替える", text)
        self.assertIn('data-sort-mode="unit"', text)
        self.assertIn('data-sort-mode="price"', text)
        self.assertIn('data-sort-mode="quantity"', text)
        self.assertIn("支払総額が安い", text)
        self.assertIn("大容量", text)
        self.assertIn("data-sortable-products", text)

    def test_product_strength_tags_identify_unit_price_total_price_and_capacity(self):
        products = [
            {"source_id":"a","name":"A","unit_price":18.0,"price_yen":3600,"quantity":{"total":200}},
            {"source_id":"b","name":"B","unit_price":20.0,"price_yen":3000,"quantity":{"total":150}},
            {"source_id":"c","name":"C","unit_price":19.0,"price_yen":3800,"quantity":{"total":220}},
        ]
        tags = product_strength_tags(products)
        self.assertIn(("unit","単価◎"), tags["a"])
        self.assertIn(("price","総額◎"), tags["b"])
        self.assertIn(("quantity","大容量◎"), tags["c"])

    def test_strength_tags_render_on_product_cards(self):
        text = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        self.assertIn("strength-tags", text)
        self.assertIn("単価◎", text)
        self.assertTrue("総額◎" in text or "大容量◎" in text)

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
