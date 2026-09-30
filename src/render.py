from __future__ import annotations
import html, json, re
from pathlib import Path
from .config import GA_MEASUREMENT_ID, SITE_ID, SITE_NAME, SITE_URL

METRIC={'per_piece':'1枚','per_100g':'100g'}
SIZE={'newborn':'新生児','s':'S','m':'M','l':'L','big':'BIG','big_plus':'BIGより大きい'}
TYPE={'tape':'テープ','pants':'パンツ'}

def icon_svg(name: str, cls: str=''):
    common=f'class="icon {esc(cls)}" viewBox="0 0 96 96" aria-hidden="true"'
    icons={
        'diapers': f'''<svg {common}><path d="M20 30c7 7 15 10 28 10s21-3 28-10v29c0 10-8 18-18 18H38c-10 0-18-8-18-18V30Z" fill="currentColor" opacity=".16"/><path d="M22 29c8 8 16 11 26 11s18-3 26-11M20 48c9 5 18 7 28 7s19-2 28-7M34 55c0 9 5 17 14 22m14-22c0 9-5 17-14 22" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
        'wipes': f'''<svg {common}><rect x="18" y="30" width="60" height="42" rx="12" fill="currentColor" opacity=".16"/><path d="M27 40h42M30 58h36" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/><path d="M39 30c1-10 17-10 18 0" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/></svg>''',
        'formula': f'''<svg {common}><path d="M31 22h34l5 12v42H26V34l5-12Z" fill="currentColor" opacity=".16"/><path d="M31 22h34l5 12v42H26V34l5-12Zm-3 17h40M36 55h24" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
        'diaper_bags': f'''<svg {common}><path d="M30 31h36l5 46H25l5-46Z" fill="currentColor" opacity=".16"/><path d="M30 31h36l5 46H25l5-46Zm9 0c0-10 18-10 18 0" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
        'price': f'''<svg {common}><path d="M24 23h30l19 19-31 31-19-19V23Z" fill="currentColor" opacity=".16"/><path d="M24 23h30l19 19-31 31-19-19V23Zm12 13h.1M49 38c-8 0-8 10 0 10s8 10 0 10m0-24v28" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
        'check': f'''<svg {common}><circle cx="48" cy="48" r="30" fill="currentColor" opacity=".14"/><path d="m34 48 9 9 20-22" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
        'chick': f'''<svg {common}><circle cx="48" cy="51" r="27" fill="currentColor" opacity=".18"/><path d="M27 52c0-15 9-28 21-28s21 13 21 28c0 15-9 25-21 25S27 67 27 52Z" fill="currentColor" opacity=".25"/><circle cx="40" cy="48" r="3.5" fill="currentColor"/><circle cx="56" cy="48" r="3.5" fill="currentColor"/><path d="M43 58h10l-5 5-5-5Z" fill="currentColor"/><path d="M30 55c-7 1-10 5-11 10m47-10c7 1 10 5 11 10M42 23l6-8 6 8" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
    }
    return icons.get(name, icons['price'])

def hero_visual():
    return f'''<div class="hero-art" aria-label="ベビー用品を同じ単位で比較するイメージ">
      <div class="hero-blob hero-blob-a"></div><div class="hero-blob hero-blob-b"></div>
      <div class="hero-art-card hero-art-main"><div class="hero-art-icon hero-art-diaper">{icon_svg('diapers')}</div><div><small>紙おむつ</small><strong>¥21.4<em>/枚</em></strong></div></div>
      <div class="hero-art-card hero-art-wipes"><div class="hero-art-icon">{icon_svg('wipes')}</div><span>おしりふき</span></div>
      <div class="hero-art-card hero-art-formula"><div class="hero-art-icon">{icon_svg('formula')}</div><span>粉ミルク</span></div>
      <div class="hero-art-tag">{icon_svg('price')}<b>単価で比較</b></div>
      <div class="hero-mascot">{icon_svg('chick')}<span>くらべる！</span></div>
      <div class="hero-spark s1">✦</div><div class="hero-spark s2">●</div><div class="hero-spark s3">✦</div>
    </div>'''

