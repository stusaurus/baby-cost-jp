"""Public educational calculator for home and nursery diaper demand.

No personal details or raw numerical inputs are sent to the backend.
"""
import json
from .config import SITE_URL
from .purchase import purchase_inputs
from .render import shell, static_version, presentation_product_name


def render_nursery_diaper_guide(pants_m_products):
    """Illustrate home/nursery need and verified pants-M checkout choices."""
    nursery_url = f"{SITE_URL}guides/nursery-diapers/"
    eligible = []
    for product in pants_m_products:
        verified = purchase_inputs(product)
        url = product.get("url") or product.get("affiliate_url") or ""
        if not verified or not url.startswith("https://hb.afl.rakuten.co.jp/hgc/"):
            continue
        eligible.append({
            "id": str(product.get("source_id", "")),
            "name": presentation_product_name(product.get("name", "")),
            "price": verified["price"],
            "pieces": verified["total"],
            "url": url,
        })
    json_catalog = json.dumps(eligible, ensure_ascii=False, separators=(",", ":"))
    json_catalog = (json_catalog.replace("<", "\\u003c")
                                .replace(">", "\\u003e")
                                .replace("&", "\\u0026"))
    body = f'''<section class="page-head nursery-head">
<a href="{SITE_URL}diapers/">← 紙おむつの比較へ</a>
<div class="section-kicker">HOME × NURSERY / DIAPER PLAN</div>
<h1>保育園のおむつ、<br>何枚買えばいい？</h1>
<p>家庭で使う分と、園に持参する分を分けて計算。登園日数・手持ち在庫・おむつサブスク利用に合わせて、買いすぎを防ぐ目安を確認できます。</p>
</section>
<section class="nursery-setup" aria-labelledby="nursery-calc-title" id="nursery-calculator">
<div class="section-kicker">CALCULATE YOUR NEED</div>
<h2 id="nursery-calc-title">家庭分＋園で使う分を分ける</h2>
<p>最初の数字は<strong>計算例</strong>です。園のしおりや連絡事項を確認し、実際の枚数に書き換えてください。</p>
<form data-nursery-form novalidate>
<fieldset class="nursery-fields"><legend>1. 日数を決める</legend>
<label>計算する期間<select name="period" data-nursery-field><option value="7">7日間</option><option value="14" selected>14日間</option><option value="30">30日間</option></select></label>
<label>期間中の登園日数<input name="attend" data-nursery-field type="number" inputmode="numeric" min="0" max="30" step="1" value="10" required></label>
</fieldset>
<fieldset class="nursery-fields"><legend>2. 家庭と園での使用量を分ける</legend>
<label>登園日の家庭での使用枚数／日<input name="homeAttend" data-nursery-field type="number" inputmode="numeric" min="0" max="30" step="1" value="3" required></label>
<label>登園しない日の家庭での使用枚数／日<input name="homeOff" data-nursery-field type="number" inputmode="numeric" min="0" max="30" step="1" value="6" required></label>
<label>園でのおむつの用意<select name="mode" data-nursery-field><option value="bring">家庭から持参する</option><option value="subscription">園のサブスク・園支給を使う</option></select></label>
<label data-nursery-bring>登園日の園での使用予定枚数／日<input name="nurseryDaily" data-nursery-field type="number" inputmode="numeric" min="0" max="30" step="1" value="5" required></label>
<label data-nursery-bring>園に追加で置いておく予備枚数<input name="reserve" data-nursery-field type="number" inputmode="numeric" min="0" max="100" step="1" value="5" required></label>
</fieldset>
<fieldset class="nursery-fields"><legend>3. 手持ちを差し引く</legend>
<label>家庭と園で使える、同サイズの手持ち枚数<input name="stock" data-nursery-field type="number" inputmode="numeric" min="0" max="1000" step="1" value="20" required></label>
<p class="nursery-note">園に預けた在庫を含める場合は二重計上しないでください。サイズが異なるおむつは合計に入れません。</p>
</fieldset>
<p class="nursery-error" data-nursery-error role="alert" hidden></p>
<button class="nursery-submit" type="submit">不足枚数と買い方を計算する →</button>
</form>
<div class="nursery-output" data-nursery-output aria-live="polite" aria-atomic="true" hidden></div>
</section>
<section class="nursery-how" aria-labelledby="nursery-explain-title">
<div class="section-kicker">WHY THE TOTAL CHANGES</div>
<h2 id="nursery-explain-title">同じ14日でも、園への持参で変わる</h2>
<p>例えば、14日間で10日登園し、登園日は家庭で3枚、登園しない日は家庭で6枚使うなら、家庭分は<strong>10日×3枚＋4日×6枚＝54枚</strong>です。</p>
<p>園への持参が必要で、登園日ごとに5枚使い、園の予備を5枚追加する例では、園分は<strong>10日×5枚＋予備5枚＝55枚</strong>。合わせて109枚、手持ち20枚なら<strong>追加で89枚</strong>必要です。サブスクで園分を家庭で購入しない場合は、家庭の54枚だけを計算し、手持ち20枚なら34枚不足します。</p>
<p>園の指定枚数は施設や利用形態によって異なります。予備枚数は交換予測ではなく、保護者が設定する<strong>追加の確保量</strong>です。園から指示された持参枚数や補充頻度がある場合は、そちらを優先してください。</p>
</section>
<section class="nursery-how" aria-labelledby="nursery-buy-title">
<div class="section-kicker">WHAT TO CHECK BEFORE BUYING</div>
<h2 id="nursery-buy-title">購入前に確認すること</h2>
<ol>
<li>園への持参が必要か、サブスク・園支給を利用できるかを確認する。</li>
<li>指定されたおむつのメーカー・サイズ・記名・予備枚数を確認する。</li>
<li>家庭と園に残っている同じサイズの在庫だけを数える。</li>
<li>必要枚数と販売セット数の差を確認し、サイズ変更が近いと感じる場合は買いすぎに注意する。</li>
</ol>
<p>計算結果は家庭で購入する枚数の例です。園のサブスク料金・契約条件・在庫補充ルールは計算に含みません。赤ちゃんのおむつ選びは、現在の体重・フィット・メーカー表示も確認してください。</p>
<h3>園のルールが一律でない根拠</h3>
<p>施設の案内には「おむつ6枚を持参」という例がある一方、園によってサブスク利用時は持参不要の例もあります。自治体が保育園向けのサブスクを導入している事例もあります。</p>
<ul>
<li><a href="https://crescendreams.jp/kaede/faq/" target="_blank" rel="noopener noreferrer">かえで保育園｜よくある質問（持参枚数の一例）</a></li>
<li><a href="https://www.skip-hoikuen.com/question/" target="_blank" rel="noopener noreferrer">すきっぷ保育園｜Q&amp;A（園ごとのサブスクの扱い）</a></li>
<li><a href="https://www.city.koto.lg.jp/280306/omutusabusuku240131.html" target="_blank" rel="noopener noreferrer">江東区｜区立保育園のおむつサブスク導入について</a></li>
</ul>
<p>これらは施設ごとの実例であり、全国共通の必要枚数ではありません。通園先の最新案内を優先してください。</p>
</section>
<section class="nursery-related">
<h2>パンツMの送料込み対象商品を比較</h2>
<p>上の計算例に合うセットを比べる場合でも、サイズ・タイプは購入前に必ず確認してください。パンツM以外を使用中なら、タイプ・サイズの一覧から選び直してください。</p>
<a href="{SITE_URL}diapers/pants/m/?plan=14d#purchase-planner" data-nav-source="nursery_to_pants_m" data-category-id="diapers">パンツMの購入セット数を詳しく比較する →</a>
<a href="{SITE_URL}diapers/" data-nav-source="nursery_to_diaper_index" data-category-id="diapers">ほかのタイプ・サイズを比較する →</a>
</section>
<script type="application/json" id="nursery-catalog">{json_catalog}</script>
<script defer src="{SITE_URL}static/nursery.js?v={static_version("nursery.js")}"></script>'''
    return shell(
        "保育園のおむつは何枚必要？家庭・園の持参分と買い足しを計算",
        "保育園のおむつの必要枚数を、登園日数・家庭の使用枚数・園の持参分・サブスク・手持ち在庫に分けて計算。パンツMの検証済み販売セットで支払額と余りも比較できます。",
        body, nursery_url
    )
