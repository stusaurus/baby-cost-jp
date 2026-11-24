"""L/BIG whole-sale-set buying paths: preserve segment identity and fail closed."""
import unittest
from datetime import datetime, timezone
from src.config import load_categories, SITE_URL
from src.render import render_comparison, render_diaper_index, render_home

NOW = datetime(2026, 11, 24, tzinfo=timezone.utc)

def sku(key, size, pieces, price, *, shipping='rakuten_postage_filter', confidence=.99):
    return dict(source_id=key, name=f'赤ちゃん用 パンツ {size}サイズ {pieces}枚',
                price_yen=price, unit_price=price/pieces, unit_metric='per_piece',
                quantity=dict(total=pieces, base_unit='piece', evidence=f'{pieces}枚',
                              confidence=confidence, pack_count=1),
                shipping_basis=shipping, url='https://hb.afl.rakuten.co.jp/hgc/'+key,
                image='', manufacturer='テスト', brand='テスト', shop='テスト', attributes={})

class PantsLargePlannerTests(unittest.TestCase):
    def setUp(self):
        self.cats = load_categories()
        self.cat = self.cats['diapers']
        self.segments = {s['id']: s for s in self.cat['segments']}

    def page(self, key, products):
        return render_comparison(self.cats, 'diapers', self.cat, self.segments[key], products, NOW)

    def test_exact_size_whole_sale_sets_and_metadata(self):
        for size in ('l','big'):
            with self.subTest(size=size):
                key = 'pants-'+size
                rows = [sku(key+'-80', size, 80, 2800), sku(key+'-160', size, 160, 5100)]
                html = self.page(key, rows)
                self.assertIn(f'<title>おむつ パンツ{size.upper()}サイズ｜1枚あたり価格・まとめ買い総額比較</title>', html)
                self.assertIn(f'パンツ{size.upper()}をあと14日使う予定なら？', html)
                self.assertIn('1日5枚 × 14日：必要70枚', html)
                self.assertIn('¥2,800', html)
                self.assertIn('¥5,100', html)
                self.assertIn('1日5枚・14日分は計算例', html)
                self.assertIn('id="purchase-planner"', html)
                self.assertIn('data-product-type="pants"', html)
                self.assertIn(f'data-size="{size}"', html)
                self.assertNotIn('パンツMをあと14日', html)
                self.assertNotIn('パンツSをあと14日', html)
                self.assertIn(f'rel="canonical" href="{SITE_URL}diapers/pants/{size}/"', html)
                self.assertIn('content="index,follow"', html)

    def test_unverified_and_missing_offers_never_advertise_calculator(self):
        for size in ('l','big'):
            key = 'pants-'+size
            good = sku(key+'-80', size, 80, 2800)
            for rows in ([], [good], [good, sku('unknown',size,160,5100,shipping='unknown')],
                         [good,sku('weak',size,160,5100,confidence=.5)]):
                with self.subTest(size=size, rows=len(rows)):
                    html = self.page(key, rows)
                    self.assertNotIn('id="purchase-planner"', html)
                    self.assertNotIn('まとめ買い総額比較</title>', html)
                    snapshots={key:{'products':rows}}
                    hub = render_diaper_index(self.cats,NOW,snapshots)
                    home = render_home(self.cats,{},[],[],[],NOW,diaper_snapshots=snapshots)
                    for surface in (hub,home):
                        self.assertNotIn(f'diapers/pants/{size}/#purchase-planner',surface)
                    self.assertIn(f'href="{SITE_URL}diapers/pants/{size}/"',hub)

    def test_home_and_hub_links_match_each_ready_segment(self):
        snapshots={}
        for size in ('l','big'):
            key='pants-'+size
            snapshots[key]={'products':[sku(key+'-80',size,80,2800),sku(key+'-160',size,160,5100)]}
        hub = render_diaper_index(self.cats,NOW,snapshots)
        home = render_home(self.cats,{},[],[],[],NOW,diaper_snapshots=snapshots)
        for size in ('l','big'):
            target=f'href="{SITE_URL}diapers/pants/{size}/#purchase-planner"'
            self.assertIn(target,hub)
            self.assertIn(target,home)
            self.assertIn(f'data-nav-source="diaper_index_pants_{size}_planner"',hub)
        self.assertNotIn('diapers/pants/big_plus/#purchase-planner',home)
        self.assertNotIn('diapers/tape/l/#purchase-planner',home)