def esc(v): return html.escape(str(v or ''))
def yen(v): return f'¥{float(v):.1f}' if float(v)<100 else f'¥{float(v):,.0f}'
def segment_url(category, segment):
    if category['parser']=='diapers': return f"{SITE_URL}diapers/{segment['type']}/{segment['size']}/"
    return f"{SITE_URL}{category['path']}/"

def display_product_name(name: str) -> str:
    """Remove obvious campaign noise for display without changing product identity/data."""
    text=str(name or '').strip()
    prefix_patterns=[
        r'^\s*[【\[][^】\]]*(?:ポイント|クーポン|エントリー|最安値|激アツ|本日|サンプルCP)[^】\]]*[】\]]\s*',
        r'^\s*＼[^／]*(?:ポイント|クーポン|エントリー|最安値|激アツ|本日|サンプルCP)[^／]*／\s*',
    ]
    changed=True
    while changed:
        changed=False
        for pattern in prefix_patterns:
            new=re.sub(pattern,'',text,flags=re.I)
            if new!=text:
                text=new.strip(); changed=True
    text=re.sub(r'\s*[【\[](?:D|iris_[^】\]]+|smtb-s|△)[】\]]\s*$', '', text, flags=re.I).strip()
    return re.sub(r'\s+',' ',text) or str(name or '').strip()


def how_visual():
    return f'''<section class="how-visual"><div class="how-intro"><div class="how-mascot">{icon_svg('chick')}</div><div><div class="section-kicker">HOW TO USE</div><h2>3ステップで、すぐ比較</h2><p>欲しいものを選んだら、あとは単価順に見るだけ。</p></div></div><div class="how-steps"><div class="how-step"><span>01</span><div class="how-step-icon">{icon_svg('diapers')}</div><b>条件を選ぶ</b><small>サイズやカテゴリを選択</small></div><div class="how-arrow">→</div><div class="how-step"><span>02</span><div class="how-step-icon">{icon_svg('price')}</div><b>単価で比べる</b><small>1枚・100gで同条件化</small></div><div class="how-arrow">→</div><div class="how-step"><span>03</span><div class="how-step-icon">{icon_svg('check')}</div><b>楽天で確認</b><small>価格・在庫を最終チェック</small></div></div></section>'''

def analytics_head():
    if not GA_MEASUREMENT_ID: return ''
    gid=esc(GA_MEASUREMENT_ID)
    return f'''<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}};window.gtag=gtag;window.BABY_COST={{root:'/baby-cost-jp/',siteId:'{SITE_ID}'}};(function(){{let o=false;try{{o=localStorage.getItem('baby_cost_operator_test_v1')==='1'}}catch(_ ){{}}const p=new URLSearchParams(location.search);if(p.get('test')==='1'||p.get('test')==='0'){{o=p.get('test')==='1';try{{o?localStorage.setItem('baby_cost_operator_test_v1','1'):localStorage.removeItem('baby_cost_operator_test_v1')}}catch(_ ){{}}const u=new URL(location.href);u.searchParams.delete('test');history.replaceState(history.state,'',u.href)}}window.BABY_COST_OPERATOR_TEST=o;gtag('js',new Date());gtag('config','{gid}',{{site_id:'{SITE_ID}',operator_test:o?'1':undefined}})}})();</script><script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>'''

