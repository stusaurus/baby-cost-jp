from __future__ import annotations
import html, json, re, hashlib
from pathlib import Path
from .config import GA_MEASUREMENT_ID, SITE_ID, SITE_NAME, SITE_URL

METRIC={'per_piece':'1枚','per_100g':'100g'}
SIZE={'newborn':'新生児','s':'S','m':'M','l':'L','big':'BIG','big_plus':'BIGより大きい'}
TYPE={'tape':'テープ','pants':'パンツ'}

def static_version(name):
    return hashlib.sha256((Path(__file__).parent/'static'/name).read_bytes()).hexdigest()[:12]

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

def guide_scene(kind='find'):
    """Original bird guide: a different task at each stop, not a decorative stamp."""
    prop = {'find':'<circle cx="107" cy="57" r="19" fill="#eef7f4" stroke="#537b75" stroke-width="4"/><path d="m93 72-18 20" stroke="#537b75" stroke-width="7" stroke-linecap="round"/><path d="m108 47 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z" fill="#d5a458"/>',
      'tray':'<path d="M12 89h108l-9 22H23Z" fill="#d6b18a" stroke="#957252" stroke-width="2"/><rect x="80" y="65" width="23" height="24" rx="6" fill="#a9c7ca"/><rect x="33" y="68" width="24" height="21" rx="5" fill="#fffaf0"/>',
      'stage':'<rect x="91" y="84" width="33" height="30" rx="4" fill="#a9becb"/><path d="m106 87 2 5 6 1-4 4 1 5-5-3-4 3 1-5-4-4 5-1Z" fill="#fff8df"/>',
      'size':'<path d="M85 91h16V76h17V59h18" fill="none" stroke="#aa8961" stroke-width="3"/><path d="m130 42 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z" fill="#d5a458"/>'}.get(kind,'')
    return f'''<svg class="guide-scene" viewBox="0 0 150 130" aria-hidden="true"><path d="M23 70q-7-34 27-43 34-10 39 26l-1 32q-15 28-47 19Q20 98 23 70Z" fill="#e2bb65"/><path d="M27 78q8-9 24 0" fill="none" stroke="#bc974c" stroke-width="3" stroke-linecap="round"/><circle cx="58" cy="54" r="3" fill="#435b5b"/><path d="m70 61 14 4-13 8Z" fill="#c98262"/><path d="m35 104-3 10m25-8 4 9" stroke="#977a55" stroke-width="3" stroke-linecap="round"/><path d="m44 27 4-11 7 9" fill="none" stroke="#b99349" stroke-width="3"/>{prop}</svg>'''