class FinalDiaperSizePlannerTests(unittest.TestCase):
    setUp = PantsLargePlannerTests.setUp
    page = PantsLargePlannerTests.page
    def test_final_two_sizes_have_exact_identity_and_calculation(self):
        cases = (('tape-l','tape','l','テープL'),
                 ('pants-big-plus','pants','big_plus','パンツBIGより大きい'))
        for key,kind,size,label in cases:
            with self.subTest(key=key):
                rows = [sku(key+'-80',size,80,2800),sku(key+'-160',size,160,5100)]
                html = self.page(key,rows)
                self.assertIn(f'<title>おむつ {label}サイズ｜1枚あたり価格・まとめ買い総額比較</title>',html)
                self.assertIn(f'{label}をあと14日使う予定なら？',html)
                self.assertIn('1日5枚 × 14日：必要70枚',html)
                self.assertIn('¥2,800',html)
                self.assertIn('¥5,100',html)
                self.assertIn('1日5枚・14日分は計算例',html)
                self.assertIn('id="purchase-planner"',html)
                self.assertIn(f'data-product-type="{kind}"',html)
                self.assertIn(f'data-size="{size}"',html)
                self.assertIn(f'rel="canonical" href="{SITE_URL}diapers/{kind}/{size}/"',html)
                self.assertIn('content="index,follow"',html)
                self.assertNotIn('パンツBIGをあと14日',html)
                self.assertNotIn('パンツLをあと14日',html)
                for surface in (
                    render_diaper_index(self.cats,NOW,{key:{'products':rows}}),
                    render_home(self.cats,{},[],[],[],NOW,diaper_snapshots={key:{'products':rows}}),
                ):
                    self.assertIn(f'href="{SITE_URL}diapers/{kind}/{size}/#purchase-planner"',surface)
                    other = 'diapers/pants/big/' if key=='pants-big-plus' else 'diapers/pants/l/'
                    self.assertNotIn(other+'#purchase-planner',surface)

    def test_final_two_sizes_fail_closed_without_verified_catalog(self):
        for key,kind,size in (('tape-l','tape','l'),('pants-big-plus','pants','big_plus')):
            good = sku(key+'-80',size,80,2800)
            for rows in ([],[good],[good,sku('bad',size,160,5100,shipping='unknown')],
                         [good,sku('bad',size,160,5100,confidence=.5)]):
                with self.subTest(key=key,rows=len(rows)):
                    html = self.page(key,rows)
                    self.assertNotIn('id="purchase-planner"',html)
                    self.assertNotIn('まとめ買い総額比較</title>',html)
                    snapshots={key:{'products':rows}}
                    for surface in (
                        render_diaper_index(self.cats,NOW,snapshots),
                        render_home(self.cats,{},[],[],[],NOW,diaper_snapshots=snapshots),
                    ):
                        self.assertNotIn(f'diapers/{kind}/{size}/#purchase-planner',surface)

    def test_all_nine_ready_sizes_have_one_direct_link_each(self):
        snapshots = {key:{'products':[sku(key+'-80',s['size'],80,2800),
                                       sku(key+'-160',s['size'],160,5100)]}
                     for key,s in self.segments.items()}
        self.assertEqual(len(snapshots),9)
        for surface in (
            render_diaper_index(self.cats,NOW,snapshots),
            render_home(self.cats,{},[],[],[],NOW,diaper_snapshots=snapshots),
        ):
            self.assertEqual(surface.count('class="home-purchase-path"'),9)
            for s in self.segments.values():
                self.assertEqual(surface.count(f'href="{SITE_URL}diapers/{s["type"]}/{s["size"]}/#purchase-planner"'),1)
