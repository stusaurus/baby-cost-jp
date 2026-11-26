import unittest
from src.parsing import parse_for_segment_detailed

class DiaperBagScopeTest(unittest.TestCase):
    def test_food_packaging_bags_are_not_ranked(self):
        names = [
            "PP食パン袋 1斤用 LEタイプ 200枚 エコノミータイプ HEIKO 送料無料 パン袋 ビニール袋 飲食店 カフェ 使い捨て 消臭袋 防臭袋 包装 小分け 食パン オムツ おむつ袋",
            "【送料無料】HEIKO PP食パン袋 1斤用 200枚 おむつ 防臭袋",
            "食品包装袋 200枚 おむつ袋 消臭袋",
        ]
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(parse_for_segment_detailed(name, "diaper_bags", {}), (None, "food_packaging_bag"))

    def test_existing_dedicated_products_remain_eligible(self):
        for name, total in [
            ("Bbaoo おむつが臭わない袋 SSサイズ 300枚 18×29cm におわない袋 7層構造 消臭袋 赤ちゃん用 おむつ処理袋", 300),
            ("Deefre おむつが臭わない袋 375枚入 携帯タイプ におわない袋 SSサイズ 便利なロール状 おむつごみ袋 防臭袋", 375),
            ("おむつが臭わない袋 防臭袋 BOS 消臭袋 540枚 おむつ ゴミ箱", 540),
            ("防臭袋 におわない袋 特殊素材 防臭力 NIOGUARD Mサイズ 180枚入り 赤ちゃん オムツ袋", 180),
            ("おむつ 防臭袋 ベビー 300枚×2個 消臭バッグ", 600),
        ]:
            with self.subTest(name=name):
                parsed, reason = parse_for_segment_detailed(name, "diaper_bags", {})
                self.assertEqual(reason, "")
                self.assertEqual(parsed["quantity"]["total"], total)
