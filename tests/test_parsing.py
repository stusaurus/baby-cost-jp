import unittest

from src.parsing import parse_for_segment, parse_piece_quantity, parse_weight_quantity, unit_price


class ParsingTests(unittest.TestCase):
    def test_piece_multiplication(self):
        q = parse_piece_quantity("おしりふき 80枚×20個")
        self.assertEqual(q.total, 1600)
        self.assertGreater(q.confidence, 0.98)

    def test_piece_bundle(self):
        q = parse_piece_quantity("おむつ 66枚 3パックセット")
        self.assertEqual(q.total, 198)

    def test_weight_multiplication(self):
        q = parse_weight_quantity("粉ミルク 800g×2缶セット")
        self.assertEqual(q.total, 1600)
        self.assertEqual(q.base_unit, "g")

    def test_diaper_segment_exact_match(self):
        m = {"type": "pants", "size": "m"}
        good = parse_for_segment("パンパース おむつ パンツ Mサイズ 66枚×3個", "diapers", m)
        bad = parse_for_segment("パンパース おむつ パンツ Lサイズ 58枚×3個", "diapers", m)
        self.assertIsNotNone(good)
        self.assertIsNone(bad)

    def test_m_subvariants_stay_in_m(self):
        haihai = parse_for_segment("ムーニー おむつ パンツ Mはいはい 52枚×3個", "diapers", {"type":"pants","size":"m"})
        tacchi = parse_for_segment("ムーニー おむつ パンツ Mたっち 50枚×3個", "diapers", {"type":"pants","size":"m"})
        self.assertIsNotNone(haihai)
        self.assertEqual(haihai["attributes"]["fit_stage"], "はいはい")
        self.assertIsNotNone(tacchi)
        self.assertEqual(tacchi["attributes"]["fit_stage"], "たっち")

    def test_rejects_multi_size_diaper_listing(self):
        row = parse_for_segment(
            "パンパース おむつ パンツ M/L/BIG/BIGより大きい 30枚",
            "diapers",
            {"type":"pants","size":"big_plus"},
        )
        self.assertIsNone(row)

    def test_rejects_size_selection_disclosed_in_caption(self):
        row = parse_for_segment(
            "パンパース おむつ パンツ BIGより大きい 30枚×3個",
            "diapers",
            {"type":"pants","size":"big_plus"},
            supplemental_text="M・L・BIG・BIGより大きいからサイズを選べます",
        )
        self.assertIsNone(row)

    def test_rejects_mixed_tape_and_pants_listing(self):
        row = parse_for_segment(
            "ムーニー おむつ テープ パンツ Mサイズ 52枚",
            "diapers",
            {"type":"pants","size":"m"},
        )
        self.assertIsNone(row)

    def test_keeps_fixed_big_plus_listing(self):
        row = parse_for_segment(
            "グーン おむつ パンツ BIGより大きいサイズ 30枚×3個",
            "diapers",
            {"type":"pants","size":"big_plus"},
            supplemental_text="BIGより大きいサイズの商品説明",
        )
        self.assertIsNotNone(row)
        self.assertEqual(row["attributes"]["size"], "big_plus")

    def test_wipes_excludes_flushable(self):
        row = parse_for_segment("トイレに流せる おしりふき 72枚×12個", "wipes", {})
        self.assertIsNone(row)

    def test_formula_excludes_follow_up(self):
        row = parse_for_segment("和光堂 ぐんぐん フォローアップミルク 830g×2缶", "formula", {})
        self.assertIsNone(row)

    def test_unit_price(self):
        q = {"total": 200, "base_unit": "piece"}
        self.assertEqual(unit_price(4000, "per_piece", q), 20)
        q2 = {"total": 1600, "base_unit": "g"}
        self.assertEqual(unit_price(4800, "per_100g", q2), 300)


if __name__ == "__main__":
    unittest.main()
