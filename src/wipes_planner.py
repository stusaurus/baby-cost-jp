"""One-month baby-wipes purchase planning from verified live catalog evidence.

Never present a per-sheet allocation as an actual checkout price, and never
infer a baby's individual usage or manufacturer sheet thickness.
"""
import html
import json
from urllib.parse import urlsplit

from .purchase import purchase_inputs


def verified_wipes_offers(products, display_name=str):
    """Return only quantity-verified, postage-filtered real Rakuten links."""
    offers = []
    for rank, product in enumerate(products, 1):
        inputs = purchase_inputs(product)
        url = product.get("url") or product.get("affiliate_url") or ""
        if not inputs or not isinstance(url, str):
            continue
        try:
            parsed = urlsplit(url)
            valid_url = (parsed.scheme == "https"
                         and parsed.hostname == "hb.afl.rakuten.co.jp"
                         and parsed.path.startswith("/hgc/")
                         and parsed.username is None and parsed.password is None
                         and parsed.port in (None, 443))
        except ValueError:
            valid_url = False
        if not valid_url:
            continue
        offers.append({
            "id": str(product.get("source_id") or ""),
            "name": str(display_name(product.get("name") or ""))[:180],
            "price": inputs["price"], "pieces": inputs["total"],
            "rank": rank, "url": url,
        })
    return offers


def render_wipes_planner(products, display_name, script_url):
    """Render one crawlable real-catalog example plus editable local calculator."""
    offers = verified_wipes_offers(products, display_name)
    example_need = 20 * 30
    example_stock = 200
    example_shortage = example_need - example_stock

    if offers:
        candidates = [
            dict(row, sets=(example_shortage + row["pieces"] - 1) // row["pieces"])
            for row in offers
        ]
        for row in candidates:
            row["payment"] = row["sets"] * row["price"]
            row["excess"] = row["sets"] * row["pieces"] - example_shortage
        ]
        cheapest = min(candidates, key=lambda p: (p["payment"], p["excess"], p["rank"]))
        least_excess = min(candidates, key=lambda p: (p["excess"], p["payment"], p["rank"]))
        safe_name = html.escape(cheapest["name"], quote=True)
        static_result = (
            f'<p>販売枚数・価格・送料条件を確認できた<strong>{len(offers)}商品</strong>の中で、'
            f'必要な400枚を買い足す場合の支払額が最小なのは'
            f'「<strong>{safe_name}</strong>」です。'
            f'販売単位は<strong>{cheapest["pieces"]:,}枚×{cheapest["sets"]}セット</strong>、'
            f'掲載時の支払額は<strong>¥{cheapest["payment"]:,}</strong>、'
            f'購入後の余りは<strong>{cheapest["excess"]:,}枚</strong>になります。</p>'
        )
        if cheapest["id"] != least_excess["id"] or cheapest["rank"] != least_excess["rank"]:
            static_result += (
                f'<p>余りが最も少ない候補は<strong>{least_excess["excess"]:,}枚</strong>残り、'
                f'その支払額は<strong>¥{least_excess["payment"]:,}</strong>です。'
                f'最少支払額の商品とは違うため、どちらを優先するかで選択が変わります。</p>'
            )
        else:
            static_result += '<p>今回の例では、支払額と余りが最小の候補は同じです。</p>'
    else:
        static_result = '<p>現在、販売枚数・価格・送料条件を確認できた商品がないため、支払額の例示はできません。必要枚数は計算できます。</p>'

    script_json = json.dumps(offers, ensure_ascii=False, separators=(",", ":"))
    script_json = (script_json.replace("<", "\\u003c").replace(">", "\\u003e")
                  .replace("&", "\\u0026"))
    return f'''<section class="wipes-planner" id="wipes-plan" aria-labelledby="wipes-plan-heading">
<div class="section-kicker">ONE MONTH / BUYING GUIDE</div>
<h2 id="wipes-plan-heading">おしりふきは1か月に何枚必要？</h2>
<p>必要枚数は<strong>1日の使用枚数×日数</strong>で計算し、手持ちの分を引いて買い足し枚数を出します。まとめ買いは1枚単価だけでなく、実際の<strong>セット数・支払総額・余る枚数</strong>で確認しましょう。</p>
<p>使用量はお子さんによって異なります。アカチャンホンポの調査では新生児期の平均は<strong>1日19.8枚</strong>と報告されていますが、ここでの20枚/日は計算例であり、すべての家庭の推奨枚数ではありません。<a href="https://www.akachan.jp/ah_labo/questionnaire/230922/" target="_blank" rel="noopener noreferrer">出典：アカチャンホンポ「おしりふき、1日何枚使う？」</a></p>
<div class="wipes-static-example"><h3>30日分の計算例：在庫200枚なら追加400枚</h3>
<p><strong>20枚/日 × 30日 = 600枚</strong>。すでに200枚あるなら<strong>600 − 200 = 400枚不足</strong>です。以下の購入セット計算は、足りない400枚を商品ごとの販売単位で切り上げます。</p>
{static_result}
<p class="wipes-caveat">これは掲載商品内での比較例です。実際の在庫や販売条件は変わります。厚手・薄手、シートの大きさ・肌との相性を同一視せず、赤ちゃんに合う種類か先に確かめてください。</p>
</div>
<form class="wipes-plan-form" data-wipes-plan-form novalidate>
<fieldset><legend>家庭の使用ペースで計算</legend>
<label>1日に使う枚数<input type="number" name="daily" inputmode="numeric" min="0" max="200" step="1" value="20" required></label>
<label>何日分そろえる？<select name="period"><option value="7">7日分</option><option value="14">14日分</option><option value="30" selected>30日分</option></select></label>
<label>今あるおしりふき（枚数）<input type="number" name="stock" inputmode="numeric" min="0" max="30000" step="1" value="200" required></label>
</fieldset>
<button type="submit" class="wipes-plan-submit">必要枚数・買い方を計算する →</button>
<p class="wipes-plan-error" data-wipes-plan-error role="alert" hidden></p>
</form>
<div class="wipes-plan-output" data-wipes-plan-output aria-live="polite" aria-atomic="true" hidden></div>
<p class="wipes-caveat">各商品の販売セットを分割購入できるとは限りません。送料条件は掲載時点の取得対象に基づきます。地域別の加算送料、購入上限、在庫、クーポン、ポイントを購入前に楽天で確認してください。計算入力の生の数値は送信しません。</p>
<script type="application/json" id="wipes-plan-catalog">{script_json}</script>
<script defer src="{html.escape(script_url, quote=True)}"></script>
</section>'''
