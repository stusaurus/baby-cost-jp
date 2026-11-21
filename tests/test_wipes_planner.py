"""Wipes purchase calculator: hard checks on evidence, URL safety and indexing."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from src.wipes_planner import render_wipes_planner, verified_wipes_offers

ROOT=Path(__file__).resolve().parents[1]


def product(id, price, pieces, shipping="rakuten_postage_filter", url="https://hb.afl.rakuten.co.jp/hgc/test"):
    return {"name":f"テスト おしりふき {pieces}枚","source_id":id,"price_yen":price,
            "quantity":{"total":pieces,"base_unit":"piece","confidence":0.99,"evidence":f"{pieces}枚"},
            "shipping_basis":shipping,"url":url}


class WipesPlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable,"scripts/build_site.py","--fixture"],cwd=ROOT,check=True)

    def test_only_verifiable_postage_filtered_affiliate_offers(self):
        ok=product("ok",1417,640)
        candidates=[
            ok,product("no-shipping",50,200,shipping="unknown"),
            product("no-price",0,500),product("no-count",2000,0),
            product("lookalike",100,500,url="https://hb.afl.rakuten.co.jp.evil.example/hgc/x"),
            product("wrong-host",100,500,url="https://example.com/hgc/x"),
            product("javascript",100,500,url="javascript:alert(1)")
        ]
        rows=verified_wipes_offers(candidates)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["id"],"ok")
        self.assertEqual(rows[0]["pieces"],640)
        self.assertEqual(rows[0]["rank"],1)

    def test_crawlable_example_with_true_set_checkout_and_waste(self):
        products=[product("a",3000,1200),product("b",1417,640),product("c",1500,450)]
        rendered=render_wipes_planner(products,str,"https://example.com/static/wipes_plan.js")
        self.assertIn("20枚/日 × 30日 = 600枚",rendered)
        self.assertIn("600 − 200 = 400枚不足",rendered)
        self.assertIn("¥1,417",rendered)
        self.assertIn("240枚",rendered)
        self.assertIn("50枚",rendered)
        self.assertIn("¥1,500",rendered)
        self.assertIn("販売枚数・価格・送料条件を確認できた",rendered)
        self.assertIn("出典：アカチャンホンポ",rendered)
        self.assertIn('name="daily"',rendered)
        self.assertIn('id="wipes-plan-catalog"',rendered)

    def test_script_json_is_escaped_and_catalog_parseable(self):
        unsafe=product("safe-id",2500,800)
        unsafe["name"]='</script><img src=x onerror=alert(1)>'
        section=render_wipes_planner([unsafe],str,"/static/wipes_plan.js")
        match=re.search(r'<script type="application/json" id="wipes-plan-catalog">(.*?)</script>',section)
        self.assertIsNotNone(match)
        self.assertNotIn("<", match.group(1))
        values=json.loads(match.group(1))
        self.assertEqual(values[0]["name"],unsafe["name"])
        self.assertEqual(values[0]["price"],2500)
        self.assertEqual(values[0]["pieces"],800)

    def test_empty_catalog_never_invents_a_price(self):
        rendered=render_wipes_planner([],str,"/static/wipes_plan.js")
        self.assertIn("支払額の例示はできません",rendered)
        self.assertIn('id="wipes-plan-catalog">[]</script>',rendered)
        self.assertNotIn("支払額は<strong>¥",rendered)

    def test_existing_index_is_the_only_new_entrypoint(self):
        wipes=(ROOT/"site/wipes/index.html").read_text(encoding="utf-8")
        self.assertIn('id="wipes-plan"',wipes)
        self.assertIn('name="daily"',wipes)
        self.assertIn("1か月に何枚必要",wipes)
        self.assertIn("まとめ買い",wipes)
        self.assertIn("static/wipes_plan.js",wipes)
        self.assertIn('content="index,follow"',wipes)
        self.assertIn('rel="canonical" href="https://stusaurus.github.io/baby-cost-jp/wipes/"',wipes)
        self.assertLess(wipes.index("取得対象内の最安単価"),wipes.index('id="wipes-plan"'))
        self.assertLess(wipes.index('id="wipes-plan"'),wipes.index('id="products"'))
        self.assertIn("https://stusaurus.github.io/baby-cost-jp/wipes/", (ROOT/"site/sitemap.xml").read_text(encoding="utf-8"))
        other=(ROOT/"site/formula/index.html").read_text(encoding="utf-8")
        self.assertNotIn('id="wipes-plan"',other)
        self.assertNotIn("static/wipes_plan.js",other)


if __name__=="__main__":
    unittest.main()
