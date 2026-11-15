"""Non-identifying pre-validation diagnostics for live comparison catalog drops.

This module only describes count changes. It does not accept previously
published listings as current offers and never changes validator thresholds.
"""
import re


def describe_segment_counts(latest, previous, audit):
    prior = (previous or {}).get("categories") or {}
    current = (latest or {}).get("categories") or {}
    segments = (audit or {}).get("segments") or {}
    reports = []
    for segment_id in sorted(segments):
        stat = segments[segment_id]
        old_count = len((prior.get(segment_id) or {}).get("products") or [])
        now_count = len((current.get(segment_id) or {}).get("products") or [])
        raw_count = max(0, int(stat.get("raw_candidates") or 0))
        reason_counts = {
            key: int(value)
            for key, value in (stat.get("problem_exclusions") or {}).items()
            if isinstance(key, str)
            and re.fullmatch(r"[a-z0-9_]{1,80}", key)
            and isinstance(value, int) and value >= 0
        }
        reports.append({
            "segment": segment_id,
            "previousPublished": old_count,
            "eligibleNow": now_count,
            "rawCandidates": raw_count,
            "reasonCounts": dict(sorted(reason_counts.items())),
            "sharpDrop": old_count >= 5 and now_count < old_count * 0.4,
            "emptyPreviouslyPopulated": old_count >= 2 and now_count == 0,
        })
    return reports
