"""A8 mogumo guide: verify official creative and generated site discovery."""
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

from src.config import SITE_URL
from src.meal_guide import AD_CREATIVE, HOME_ENTRY, PAGE_URL, render_toddler_meal_guide, validate_official_creative

ROOT = Path(__file__).resolve().parents[1]


class PageAudit(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.h1 = 0
        self.links = []
        self.pixels = []
        self.canonicals = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'h1':
            self.h1 += 1
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonicals.append(a.get('href'))
        if tag == 'a' and a.get('href'):
            self.links.append(a)
        if tag == 'img' and 'a8.net/0.gif' in a.get('src', ''):
            self.pixels.append(a)


class MogumoGuideTests(unittest.TestCase):
    def test_official_ad_is_unchanged_and_disclosed(self):
        html = render_toddler_meal_guide()
        validate_official_creative(html)
        self.assertEqual(html.count(AD_CREATIVE), 1)
        self.assertIn('広告｜A8.netアフィリエイト', html)
        audit = PageAudit(html)
        self.assertEqual(audit.h1, 1)
        self.assertEqual(audit.canonicals, [PAGE_URL])
        ads = [a for a in audit.links if 'px.a8.net' in a['href']]
        self.assertEqual(ads, [{
            'href': 'https://px.a8.net/svt/ejp?a8mat=4BGCF1+9W19AY+5CLW+5YJRM',
            'rel': 'nofollow',
        }])
        self.assertEqual(audit.pixels, [{
            'border':'0', 'width':'1', 'height':'1',
            'src':'https://www16.a8.net/0.gif?a8mat=4BGCF1+9W19AY+5CLW+5YJRM',
            'alt':'',
        }])

    def test_family_guidance_and_cost_terms_are_not_advertised_as_verified_prices(self):
        html = render_toddler_meal_guide()
        for phrase in ('1歳半〜6歳', '12週間', '送料', '2週間ごと',
                       '3週間ごと', '4週間ごと', '受取回数', 'アレルギー', '定期便利用規約'):
            self.assertIn(phrase, html)
        self.assertNotIn('最安保証', html)
        self.assertNotIn('月額2,500円', html)
        self.assertNotIn('必ず解約できる', html)
        self.assertIn('static/meal-guide.js', html)
        self.assertIn('data-toddler-meal-planner', html)

    def test_missing_pixel_or_duplicate_creative_fails_closed(self):
        html = render_toddler_meal_guide()
        with self.assertRaises(ValueError):
            validate_official_creative(html.replace('www16.a8.net', 'www18.a8.net'))
        with self.assertRaises(ValueError):
            validate_official_creative(html + AD_CREATIVE)
        with self.assertRaises(ValueError):
            validate_official_creative(html.replace('広告｜A8.netアフィリエイト', ''))

    def test_fixture_build_includes_page_and_home_link_only_once(self):
        subprocess.run([sys.executable, 'scripts/build_site.py', '--fixture'], cwd=ROOT, check=True, capture_output=True, text=True)
        home = (ROOT/'site/index.html').read_text(encoding='utf-8')
        guide = (ROOT/'site/guides/toddler-meals/index.html').read_text(encoding='utf-8')
        sitemap = (ROOT/'site/sitemap.xml').read_text(encoding='utf-8')
        self.assertIn(HOME_ENTRY, home)
        self.assertEqual(home.count(PAGE_URL), 1)
        self.assertIn(AD_CREATIVE, guide)
        self.assertEqual(sitemap.count(PAGE_URL), 1)
        self.assertNotIn('a8mat=4BGCF1+9W19AY+5CLW+5YJRM', home)
        self.assertIn(SITE_URL+'guides/toddler-meals/', guide)


if __name__ == '__main__':
    unittest.main()
