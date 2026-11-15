"""The production guard stays strict while upstream evidence shortfall becomes observable."""
import unittest

from scripts.quality_count_diagnostics import describe_segment_counts


class QualityCountDiagnosticsTests(unittest.TestCase):
    def test_sharp_drop_and_exclusion_counts_are_visible_without_product_details(self):
        previous = {"categories": {"pants-s": {"products": [{"source_id": f"x{i}"} for i in range(10)]}}}
        latest = {"categories": {"pants-s": {"products": [{"source_id": "current_secret"}]}}}
        audit = {"segments": {"pants-s": {
            "raw_candidates": 40, "published_count": 1,
            "problem_exclusions": {"ambiguous_diaper_size": 23, "free form error test": 2},
            "published_products": [{"name": "Private Candidate", "source_id": "current_secret"}],
        }}}
        report = describe_segment_counts(latest, previous, audit)
        self.assertEqual(report[0]["segment"], "pants-s")
        self.assertEqual(report[0]["previousPublished"], 10)
        self.assertEqual(report[0]["eligibleNow"], 1)
        self.assertEqual(report[0]["rawCandidates"], 40)
        self.assertTrue(report[0]["sharpDrop"])
        self.assertFalse(report[0]["emptyPreviouslyPopulated"])
        self.assertEqual(report[0]["reasonCounts"], {"ambiguous_diaper_size": 23})
        self.assertNotIn("Private Candidate", str(report))
        self.assertNotIn("current_secret", str(report))

    def test_empty_previous_and_boundaries_are_not_guessed(self):
        prior = {"categories": {"a": {"products": [{} for _ in range(5)]},
                                "b": {"products": [{} for _ in range(2)]},
                                "c": {"products": [{} for _ in range(4)]}}}
        current = {"categories": {"a": {"products": [{}, {}]},
                                  "b": {"products": []},
                                  "c": {"products": [{}, {}, {}]}}}
        audit = {"segments": {k: {"raw_candidates": 4, "problem_exclusions": {}}
                              for k in ("c", "b", "a")}}
        report = {r["segment"]: r for r in describe_segment_counts(current, prior, audit)}
        self.assertFalse(report["a"]["sharpDrop"])  # exactly 40% is not a drop
        self.assertTrue(report["b"]["emptyPreviouslyPopulated"])
        self.assertFalse(report["c"]["sharpDrop"])

    def test_diagnostics_do_not_restore_expired_previous_products(self):
        prev = {"categories": {"pants-s": {"products": [{"source_id": "old"}]}}}
        latest = {"categories": {"pants-s": {"products": []}}}
        audit = {"segments": {"pants-s": {"raw_candidates": 0, "problem_exclusions": {}}}}
        result = describe_segment_counts(latest, prev, audit)
        self.assertEqual(result[0]["eligibleNow"], 0)
        self.assertEqual(len(latest["categories"]["pants-s"]["products"]), 0)
        self.assertEqual(result[0]["previousPublished"], 1)


if __name__ == "__main__":
    unittest.main()
