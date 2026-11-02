"""Purchase inputs from accepted catalog evidence; never parse display labels."""
import math


def purchase_inputs(product):
    if not isinstance(product, dict):
        return None
    q = product.get('quantity') or {}
    if not isinstance(q, dict):
        return None
    price, total = product.get('price_yen'), q.get('total')
    def integer(value):
        return type(value) in (int, float) and math.isfinite(value) and value > 0 and value == int(value)
    if not integer(total) or total > 20000 or q.get('base_unit') != 'piece':
        return None
    confidence = q.get('confidence')
    if type(confidence) not in (int, float) or not math.isfinite(confidence) or not .88 <= confidence <= 1 or not q.get('evidence'):
        return None
    if not integer(price) or price > 999999999:
        return None
    if product.get('shipping_basis') != 'rakuten_postage_filter':
        return None
    return {'price': int(price), 'total': int(total), 'verified': True}


def purchase_result_html(product):
    inputs = purchase_inputs(product)
    if inputs is None:
        return '<p class="purchase-unavailable">購入計算はできません。販売総枚数・価格・送料条件の確認が必要です。</p>'
    total, price, needed = inputs['total'], inputs['price'], 150
    sets = (needed + total - 1) // total
    # Exact integer rounding to one decimal, matching the client implementation.
    cost_tenths = (price * needed * 20 + total) // (total * 2)
    return f'''<p class="purchase-context">1日5枚 × 30日：必要150枚</p><dl class="purchase-metrics"><div><dt>必要購入セット数</dt><dd>{sets:,}<small>セット</small></dd></div><div class="purchase-payment"><dt>購入時の支払額（掲載条件）</dt><dd>¥{sets * price:,}</dd></div><div><dt>1セットの総枚数</dt><dd>{total:,}<small>枚</small></dd></div><div><dt>購入後に余る枚数</dt><dd>{sets * total - needed:,}<small>枚</small></dd></div></dl><p class="purchase-equivalent">使用150枚分の費用相当額：約¥{cost_tenths / 10:,.1f}（按分・支払額とは別）</p>'''
