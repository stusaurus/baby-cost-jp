"""Evidence-gated M-size tape/pants side-by-side checkout comparison.

Price examples are computed from *whole retailer sale sets* in the current
published snapshot. This guide never asserts that price determines fit.
"""
from __future__ import annotations

import json
import re
from urllib.parse import parse_qs, urlsplit

from .config import SITE_URL
from .purchase import purchase_inputs
from .render import esc, presentation_product_name, shell, static_version

GUIDE_PATH = "guides/m-diapers-tape-vs-pants/"
GUIDE_URL = SITE_URL + GUIDE_PATH
TYPE_PATHS = {
    "tape-m": SITE_URL + "diapers/tape/m/#purchase-planner",
    "pants-m": SITE_URL + "diapers/pants/m/#purchase-planner",
}


def verified_offers(snapshots, segment_id):
    """No partial rankings: all displayed SKUs must satisfy the planner gate."""
    products = ((snapshots or {}).get(segment_id) or {}).get("products", [])
    if len(products) < 2 or not all(purchase_inputs(p) is not None for p in products):
        return []
    return products


def guide_available(snapshots):
    return bool(verified_offers(snapshots, "tape-m") and
                verified_offers(snapshots, "pants-m"))


def lowest_checkout(products, needed):
    """Stable preference: lower actual bill, then fewer leftovers, then source ID."""
    if not products or not isinstance(needed, int) or needed <= 0:
        return None
    offers = []
    for product in products:
        verified = purchase_inputs(product)
        if verified is None:
            return None
        qty = verified["total"]
        sets = (needed + qty - 1) // qty
        offers.append({
            "product": product,
            "sets": sets,
            "bought": sets * qty,
            "payment": sets * verified["price"],
            "surplus": sets * qty - needed,
            "per_set": qty,
        })
    return min(offers, key=lambda x: (
        x["payment"], x["surplus"],
        str(x["product"].get("source_id", "")),
    ))


def verified_retail_link(product):
    """Only expose the exact catalog SKU's Rakuten affiliate link.

    Verify store and item against the mobile destination encoded by the
    Rakuten API; the desktop target must refer to that same store.
    Never derive a shopping URL from a display title or accept redirects to
    an arbitrary host.
    """
    if not isinstance(product, dict):
        return ""
    source_id = product.get("source_id")
    if not isinstance(source_id, str) or source_id.count(":") != 1:
        return ""
    shop, item = source_id.split(":", 1)
    if not (re.fullmatch(r"[A-Za-z0-9_-]+", shop) and
            re.fullmatch(r"[A-Za-z0-9_-]+", item)):
        return ""
    url = product.get("affiliate_url") or product.get("url")
    if not isinstance(url, str) or not url or any(ord(ch) < 33 for ch in url):
        return ""
    try:
        outer = urlsplit(url)
        if (outer.scheme != "https" or outer.netloc != "hb.afl.rakuten.co.jp" or
                not outer.path.startswith("/hgc/") or not outer.path[5:].strip("/") or
                outer.fragment):
            return ""
        params = parse_qs(outer.query)
        mobile, desktop = params.get("m", []), params.get("pc", [])
        if len(mobile) != 1 or len(desktop) != 1:
            return ""
        m, pc = urlsplit(mobile[0]), urlsplit(desktop[0])
        if (m.scheme not in ("http", "https") or
                m.netloc != "m.rakuten.co.jp" or
                pc.scheme != "https" or pc.netloc != "item.rakuten.co.jp"):
            return ""
        mobile_parts = m.path.strip("/").split("/")
        desktop_parts = pc.path.strip("/").split("/")
        if (len(mobile_parts) != 3 or
                [p.lower() for p in mobile_parts] !=
                [shop.lower(), "i", item.lower()] or
                len(desktop_parts) < 2 or desktop_parts[0].lower() != shop.lower()):
            return ""
    except ValueError:
        return ""
    return url