def room_svg(kind):
    """Four original nursery scenes share a skyline and ground, with distinct objects."""
    common='<path d="M8 140q38-24 72-6t78 1 74 5v34H8Z" fill="#fffaf0"/><path d="M15 152h210" stroke="#ae9279" stroke-opacity=".35" stroke-width="2" stroke-dasharray="3 6"/>'
    scenes={
      'diapers': '<path d="M44 66c-18 0-24-22-7-31 6-24 36-24 45-5 21-4 28 25 11 31Z" fill="#fffaf3"/><path d="M86 58q37 16 72 0l-1 55q-7 25-35 25t-35-25Z" fill="#fffdf8" stroke="#b39374" stroke-width="2.5"/><path d="M88 71q36 15 68 0m-62 21q16 6 19 37m38-37q-16 6-20 37" fill="none" stroke="#b39374" stroke-width="2.5"/><path d="M94 77q27 9 53 0" stroke="#bb9c7e" stroke-dasharray="3 4" fill="none"/><rect x="32" y="113" width="44" height="28" rx="8" fill="#e3be83"/><path d="m188 44 3 8 9 2-9 3-3 8-3-8-8-3 8-2Z" fill="#cb9b54"/>',
      'wipes':'<path d="M50 43q-23 29 0 38t0-38Z" fill="#7eaeb5"/><path d="M184 23q-15 20 0 27t0-27Z" fill="#bfd2d1"/><rect x="55" y="91" width="138" height="52" rx="19" fill="#8fb8ba" stroke="#5f8e94" stroke-width="2"/><rect x="89" y="79" width="62" height="21" rx="8" fill="#edf4ec"/><path d="M109 80q-27-34 4-42 33 5 26 42" fill="#fffdf7" stroke="#b7b9a4" stroke-width="2"/><path d="M74 117h98" stroke="#dce8df" stroke-width="2"/><path d="M15 150q22-24 37-6l19-14 29 20" fill="#e9dac2"/>',
      'formula':'<path d="M164 25a27 27 0 1 0 28 38 23 23 0 0 1-28-38" fill="#d5ac59"/><path d="M100 23q5-17 16 0v14h-16Z" fill="#d9b596"/><rect x="92" y="36" width="33" height="16" rx="5" fill="#8fa8b9"/><path d="M94 53q-15 12-14 24v55q0 13 13 13h35q12 0 12-13V77q-1-13-17-24Z" fill="#fffaf0" stroke="#a78e75" stroke-width="2"/><path d="M81 99h59v32q0 13-12 13H93q-12 0-12-13Z" fill="#ecddbb"/><path d="M118 70h12m-12 12h12m-12 12h12" stroke="#a5b6c0" stroke-width="2"/><path d="m47 73 3 8 9 2-9 3-3 8-3-8-8-3 8-2Z" fill="#d5ac59"/><rect x="158" y="111" width="39" height="33" rx="5" fill="#d6bba4"/>',
      'diaper_bags':'<path d="M47 84h51l5 60H43Z" fill="#f6e8e0" stroke="#bba59f" stroke-width="2"/><path d="M57 84q0-23 16-23t16 23" stroke="#bba59f" fill="none" stroke-width="2"/><rect x="126" y="72" width="52" height="70" rx="10" fill="#b4a9bd" stroke="#8e829f" stroke-width="2"/><rect x="121" y="65" width="62" height="11" rx="5" fill="#c8becc"/><path d="M143 63v-5h19v5" stroke="#8e829f" fill="none" stroke-width="2"/><path d="m65 35 3 8 9 2-9 3-3 8-3-8-8-3 8-2Zm137 51 3 7 7 2-7 3-3 7-3-7-7-3 7-2Z" fill="#cbab67"/>'
    }
    return f'<svg class="room-art" viewBox="0 0 240 174" aria-hidden="true">{common}{scenes.get(kind,scenes["diapers"])}</svg>'

def hero_visual():
    return f'<div class="hero-art hero-mascot">{guide_scene("find")}<span>同じ単位で、いっしょに探そう。</span></div>'


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
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="{robots}"><link rel="canonical" href="{esc(canonical)}"><link rel="stylesheet" href="{SITE_URL}static/styles.css?v={static_version("styles.css")}">{analytics_head()}</head><body><header class="top"><a class="brand" href="{SITE_URL}"><span class="brand-mark">{icon_svg('chick')}</span><span>{SITE_NAME}</span></a><a href="{SITE_URL}method/">比較方法</a></header><main>{body}</main><footer><div class="footer-brand"><span>{icon_svg('chick')}</span><b>{SITE_NAME}</b></div><p>価格・枚数等は取得時点の情報です。購入前に販売ページで最新情報をご確認ください。</p></footer><script src="{SITE_URL}static/analytics.js"></script><script src="{SITE_URL}static/app.js?v={static_version("app.js")}"></script></body></html>'''

def trust_strip():
    return f'''<div class="trust-strip" aria-label="比較方針"><span>{icon_svg('check')}送料込み対象</span><span>{icon_svg('check')}選択式商品は除外</span><span>{icon_svg('check')}単価を自動計算</span><span>{icon_svg('check')}毎日更新</span></div>'''

def selector(categories, current_type='', current_size=''):
    segs=[]
    for s in categories['diapers']['segments']:
        segs.append({'type':s['type'],'size':s['size'],'url':segment_url(categories['diapers'],s)})
    return f'''<section class="selector visual-selector" id="diaper-selector" data-segments='{esc(json.dumps(segs,ensure_ascii=False))}' data-current-type="{esc(current_type)}" data-current-size="{esc(current_size)}">
      <div class="selector-heading"><div class="selector-illustration">{guide_scene("size")}</div><div><div class="section-kicker">DIAPER FINDER</div><h2>ぴったりサイズの小道</h2><p class="section-lead">タイプを選んで、サイズの積み木をタップ。</p></div></div>
      <div class="filter-label">タイプ</div><div class="type-chips" role="group" aria-label="おむつタイプ"><button type="button" class="filter-chip type-chip" data-value="pants">{icon_svg("diapers")}<span>パンツ</span><small>はくタイプ</small></button><button type="button" class="filter-chip type-chip" data-value="tape">{icon_svg("diapers")}<span>テープ</span><small>とめるタイプ</small></button></div>
      <div class="filter-label">サイズの小道</div><div class="size-chips" role="group" aria-label="おむつサイズ"></div>
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
    return f'''<section class="featured-deals"><div class="featured-deals-head"><div><div class="section-kicker">TODAY'S PICKS</div><h2>今日の買い候補<span class="section-subtitle">きょうの、いいもの発見。</span></h2><p>現在取得できる同条件商品の中で、中央値との差が大きい候補です。</p></div><div class="featured-deals-mascot">{guide_scene("find")}</div></div><div class="deal-grid">{''.join(cards)}</div><p class="deal-disclaimer">※ 過去価格との比較ではありません。現在の比較対象内での相対的な価格差です。</p></section>'''


