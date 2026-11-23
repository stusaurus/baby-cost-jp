"""Evidence-gated M-size tape/pants side-by-side checkout comparison.

Price examples are computed from *whole retailer sale sets* in the current
published snapshot. This guide never asserts that price determines fit.
"""
from __future__ import annotations

from .config import SITE_URL
from .purchase import purchase_inputs
from .render import esc, presentation_product_name, shell

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
    paths = (
        '<nav class="m-type-paths" aria-label="Mサイズの商品別購入計算へのリンク">'
        f'<a href="{TYPE_PATHS["tape-m"]}" data-nav-source="m_type_tape_planner" '
        'data-category-id="diapers" data-product-type="tape" data-size="m">'
        'テープMの購入セット数を計算する →</a>'
        f'<a href="{TYPE_PATHS["pants-m"]}" data-nav-source="m_type_pants_planner" '
        'data-category-id="diapers" data-product-type="pants" data-size="m">'
        'パンツMの購入セット数を計算する →</a>'
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
        '<div class="m-type-scroll"><table class="m-type-table">'
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
        intro + choice + table + faq + footer,
        GUIDE_URL,
    )