def render_m_diaper_type_guide(snapshots, updated_at):
    ready = guide_available(snapshots)
    tape = verified_offers(snapshots, "tape-m")
    pants = verified_offers(snapshots, "pants-m")
    intro = (
        '<section class="page-head m-type-guide-head">'
        f'<a href="{SITE_URL}diapers/">← 紙おむつのサイズ別一覧</a>'
        '<div class="section-kicker">M SIZE / TAPE vs PANTS</div>'
        '<h1>Mサイズのおむつは、テープとパンツのどちらが安い？</h1>'
        '<p>同じ必要枚数にそろえ、<strong>1枚単価ではなく、実際に購入する販売セット単位の支払総額</strong>'
        'を比較します。テープとパンツは使いやすさが異なるため、安さだけで切り替えを決めないでください。</p>'
        '</section>'
    )
    choice = (
        '<section class="m-type-choice" aria-labelledby="m-type-choice-title">'
        '<h2 id="m-type-choice-title">まず、タイプの違いを確認</h2>'
        '<p><strong>テープ：</strong>寝かせた状態でテープを留めて調整するタイプ。'
        '<strong>パンツ：</strong>足からはかせるタイプ。赤ちゃんの動きや、保護者のおむつ替えのしやすさで選びます。'
        'どちらもMサイズがありますが、使える体重やフィットはメーカー・商品ごとに確認してください。</p>'
        '<p>メーカー資料：'
        '<a href="https://jp.moony.com/ja/tips/baby/childcare/diapers/bm0084.html" '
        'target="_blank" rel="noopener noreferrer">ムーニー公式｜Mサイズの選び方</a>、'
        '<a href="https://www.pampers.jp/newborn/development/article/diaper-size-up" '
        'target="_blank" rel="noopener noreferrer">パンパース公式｜サイズアップの目安</a>。</p>'
        '</section>'
    )
    # If either type lacks sufficient validated offers, the linked calculator
    # may be absent. Link to the real comparison page, not a dead fragment.
    tape_path = TYPE_PATHS["tape-m"] if ready else TYPE_PATHS["tape-m"].split("#")[0]
    pants_path = TYPE_PATHS["pants-m"] if ready else TYPE_PATHS["pants-m"].split("#")[0]
    tape_label = "テープMの購入セット数を計算する →" if ready else "テープMの比較ページを見る →"
    pants_label = "パンツMの購入セット数を計算する →" if ready else "パンツMの比較ページを見る →"
    paths = (
        '<nav class="m-type-paths" aria-label="Mサイズの商品別購入計算へのリンク">'
        f'<a href="{tape_path}" data-nav-source="m_type_tape_planner" '
        'data-category-id="diapers" data-product-type="tape" data-size="m">'
        f'{tape_label}</a>'
        f'<a href="{pants_path}" data-nav-source="m_type_pants_planner" '
        'data-category-id="diapers" data-product-type="pants" data-size="m">'
        f'{pants_label}</a>'
        '</nav>'
    )
    if not ready:
        fallback = (
            '<section class="m-type-empty">'
            '<h2>両タイプの購入総額を比較するための商品が不足しています</h2>'
            '<p>販売枚数・整数価格・送料条件を確認できた商品がそれぞれ2件以上ある時だけ'
            '比較例を表示します。検証ができない価格や推定価格は掲載しません。</p>'
            f'{paths}</section>'
        )
        return shell(
            'Mサイズのテープ・パンツ購入比較｜現在の掲載条件を確認中',
            'Mサイズのテープ・パンツを買う際の支払総額を比較。掲載条件を確認できた場合に購入例を掲載します。',
            intro + choice + fallback,
            GUIDE_URL,
            noindex=True,
        )

    # One validated, static snapshot powers both the crawlable examples and
    # the optional local-only interactive calculation. No dynamic price lookup.
    def planner_offers(products):
        return [
            {
                "id": str(p.get("source_id", "")),
                "name": presentation_product_name(p.get("name", ""))[:120],
                "price": purchase_inputs(p)["price"],
                "total": purchase_inputs(p)["total"],
                "verified": True,
                "url": verified_retail_link(p),
            }
            for p in products
        ]
    safe_json = json.dumps(
        {"tape": planner_offers(tape), "pants": planner_offers(pants)},
        ensure_ascii=False, separators=(",", ":"),
    ).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    interactive = (
        '<section class="m-type-personal" data-m-type-planner aria-labelledby="m-type-personal-title">'
        '<div class="section-kicker">YOUR BUYING PLAN</div>'
        '<h2 id="m-type-personal-title">わが家の枚数・日数・在庫で、買い足し額を比較</h2>'
        '<p>テープとパンツを同じ使用枚数・日数で計算します。'
        '手持ち在庫はタイプごとに入力してください。別のタイプを同じ在庫として二重計上しません。</p>'
        '<div class="m-type-personal-inputs">'
        '<label for="m-type-daily">1日に使う枚数'
        '<input id="m-type-daily" data-m-type-input="daily" type="number" min="1" max="30" step="1" inputmode="numeric" value="6">枚</label>'
        '<label for="m-type-days">購入予定の日数'
        '<input id="m-type-days" data-m-type-input="days" type="number" min="1" max="90" step="1" inputmode="numeric" value="14">日</label>'
        '<label for="m-type-tape-stock">手持ちのテープM'
        '<input id="m-type-tape-stock" data-m-type-input="tape-stock" type="number" min="0" max="10000" step="1" inputmode="numeric" value="0">枚</label>'
        '<label for="m-type-pants-stock">手持ちのパンツM'
        '<input id="m-type-pants-stock" data-m-type-input="pants-stock" type="number" min="0" max="10000" step="1" inputmode="numeric" value="0">枚</label>'
        '</div>'
        '<div class="m-type-personal-presets" role="group" aria-label="購入予定期間">'
        '<span>期間を選ぶ：</span>'
        '<button type="button" data-m-type-days-choice="7" aria-pressed="false">7日</button>'
        '<button type="button" data-m-type-days-choice="14" aria-pressed="true">14日</button>'
        '<button type="button" data-m-type-days-choice="30" aria-pressed="false">30日</button>'
        '</div>'
        '<p class="m-type-personal-error" data-m-type-error role="alert" hidden></p>'
        '<div data-m-type-live hidden>'
        '<p class="m-type-personal-needed">この期間の必要枚数：<strong data-m-type-field="needed"></strong></p>'
        '<div class="m-type-personal-cards">'
        '<article class="m-type-plan-card" data-m-type-card="tape">'
        '<h3>テープM</h3>'
        '<strong class="m-type-plan-payment" data-m-type-field="payment"></strong>'
        '<dl><div><dt>不足枚数</dt><dd data-m-type-field="shortage"></dd></div>'
        '<div><dt>必要な販売セット</dt><dd data-m-type-field="sets"></dd></div>'
        '<div><dt>購入する枚数</dt><dd data-m-type-field="bought"></dd></div>'
        '<div><dt>使用後の余り（在庫込み）</dt><dd data-m-type-field="surplus"></dd></div></dl>'
        '<p class="m-type-plan-item" data-m-type-field="name"></p>'
        '<a class="m-type-plan-buy" data-m-type-buy hidden target="_blank" '
        'rel="nofollow sponsored noopener" data-affiliate="rakuten" '
        'data-category-id="diapers" data-product-type="tape" data-size="m" '
        'data-unit-metric="per_piece" data-conversion-source="m_type_personal_planner" '
        'data-click-position="m_type_personal_result">楽天でこの商品の価格・在庫を見る →</a>'
        f'<a class="m-type-plan-fallback" data-m-type-fallback hidden href="{TYPE_PATHS["tape-m"].split("#")[0]}">'
        'テープMの比較ページで商品を確認 →</a></article>'
        '<article class="m-type-plan-card" data-m-type-card="pants">'
        '<h3>パンツM</h3>'
        '<strong class="m-type-plan-payment" data-m-type-field="payment"></strong>'
        '<dl><div><dt>不足枚数</dt><dd data-m-type-field="shortage"></dd></div>'
        '<div><dt>必要な販売セット</dt><dd data-m-type-field="sets"></dd></div>'
        '<div><dt>購入する枚数</dt><dd data-m-type-field="bought"></dd></div>'
        '<div><dt>使用後の余り（在庫込み）</dt><dd data-m-type-field="surplus"></dd></div></dl>'
        '<p class="m-type-plan-item" data-m-type-field="name"></p>'
        '<a class="m-type-plan-buy" data-m-type-buy hidden target="_blank" '
        'rel="nofollow sponsored noopener" data-affiliate="rakuten" '
        'data-category-id="diapers" data-product-type="pants" data-size="m" '
        'data-unit-metric="per_piece" data-conversion-source="m_type_personal_planner" '
        'data-click-position="m_type_personal_result">楽天でこの商品の価格・在庫を見る →</a>'
        f'<a class="m-type-plan-fallback" data-m-type-fallback hidden href="{TYPE_PATHS["pants-m"].split("#")[0]}">'
        'パンツMの比較ページで商品を確認 →</a></article>'
        '</div>'
        '<p class="m-type-personal-verdict" data-m-type-field="verdict" aria-live="polite"></p>'
        '<p class="m-type-personal-stock-note" data-m-type-field="stock-note"></p>'
        '</div>'
        '<p class="m-type-personal-caveat">各タイプの掲載商品から、同じ1商品を販売セット単位で買い足した場合の最小支払額です。'
        '異なる商品を混ぜた最適化や、現在の在庫・販売価格の保証ではありません。'
        '比較結果は端末内だけで計算し、入力内容を保存・送信しません。'
        '購入前に販売ページでサイズ・枚数・配送先の送料・現在価格・在庫を確認してください。'
        '価格だけで赤ちゃんに合うタイプを選ばないでください。</p>'
        f'<script type="application/json" data-m-type-snapshot>{safe_json}</script>'
        f'<script defer src="{SITE_URL}static/m_type_planner.js?v={static_version("m_type_planner.js")}"></script>'
        '</section>'
    )

    rows = []
    example_days = (7, 14, 30)
    for days in example_days:
        need = 6 * days
        t = lowest_checkout(tape, need)
        p = lowest_checkout(pants, need)
        if not t or not p:
            raise ValueError("Previously validated M catalog became unverified")
        difference = abs(t["payment"] - p["payment"])
        if t["payment"] == p["payment"]:
            compare = "この条件では同額"
        elif t["payment"] < p["payment"]:
            compare = f"テープの掲載候補が¥{difference:,}少ない"
        else:
            compare = f"パンツの掲載候補が¥{difference:,}少ない"
        def entry(selected):
            name = presentation_product_name(selected["product"].get("name", ""))
            return (
                f'<strong>¥{selected["payment"]:,}</strong>'
                f'<small>{selected["sets"]}販売セット・計{selected["bought"]}枚購入'
                f' ／ {need}枚使用後に{selected["surplus"]}枚余る</small>'
                f'<span class="m-type-product-name">{esc(name[:100])}</span>'
            )
        rows.append(
            f'<tr><th scope="row">{days}日分'
            f'<small>例：6枚/日×{days}日＝{need}枚</small></th>'
            f'<td>{entry(t)}</td><td>{entry(p)}</td>'
            f'<td>{compare}</td></tr>'
        )
    table = (
        '<section class="m-type-results" aria-labelledby="m-type-results-title">'
        '<div class="section-kicker">REAL BUNDLE CHECKOUT</div>'
        '<h2 id="m-type-results-title">7日・14日・30日分を買うと、支払額はいくら？</h2>'
        f'<p>現在、販売総枚数と送料条件を確認できたテープM<strong>{len(tape)}商品</strong>、'
        f'パンツM<strong>{len(pants)}商品</strong>から比較しています。'
        '両タイプとも<strong>1日6枚、手持ち在庫0枚</strong>と仮定。'
        '毎日の使用枚数は実際の状況に合わせて各ページの計算機で変更できます。</p>'
        '<div class="m-type-scroll" role="region" aria-label="販売セット単位の購入総額の比較表" tabindex="0"><table class="m-type-table">'
        '<thead><tr><th scope="col">購入予定</th><th scope="col">テープM</th>'
        '<th scope="col">パンツM</th><th scope="col">支払額の比較</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
        '<p class="m-type-caveat">ここでいう「少ない」は、取得対象商品の中で、'
        '指定枚数を満たすために販売セットごと購入した支払額の比較です。'
        '商品の肌への適合、吸収力、成長に伴うサイズ変更は評価していません。'
        'ポイント・クーポン、地域追加送料、販売店の最新価格・在庫は反映できない場合があります。'
        '30日分の表示はまとめ買いを勧めるものではありません。</p>'
        '</section>'
    )
    faq = (
        '<section class="m-type-faq" aria-labelledby="m-type-faq-title">'
        '<h2 id="m-type-faq-title">購入前によくある3つの疑問</h2>'
        '<h3>1枚単価が安い方を買えば、支払額も安い？</h3>'
        '<p>必ずしも同じではありません。大容量セットを2つ買う必要があれば、'
        '1枚単価が低くても当日支払う金額は高くなる場合があります。上の表は販売セット数を整数で計算します。</p>'
        '<h3>テープからパンツへ替えるのはいつ？</h3>'
        '<p>月齢だけでは決められません。赤ちゃんの動き、交換のしやすさ、'
        'メーカー表示の体重目安と装着時のフィットを確認します。'
        '価格の比較だけでおむつの適合を判断しないでください。</p>'
        '<h3>まとめ買いで余ったら？</h3>'
        '<p>使用予定日数を短めに設定し、今のタイプ・サイズで使い切れるか確認してください。'
        '在庫がある場合は、商品別計算機で同じタイプ・サイズの手持ち枚数を差し引いて検討できます。</p>'
        '</section>'
    )
    footer = (
        '<p class="m-type-updated">'
        f'掲載データ更新：{updated_at:%Y-%m-%d %H:%M} JST。'
        '店頭のリアルタイム在庫・最終決済額の確認を保証するものではありません。</p>'
        f'{paths}'
        f'<p class="m-type-back"><a href="{SITE_URL}diapers/">すべてのおむつサイズを見る →</a></p>'
    )
    return shell(
        'Mサイズのおむつ テープとパンツはどちらが安い？｜必要セット数・購入総額比較',
        'テープMとパンツMのどちらが安い？同じ1日6枚で7日・14日・30日分の必要販売セット数・実支払額・余る枚数を、検証済み商品で比較。サイズ適合は別に確認。',
        intro + choice + interactive + table + faq + footer,
        GUIDE_URL,
    )