def price_drops_section(rows):
    if not rows:
        return ''
    cards=[]
    for i,row in enumerate(rows, start=1):
        p=row["product"]
        image=f'<div class="drop-image"><img src="{esc(p.get("image"))}" alt="" loading="lazy" decoding="async"></div>' if p.get("image") else f'<div class="drop-image drop-image-fallback">{icon_svg("price")}</div>'
        medal=f'{i:02}'
        cards.append(f'''<a class="drop-card drop-rank-{i}" href="{esc(row["url"])}" data-nav-source="price_drop" data-category-id="{esc(row["category_id"])}"><div class="drop-rank">{medal}<span>位</span></div><div class="drop-badge">前回より {row["drop_percent"]:.0f}%↓</div>{image}<div class="drop-copy"><small>{esc(row["category_label"])} / {esc(row["segment_label"])}</small><strong>¥{p["price_yen"]:,}</strong><p>{esc(display_product_name(p["name"]))}</p><span>¥{row["drop_yen"]:,}安い・比較を見る →</span></div></a>''')
    return f'''<section class="price-drops"><div class="price-drops-head"><div><div class="section-kicker">PRICE DROP RANKING</div><h2>値下がりランキング<span class="section-subtitle">価格が下がった、ちいさなステージ。</span></h2><p>前回公開時と同じ商品・同じ内容量だけを比較し、値下がり率順に並べています。</p></div><div class="price-drops-icon">{guide_scene("stage")}</div></div><div class="drop-grid">{''.join(cards)}</div><p class="drop-note">※ 前回取得時との比較です。長期的な最安値やセールを示すものではありません。</p></section>'''

def recent_trends_section(rows):
    if not rows:
        return ''
    cards=[]
    for row in rows:
        p=row["product"]
        spark=price_history_sparkline(p.get("price_history") or [])
        cards.append(f'''<a class="trend-card" href="{esc(row["url"])}" data-nav-source="recent_price_trend" data-category-id="{esc(row["category_id"])}"><div class="trend-card-head"><span>{esc(row["category_label"])}</span><b>{row["points"]}回分</b></div><h3>{esc(display_product_name(p["name"]))}</h3>{spark}<div class="trend-card-foot"><strong>{row["drop_percent"]:.0f}%↓</strong><span>¥{row["start_price_yen"]:,} → ¥{row["current_price_yen"]:,}</span></div></a>''')
    return f'''<section class="recent-trends"><div class="recent-trends-head"><div><div class="section-kicker">RECENT TREND</div><h2>最近安くなっている商品</h2><p>3回以上の履歴がある商品のうち、最初の記録より現在価格が下がっているものです。</p></div>{icon_svg("price")}</div><div class="trend-grid">{''.join(cards)}</div></section>'''