def shell(title, desc, body, canonical, noindex=False):
    robots='noindex,follow' if noindex else 'index,follow'
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="{robots}"><link rel="canonical" href="{esc(canonical)}"><link rel="stylesheet" href="{SITE_URL}static/styles.css">{analytics_head()}</head><body><header class="top"><a class="brand" href="{SITE_URL}"><span class="brand-mark">{icon_svg('chick')}</span><span>{SITE_NAME}</span></a><a href="{SITE_URL}method/">比較方法</a></header><main>{body}</main><footer><div class="footer-brand"><span>{icon_svg('chick')}</span><b>{SITE_NAME}</b></div><p>価格・枚数等は取得時点の情報です。購入前に販売ページで最新情報をご確認ください。</p></footer><script src="{SITE_URL}static/analytics.js"></script><script src="{SITE_URL}static/app.js"></script></body></html>'''

def trust_strip():
    return f'''<div class="trust-strip" aria-label="比較方針"><span>{icon_svg('check')}送料込み対象</span><span>{icon_svg('check')}選択式商品は除外</span><span>{icon_svg('check')}単価を自動計算</span><span>{icon_svg('check')}毎日更新</span></div>'''

def selector(categories, current_type='', current_size=''):
    segs=[]
    for s in categories['diapers']['segments']:
        segs.append({'type':s['type'],'size':s['size'],'url':segment_url(categories['diapers'],s)})
    return f'''<section class="selector visual-selector" id="diaper-selector" data-segments='{esc(json.dumps(segs,ensure_ascii=False))}' data-current-type="{esc(current_type)}" data-current-size="{esc(current_size)}">
      <div class="selector-heading"><div class="selector-illustration">{icon_svg('diapers')}</div><div><div class="section-kicker">DIAPER FINDER</div><h2>ぴったりの条件から探す</h2><p class="section-lead">タイプとサイズをタップするだけ。</p></div></div>
      <div class="filter-label">タイプ</div><div class="type-chips" role="group" aria-label="おむつタイプ"><button type="button" class="filter-chip type-chip" data-value="pants">パンツ</button><button type="button" class="filter-chip type-chip" data-value="tape">テープ</button></div>
      <div class="filter-label">サイズ</div><div class="size-chips" role="group" aria-label="おむつサイズ"></div>
      <button id="diaper-go" class="selector-go">この条件の最安を見る <span>→</span></button>
    </section>'''
def _home_price(snapshot, metric):
    if not snapshot: return ''
    p=snapshot[0]
    return f'<em>取得対象内 {yen(p["unit_price"])} / {METRIC[metric]}〜</em>'

def featured_deals_section(deals):
    if not deals:
        return ''
    cards=[]
    category_icon={'diapers':'diapers','wipes':'wipes','formula':'formula','diaper_bags':'diaper_bags'}
    for row in deals:
        p=row['product']
        image=f'<div class="deal-image"><img src="{esc(p.get("image"))}" alt="" loading="lazy" decoding="async"></div>' if p.get('image') else f'<div class="deal-image deal-image-fallback">{icon_svg(category_icon.get(row["category_id"],"price"))}</div>'
        cards.append(f'''<a class="deal-card deal-card--{esc(row["category_id"])}" href="{esc(row["url"])}" data-nav-source="featured_deal" data-category-id="{esc(row["category_id"])}"><div class="deal-top"><span>{esc(row["category_label"])}</span><b>中央値より {row["gap_percent"]:.0f}%低い</b></div>{image}<div class="deal-copy"><small>{esc(row["segment_label"])}</small><strong>{yen(row["unit_price"])}<em> / {METRIC[row["metric"]]}</em></strong><p>{esc(display_product_name(p["name"]))}</p><span>比較を見る →</span></div></a>''')
    return f'''<section class="featured-deals"><div class="featured-deals-head"><div><div class="section-kicker">TODAY'S PICKS</div><h2>今日の買い候補</h2><p>現在取得できる同条件商品の中で、中央値との差が大きい候補です。</p></div><div class="featured-deals-mascot">{icon_svg("chick")}</div></div><div class="deal-grid">{''.join(cards)}</div><p class="deal-disclaimer">※ 過去価格との比較ではありません。現在の比較対象内での相対的な価格差です。</p></section>'''


