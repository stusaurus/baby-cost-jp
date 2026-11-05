"""Evidence-based diaper purchase decisions; independent of page rendering."""
from dataclasses import dataclass
from math import ceil
from typing import Optional

from .purchase import purchase_inputs


@dataclass(frozen=True)
class Decision:
    status: str
    title: str
    detail: str
    required: int
    available: int
    shortage: int
    sets: Optional[int] = None
    payment_yen: Optional[int] = None
    surplus: Optional[int] = None


def decide(product, *, daily_use, days=30, usable_stock=0, size_review_days=None):
    """Never recommend extra stock beyond the known size-review horizon.

    Price and quantity are accepted only via purchase_inputs() evidence gate.
    A size review date is a planning boundary, not a growth prediction.
    """
    def valid_nonnegative_int(v):
        return type(v) is int and 0 <= v <= 100000
    if not valid_nonnegative_int(daily_use) or not valid_nonnegative_int(days) or days > 365 or not valid_nonnegative_int(usable_stock):
        raise ValueError("daily_use, days and usable_stock must be nonnegative bounded integers")
    if size_review_days is not None:
        if not valid_nonnegative_int(size_review_days) or size_review_days > 365:
            raise ValueError("size_review_days must be a bounded integer")
        days = min(days, size_review_days)
    required = daily_use * days
    shortage = max(0, required - usable_stock)
    if shortage == 0:
        return Decision("no_buy", "今は買い足し不要", "入力した使用予定量は手持ち在庫で足ります。", required, usable_stock, 0, 0, 0, 0)
    evidence = purchase_inputs(product)
    if evidence is None:
        return Decision("unverified", "購入条件の確認が必要", "価格・総枚数・送料条件の根拠が不足しています。", required, usable_stock, shortage)
    sets = ceil(shortage / evidence["total"])
    surplus = sets * evidence["total"] - shortage
    title = "必要な数量を確認できました"
    detail = f"不足{shortage}枚に対して{sets}セット、購入後の余剰は{surplus}枚です。"
    if size_review_days is not None and surplus:
        title = "サイズ見直し前の余剰に注意"
        detail += " サイズの変更時期は予測できないため、買い足し前にサイズを確認してください。"
    return Decision("buy", title, detail, required, usable_stock, shortage, sets, sets * evidence["price"], surplus)
