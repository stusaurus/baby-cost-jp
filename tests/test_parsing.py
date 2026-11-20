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

    def test_pet_manner_wear_and_seller_description_are_not_baby_diapers(self):
        from src.parsing import parse_for_segment_detailed
        segment = {"type": "pants", "size": "s"}
        pet_offers = [
            ("マナーウェア 男の子用 パンツ Sサイズ 40枚", ""),
            ("犬用 マナーウェア パンツ Sサイズ 40枚", ""),
            ("犬のオムツ パンツ Sサイズ 40枚", ""),
            ("猫用 おむつ パンツ Sサイズ 40枚", ""),
            ("紙おむつ パンツ Sサイズ 40枚", "販売店説明: 犬用のマナーウェアです"),
            ("おむつ パンツ Sサイズ 40枚", "小型犬・わんちゃん向け"),
        ]
        for title, supplemental in pet_offers:
            with self.subTest(title=title, supplemental=supplemental):
                parsed, reason = parse_for_segment_detailed(
                    title, "diapers", segment, supplemental_text=supplemental
                )
                self.assertIsNone(parsed)
                self.assertEqual(reason, "excluded_scope")

    def test_regular_baby_pants_remain_eligible_after_pet_exclusion(self):
        from src.parsing import parse_for_segment_detailed
        parsed, reason = parse_for_segment_detailed(
            "メリーズ 紙おむつ パンツ Sサイズ 62枚×3個", "diapers",
            {"type": "pants", "size": "s"},
            supplemental_text="乳児向けの通常タイプ",
        )
        self.assertEqual(reason, "")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["quantity"]["total"], 186)

    def test_explicit_regional_postage_exception_is_not_free_shipping(self):
        from src.parsing import parse_for_segment_detailed
        seg = {"type": "pants", "size": "l"}
        excluded = [
            (
                "【パンツ Lサイズ】メリーズさらさらエアスルー (9~14kg)162枚 "
                "54枚×3パック★SDGs提携協力倉庫より発送★送料無料"
                "(沖縄・北海道・離島を除く)☆"
                "(北海道は1000円。沖縄・離島は2000円自動加算。）",
                "",
            ),
            ("メリーズ パンツ Lサイズ 54枚×3パック", "北海道・沖縄は別途送料が必要です"),
            ("メリーズ パンツ Lサイズ 54枚×3パック", "離島は追加配送料が発生します"),
            ("メリーズ パンツ Lサイズ 54枚×3パック", "沖縄県は送料別となります"),
        ]
        for title, supplemental in excluded:
            with self.subTest(title=title, supplemental=supplemental):
                row, reason = parse_for_segment_detailed(
                    title, "diapers", seg, supplemental_text=supplemental
                )
                self.assertIsNone(row)
                self.assertEqual(reason, "regional_shipping_surcharge")

    def test_no_false_postage_exception_for_ordinary_shipping_claims(self):
        from src.parsing import parse_for_segment_detailed
        seg = {"type": "pants", "size": "l"}
        admitted = [
            "メリーズ パンツ Lサイズ 54枚×3パック 送料無料",
            "メリーズ パンツ Lサイズ 54枚×3パック 北海道の倉庫から発送 送料無料",
            "メリーズ パンツ Lサイズ 54枚×3パック 北海道・沖縄も追加料金なし",
            "メリーズ パンツ Lサイズ 54枚×3パック 全国どこでも送料無料",
        ]
        for title in admitted:
            with self.subTest(title=title):
                row, reason = parse_for_segment_detailed(title, "diapers", seg)
                self.assertEqual(reason, "")
                self.assertIsNotNone(row)

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