def render_home(categories, snapshots, deals, price_drops, recent_trends, updated_at):
    rooms=[]
    info=[('diapers','おむつのおへや','紙おむつ','サイズ・タイプを選ぶ'),('wipes','ふきふきの泉','おしりふき','1枚あたりで比べる'),('formula','ミルクの月あかり','粉ミルク','100gあたりで比べる'),('diaper_bags','におわない星空','防臭袋','1枚あたりで比べる')]
    for cid,room,name,caption in info:
        href='#diaper-selector' if cid=='diapers' else f'{SITE_URL}{categories[cid]["path"]}/'
        live='' if cid=='diapers' else _home_price(snapshots.get(cid),categories[cid]['metric'])
        rooms.append(f'''<a class="room-gateway room--{cid} cat" href="{href}" data-nav-source="home_category" data-category-id="{cid}"><span class="room-name">{room}</span><div class="cat-icon">{room_svg(cid)}</div><strong>{name}<span>↗</span></strong><small>{caption}</small>{live}</a>''')
    body=f'''<section class="playground-hero hero" aria-labelledby="playground-title"><div class="sky-cloud cloud-left" aria-hidden="true"></div><div class="sky-cloud cloud-right" aria-hidden="true"></div><span class="sky-star star-left" aria-hidden="true">✦</span><span class="sky-star star-right" aria-hidden="true">✦</span><div class="hero-title"><p class="eyebrow">BABY SHOPPING PLAYGROUND</p><h1 id="playground-title">ちいさな毎日の、<br><span>いいもの探し。</span></h1><p>ベビー用品を、1枚・100gの単価で比較。<br>同じ条件にそろえて、心地よく選ぼう。</p><span class="room-prompt">どれを比べる？ <span>↓</span></span></div><div class="nursery-rooms" id="categories">{''.join(rooms)}</div>{hero_visual()}<div class="hero-floor" aria-hidden="true"><span>1枚</span><span>100g</span><span>くらべる</span></div></section>{selector(categories)}{featured_deals_section(deals)}{price_drops_section(price_drops)}{recent_trends_section(recent_trends)}{how_visual()}<section class="quality-card quality-visual"><div class="quality-icon">{icon_svg('check')}</div><div><div class="section-kicker">OUR LITTLE PROMISE</div><h2>「安いけど条件が違う」を入れません</h2><p>紙おむつはテープ／パンツとサイズを分離。販売ページでサイズを選ぶ商品や、数量を安全に読み取れない商品は除外します。</p>{trust_strip()}</div><a href="{SITE_URL}method/">比較ルールを見る →</a></section><p class="updated">最終更新 {updated_at:%Y-%m-%d %H:%M} JST</p>'''
    return shell('ベビー用品コスパ比較 | 1枚・100g単価で比較','紙おむつ、おしりふき、粉ミルクなどを単価換算して比較します。',body,SITE_URL)

def render_diaper_index(categories, updated_at):
    rows=[]
    for s in categories['diapers']['segments']:
        rows.append(f'<a class="choice choice--{s["type"]}" data-nav-source="diaper_index" data-category-id="diapers" href="{segment_url(categories["diapers"],s)}"><div class="choice-icon">{icon_svg("diapers")}</div><span class="choice-type">{TYPE[s["type"]]}</span><b>{SIZE[s["size"]]}</b><span>1枚あたりを見る →</span></a>')
    body=f'''<section class="page-head diaper-head"><a href="{SITE_URL}">← トップ</a><div class="page-head-art">{icon_svg("diapers")}</div><div class="section-kicker">DIAPERS</div><h1>紙おむつを<br>1枚あたりで比較</h1><p>テープ／パンツとサイズをそろえた商品だけを比較します。</p>{trust_strip()}</section>{selector(categories)}<section class="home-section"><h2>すべての比較条件</h2><div class="choices">{''.join(rows)}</div></section><p class="updated">最終更新 {updated_at:%Y-%m-%d %H:%M} JST</p>'''
    return shell('紙おむつ 1枚あたり価格比較','テープ・パンツ、サイズ別に紙おむつの1枚あたり価格を比較。',body,f'{SITE_URL}diapers/')


def compare_panel():
    return '''<div class="compare-dock" data-compare-dock hidden aria-label="比較トレー"><div class="tray-handle" aria-hidden="true"></div><div class="tray-slots" data-tray-slots></div><div class="compare-dock-copy"><span data-compare-count aria-live="polite">0件選択</span><small data-compare-remaining>あと3商品選べます</small></div><div class="compare-dock-actions"><button type="button" class="compare-clear" data-compare-clear>クリア</button><button type="button" class="compare-open" data-compare-open disabled>くらべてみる</button></div></div><div class="compare-modal" data-compare-modal hidden><div class="compare-modal-backdrop" data-compare-close></div><section class="compare-dialog" role="dialog" aria-modal="true" aria-labelledby="compare-dialog-title"><div class="compare-dialog-head"><div><div class="section-kicker">SIDE BY SIDE</div><h2 id="compare-dialog-title">トレーの中で、くらべてみよう。</h2></div><button type="button" class="compare-close" data-compare-close aria-label="閉じる">×</button></div><div class="compare-table" data-compare-table></div><p class="compare-note">価格・在庫は変動します。購入前に楽天の商品ページで最新情報をご確認ください。</p></section></div>'''



