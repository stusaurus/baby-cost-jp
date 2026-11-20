import subprocess
import sys
import unittest
from pathlib import Path

from scripts.build_site import attach_price_changes, attach_price_history, brand_page_groups, history_trend_candidate, normalize_products
from src.render import brand_comparison_section, brand_page_url, display_product_name, presentation_product_name, price_history_sparkline, product_brand_label, product_card, product_strength_tags, render_brand_page

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

    def test_comparison_explains_unit_cost_versus_checkout_and_links_related_category(self):
        text = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        self.assertIn("1枚単価と、必要セット数を含む支払額を比べる", text)
        self.assertIn("おしりふきの1枚単価も比べる", text)
        self.assertIn("1セットの販売価格が最小の候補", text)
        self.assertIn("https://stusaurus.github.io/baby-cost-jp/wipes/", text)

    def test_fourteen_day_purchase_decision_uses_verified_real_set_cost(self):
        from src.render import render_fourteen_day_purchase_decision

        def eligible(name, code, price, pieces, shipping="rakuten_postage_filter"):
            return {
                "name": name, "source_id": code, "price_yen": price,
                "quantity": {"total": pieces, "base_unit": "piece",
                             "confidence": .99, "evidence": f"{pieces}枚"},
                "shipping_basis": shipping,
            }

        products = [
            eligible("パンパース パンツM 160枚", "a", 4000, 160),
            eligible("メリーズ パンツM 64枚", "b", 5000, 64),
            eligible("安価だが送料不明 50枚", "c", 100, 50, shipping="unknown"),
        ]
        html = render_fourteen_day_purchase_decision(products)
        self.assertIn('id="14day-example"', html)
        self.assertIn("不足は50枚", html)
        self.assertIn("¥4,000", html)
        self.assertIn("¥5,000", html)
        self.assertIn("110枚", html)
        self.assertIn("14枚", html)
        self.assertIn("¥1,000増やすと", html)
        self.assertIn("余りを96枚減らせる", html)
        self.assertIn("検証できる2商品内", html)
        self.assertNotIn("安価だが送料不明", html)
        self.assertIn('href="#purchase-planner"', html)

    def test_fourteen_day_purchase_decision_empty_or_single_offer(self):
        from src.render import render_fourteen_day_purchase_decision
        self.assertEqual(render_fourteen_day_purchase_decision([]), "")
        single = [{
            "name": "ムーニー パンツM 80枚", "source_id": "only",
            "price_yen": 2500, "quantity": {
                "total": 80, "base_unit": "piece", "confidence": .99,
                "evidence": "80枚"
            }, "shipping_basis": "rakuten_postage_filter",
        }]
        html = render_fourteen_day_purchase_decision(single)
        self.assertEqual(html.count('class="fourteen-day-option"'), 1)
        self.assertIn("同じ商品", html)
        self.assertNotIn("¥0増やすと", html)

    def test_pants_m_has_crawlable_14day_decision_without_other_segment_spill(self):
        pants = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        tape = (ROOT / "site/diapers/tape/m/index.html").read_text(encoding="utf-8")
        self.assertIn('id="14day-example"', pants)
        self.assertIn("販売セット単位の支払額と余り", pants)
        self.assertIn('href="#purchase-planner"', pants)
        self.assertNotIn('id="14day-example"', tape)

    def test_pants_m_14day_entry_does_not_change_other_segments(self):
        pants = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        tape = (ROOT / "site/diapers/tape/m/index.html").read_text(encoding="utf-8")
        self.assertIn("14日・30日分の必要セット数と支払額", pants)
        self.assertIn("パンツMをあと14日使う予定なら？", pants)
        self.assertIn("必要70枚", pants)
        self.assertIn("不足するのは50枚", pants)
        self.assertIn('href="#purchase-planner"', pants)
        self.assertIn('https://stusaurus.github.io/baby-cost-jp/diapers/pants/m/', pants)
        self.assertNotIn("パンツMをあと14日使う予定なら？", tape)
        self.assertNotIn("14日・30日分の必要セット数と支払額", tape)

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

    def test_home_uses_responsive_shop_art(self):
        text = (ROOT / "site/index.html").read_text(encoding="utf-8")
        self.assertIn("shop-wide.webp", text)
        self.assertIn("shop-mobile.webp", text)
        self.assertNotIn("<svg", text)
        self.assertIn('fetchpriority="high"', text)
        self.assertIn('aria-label="ベビー用品の売り場"', text)
        self.assertIn("DIAPER FINDER", text)

    def test_diaper_selector_uses_visual_chips(self):
        text = (ROOT / "site/diapers/index.html").read_text(encoding="utf-8")
        self.assertIn("type-chip", text)
        self.assertIn("size-chips", text)
        self.assertNotIn('id="diaper-type"', text)

    def test_brand_wordmark_and_three_step_flow_render(self):
        text = (ROOT / "site/index.html").read_text(encoding="utf-8")
        self.assertIn("brand-mark", text)
        self.assertIn("THE LITTLE BABY SHOP", text)
        self.assertNotIn("hero-mascot", text)
        self.assertIn("3ステップで、すぐ比較", text)
        self.assertIn("HOW TO USE", text)

    def test_opening_sale_badge_removed_only_from_presentation(self):
        raw = "【オープン記念セール】 グーン ぐんぐん吸収パンツ Mサイズ おむつ 64枚×3個 計192枚"
        clean = "グーン ぐんぐん吸収パンツ Mサイズ おむつ 64枚×3個 計192枚"
        self.assertEqual(presentation_product_name(raw), clean)
        self.assertEqual(display_product_name(raw), raw)
        self.assertEqual(presentation_product_name(clean), clean)
        self.assertEqual(presentation_product_name("【オープン記念セール】"), "【オープン記念セール】")
        self.assertEqual(
            presentation_product_name("【オープン記念セール】 【Mサイズ】 おむつ 64枚×3個"),
            "【Mサイズ】 おむつ 64枚×3個",
        )

    def test_shop_badge_cleanup_preserves_price_count_and_affiliate_evidence(self):
        raw = "【オープン記念セール】 グーン パンツ Mサイズ 64枚×3個"
        p = {
            "name": raw, "source_id": "rakuten:64x3", "price_yen": 4480,
            "unit_price": 4480 / 192, "unit_metric": "per_piece",
            "quantity": {"total": 192, "base_unit": "piece", "pack_count": 3, "evidence": "64枚×3個"},
            "shop": "テスト販売店", "brand": "グーン", "manufacturer": "グーン",
            "url": "https://item.rakuten.co.jp/shop/test", "image": "", "attributes": {},
        }
        markup = product_card(
            p, 1, "diapers", {"type": "pants", "size": "m"},
            best_unit_price=p["unit_price"], purchase=True,
        )
        self.assertIn('<h3 class="product-title"', markup)
        headline = markup.split('<h3 class="product-title"', 1)[1].split('</h3>', 1)[0]
        self.assertNotIn("オープン記念セール", headline.split('>', 1)[1])
        self.assertIn("64枚×3個", headline)
        self.assertIn('class="full-name"', markup)
        self.assertIn(raw, markup)
        self.assertIn("¥4,480", markup)
        self.assertIn("合計 192枚", markup)
        self.assertIn("https://item.rakuten.co.jp/shop/test", markup)
        self.assertIn('data-product-name="', markup)

    def test_comparison_pages_have_department_context(self):
        text = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        self.assertIn("department-label--diapers", text)
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
        self.assertIn("比較トレーに入れる", text)
        self.assertIn("data-compare-add", text)
        self.assertIn("data-compare-dock", text)
        self.assertIn("data-compare-modal", text)
        self.assertIn("トレーの中で、くらべてみよう。", text)

    def test_home_has_dynamic_featured_deals(self):
        import json
        text = (ROOT / "site/index.html").read_text(encoding="utf-8")
        latest = json.loads((ROOT / "site/data/latest.json").read_text(encoding="utf-8"))
        self.assertIn("今日の比較候補", text)
        self.assertIn('class="shop-browse" href="#featured-deals"', text)
        self.assertIn('class="featured-deals" id="featured-deals"', text)
        self.assertLess(text.index('class="featured-deals"'), text.index('id="growth-finder"'))
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
        self.assertIn("必要枚数分の購入額が安い", text)
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

    def test_buying_guide_is_rendered_on_comparison_pages(self):
        text = (ROOT / "site/diapers/pants/m/index.html").read_text(encoding="utf-8")
        self.assertIn("今日はどんな買い方？", text)
        self.assertIn('data-buy-goal="unit"', text)
        self.assertIn('data-buy-goal="price"', text)
        self.assertIn('data-buy-goal="quantity"', text)
        self.assertIn("ストック派", text)
        self.assertIn("data-buy-guide-result", text)

    def test_price_changes_require_same_product_and_quantity(self):
        current = [{
            "source_id":"same","name":"A","price_yen":900,"unit_price":9.0,
            "quantity":{"total":100,"base_unit":"piece"}
        },{
            "source_id":"changed-pack","name":"B","price_yen":1000,"unit_price":10.0,
            "quantity":{"total":100,"base_unit":"piece"}
        }]
        previous = {"products":[
            {"source_id":"same","price_yen":1000,"unit_price":10.0,"quantity":{"total":100,"base_unit":"piece"}},
            {"source_id":"changed-pack","price_yen":1200,"unit_price":12.0,"quantity":{"total":90,"base_unit":"piece"}}
        ]}
        drops = attach_price_changes(current, previous)
        self.assertEqual(current[0]["price_change"]["status"], "down")
        self.assertEqual(current[0]["price_change"]["price_delta_yen"], -100)
        self.assertNotIn("price_change", current[1])
        self.assertEqual(len(drops), 1)

    def test_product_card_renders_previous_price_trend(self):
        product = {
            "quantity":{"total":100,"base_unit":"piece","pack_count":1,"evidence":"100枚"},
            "attributes":{},"name":"テスト商品 100枚","brand":"test","manufacturer":"test","shop":"shop",
            "image":"","unit_price":9.0,"unit_metric":"per_piece","price_yen":900,
            "url":"https://example.invalid","source_id":"trend-1",
            "price_change":{"status":"down","previous_price_yen":1000,"price_delta_yen":-100,"previous_unit_price":10.0,"unit_delta":-1.0}
        }
        html = product_card(product, 1, "diapers", {"type":"pants","size":"m"}, best_unit_price=9.0)
        self.assertIn("前回より ¥100↓", html)
        self.assertIn("price-trend--down", html)

    def test_price_changes_json_is_generated(self):
        self.assertTrue((ROOT / "site/data/price-changes.json").exists())

    def test_price_history_accumulates_only_same_quantity(self):
        products = [{
            "source_id":"same","name":"A","price_yen":900,"unit_price":9.0,
            "quantity":{"total":100,"base_unit":"piece"}
        },{
            "source_id":"changed","name":"B","price_yen":950,"unit_price":9.5,
            "quantity":{"total":100,"base_unit":"piece"}
        }]
        old_history = {"segments":{"pants-m":{"products":{
            "same":{"name":"A","base_unit":"piece","total":100,"points":[{"at":"2026-09-29T00:00:00+09:00","price_yen":1000,"unit_price":10.0}]},
            "changed":{"name":"B","base_unit":"piece","total":90,"points":[{"at":"2026-09-29T00:00:00+09:00","price_yen":1000,"unit_price":11.1}]}
        }}}}
        out = attach_price_history(products,"pants-m",old_history,None,None,"2026-09-30T00:00:00+09:00")
        self.assertEqual(len(products[0]["price_history"]),2)
        self.assertNotIn("price_history",products[1])
        self.assertEqual(len(out["products"]["changed"]["points"]),1)

    def test_sparkline_renders_for_two_or_more_points(self):
        html = price_history_sparkline([
            {"price_yen":1000},{"price_yen":950},{"price_yen":900}
        ])
        self.assertIn("mini-history--down", html)
        self.assertIn("<polyline", html)
        self.assertIn("直近3回で ¥100↓", html)
        self.assertEqual(price_history_sparkline([{"price_yen":1000}]), "")

    def test_history_trend_requires_three_points_and_price_drop(self):
        category={"name":"紙おむつ","metric":"per_piece","path":"diapers","parser":"diapers"}
        segment={"id":"pants-m","label":"パンツ・M","type":"pants","size":"m"}
        product={"name":"A","price_history":[
            {"price_yen":1200},{"price_yen":1100},{"price_yen":900}
        ]}
        row=history_trend_candidate(product,"diapers",category,segment)
        self.assertIsNotNone(row)
        self.assertEqual(row["drop_yen"],300)
        self.assertEqual(row["points"],3)
        self.assertIsNone(history_trend_candidate({"price_history":[{"price_yen":1000},{"price_yen":900}]},"diapers",category,segment))
        self.assertIsNone(history_trend_candidate({"price_history":[{"price_yen":900},{"price_yen":950},{"price_yen":1000}]},"diapers",category,segment))

    def test_home_has_price_drop_ranking_copy(self):
        text=(ROOT / "site/index.html").read_text(encoding="utf-8")
        # Fixture builds do not have a previous snapshot, so the section may be absent.
        self.assertNotIn("長期的な最安値", text) if "値下がりランキング" not in text else self.assertIn("PRICE DROP RANKING", text)

    def test_diaper_brand_comparison_groups_known_brands(self):
        products = [
            {"name":"パンパース パンツ M 100枚","brand":"P&G","manufacturer":"P&G","unit_price":20.0,"price_yen":2000,"quantity":{"total":100},"image":""},
            {"name":"メリーズ パンツ M 90枚","brand":"花王","manufacturer":"花王","unit_price":21.0,"price_yen":1890,"quantity":{"total":90},"image":""},
            {"name":"パンパース パンツ M 120枚","brand":"P&G","manufacturer":"P&G","unit_price":19.0,"price_yen":2280,"quantity":{"total":120},"image":""},
        ]
        self.assertEqual(product_brand_label(products[0]), "パンパース")
        html = brand_comparison_section(products,"diapers","1枚")
        self.assertIn("ブランドの棚", html)
        self.assertIn("パンパース", html)
        self.assertIn("メリーズ", html)
        self.assertIn("2商品掲載", html)
        self.assertIn('data-brand-filter="パンパース"', html)

    def test_brand_compare_not_rendered_for_non_diapers(self):
        products=[{"name":"A","unit_price":1.0,"price_yen":100,"quantity":{"total":100}}]
        self.assertEqual(brand_comparison_section(products,"wipes","1枚"), "")

    def test_brand_page_groups_only_include_known_brands_with_two_products(self):
        products = [
            {"name":"パンパース パンツ M 100枚"},
            {"name":"パンパース パンツ M 120枚"},
            {"name":"メリーズ パンツ M 90枚"},
            {"name":"謎ブランド パンツ M 90枚","brand":"謎ブランド"},
        ]
        groups = brand_page_groups(products)
        self.assertIn("パンパース", groups)
        self.assertEqual(len(groups["パンパース"]), 2)
        self.assertNotIn("メリーズ", groups)
        self.assertNotIn("謎ブランド", groups)

    def test_brand_url_rescue_is_not_indexed_and_reaches_parent(self):
        from scripts.validate_site import inspect_pages
        from src.config import SITE_URL

        route = "diapers/pants/m/goon/"
        stub = (ROOT / "site" / route / "index.html").read_text(encoding="utf-8")
        parent = SITE_URL + "diapers/pants/m/"
        self.assertIn('<meta name="robots" content="noindex,follow">', stub)
        self.assertIn(f'<meta http-equiv="refresh" content="0; url={parent}">', stub)
        self.assertIn(f'<link rel="canonical" href="{parent}">', stub)
        self.assertIn(f'<a href="{parent}">', stub)
        self.assertNotIn('content="10;', stub)
        self.assertNotIn(SITE_URL + route, (ROOT / "site/sitemap.xml").read_text(encoding="utf-8"))
        pages, errors = inspect_pages(ROOT / "site", SITE_URL)
        self.assertEqual(errors, [])
        self.assertEqual(pages[SITE_URL + route].robots, "noindex,follow")

    def test_brand_route_history_survives_zero_offers_and_rejects_unknown_paths(self):
        from src.config import load_categories
        from scripts.build_site import stable_brand_routes
        categories = load_categories()
        prior = {
            "brand_page_history": [
                "diapers/pants/m/goon/",
                "diapers/pants/m/merries/",
                "../../bad/",
                "diapers/pants/m/unknown-brand/",
            ],
        }
        allowed, history = stable_brand_routes(
            categories, prior,
            {"pants-m": {"products": []}},
            [],
        )
        self.assertIn("diapers/pants/m/goon/", history)
        self.assertIn("diapers/pants/m/merries/", history)
        self.assertNotIn("../../bad/", history)
        self.assertNotIn("diapers/pants/m/unknown-brand/", history)
        self.assertIn("diapers/pants/m/goon/", allowed)

    def test_brand_route_history_remembers_single_eligible_product(self):
        from src.config import load_categories
        from scripts.build_site import stable_brand_routes
        categories=load_categories()
        _, history=stable_brand_routes(
            categories, {}, {"pants-m":{"products":[{
                "name":"パンパース おむつ パンツ Mサイズ 66枚", "brand":"パンパース"
            }]}}, [],
        )
        self.assertIn("diapers/pants/m/pampers/", history)

    def test_brand_page_url_is_stable(self):
        segment={"type":"pants","size":"m"}
        self.assertTrue(brand_page_url(segment,"パンパース").endswith("/diapers/pants/m/pampers/"))
        self.assertEqual(brand_page_url(segment,"その他"), "")

    def test_brand_dedicated_page_has_unique_copy_and_canonical(self):
        category={"name":"紙おむつ","metric":"per_piece","parser":"diapers","path":"diapers"}
        segment={"id":"pants-m","type":"pants","size":"m","label":"パンツ・M"}
        products=[
            {"source_id":"a","name":"パンパース パンツ M 100枚","brand":"パンパース","manufacturer":"P&G","shop":"A","image":"","unit_price":20.0,"unit_metric":"per_piece","price_yen":2000,"url":"https://example.invalid/a","quantity":{"total":100,"base_unit":"piece","pack_count":1,"evidence":"100枚"},"attributes":{}},
            {"source_id":"b","name":"パンパース パンツ M 120枚","brand":"パンパース","manufacturer":"P&G","shop":"B","image":"","unit_price":19.0,"unit_metric":"per_piece","price_yen":2280,"url":"https://example.invalid/b","quantity":{"total":120,"base_unit":"piece","pack_count":1,"evidence":"120枚"},"attributes":{}},
        ]
        from datetime import datetime
        from zoneinfo import ZoneInfo
        html=render_brand_page({},category,segment,"パンパース",products,datetime(2026,9,30,12,0,tzinfo=ZoneInfo("Asia/Tokyo")))
        self.assertIn("パンパース",html)
        self.assertIn("THE BRAND SHELF",html)
        self.assertIn("2商品",html)
        self.assertIn("販売価格帯",html)
        self.assertIn("/diapers/pants/m/pampers/",html)
        self.assertIn('meta name="robots" content="index,follow"',html)

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

    def test_nested_bundle_breakdown_is_not_mislabeled_as_manufacturer_pack(self):
        from src.parsing import parse_piece_quantity
        name=("【お買得！186枚×2個セット】メリーズ パンツ Mサイズ "
              "372枚 62枚x6セット 紙おむつ")
        q=parse_piece_quantity(name).as_dict()
        item={
            "quantity":q,"attributes":{},"name":name,"brand":"メリーズ",
            "manufacturer":"花王","shop":"fixture","image":"",
            "unit_price":12180/372,"unit_metric":"per_piece",
            "price_yen":12180,"shipping_basis":"rakuten_postage_filter",
            "url":"https://example.invalid/unchanged","source_id":"nested-pack",
        }
        html=product_card(item,4,"diapers",{"type":"pants","size":"m"},
                          best_unit_price=20.0,purchase=True)
        self.assertIn("合計 372枚",html)
        self.assertIn("¥12,180",html)
        self.assertIn("¥12,180 ÷ 372枚",html)
        self.assertIn("186枚×2個 / 62枚x6セット",html)
        self.assertNotIn("2パック相当",html)
        self.assertNotIn("1パック相当",html)
        self.assertIn("https://example.invalid/unchanged",html)
        self.assertIn("必要購入セット数",html)
        self.assertIn("購入時の支払額",html)

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