def render_home(categories, snapshots, deals, updated_at):
    cards=[]
    info=[
        ('diapers','紙おむつ','サイズ・タイプ別 / 1枚','サイズを選んで比較','diapers'),
        ('wipes','おしりふき','1枚あたり','枚数違いを1枚単価に','wipes'),
        ('formula','粉ミルク','100gあたり','容量違いを100g単価に','formula'),
        ('diaper_bags','おむつ用防臭袋','1枚あたり','箱・セット違いを1枚単価に','diaper_bags'),
    ]
    for cid,name,metric,desc,icon in info:
        href=f'{SITE_URL}{categories[cid]["path"]}/'
        live='' if cid=='diapers' else _home_price(snapshots.get(cid),categories[cid]['metric'])
        cards.append(f'''<a class="cat cat--{cid}" data-nav-source="home_category" data-category-id="{cid}" href="{href}"><div class="cat-icon">{icon_svg(icon)}</div><div class="cat-copy"><span class="cat-kicker">{esc(metric)}</span><strong>{esc(name)}</strong><span>{esc(desc)}</span>{live}<b>比較を見る <i>→</i></b></div></a>''')
    body=f'''<section class="hero hero-visual"><div class="hero-copy"><p class="eyebrow">BABY COST CHECK</p><h1>ベビー用品、<br><span>ちゃんと比べて</span>選ぼう。</h1><p>セット数や容量の違いをそろえて、1枚・100gなど同じ単位で比較。見かけの価格に迷わないためのシンプルな比較サイトです。</p>{trust_strip()}</div>{hero_visual()}</section>{selector(categories)}{featured_deals_section(deals)}<section class="home-section category-section"><div class="section-kicker">COMPARE</div><h2>なにを比べる？</h2><p class="section-lead">気になるカテゴリから、いちばん安い候補をすぐチェック。</p><div class="cats">{''.join(cards)}</div></section>{how_visual()}<section class="quality-card quality-visual"><div class="quality-icon">{icon_svg('check')}</div><div><div class="section-kicker">QUALITY FILTER</div><h2>「安いけど条件が違う」を入れません</h2><p>紙おむつはテープ／パンツとサイズを分離。販売ページでサイズを選ぶ商品や、数量を安全に読み取れない商品は除外します。</p></div><a href="{SITE_URL}method/">比較ルールを見る →</a></section><p class="updated">最終更新 {updated_at:%Y-%m-%d %H:%M} JST</p>'''
    return shell('ベビー用品コスパ比較 | 1枚・100g単価で比較','紙おむつ、おしりふき、粉ミルクなどを単価換算して比較します。',body,SITE_URL)
def render_diaper_index(categories, updated_at):
    rows=[]
    for s in categories['diapers']['segments']:
        rows.append(f'<a class="choice choice--{s["type"]}" data-nav-source="diaper_index" data-category-id="diapers" href="{segment_url(categories["diapers"],s)}"><div class="choice-icon">{icon_svg("diapers")}</div><span class="choice-type">{TYPE[s["type"]]}</span><b>{SIZE[s["size"]]}</b><span>1枚あたりを見る →</span></a>')
    body=f'''<section class="page-head diaper-head"><a href="{SITE_URL}">← トップ</a><div class="page-head-art">{icon_svg("diapers")}</div><div class="section-kicker">DIAPERS</div><h1>紙おむつを<br>1枚あたりで比較</h1><p>テープ／パンツとサイズをそろえた商品だけを比較します。</p>{trust_strip()}</section>{selector(categories)}<section class="home-section"><h2>すべての比較条件</h2><div class="choices">{''.join(rows)}</div></section><p class="updated">最終更新 {updated_at:%Y-%m-%d %H:%M} JST</p>'''
    return shell('紙おむつ 1枚あたり価格比較','テープ・パンツ、サイズ別に紙おむつの1枚あたり価格を比較。',body,f'{SITE_URL}diapers/')


def compare_panel():
    return '''<div class="compare-dock" data-compare-dock hidden><div class="compare-dock-copy"><span data-compare-count>0件選択</span><small>最大3商品</small></div><div class="compare-dock-actions"><button type="button" class="compare-clear" data-compare-clear>クリア</button><button type="button" class="compare-open" data-compare-open disabled>選んだ商品を比較</button></div></div><div class="compare-modal" data-compare-modal hidden><div class="compare-modal-backdrop" data-compare-close></div><section class="compare-dialog" role="dialog" aria-modal="true" aria-labelledby="compare-dialog-title"><div class="compare-dialog-head"><div><div class="section-kicker">SIDE BY SIDE</div><h2 id="compare-dialog-title">選んだ商品を比較</h2></div><button type="button" class="compare-close" data-compare-close aria-label="閉じる">×</button></div><div class="compare-table" data-compare-table></div><p class="compare-note">価格・在庫は変動します。購入前に楽天の商品ページで最新情報をご確認ください。</p></section></div>'''



