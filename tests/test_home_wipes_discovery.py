"""The existing wipes calculator must be discoverable without new thin SEO pages."""
import unittest
from datetime import datetime, timezone

from src.config import SITE_URL, load_categories
from src.render import render_home
from src.wipes_planner import render_wipes_planner


class WipesHomeDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.categories = load_categories()

    def home(self):
        return render_home(self.categories, {}, [], [], [],
                           datetime(2026, 11, 22, tzinfo=timezone.utc))

    def test_one_contextual_home_link_reaches_existing_calculator(self):
        html = self.home()
        self.assertIn('id="home-wipes-title"', html)
        self.assertIn("おしりふきは1か月に何枚必要？", html)
        self.assertIn("1日20枚を30日間使うなら600枚", html)
        self.assertIn("手持ち200枚を差し引くと、買い足しは400枚", html)
        self.assertIn("必要な購入数・支払総額・余る枚数", html)
        self.assertIn("実際の使用枚数は家庭によって異なります", html)
        href = SITE_URL + "wipes/#wipes-plan"
        self.assertEqual(html.count('href="' + href + '"'), 1)
        self.assertIn('data-nav-source="home_wipes_planner"', html)
        self.assertIn('data-category-id="wipes"', html)

        # The exact hash exists on the indexable existing product page.
        wipes = render_wipes_planner([], str, SITE_URL + "static/wipes_plan.js")
        self.assertIn('id="wipes-plan"', wipes)

    def test_existing_home_navigation_and_seo_are_preserved(self):
        html = self.home()
        self.assertIn('data-nav-source="home_nursery_planner"', html)
        self.assertIn('data-nav-source="home_category"', html)
        self.assertIn("必要枚数・購入額を計算", html)
        self.assertIn('href="#diaper-selector"', html)
        self.assertIn('name="robots" content="index,follow"', html)
        self.assertIn('rel="canonical" href="' + SITE_URL + '"', html)
        self.assertNotIn('href="' + SITE_URL + "wipes-plan/", html)

    def test_no_unverified_checkout_price_or_guaranteed_usage_claims(self):
        html = self.home()
        section = html.split('<section class="nursery-home-promo wipes-home-promo"', 1)[1].split('</section>', 1)[0]
        for phrase in ('最安保証', 'すべての家庭で必要', '20枚が推奨', '¥0', '必ず購入'):
            self.assertNotIn(phrase, section)


if __name__ == "__main__":
    unittest.main()
