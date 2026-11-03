"""Family-focused frozen toddler meal costs; contains the unchanged A8 creative.

No product price, delivery fee, approval conditions or clinical suitability
are inferred from the affiliate link. The planner uses user-entered data only.
"""
from __future__ import annotations

from .config import SITE_URL
from .render import shell, static_version

SLUG = "guides/toddler-meals/"
PAGE_URL = SITE_URL + SLUG
AD_CREATIVE = '''<a href="https://px.a8.net/svt/ejp?a8mat=4BGCF1+9W19AY+5CLW+5YJRM" rel="nofollow">【子どもお墨付き】冷凍幼児食モグモ </a>
<img border="0" width="1" height="1" src="https://www16.a8.net/0.gif?a8mat=4BGCF1+9W19AY+5CLW+5YJRM" alt="">'''

HOME_ENTRY = (
    '<section class="toddler-entry" aria-labelledby="toddler-entry-title">'
    '<div class="section-kicker">TODDLER MEAL PLANNER</div>'
    '<h2 id="toddler-entry-title">幼児食の定期便、食費はいくら？</h2>'
    '<p>1歳半〜6歳の食事を考える家庭向け。食数・送料・配送周期から、'
    '12週間の支払額と余る食数を計算できます。</p>'
    f'<a href="{PAGE_URL}" data-nav-source="toddler_meal_planner">幼児食の費用を計算する →</a>'
    '</section>'
)

PAGE_STYLE = r"""
.toddler-page{max-width:960px;margin:0 auto;padding:24px 20px 70px;color:#2a4035}
.toddler-page *{box-sizing:border-box}
.toddler-page .tm-eyebrow{font-size:13px;font-weight:800;letter-spacing:.09em;color:#557c61}
.toddler-page .tm-lead{font-size:16px;color:#53665b;line-height:1.9;max-width:760px}
.toddler-page h1{font-size:clamp(28px,5vw,40px);line-height:1.4;margin:12px 0 18px}
.toddler-page h2{font-size:clamp(20px,3.7vw,25px);line-height:1.4;margin:0 0 15px}
.toddler-page .tm-card{margin:24px 0;background:#fffefa;border:1px solid #d8e4d5;border-radius:18px;padding:clamp(17px,4vw,30px);box-shadow:0 3px 14px rgba(39,67,44,.05)}
.toddler-page .tm-card form{margin:0}
.toddler-page .tm-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 16px}
.toddler-page label{display:grid;gap:7px;font-size:14px;font-weight:750;color:#2b4435}
.toddler-page label small{font-size:12px;font-weight:400;color:#617468}
.toddler-page input,.toddler-page select{width:100%;min-height:48px;padding:11px 12px;border:1px solid #9cb69f;border-radius:9px;background:#fff;font:inherit;font-size:16px;color:#193829}
.toddler-page input:focus-visible,.toddler-page select:focus-visible,.toddler-page a:focus-visible,.toddler-page button:focus-visible{outline:3px solid #8db9a0;outline-offset:3px}
.toddler-page .tm-hint{font-size:13px;line-height:1.8;color:#52695b}
.toddler-page button{width:100%;margin:20px 0 0;min-height:48px;background:#2b6648;border:0;border-radius:10px;color:#fff;font-weight:800;font-size:16px;cursor:pointer}
.toddler-page button:hover{background:#204b36}
.toddler-page [hidden]{display:none!important}
.toddler-page .tm-results{margin-top:26px;padding-top:24px;border-top:1px solid #d8e4d5}
.toddler-page .tm-metrics{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.toddler-page .tm-metric{padding:17px;border-radius:12px;background:#f4f8f1;border:1px solid #d5e5d1}
.toddler-page .tm-metric span{display:block;font-size:12px;line-height:1.6}
.toddler-page .tm-metric strong{display:block;font-size:clamp(20px,3.5vw,29px);margin-top:5px}
.toddler-page .tm-result-copy{padding:13px 15px;border-radius:11px;background:#f5f0e3;margin-top:15px}
.toddler-page .tm-result-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:15px 0}
.toddler-page .tm-result-grid dt{font-size:12px;color:#607065}
.toddler-page .tm-result-grid dd{margin:2px 0 0;font-weight:750}
.toddler-page .tm-ad{background:#f1f6f0;border:2px solid #bcd4bd}
.toddler-page .tm-ad-label{margin:0 0 10px;color:#536554;font-size:12px;font-weight:800}
.toddler-page .tm-ad-creative a{display:block;max-width:540px;background:#306b4c;color:#fff;text-align:center;min-height:48px;padding:13px 17px;border-radius:11px;text-decoration:none;font-size:16px;font-weight:800}
.toddler-page .tm-ad-creative a:hover{background:#244f39}
.toddler-page ul{padding-left:23px}.toddler-page li{margin:10px 0}
.toddler-page .tm-footnote{font-size:12px;color:#617067;line-height:1.8}
.toddler-entry{margin:24px auto;padding:26px;border:1px solid #c9decf;border-radius:18px;max-width:980px;background:#f2f8ee}
.toddler-entry h2{margin:7px 0}.toddler-entry p{line-height:1.8}
.toddler-entry a{display:inline-block;margin-top:10px;background:#2b6648;color:#fff;padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:800}
@media(max-width:640px){.toddler-page{padding:18px 14px 48px}.toddler-page .tm-grid,.toddler-page .tm-metrics{grid-template-columns:1fr}.toddler-page .tm-card{padding:17px}.toddler-entry{margin:20px 12px;padding:20px}}
"""


