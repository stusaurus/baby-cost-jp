import unittest
from src.purchase_decision import decide

VALID = {
    "price_yen": 980,
    "shipping_basis": "rakuten_postage_filter",
    "quantity": {"total": 60, "base_unit": "piece", "confidence": 0.99, "evidence": "catalog verified"},
}


def test_no_buy_when_stock_covers_need_even_if_product_unverified():
    d = decide({}, daily_use=5, days=30, usable_stock=150)
    assert (d.status, d.payment_yen, d.sets, d.shortage) == ("no_buy", 0, 0, 0)


def test_exact_quantity_and_payment():
    d = decide(VALID, daily_use=5, days=30, usable_stock=30)
    assert (d.required, d.shortage, d.sets, d.payment_yen, d.surplus) == (150, 120, 2, 1960, 0)


def test_shortage_and_surplus():
    d = decide(VALID, daily_use=5, days=30, usable_stock=10)
    assert (d.shortage, d.sets, d.surplus) == (140, 3, 40)


def test_size_review_is_horizon_not_growth_prediction():
    d = decide(VALID, daily_use=5, days=30, usable_stock=0, size_review_days=10)
    assert (d.required, d.sets, d.surplus, d.title) == (50, 1, 10, "サイズ見直し前の余剰に注意")


def test_missing_price_or_shipping_is_not_a_recommendation():
    d = decide({"price_yen": 980}, daily_use=5)
    assert d.status == "unverified" and d.payment_yen is None


INVALID_CASES = [
    {"daily_use": -1},
    {"daily_use": 1.5},
    {"daily_use": True},
    {"daily_use": 5, "days": 366},
    {"daily_use": 5, "usable_stock": -2},
    {"daily_use": 5, "size_review_days": -1},
]


def test_reject_invalid_inputs():
    for kwargs in INVALID_CASES:
        with unittest.TestCase().assertRaises(ValueError):
            decide(VALID, **kwargs)
