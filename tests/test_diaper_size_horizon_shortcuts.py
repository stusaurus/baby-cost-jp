"""A chosen diaper-size review date is an input, not an age/weight forecast."""
import unittest

from src.render import diaper_purchase_planner


class DiaperSizeHorizonShortcutTests(unittest.TestCase):
    def test_optional_7_14_30_day_choices_and_unknown_default(self):
        html = diaper_purchase_planner([])
        for n in (7, 14, 30):
            self.assertIn(f'data-purchase-size-choice="{n}"', html)
            self.assertIn(f'{n}日くらい', html)
        self.assertIn('data-purchase-size-choice="" aria-pressed="true"', html)
        self.assertEqual(html.count('data-purchase-size-choice="'), 4)
        self.assertIn('今のサイズをあと何日使う予定', html)
        self.assertNotIn('今のMサイズをあと何日使う予定', html)
        self.assertIn('サイズが変わる時期を予測するものではありません', html)
        self.assertIn('data-purchase-stock', html)
        self.assertIn('data-purchase-daily', html)
        self.assertIn('data-purchase-days', html)

    def test_original_controls_retained_without_new_product_claims(self):
        html = diaper_purchase_planner([])
        for count in (4, 5, 6, 8):
            self.assertIn(f'data-usage="{count}"', html)
        for days in (7, 14, 30):
            self.assertIn(f'data-purchase-days-choice="{days}"', html)
        self.assertIn('地域追加送料・数量制限・価格変更', html)
        self.assertIn('月齢からの予測はしません', html)
        self.assertNotIn('楽天で購入できます', html)


if __name__ == '__main__':
    unittest.main()
