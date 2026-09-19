from __future__ import annotations
import html, json
from pathlib import Path
from .config import GA_MEASUREMENT_ID, SITE_ID, SITE_NAME, SITE_URL

METRIC={'per_piece':'1枚','per_100g':'100g'}
SIZE={'newborn':'新生児','s':'S','m':'M','l':'L','big':'BIG','big_plus':'BIGより大きい'}
TYPE={'tape':'テープ','pants':'パンツ'}

def esc(v): return html.escape(str(v or ''))
def yen(v): return f'¥{float(v):.1f}' if float(v)<100 else f'¥{float(v):,.0f}'
def segment_url(category, segment):
    if category['parser']=='diapers': return f"{SITE_URL}diapers/{segment['type']}/{segment['size']}/"
    return f"{SITE_URL}{category['path']}/"

def analytics_head():
    if not GA_MEASUREMENT_ID: return ''
    gid=esc(GA_MEASUREMENT_ID)
    return f'''<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}};window.gtag=gtag;window.BABY_COST={{root:'/baby-cost-jp/',siteId:'{SITE_ID}'}};(function(){{let o=false;try{{o=localStorage.getItem('baby_cost_operator_test_v1')==='1'}}catch(_ ){{}}const p=new URLSearchParams(location.search);if(p.get('test')==='1'||p.get('test')==='0'){{o=p.get('test')==='1';try{{o?localStorage.setItem('baby_cost_operator_test_v1','1'):localStorage.removeItem('baby_cost_operator_test_v1')}}catch(_ ){{}}const u=new URL(location.href);u.searchParams.delete('test');history.replaceState(history.state,'',u.href)}}window.BABY_COST_OPERATOR_TEST=o;gtag('js',new Date());gtag('config','{gid}',{{site_id:'{SITE_ID}',operator_test:o?'1':undefined}})}})();</script><script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>'''

