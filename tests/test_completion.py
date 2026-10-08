import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from src.parsing import parse_piece_quantity, parse_weight_quantity, parse_for_segment, unit_price
from scripts.validate_site import validate
from src.config import load_categories

ROOT=Path(__file__).resolve().parents[1]

class CompletionTests(unittest.TestCase):
    def test_real_bundle_forms(self):
        for name,total in [('【3個セット】テープ 新生児 72枚',216),('【まとめ買い×4点セット】テープ S 70枚入',280),('80枚×36個 80枚入',2880),('70枚×40パック 70枚×10パック×4セット',2800),('[6個セット] パンツ M 420枚（70枚×6）',420),('186枚×2個セット 372枚 62枚x6セット',372),('パンツ M 52枚×4袋 52枚',208)]:
            with self.subTest(name=name): self.assertEqual(parse_piece_quantity(name).total,total)
        for name,total in [('800g 2缶パック×2個（4缶）',3200),('780g／缶 1パック（2缶）',1560),('800g （8缶）',6400)]:
            with self.subTest(name=name): self.assertEqual(parse_weight_quantity(name).total,total)

    def test_ambiguous_quantities_rejected(self):
        for name in ['80枚×36個 80枚×20個','S100枚 S300枚 L50枚 L200枚','80枚 60枚','72枚×3個 72枚×4個','0枚','2.5枚']:
            with self.subTest(name=name): self.assertIsNone(parse_piece_quantity(name))
        self.assertIsNone(parse_weight_quantity('粉ミルク 800g×2缶 800g×4缶'))

    def test_special_and_conditional_products_excluded(self):
        for title,parser,seg in [('おしりふき 流せる 60枚×15個','wipes',{}),('おしりふき 80枚×20個 初回限定','wipes',{}),('パンツ Mサイズ 夜用 32枚','diapers',{'type':'pants','size':'m'}),('ミルク泡立て器 800g','formula',{}),('おむつ 防臭袋 S100枚 L200枚','diaper_bags',{})]:
            self.assertIsNone(parse_for_segment(title,parser,seg),title)
        self.assertIsNone(parse_for_segment('おむつ 新生児用 72枚','diapers',{'type':'tape','size':'newborn'}))
        self.assertIsNone(parse_for_segment('おしりふき 80枚×20個','wipes',{},'パック数を選べます'))
        self.assertEqual(parse_for_segment('おしりふき 厚手 80枚×20個','wipes',{})['attributes']['variant'],'thick')

    def test_nonfinite_unit_price_excluded(self):
        self.assertIsNone(unit_price(float('nan'),'per_piece',{'total':80,'base_unit':'piece'}))

    def test_generated_discovery_and_growth(self):
        subprocess.run([sys.executable,'scripts/build_site.py','--fixture'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable,'scripts/generate_seo_files.py'],cwd=ROOT,env={**os.environ,'SITE_URL':'https://stusaurus.github.io/baby-cost-jp/'},check=True,stdout=subprocess.DEVNULL)
        validate(ROOT/'site',fixture=True)
        home=(ROOT/'site/index.html').read_text()
        self.assertEqual(home.count('data-growth-stage='),4)
        self.assertIn('月齢・成長から探す',home)
        self.assertIn('商品から探す',home)
        self.assertIn('shop-mobile.webp',home)
        m=(ROOT/'site/diapers/pants/m/index.html').read_text()
        self.assertIn('diapers/pants/l/',m)
        self.assertIn('data-save-id=',m)
        self.assertIn('BreadcrumbList',m)
        sitemap=(ROOT/'site/sitemap.xml').read_text()
        self.assertNotIn('/diapers/tape/newborn/',sitemap)
        self.assertNotIn('<lastmod>',sitemap)
        wipes=(ROOT/'site/wipes/index.html').read_text()
        self.assertIn('用途の異なる商品を混ぜずに比較',wipes)
        self.assertTrue((ROOT/'site/404.html').exists())

    def test_quality_gate_catches_mismatch(self):
        latest_path=ROOT/'site/data/latest.json'; original=latest_path.read_text()
        try:
            latest=json.loads(original);latest['categories']['pants-m']['products'][0]['unit_price']=float('nan')
            latest_path.write_text(json.dumps(latest))
            with self.assertRaisesRegex(RuntimeError,'unit calculation'):validate(ROOT/'site',fixture=True)
        finally:latest_path.write_text(original)
