"""Diaper index links to the pants-M planner only for trustworthy offers."""
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import load_categories
from src.render import render_diaper_index, diaper_purchase_planner


class DiaperPlannerEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.categories = load_categories()

    def test_purchase_controls_html_is_well_formed(self):
        """The purchase controls must remain a real div containing fieldsets."""
        from html.parser import HTMLParser

        class ControlsParser(HTMLParser):
            controls = 0
            fieldsets = 0
            inside_controls = False
            depth = 0

            def handle_starttag(self, tag, attrs):
                values = dict(attrs)
                if tag == "div" and values.get("class") == "purchase-controls":
                    self.controls += 1
                    self.inside_controls = True
                    self.depth = 1
                elif self.inside_controls:
                    if tag == "fieldset":
                        self.fieldsets += 1
                    if tag == "div":
                        self.depth += 1

            def handle_endtag(self, tag):
                if self.inside_controls and tag == "div":
                    self.depth -= 1
                    if self.depth == 0:
                        self.inside_controls = False

        html = diaper_purchase_planner([])
        parser = ControlsParser()
        parser.feed(html)
        self.assertEqual(parser.controls, 1)
        self.assertEqual(parser.fieldsets, 2)
        self.assertNotIn('class="purchase-controls><fieldset>', html)

    @staticmethod
    def verified_offer(price, pieces=80, *, confidence=.99, shipping="rakuten_postage_filter"):
        return {
            "unit_price": price / pieces,
            "price_yen": price,
            "quantity": {
                "total": pieces, "base_unit": "piece", "confidence": confidence,
                "evidence": f"{pieces}枚",
            },
            "shipping_basis": shipping,
        }

    def test_entry_requires_two_verified_products(self):
        products = [self.verified_offer(2000), self.verified_offer(2100)]
        html = render_diaper_index(
            self.categories, datetime(2026, 11, 5),
            {"pants-m": {"products": products}},
        )
        self.assertIn('data-nav-source="diaper_index_planner"', html)
        self.assertIn("/diapers/pants/m/#purchase-planner", html)

    def test_entry_hidden_for_empty_single_or_unverified_products(self):
        a = self.verified_offer(2000)
        b = self.verified_offer(2100)
        for products in (
            [], [a],
            [a, self.verified_offer(2100, confidence=.5)],
            [a, self.verified_offer(2100, shipping="unknown")],
        ):
            with self.subTest(count=len(products)):
                html = render_diaper_index(
                    self.categories, datetime(2026, 11, 5),
                    {"pants-m": {"products": products}},
                )
                self.assertNotIn('data-nav-source="diaper_index_planner"', html)
                self.assertNotIn("/diapers/pants/m/#purchase-planner", html)


if __name__ == "__main__":
    unittest.main()