def price_history_sparkline(points):
    if len(points) < 2:
        return ''
    values=[float(p.get("price_yen",0)) for p in points if p.get("price_yen") is not None]
    if len(values) < 2:
        return ''
    lo=min(values); hi=max(values)
    span=hi-lo
    width=100; height=28
    coords=[]
    for i,value in enumerate(values):
        x=0 if len(values)==1 else (i/(len(values)-1))*width
        y=height/2 if span<1e-9 else height-((value-lo)/span)*height
        coords.append(f'{x:.1f},{y:.1f}')
    first=values[0]; last=values[-1]
    if last<first:
        kind='down'; label=f'直近{len(values)}回で ¥{int(round(first-last)):,}↓'
    elif last>first:
        kind='up'; label=f'直近{len(values)}回で ¥{int(round(last-first)):,}↑'
    else:
        kind='same'; label=f'直近{len(values)}回は同価格'
    weather={"down":"↘","up":"↗","same":"☁"}[kind]
    return f'''<div class="mini-history mini-history--{kind}"><span class="price-weather" aria-hidden="true">{weather}</span><div><span>価格のうごき</span><b>{esc(label)}</b></div><svg viewBox="-3 -4 {width+6} {height+8}" role="img" aria-label="{esc(label)}"><polyline points="{' '.join(coords)}" fill="none" stroke="currentColor" stroke-width="1.5" vector-effect="non-scaling-stroke" stroke-linecap="round" stroke-linejoin="round"/><circle cx="{coords[-1].split(',')[0]}" cy="{coords[-1].split(',')[1]}" r="2.6" fill="currentColor"/></svg><small>¥{int(round(first)):,} → ¥{int(round(last)):,}</small></div>'''


def product_brand_label(product):
    name=product.get('name','')
    known=[
        ('パンパース','パンパース'),('メリーズ','メリーズ'),('ムーニー','ムーニー'),
        ('マミーポコ','マミーポコ'),('グーン','グーン'),('GOO.N','グーン'),
        ('Genki','Genki!'),('ゲンキ','Genki!'),('Whito','Whito'),
    ]
    for needle,label in known:
        if needle.lower() in name.lower():
            return label
    raw=(product.get('brand') or product.get('manufacturer') or '').strip()
    return raw[:24] if raw else 'その他'


BRAND_SLUGS={
    'パンパース':'pampers',
    'メリーズ':'merries',
    'ムーニー':'moony',
    'マミーポコ':'mamypoko',
    'グーン':'goon',
    'Genki!':'genki',
    'Whito':'whito',
}

def brand_slug(label):
    return BRAND_SLUGS.get(label,'')

def brand_page_url(segment, label):
    slug=brand_slug(label)
    if not slug:
        return ''
    return f"{SITE_URL}diapers/{segment['type']}/{segment['size']}/{slug}/"


