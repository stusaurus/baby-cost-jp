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

    def test_consistent_but_different_nested_pack_summaries_keep_only_total(self):
        title = ("【お買得！186枚×2個セット】メリーズ パンツ Mサイズ "
                 "372枚 62枚x6セット 紙おむつ")
        q = parse_piece_quantity(title)
        self.assertIsNotNone(q)
        self.assertEqual(q.total, 372)
        self.assertEqual(q.base_unit, "piece")
        self.assertEqual(q.pack_count, 1)
        self.assertGreaterEqual(q.confidence, .99)
        self.assertIn("186枚×2個", q.evidence)
        self.assertIn("62枚x6セット", q.evidence)
        parsed = parse_for_segment(title, "diapers", {"type":"pants","size":"m"})
        self.assertEqual(parsed["quantity"]["total"], 372)
        self.assertEqual(parsed["quantity"]["pack_count"], 1)
        self.assertAlmostEqual(unit_price(12180, "per_piece", parsed["quantity"]), 12180/372)

    def test_one_consistent_explicit_breakdown_preserves_pack_count(self):
        q = parse_piece_quantity("グーン パンツ Mサイズ 64枚×3個 計192枚")
        self.assertEqual((q.total,q.pack_count,q.evidence),(192,3,"64枚×3個"))
        q2 = parse_piece_quantity("パンパース おむつ パンツ Mサイズ 62枚×3セット 186枚")
        self.assertEqual((q2.total,q2.pack_count),(186,3))

    def test_conflicting_total_remains_rejected_not_sorted_or_guessed(self):
        self.assertIsNone(parse_piece_quantity(
            "メリーズ パンツ M 186枚×2セット 62枚×5セット"))
        self.assertIsNone(parse_piece_quantity(
            "おしりふき 80枚×2個 90枚×3個"))

    def test_weight_variants_keep_existing_behavior(self):
        q = parse_weight_quantity("粉ミルク 800g×2缶 400g×4缶")
        self.assertEqual((q.total,q.pack_count),(1600,2))

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

    def test_rejects_multi_size_listing_when_each_size_has_a_count(self):
        row = parse_for_segment(
            "グーン パンツ M 66枚 / L 56枚 / BIG 50枚 / BIGより大きい 34枚",
            "diapers",
            {"type":"pants","size":"big_plus"},
        )
        self.assertIsNone(row)

    def test_rejects_big_and_big_plus_when_both_have_separate_counts(self):
        row = parse_for_segment(
            "メリーズ パンツ ビッグ38枚 ビッグより大きい24枚",
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

    def test_keeps_big_plus_alias_with_big_marketing_word(self):
        row = parse_for_segment(
            "マミーポコパンツ ビッグ大36枚 大容量 ビッグ 男女共用 ビッグより大きい",
            "diapers",
            {"type":"pants","size":"big_plus"},
        )
        self.assertIsNotNone(row)

    def test_s_size_is_not_confused_by_contextual_newborn_word(self):
        row = parse_for_segment(
            "メリーズ テープ Sサイズ 62枚×4個 出産準備 新生児 肌に優しい",
            "diapers",
            {"type":"tape","size":"s"},
        )
        self.assertIsNotNone(row)

    def test_newborn_is_not_confused_by_smtb_shipping_token(self):
        row = parse_for_segment(
            "メリーズ テープ 新生児用 68枚×4個 送料無料 【smtb-s】",
            "diapers",
            {"type":"tape","size":"newborn"},
        )
        self.assertIsNotNone(row)

    def test_unique_size_count_beats_stray_seo_size_word(self):
        row = parse_for_segment(
            "ムーニー テープ Mサイズ 46枚×4パック 赤ちゃん用品 Sサイズ 香川県",
            "diapers",
            {"type":"tape","size":"m"},
        )
        self.assertIsNotNone(row)
        self.assertEqual(row["attributes"]["size"], "m")

    def test_unique_big_count_beats_stray_l_keyword(self):
        row = parse_for_segment(
            "メリーズ パンツ ビッグ 38枚×3個 まとめ買い Lサイズ 赤ちゃん",
            "diapers",
            {"type":"pants","size":"big"},
        )
        self.assertIsNotNone(row)
        self.assertEqual(row["attributes"]["size"], "big")

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