def product_strength_tags(products):
    if not products:
        return {}
    best_unit=min(float(p['unit_price']) for p in products)
    best_price=min(int(p['price_yen']) for p in products)
    max_quantity=max(float(p['quantity']['total']) for p in products)
    result={}
    for p in products:
        key=p.get('source_id') or p.get('name')
        tags=[]
        if abs(float(p['unit_price'])-best_unit)<1e-9:
            tags.append(('unit','単価◎'))
        if int(p['price_yen'])==best_price:
            tags.append(('price','総額◎'))
        if abs(float(p['quantity']['total'])-max_quantity)<1e-9:
            tags.append(('quantity','大容量◎'))
        if tags:
            result[key]=tags
    return result

def product_card(p, rank, category_id, segment, best_unit_price=None, strength_tags=None):
    q=p['quantity']; total=q['total']; unit='g' if q['base_unit']=='g' else '枚'; total_txt=f'{total:g}{unit}'
    packs=q.get('pack_count',1); pack=f' / {packs}パック相当' if packs>1 else ''
    stage=p.get('attributes',{}).get('fit_stage',''); stage_html=f'<span class="tag">{esc(stage)}</span>' if stage else ''
    display=display_product_name(p['name'])
    strength_tags=strength_tags or []
    strength_html=''.join(f'<span class="strength-tag strength-tag--{kind}">{esc(label)}</span>' for kind,label in strength_tags)
    strength_row=f'<div class="strength-tags">{strength_html}</div>' if strength_html else ''
    attrs=f'''data-affiliate="rakuten" data-category-id="{esc(category_id)}" data-product-name="{esc(p['name'])}" data-product-id="{esc(p.get('source_id'))}" data-size="{esc(segment.get('size',''))}" data-product-type="{esc(segment.get('type',''))}" data-unit-metric="{esc(p['unit_metric'])}" data-unit-price="{p['unit_price']:.4f}" data-rank="{rank}" data-click-position="comparison_card"'''
    full_name=f'''<details class="full-name"><summary>商品名全文</summary><p>{esc(p['name'])}</p></details>''' if display!=p['name'] else ''
    shop=f'<span class="shop">{esc(p.get("shop"))}</span>' if p.get('shop') else ''
    gap=(p['unit_price']-best_unit_price) if best_unit_price is not None else 0
    badge='最安' if rank==1 else (f'1位より +{yen(gap)} / {METRIC[p["unit_metric"]]}' if gap>0 else f'{rank}位')
    image=f'<div class="product-image"><img src="{esc(p.get("image"))}" alt="" loading="lazy" decoding="async"></div>' if p.get('image') else ''
    return f'''<article class="product product-rank-{rank}" id="rank-{rank}" data-sort-unit="{p['unit_price']:.6f}" data-sort-price="{p['price_yen']}" data-sort-quantity="{q['total']:.6f}" data-original-rank="{rank}"><div class="rank rank-{rank}">{rank}</div><div class="product-main"><div class="product-overview">{image}<div class="product-info"><div class="maker-row"><div class="maker">{esc(p.get('brand') or p.get('manufacturer'))} {stage_html}</div>{shop}</div><h3 class="product-title" title="{esc(p['name'])}">{esc(display)}</h3>{strength_row}<div class="price-row"><div class="unit"><b>{yen(p['unit_price'])}</b><span> / {METRIC[p['unit_metric']]}</span></div><span class="rank-badge">{badge}</span></div></div></div><div class="facts"><span><small>内容量</small><b>合計 {total_txt}{pack}</b></span><span><small>販売価格</small><b>¥{p['price_yen']:,}</b></span></div>{full_name}<details><summary>単価の計算を見る</summary><p>¥{p['price_yen']:,} ÷ {total_txt}{' × 100' if p['unit_metric']=='per_100g' else ''} = {yen(p['unit_price'])} / {METRIC[p['unit_metric']]}</p><small>数量根拠: {esc(q.get('evidence'))}</small></details><div class="product-actions"><button type="button" class="compare-add" data-compare-add data-compare-id="{esc(p.get('source_id'))}" data-compare-name="{esc(display)}" data-compare-unit="{p['unit_price']:.4f}" data-compare-unit-label="{esc(METRIC[p['unit_metric']])}" data-compare-price="{p['price_yen']}" data-compare-quantity="{esc(total_txt)}" data-compare-image="{esc(p.get('image'))}" data-compare-rank="{rank}"><span>＋</span> 比較に追加</button><a class="cta" href="{esc(p.get('url'))}" target="_blank" rel="nofollow sponsored noopener" {attrs}>楽天で価格・在庫を見る</a></div></div></article>'''