def brand_comparison_section(products, category_id, metric, segment=None):
    if category_id!='diapers' or len(products)<2:
        return ''
    groups={}
    for p in products:
        label=product_brand_label(p)
        groups.setdefault(label,[]).append(p)
    if len(groups)<2:
        return ''

    rows=[]
    for label,items in groups.items():
        best=min(items,key=lambda p:p['unit_price'])
        rows.append({
            'label':label,
            'count':len(items),
            'best_unit':min(float(p['unit_price']) for p in items),
            'best_price':min(int(p['price_yen']) for p in items),
            'max_quantity':max(float(p['quantity']['total']) for p in items),
            'image':best.get('image',''),
        })
    rows.sort(key=lambda row:(row['best_unit'],row['best_price'],row['label']))

    cards=[]
    for i,row in enumerate(rows[:6],start=1):
        image=f'<div class="brand-card-image"><img src="{esc(row["image"])}" alt="" loading="lazy" decoding="async"></div>' if row['image'] else f'<div class="brand-card-image brand-card-image--empty">{icon_svg("diapers")}</div>'
        dedicated=brand_page_url(segment,row['label']) if segment and row['count']>=2 else ''
        dedicated_html=f'<a class="brand-page-link" href="{esc(dedicated)}">専用比較ページ →</a>' if dedicated else ''
        cards.append(f'''<div class="brand-card"><button type="button" class="brand-card-filter" data-brand-filter="{esc(row['label'])}"><span class="brand-card-rank">{i}</span>{image}<strong>{esc(row['label'])}</strong><div class="brand-card-stats"><span><small>最安単価</small><b>{yen(row['best_unit'])}<em> / {metric}</em></b></span><span><small>最安総額</small><b>¥{row['best_price']:,}</b></span><span><small>最大容量</small><b>{row['max_quantity']:g}枚</b></span></div><small class="brand-card-count">{row['count']}商品掲載</small><i>このブランドだけ見る →</i></button>{dedicated_html}</div>''')

    return f'''<section class="brand-compare" data-brand-compare><div class="brand-compare-head"><div><div class="section-kicker">BRAND COMPARE</div><h2>ブランドの本棚</h2><p>同じタイプ・サイズの掲載商品から、ブランドごとの価格と容量を比較します。</p></div><button type="button" class="brand-filter-clear" data-brand-filter-clear hidden>全ブランド表示</button></div><div class="brand-grid">{''.join(cards)}</div><p class="brand-note">※ 品質・肌との相性などの優劣ではなく、現在掲載している商品の価格・容量のみを比較しています。</p></section>'''


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
    history_html=price_history_sparkline(p.get("price_history") or [])
    change=p.get("price_change") or {}
    trend_html=''
    if change:
        delta=int(change.get("price_delta_yen",0))
        if delta<0:
            trend_html=f'<span class="price-trend price-trend--down">前回より ¥{abs(delta):,}↓</span>'
        elif delta>0:
            trend_html=f'<span class="price-trend price-trend--up">前回より ¥{abs(delta):,}↑</span>'
        else:
            trend_html='<span class="price-trend price-trend--same">前回と同価格</span>'
    attrs=f'''data-affiliate="rakuten" data-category-id="{esc(category_id)}" data-product-name="{esc(p['name'])}" data-product-id="{esc(p.get('source_id'))}" data-size="{esc(segment.get('size',''))}" data-product-type="{esc(segment.get('type',''))}" data-unit-metric="{esc(p['unit_metric'])}" data-unit-price="{p['unit_price']:.4f}" data-rank="{rank}" data-click-position="comparison_card"'''
    full_name=f'''<details class="full-name"><summary>商品名全文</summary><p>{esc(p['name'])}</p></details>''' if display!=p['name'] else ''
    shop=f'<span class="shop">{esc(p.get("shop"))}</span>' if p.get('shop') else ''
    gap=(p['unit_price']-best_unit_price) if best_unit_price is not None else 0
    badge='最安' if rank==1 else (f'1位より +{yen(gap)} / {METRIC[p["unit_metric"]]}' if gap>0 else f'{rank}位')
    image=f'<div class="product-image"><img src="{esc(p.get("image"))}" alt="" loading="lazy" decoding="async"></div>' if p.get('image') else ''
    return f'''<article class="product product-rank-{rank}" id="rank-{rank}" data-sort-unit="{p['unit_price']:.6f}" data-sort-price="{p['price_yen']}" data-sort-quantity="{q['total']:.6f}" data-original-rank="{rank}" data-brand="{esc(product_brand_label(p))}"><div class="rank rank-{rank}">{rank}</div><div class="product-main"><div class="product-overview">{image}<div class="product-info"><div class="card-unit"><span class="tag-hole" aria-hidden="true"></span><small>{METRIC[p["unit_metric"]]}あたり</small><strong>{yen(p["unit_price"])}<em> / {METRIC[p["unit_metric"]]}</em></strong></div><div class="maker-row"><div class="maker">{esc(p.get('brand') or p.get('manufacturer'))} {stage_html}</div>{shop}</div><h3 class="product-title" title="{esc(p['name'])}">{esc(display)}</h3>{strength_row}{trend_html}<div class="price-row"><div class="unit"><b>{yen(p['unit_price'])}</b><span> / {METRIC[p['unit_metric']]}</span></div><span class="rank-badge">{badge}</span></div></div></div><div class="facts"><span><small>内容量</small><b>合計 {total_txt}{pack}</b></span><span><small>販売価格</small><b>¥{p['price_yen']:,}</b></span></div>{history_html}{full_name}<details><summary>単価の計算を見る</summary><p>¥{p['price_yen']:,} ÷ {total_txt}{' × 100' if p['unit_metric']=='per_100g' else ''} = {yen(p['unit_price'])} / {METRIC[p['unit_metric']]}</p><small>数量根拠: {esc(q.get('evidence'))}</small></details><div class="product-actions"><button type="button" class="compare-add" data-compare-add data-compare-id="{esc(p.get('source_id'))}" data-compare-name="{esc(display)}" data-compare-unit="{p['unit_price']:.4f}" data-compare-unit-label="{esc(METRIC[p['unit_metric']])}" data-compare-price="{p['price_yen']}" data-compare-quantity="{esc(total_txt)}" data-compare-image="{esc(p.get('image'))}" data-compare-rank="{rank}"><span>＋</span> 比較トレーに入れる</button><a class="cta" href="{esc(p.get('url'))}" target="_blank" rel="nofollow sponsored noopener" {attrs}>楽天で価格・在庫を見る</a></div></div></article>'''

