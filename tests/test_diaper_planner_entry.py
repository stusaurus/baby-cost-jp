"""Diaper index links to the pants-M planner only for sufficiently populated results."""
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import load_categories
from src.render import render_diaper_index


class DiaperPlannerEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.categories = load_categories()

    def test_entry_requires_two_verified_products(self):
        snapshots = {"pants-m": {"products": [{"unit_price": 20, "price_yen": 2000}, {"unit_price": 21, "price_yen": 2100}]}}
        html = render_diaper_index(self.categories, datetime(2026, 11, 5), snapshots)
        self.assertIn("diaper_index_planner", html)
        self.assertIn("/diapers/pants/m/#purchase-planner", html)

    def test_entry_hidden_for_empty_or_single_product(self):
        for products in ([], [{"unit_price": 20, "price_yen": 2000}]):
            with self.subTest(count=len(products)):
                html = render_diaper_index(self.categories, datetime(2026, 11, 5),
                                           {"pants-m": {"products": products}})
                self.assertNotIn("diaper_index_planner", html)


if __name__ == "__main__":
    unittest.main()