def shell(title, desc, body, canonical, noindex=False):
    robots='noindex,follow' if noindex else 'index,follow'
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="{robots}"><link rel="canonical" href="{esc(canonical)}"><link rel="stylesheet" href="{SITE_URL}static/styles.css">{analytics_head()}</head><body><header class="top"><a class="brand" href="{SITE_URL}">{SITE_NAME}</a><a href="{SITE_URL}method/">比較方法</a></header><main>{body}</main><footer>価格・枚数等は取得時点の情報です。購入前に販売ページで最新情報をご確認ください。</footer><script src="{SITE_URL}static/analytics.js"></script><script src="{SITE_URL}static/app.js"></script></body></html>'''

def selector(categories, current_type='', current_size=''):
    segs=[]
    for s in categories['diapers']['segments']:
        segs.append({'type':s['type'],'size':s['size'],'url':segment_url(categories['diapers'],s)})
    opts=''.join(f'<option value="{x}">{TYPE[x]}</option>' for x in ('pants','tape'))
    return f'''<section class="selector" id="diaper-selector" data-segments='{esc(json.dumps(segs,ensure_ascii=False))}' data-current-type="{esc(current_type)}" data-current-size="{esc(current_size)}"><h2>おむつの条件を選ぶ</h2><div class="selector-grid"><label>タイプ<select id="diaper-type">{opts}</select></label><label>サイズ<select id="diaper-size"></select></label><button id="diaper-go">この条件で比較</button></div></section>'''

def render_home(categories, snapshots, updated_at):
    cards=[]
    info=[('diapers','紙おむつ','サイズ・タイプ別 / 1枚'),('wipes','おしりふき','1枚'),('formula','粉ミルク','100g'),('diaper_bags','おむつ用防臭袋','1枚')]
    for cid,name,metric in info:
        href=f'{SITE_URL}{categories[cid]["path"]}/'
        cards.append(f'<a class="cat" data-nav-source="home_category" data-category-id="{cid}" href="{href}"><strong>{name}</strong><span>{metric}あたりで比較</span></a>')
    body=f'''<section class="hero"><p class="eyebrow">ベビー用品の「結局どれが安い？」をすぐ確認</p><h1>枚数・容量をそろえて<br>単価で比較</h1><p>セット数が違う商品も、1枚・100gなど同じ単位に換算。比較結果を先に表示します。</p></section>{selector(categories)}<section><h2>比較する商品</h2><div class="cats">{''.join(cards)}</div></section><p class="updated">最終更新 {updated_at:%Y-%m-%d %H:%M} JST</p>'''
    return shell('ベビー用品コスパ比較 | 1枚・100g単価で比較','紙おむつ、おしりふき、粉ミルクなどを単価換算して比較します。',body,SITE_URL)

def render_diaper_index(categories, updated_at):
    rows=[]
    for s in categories['diapers']['segments']:
        rows.append(f'<a class="choice" data-nav-source="diaper_index" data-category-id="diapers" href="{segment_url(categories["diapers"],s)}"><b>{TYPE[s["type"]]}・{SIZE[s["size"]]}</b><span>1枚あたりを見る</span></a>')
    body=f'''<section class="page-head"><a href="{SITE_URL}">← トップ</a><h1>紙おむつを1枚あたりで比較</h1><p>タイプとサイズをそろえて比較します。</p></section>{selector(categories)}<div class="choices">{''.join(rows)}</div>'''
    return shell('紙おむつ 1枚あたり価格比較','テープ・パンツ、サイズ別に紙おむつの1枚あたり価格を比較。',body,f'{SITE_URL}diapers/')

def product_card(p, rank, category_id, segment):
    q=p['quantity']; total=q['total']; unit='g' if q['base_unit']=='g' else '枚'; total_txt=f'{total:g}{unit}'
    packs=q.get('pack_count',1); pack=f' / {packs}パック相当' if packs>1 else ''
    stage=p.get('attributes',{}).get('fit_stage',''); stage_html=f'<span class="tag">{esc(stage)}</span>' if stage else ''
    attrs=f'''data-affiliate="rakuten" data-category-id="{esc(category_id)}" data-product-name="{esc(p['name'])}" data-product-id="{esc(p.get('source_id'))}" data-size="{esc(segment.get('size',''))}" data-product-type="{esc(segment.get('type',''))}" data-unit-metric="{esc(p['unit_metric'])}" data-unit-price="{p['unit_price']:.4f}" data-rank="{rank}" data-click-position="comparison_card"'''
    return f'''<article class="product"><div class="rank">{rank}</div><div class="product-main"><div class="maker">{esc(p.get('brand') or p.get('manufacturer'))} {stage_html}</div><h3>{esc(p['name'])}</h3><div class="unit"><b>{yen(p['unit_price'])}</b><span> / {METRIC[p['unit_metric']]}</span></div><div class="facts"><span>合計 {total_txt}{pack}</span><span>販売価格 ¥{p['price_yen']:,}</span></div><details><summary>単価の計算を見る</summary><p>¥{p['price_yen']:,} ÷ {total_txt}{' × 100' if p['unit_metric']=='per_100g' else ''} = {yen(p['unit_price'])} / {METRIC[p['unit_metric']]}</p><small>数量根拠: {esc(q.get('evidence'))}</small></details><a class="cta" href="{esc(p.get('url'))}" target="_blank" rel="nofollow sponsored noopener" {attrs}>楽天で価格を見る</a></div></article>'''

def render_comparison(categories, category_id, category, segment, products, updated_at):
    label=segment['label']; metric=METRIC[category['metric']]; noindex=len(products)<2
    if products:
        best=products[0]
        answer=f'''<section class="answer"><span>取得対象内の最安単価</span><strong>{yen(best['unit_price'])}<small> / {metric}</small></strong><p>{esc(best['name'])}</p></section><h2 class="result-title">単価が安い順</h2>'''
        cards=''.join(product_card(p,i+1,category_id,segment) for i,p in enumerate(products))
    else:
        answer='<section class="answer empty"><strong>比較できる商品が不足しています</strong><p>数量と条件を安全に確認できた商品だけを表示しています。</p></section>'
        cards=''
    selector_html=selector(categories,segment.get('type',''),segment.get('size','')) if category_id=='diapers' else ''
    body=f'''<section class="page-head"><a href="{SITE_URL}">← トップ</a><h1>{esc(label)} コスパ比較</h1><p>{metric}あたりの価格を同じ条件で比較します。</p></section><section class="comparison" data-comparison data-category-id="{category_id}" data-size="{esc(segment.get('size',''))}" data-product-type="{esc(segment.get('type',''))}" data-result-count="{len(products)}">{answer}<div class="products">{cards}</div></section>{selector_html}<section class="method-note"><h2>順位の計算</h2><p>楽天APIで送料込み／送料無料条件に絞って取得した商品のうち、数量と条件を確認できた商品を単価換算して並べています。ポイント・クーポンは順位に含めません。</p><a href="{SITE_URL}method/">詳しい比較方法</a></section><p class="updated">更新 {updated_at:%Y-%m-%d %H:%M} JST</p>'''
    title=f'{label} 1{ "枚" if category["metric"]=="per_piece" else "00g"}あたり価格比較'
    return shell(title,f'{label}を{metric}あたりに換算して価格比較。',body,segment_url(category,segment),noindex)

def render_method():
    body=f'''<section class="page-head"><a href="{SITE_URL}">← トップ</a><h1>比較方法</h1></section><section class="prose"><h2>単価をそろえる</h2><p>紙おむつ・おしりふき・防臭袋は1枚、粉ミルクは100gあたりで計算します。</p><h2>条件違いを混ぜない</h2><p>紙おむつはタイプとサイズを一致させ、数量を安全に解析できない商品は比較対象から外します。</p><h2>価格以外を断定しない</h2><p>肌との相性、品質、健康効果などをサイト側で根拠なく順位付けしません。</p></section>'''
    return shell('比較方法 | ベビー用品コスパ比較','単価計算と比較対象の選び方。',body,f'{SITE_URL}method/')

def write_page(path: Path, content: str):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content,encoding='utf-8')