def quick_compare(products):
    if not products: return ''
    cards=[]
    for i,p in enumerate(products[:3],1):
        q=p['quantity']; total=f'{q["total"]:g}{"g" if q["base_unit"]=="g" else "枚"}'
        image=f'<div class="quick-image"><img src="{esc(p.get("image"))}" alt="" loading="lazy" decoding="async"></div>' if p.get('image') else f'<div class="quick-image quick-image-fallback">{icon_svg("price")}</div>'
        medal=f'{i:02}'
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
    return f'''<section class="buying-guide" data-buying-guide><div class="buying-guide-head"><div class="buying-guide-mascot">{icon_svg("chick")}</div><div><div class="section-kicker">QUICK GUIDE</div><h2>今日はどんな買い方？</h2><p>いちばん近い買い方を選んでください。</p></div></div><div class="buying-goals"><button type="button" data-buy-goal="unit">{icon_svg("price")}<b>コツコツ派</b><small>1枚・100gあたりを抑えたい</small></button><button type="button" data-buy-goal="price">{icon_svg("check")}<b>まずは少なめ派</b><small>レジで払う総額を小さくしたい</small></button><button type="button" data-buy-goal="quantity">{icon_svg("diaper_bags")}<b>ストック派</b><small>一度に多く確保したい</small></button></div><div class="buying-guide-result" data-buy-guide-result hidden><strong></strong><span></span></div></section>'''


def comparison_mascot_tip(category_id: str, count: int):
    if category_id=='diapers':
        text='サイズとタイプが確認できた商品だけを比較します'
    elif category_id=='formula':
        text='価格だけを比較。栄養や相性は順位には含めません'
    else:
        text='数量を確認できた商品だけを同じ単位で比較します'
    return f'''<div class="result-mascot-tip"><div class="result-mascot">{icon_svg('chick')}</div><div><b>{count}商品を比較中</b><span>{esc(text)}</span></div></div>'''