def validate_official_creative(page: str) -> None:
    """Reject an incomplete/duplicated A8 link or missing ad disclosure."""
    if page.count(AD_CREATIVE) != 1:
        raise ValueError("Official A8 creative has been modified or duplicated")
    if page.count('href="https://px.a8.net/svt/ejp?a8mat=4BGCF1+9W19AY+5CLW+5YJRM" rel="nofollow"') != 1:
        raise ValueError("A8 click destination was modified")
    if page.count('src="https://www16.a8.net/0.gif?a8mat=4BGCF1+9W19AY+5CLW+5YJRM"') != 1:
        raise ValueError("A8 impression pixel was modified")
    if '広告｜A8.netアフィリエイト' not in page:
        raise ValueError("Sponsored content needs a visible disclosure")


def render_toddler_meal_guide() -> str:
    """Static guide with user-entered prices; delivery quantity is discrete."""
    body = r'''
<article class="toddler-page" data-toddler-meal-planner>
<p class="tm-eyebrow">KIDS MEAL · COST PLANNER</p>
<h1>幼児食の定期便はいくら？ 食数・送料・配送周期から12週間の費用を比較</h1>
<p class="tm-lead">「1食あたりの価格」だけでは、実際に毎回いくら支払うか分かりません。
冷凍幼児食の食数・1回の注文額・送料・配送周期を入力すると、12週間の購入量と支払総額、
使う予定の食数に対する余剰・不足を確認できます。</p>
<p class="tm-hint">対象は幼児食を検討する家庭です。モグモの公式案内では、対象年齢は1歳半〜6歳です。
乳児用ミルクや離乳初期食の代替として扱うページではありません。</p>

<section class="tm-card" aria-labelledby="tm-input-title">
<h2 id="tm-input-title">わが家の条件を入力する</h2>
<form id="tm-form" novalidate>
<div class="tm-grid">
<label>1週間で使う幼児食の食数
<input id="tm-weekly" type="number" inputmode="numeric" min="1" max="84" step="1" required placeholder="例：4">
<small>夕食・昼食など、実際に置き換えたい回数だけ</small></label>
<label>1回の配送で届く食数
<input id="tm-bundle" type="number" inputmode="numeric" min="1" max="200" step="1" required placeholder="例：12"></label>
<label>1回の配送の商品代金（税込・円）
<input id="tm-price" type="number" inputmode="numeric" min="0" max="10000000" step="1" required placeholder="注文画面の金額を入力"></label>
<label>1回の送料（税込・円）
<input id="tm-shipping" type="number" inputmode="numeric" min="0" max="1000000" step="1" required placeholder="地域・食数別の送料を入力"></label>
<label>配送周期
<select id="tm-interval" required>
<option value="2">2週間ごと</option>
<option value="3" selected>3週間ごと</option>
<option value="4">4週間ごと</option>
</select>
<small>契約プランに対応する周期を選択してください</small></label>
</div>
<button type="submit">12週間の支払総額を計算する</button>
<p id="tm-status" role="status" aria-live="polite" class="tm-hint">価格・食数は公式注文画面で確認して入力してください。入力内容は端末内で計算します。</p>
</form>
<div class="tm-results" id="tm-results" hidden aria-live="polite">
<h2>計算結果（12週間）</h2>
<div class="tm-metrics">
<div class="tm-metric"><span>12週間で支払う商品代金＋送料</span><strong id="tm-total"></strong></div>
<div class="tm-metric"><span>4週間あたりの平均支払額</span><strong id="tm-average"></strong></div>
</div>
<dl class="tm-result-grid">
<div><dt>期間内の配送回数</dt><dd id="tm-deliveries"></dd></div>
<div><dt>1食あたりの購入額（送料配分込み）</dt><dd id="tm-unit"></dd></div>
<div><dt>12週間に購入する総食数</dt><dd id="tm-purchased"></dd></div>
<div><dt>12週間で使う予定の食数</dt><dd id="tm-needed"></dd></div>
</dl>
<p class="tm-result-copy" id="tm-balance"></p>
<p class="tm-footnote">配送を初週から開始し、12週の開始時点までに届く便を数える簡易モデルです。
実際の契約開始日・スキップ・変更締め切り・お届け回数条件・保管期限は反映していません。
4週間平均は12週間の合計を3で割った額であり、月ごとの請求額ではありません。</p>
</div>
</section>

<section class="tm-card" aria-labelledby="tm-check-title">
<h2 id="tm-check-title">申し込む前に確認したいこと</h2>
<ul>
<li><b>送料：</b>配送先・食数によって変わる場合があるため、注文確定前の税込額を入力してください。</li>
<li><b>配送周期と在庫：</b>2・3・4週間ごとの配送を選ぶ前に、冷凍庫の空きと使う食数を確認してください。</li>
<li><b>定期便の変更・解約：</b>一部のコースには受取回数の条件があります。最新の契約条件・変更締め切りを必ず確認してください。</li>
<li><b>食事の適合：</b>年齢、アレルギー原材料、調理方法、必要な食事全体のバランスを製品ごとに確認してください。治療食の代替や個別の栄養指導は扱いません。</li>
</ul>
<p class="tm-footnote">参照：<a href="https://mogumo.jp/" rel="noopener">モグモ公式サイト</a>、
<a href="https://mogumo.jp/shop/customer_term" rel="noopener">公式定期便利用規約</a>。
当ページの価格計算は特定のプランの現行料金を保証するものではありません。</p>
</section>

<section class="tm-card tm-ad" aria-labelledby="tm-ad-title" id="tm-mogumo-ad">
<p class="tm-ad-label">広告｜A8.netアフィリエイト</p>
<h2 id="tm-ad-title">モグモの最新プランを確認する</h2>
<p>冷凍幼児食「モグモ」の案内ページを確認できます。食数・商品価格・送料・配送周期を確認し、
上の計算機に入力してから比較してください。</p>
<div class="tm-ad-creative">__OFFICIAL_A8_MOGUMO__</div>
<p class="tm-footnote">広告リンクを経由して購入した場合、当サイトに報酬が発生することがあります。
広告は計算式や結果に影響しません。初回限定条件・対象者・継続条件は販売ページで確認してください。</p>
</section>
<p><a href="__SITE_ROOT__">← ベビーコスパ比較トップに戻る</a></p>
</article>
'''
    if body.count('__OFFICIAL_A8_MOGUMO__') != 1:
        raise ValueError("A8 placeholder broken")
    body = body.replace('__OFFICIAL_A8_MOGUMO__', AD_CREATIVE).replace('__SITE_ROOT__', SITE_URL)
    title = '冷凍幼児食の月額費用はいくら？食数・送料・配送周期から計算 | ベビーコスパ比較'
    desc = '幼児食の定期便は月にいくら？食数・商品代金・送料・配送周期から12週間の支払額、4週間平均、1食あたりと余剰・不足食数を計算。モグモなどの検討に。'
    html = shell(title, desc, body, PAGE_URL)
    if html.count('</head>') != 1 or html.count('</body>') != 1:
        raise ValueError("Unexpected HTML shell")
    html = html.replace('</head>', '<style>' + PAGE_STYLE + '</style></head>', 1)
    js_url = SITE_URL + 'static/meal-guide.js?v=' + static_version('meal-guide.js')
    html = html.replace('</body>', f'<script src="{js_url}" defer></script></body>', 1)
    validate_official_creative(html)
    return html