def quick_compare(products):
    if not products: return ''
    cards=[]
    for i,p in enumerate(products[:3],1):
        q=p['quantity']; total=f'{q["total"]:g}{"g" if q["base_unit"]=="g" else "枚"}'
        image=f'<div class="quick-image"><img src="{esc(p.get("image"))}" alt="" loading="lazy" decoding="async"></div>' if p.get('image') else f'<div class="quick-image quick-image-fallback">{icon_svg("price")}</div>'
        medal='🥇' if i==1 else ('🥈' if i==2 else '🥉')
        cards.append(f'''<a class="quick-item quick-rank-{i}" href="#rank-{i}"><div class="quick-top"><span class="quick-medal">{medal}</span><span>{i}位</span></div>{image}<strong>{yen(p["unit_price"])}<small> / {METRIC[p["unit_metric"]]}</small></strong><p>{esc(display_product_name(p["name"]))}</p><em>{total}・¥{p["price_yen"]:,}</em></a>''')
    return f'''<section class="quick-compare"><div class="quick-head"><div><div class="section-kicker">QUICK VIEW</div><h2>上位を早見</h2></div><span>タップで商品詳細へ</span></div><div class="quick-grid">{''.join(cards)}</div></section>'''



def price_snapshot(products, metric: str):
    if len(products)<2:
        return ''
    values=sorted(float(p['unit_price']) for p in products)
    n=len(values)
    median=values[n//2] if n%2 else (values[n//2-1]+values[n//2])/2
    low=values[0]; high=values[-1]
    saving=max(0.0, median-low)
    pct=(saving/median*100) if median>0 else 0
    note=f'最安は中央値より {pct:.0f}% 低い' if pct>=1 else '最安と中央値はほぼ同水準'
    return f'''<section class="price-snapshot"><div class="price-snapshot-head"><div><div class="section-kicker">PRICE SNAPSHOT</div><h2>いまの価格感</h2></div><span>{esc(note)}</span></div><div class="price-band"><div class="price-point"><small>最安</small><strong>{yen(low)}</strong><em>/ {metric}</em></div><div class="price-line"><i></i><b></b><i></i></div><div class="price-point price-point-mid"><small>中央値</small><strong>{yen(median)}</strong><em>/ {metric}</em></div><div class="price-point"><small>高値側</small><strong>{yen(high)}</strong><em>/ {metric}</em></div></div><p>このページで現在比較できる {len(products)} 商品の単価から算出しています。過去価格との比較ではありません。</p></section>'''

def diaper_savings_simulator(products):
    if len(products)<2:
        return ''
    values=sorted(float(p['unit_price']) for p in products)
    n=len(values)
    median=values[n//2] if n%2 else (values[n//2-1]+values[n//2])/2
    best=values[0]
    diff=max(0.0,median-best)
    return f'''<section class="savings-sim" data-savings-sim data-best="{best:.4f}" data-median="{median:.4f}"><div class="savings-mascot">{icon_svg('chick')}</div><div class="savings-copy"><div class="section-kicker">SAVINGS SIMULATOR</div><h2>1か月でどれくらい変わる？</h2><p>最安単価と、このページの中央値を比べます。</p><div class="usage-chips" role="group" aria-label="1日の使用枚数"><button type="button" data-usage="4">4枚/日</button><button type="button" data-usage="5" class="is-active">5枚/日</button><button type="button" data-usage="6">6枚/日</button><button type="button" data-usage="8">8枚/日</button></div><div class="savings-result"><span>30日なら</span><strong data-savings-result>{yen(diff*5*30)}</strong><b>くらい差</b></div><small>※ 使用枚数は例です。実際の使用量に合わせて切り替えてください。</small></div></section>'''


def comparison_head_visual(category_id: str):
    icon='diapers' if category_id=='diapers' else category_id
    label={'diapers':'紙おむつ','wipes':'おしりふき','formula':'粉ミルク','diaper_bags':'防臭袋'}.get(category_id,'価格比較')
    return f'''<div class="comparison-head-art comparison-head-art--{category_id}"><div class="comparison-head-icon">{icon_svg(icon)}</div><span>{esc(label)}</span><i>PRICE CHECK</i></div>'''

def buying_guide():
    return f'''<section class="buying-guide" data-buying-guide><div class="buying-guide-head"><div class="buying-guide-mascot">{icon_svg("chick")}</div><div><div class="section-kicker">QUICK GUIDE</div><h2>どれを選ぶか迷ったら</h2><p>いちばん近い買い方を選んでください。</p></div></div><div class="buying-goals"><button type="button" data-buy-goal="unit"><span>💰</span><b>単価をとにかく重視</b><small>1枚・100gあたりを抑えたい</small></button><button type="button" data-buy-goal="price"><span>🧾</span><b>最初の支払いを抑えたい</b><small>レジで払う総額を小さくしたい</small></button><button type="button" data-buy-goal="quantity"><span>📦</span><b>まとめ買いしたい</b><small>一度に多く確保したい</small></button></div><div class="buying-guide-result" data-buy-guide-result hidden><strong></strong><span></span></div></section>'''


def comparison_mascot_tip(category_id: str, count: int):
    if category_id=='diapers':
        text='サイズとタイプが確認できた商品だけを比べているよ'
    elif category_id=='formula':
        text='価格だけを比較。栄養や相性は順位に入れていないよ'
    else:
        text='数量を確認できた商品だけを同じ単位で比べているよ'
    return f'''<div class="result-mascot-tip"><div class="result-mascot">{icon_svg('chick')}</div><div><b>{count}商品を比較中</b><span>{esc(text)}</span></div></div>'''


def render_comparison(categories, category_id, category, segment, products, updated_at):
    label=segment['label']; metric=METRIC[category['metric']]; noindex=len(products)<2
    if products:
        best=products[0]
        delta=''
        if len(products)>1:
            gap=products[1]['unit_price']-best['unit_price']
            delta=f'<span class="delta">2位と同単価</span>' if abs(gap)<0.0001 else f'<span class="delta">2位より {yen(gap)} / {metric} 安い</span>'
        answer=f'''<section class="answer"><div class="answer-medal">★</div><div class="answer-content"><div class="answer-label"><span>取得対象内の最安単価</span>{delta}</div><strong>{yen(best['unit_price'])}<small> / {metric}</small></strong><p>{esc(display_product_name(best['name']))}</p></div></section>'''
        strengths=product_strength_tags(products)
        cards=''.join(product_card(p,i+1,category_id,segment,best['unit_price'],strengths.get(p.get('source_id') or p.get('name'),[])) for i,p in enumerate(products))
    else:
        answer='<section class="answer empty"><strong>比較できる商品が不足しています</strong><p>数量と条件を安全に確認できた商品だけを表示しています。</p></section>'
        cards=''
    selector_html=selector(categories,segment.get('type',''),segment.get('size','')) if category_id=='diapers' else ''
    if category_id=='diapers':
        back=f'<a href="{SITE_URL}diapers/">← 紙おむつの条件一覧</a>'
        meta=f'''<div class="compare-meta"><span>{TYPE[segment["type"]]}</span><span>{SIZE[segment["size"]]}</span><span>{len(products)}商品を比較</span></div>'''
    else:
        back=f'<a href="{SITE_URL}">← トップ</a>'
        meta=f'''<div class="compare-meta"><span>{len(products)}商品を比較</span><span>{metric}単価</span></div>'''
    health_note=''
    if category_id=='formula':
        health_note='<p class="neutral-note">※ 粉ミルクは価格だけを比較しています。栄養・体質との相性などは順位付けしていません。</p>'
    head_visual=comparison_head_visual(category_id)
    mascot_tip=comparison_mascot_tip(category_id,len(products))
    snapshot=price_snapshot(products,metric)
    savings=diaper_savings_simulator(products) if category_id=='diapers' else ''
    body=f'''<section class="page-head comparison-page-head comparison-page-head--{category_id}">{back}{head_visual}<div class="section-kicker">PRICE COMPARISON</div><h1>{esc(label)}<br><span>コスパ比較</span></h1><p>{metric}あたりの価格を、同じ条件にそろえて比較します。</p>{meta}</section>{mascot_tip}<section class="comparison" data-comparison data-category-id="{category_id}" data-size="{esc(segment.get('size',''))}" data-product-type="{esc(segment.get('type',''))}" data-result-count="{len(products)}">{answer}{snapshot}{savings}{quick_compare(products)}{buying_guide()}<section class="view-switcher" data-view-switcher><div><div class="section-kicker">VIEW</div><h2>比べ方を切り替える</h2><p>同じ掲載商品を、目的に合わせて並べ替えます。</p></div><div class="view-buttons" role="group" aria-label="商品の並べ替え"><button type="button" class="is-active" data-sort-mode="unit">単価が安い</button><button type="button" data-sort-mode="price">支払総額が安い</button><button type="button" data-sort-mode="quantity">大容量</button></div></section><h2 class="result-title"><span>ランキング</span> <b data-result-sort-label>単価が安い順</b></h2><div class="products" data-sortable-products>{cards}</div>{compare_panel()}</section>{health_note}{selector_html}<section class="method-note method-note-visual"><div class="method-note-icon">{icon_svg("check")}</div><div><div class="section-kicker">HOW IT WORKS</div><h2>この順位に入る条件</h2><p>楽天APIで送料込み／送料無料条件に絞り、数量と条件を確認できた商品だけを単価換算しています。紙おむつはサイズ選択式やタイプ不明の商品を除外。ポイント・クーポンは順位に含めません。</p><a href="{SITE_URL}method/">詳しい比較方法を見る →</a></div></section><p class="updated">更新 {updated_at:%Y-%m-%d %H:%M} JST</p>'''
    title=f'{label} 1{ "枚" if category["metric"]=="per_piece" else "00g"}あたり価格比較'
    return shell(title,f'{label}を{metric}あたりに換算して価格比較。',body,segment_url(category,segment),noindex)

def render_method():
    steps=[
        ('01','price','単価をそろえる','紙おむつ・おしりふき・防臭袋は1枚、粉ミルクは100gあたり。セット数が違っても同じ単位に換算します。'),
        ('02','diapers','条件違いを混ぜない','紙おむつはテープ／パンツとサイズを一致。サイズ選択式やタイプ不明の商品はランキングから外します。'),
        ('03','check','実質重複を整理','同じ商品名の候補が複数ある場合は整理し、同じ商品ばかり並ばないようにします。'),
        ('04','chick','価格以外を断定しない','肌との相性・品質・栄養・健康効果などを、根拠なく順位付けしません。'),
        ('05','check','最後は販売ページで確認','価格・在庫・商品仕様は変わるため、購入前に楽天の商品ページで最新情報をご確認ください。'),
    ]
    cards=''.join(f'''<article class="method-card"><span class="method-number">{num}</span><div class="method-card-icon">{icon_svg(icon)}</div><h2>{esc(title)}</h2><p>{esc(text)}</p></article>''' for num,icon,title,text in steps)
    body=f'''<section class="page-head method-head"><a href="{SITE_URL}">← トップ</a><div class="method-hero-art"><div>{icon_svg("chick")}</div><span>ちゃんと比べる<br>ためのルール</span></div><div class="section-kicker">METHOD</div><h1>比較方法</h1><p>「安い」の前に、同じ条件で比べられることを優先します。</p></section><section class="method-grid">{cards}</section><section class="method-principle"><div class="method-principle-icon">{icon_svg("check")}</div><div><div class="section-kicker">OUR RULE</div><h2>商品数を増やすために、曖昧な商品を載せません</h2><p>候補が少なくなっても、サイズ・タイプ・数量を安全に確認できる商品を優先します。</p></div></section>'''
    return shell('比較方法 | ベビー用品コスパ比較','単価計算と比較対象の選び方。',body,f'{SITE_URL}method/')

def write_page(path: Path, content: str):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content,encoding='utf-8')