def render_brand_page(categories, category, segment, brand_label, products, updated_at):
    metric=METRIC[category['metric']]
    canonical=brand_page_url(segment,brand_label)
    best=min(products,key=lambda p:p['unit_price'])
    min_price=min(int(p['price_yen']) for p in products)
    max_price=max(int(p['price_yen']) for p in products)
    min_qty=min(float(p['quantity']['total']) for p in products)
    max_qty=max(float(p['quantity']['total']) for p in products)
    strengths=product_strength_tags(products)
    cards=''.join(product_card(p,i+1,'diapers',segment,best['unit_price'],strengths.get(p.get('source_id') or p.get('name'),[])) for i,p in enumerate(sorted(products,key=lambda p:p['unit_price'])))
    summary=f'''<section class="brand-page-summary"><div><small>掲載商品</small><strong>{len(products)}商品</strong></div><div><small>最安単価</small><strong>{yen(best['unit_price'])}<em> / {metric}</em></strong></div><div><small>販売価格帯</small><strong>¥{min_price:,}〜¥{max_price:,}</strong></div><div><small>容量</small><strong>{min_qty:g}〜{max_qty:g}枚</strong></div></section>'''
    answer=f'''<section class="answer"><div class="answer-medal">★</div><div class="answer-content"><div class="answer-label"><span>{esc(brand_label)}内の最安単価</span></div><strong>{yen(best['unit_price'])}<small> / {metric}</small></strong><p>{esc(display_product_name(best['name']))}</p></div></section>'''
    body=f'''<section class="page-head brand-page-head comparison-page-head comparison-page-head--diapers"><a href="{segment_url(category,segment)}">← {esc(segment['label'])}の全ブランド比較</a>{comparison_head_visual('diapers')}<div class="section-kicker">THE LITTLE BRAND SHOWROOM</div><h1>{esc(brand_label)}<br><span>{esc(segment['label'])} 価格比較</span></h1><p>同じブランド・同じタイプ・同じサイズにそろえ、{metric}あたりの価格を比較します。</p><div class="compare-meta"><span>{TYPE[segment['type']]}</span><span>{SIZE[segment['size']]}</span><span>{len(products)}商品を比較</span></div></section><section class="comparison brand-page-comparison" data-comparison data-category-id="diapers" data-size="{esc(segment.get('size',''))}" data-product-type="{esc(segment.get('type',''))}" data-result-count="{len(products)}">{summary}{answer}{price_snapshot(products,metric)}{buying_guide()}<section class="view-switcher" data-view-switcher><div><div class="section-kicker">VIEW</div><h2>{esc(brand_label)}を目的別に比べる</h2><p>このブランドの掲載商品だけを並べ替えます。</p></div><div class="view-buttons" role="group" aria-label="商品の並べ替え"><button type="button" class="is-active" data-sort-mode="unit">単価が安い</button><button type="button" data-sort-mode="price">支払総額が安い</button><button type="button" data-sort-mode="quantity">大容量</button></div></section><h2 class="result-title"><span>{esc(brand_label)}</span> <b data-result-sort-label>単価が安い順</b></h2><div class="products" data-sortable-products>{cards}</div>{diaper_savings_simulator(products)}<details class="extra-comparison"><summary>上位を早見</summary>{quick_compare(products)}</details>{compare_panel()}</section><section class="brand-page-seo-note"><div class="section-kicker">ABOUT THIS PAGE</div><h2>{esc(brand_label)} {esc(segment['label'])}を同条件で比較</h2><p>このページは、楽天から取得した商品のうち「{esc(brand_label)}」「{esc(segment['label'])}」と数量を安全に確認できた商品だけを掲載しています。ポイント・クーポンは順位に含めず、送料込み／送料無料条件の価格から単価を算出しています。</p></section><p class="updated">更新 {updated_at:%Y-%m-%d %H:%M} JST</p>'''
    title=f'{brand_label} {segment["label"]} 価格比較｜{metric}あたり'
    desc=f'{brand_label}の{segment["label"]}を{metric}あたりで価格比較。販売価格・容量・現在の価格推移も確認できます。'
    return shell(title,desc,body,canonical,False)


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
    body=f'''<section class="page-head comparison-page-head comparison-page-head--{category_id}">{back}{head_visual}<div class="section-kicker">PRICE COMPARISON</div><h1>{esc(label)}<br><span>コスパ比較</span></h1><p>{metric}あたりの価格を、同じ条件にそろえて比較します。</p>{meta}</section>{mascot_tip}<section class="comparison" data-comparison data-category-id="{category_id}" data-size="{esc(segment.get('size',''))}" data-product-type="{esc(segment.get('type',''))}" data-result-count="{len(products)}">{answer}{snapshot}{'<details class="condition-disclosure" id="condition-change"><summary>条件を変更する</summary>'+selector_html+'</details>' if selector_html else ''}<nav class="comparison-nav" aria-label="比較ページ内"><a href="#products">商品を見る ↓</a>{'<a href="#condition-change">条件を変更</a><a href="#brand-section">ブランド</a>' if category_id=='diapers' else ''}</nav>{buying_guide()}<section class="view-switcher" data-view-switcher><div><div class="section-kicker">VIEW</div><h2>比べ方を切り替える</h2><p>同じ掲載商品を、目的に合わせて並べ替えます。</p></div><div class="view-buttons" role="group" aria-label="商品の並べ替え"><button type="button" class="is-active" data-sort-mode="unit">単価が安い</button><button type="button" data-sort-mode="price">支払総額が安い</button><button type="button" data-sort-mode="quantity">大容量</button></div></section><h2 class="result-title"><span>ランキング</span> <b data-result-sort-label>単価が安い順</b></h2><div class="products" id="products" data-sortable-products>{cards}</div><div id="brand-section">{brand_comparison_section(products,category_id,metric,segment)}</div>{savings}<details class="extra-comparison"><summary>上位を早見・価格履歴を確認</summary>{quick_compare(products)}</details>{compare_panel()}</section>{health_note}<section class="method-note method-note-visual"><div class="method-note-icon">{icon_svg("check")}</div><div><div class="section-kicker">HOW IT WORKS</div><h2>この順位に入る条件</h2><p>楽天APIで送料込み／送料無料条件に絞り、数量と条件を確認できた商品だけを単価換算しています。紙おむつはサイズ選択式やタイプ不明の商品を除外。ポイント・クーポンは順位に含めません。</p><a href="{SITE_URL}method/">詳しい比較方法を見る →</a></div></section><p class="updated">更新 {updated_at:%Y-%m-%d %H:%M} JST</p>'''
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
