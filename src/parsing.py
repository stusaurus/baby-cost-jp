from __future__ import annotations
from dataclasses import asdict, dataclass
import re, unicodedata
import math

@dataclass(frozen=True)
class Quantity:
    total: float
    base_unit: str
    evidence: str
    confidence: float
    pack_count: int = 1
    def as_dict(self): return asdict(self)

def norm(v: str) -> str:
    t=unicodedata.normalize('NFKC', str(v or '')).replace(',','').replace('✕','×').replace('＊','×')
    return re.sub(r'\s+',' ',t).strip()

def parse_piece_quantity(title: str):
    return _parse_quantity(title, '枚', 'piece')

def _parse_quantity(title: str, unit_pattern: str, base_unit: str):
    """Accept one consistent total; never choose the largest selectable offer."""
    t=norm(title)
    counts=list(re.finditer(rf'(\d+(?:\.\d+)?)\s*({unit_pattern})',t,re.I))
    if not counts: return None
    entries=[]
    prefix=set(int(m[1]) for m in re.finditer(r'(\d+)\s*(?:個|点|袋|パック|箱|缶)\s*セット',t))
    for m in counts:
        n=float(m[1])*(1000 if m[2].lower()=='kg' else 1)
        if n<=0 or (base_unit=='piece' and not n.is_integer()): return None
        tail=t[m.end():]
        mult=re.match(r'(?:入り|入)?\s*[)）]?\s*([×xX]\s*\d+\s*(?:個|点|袋|パック|箱|缶|セット|P)?(?:入|入り)?(?:\s*[×xX]\s*\d+\s*(?:個|点|袋|パック|箱|缶|セット|P)?(?:入|入り)?)*)',tail)
        p=1; end=0
        if mult:
            for a in re.findall(r'[×xX]\s*(\d+)',mult[1]): p*=int(a)
            end=mult.end()
        else:
            bundle=re.match(r'(?:入り|入)?\s*(?:[/／]\s*缶)?\s*(?:[（(][^)]{0,20}[)）])?\s*(?:\d+\s*パック\s*)?[（(]?\s*(\d+)\s*(?:個|袋|パック|箱|缶)(?:セット|組|パック)?',tail)
            if bundle:
                p=int(bundle[1]); end=bundle.end()
                chained=re.match(r'\s*[×xX]\s*(\d+)\s*(?:個|袋|パック|箱|セット)',tail[end:])
                if chained: p*=int(chained[1]); end+=chained.end()
        if p<=0: return None
        entries.append((n,p,m[0]+tail[:end]))
    explicit=[(n,p,e) for n,p,e in entries if p>1]
    if explicit:
        totals={n*p for n,p,e in explicit}
        if len(totals)!=1: return None
        total=next(iter(totals)); bases={n for n,p,e in explicit}
        if any(p==1 and n not in bases and n!=total for n,p,e in entries): return None
        n,p,e=explicit[0]
    else:
        vals={n for n,p,e in entries}
        if len(vals)!=1 or len(prefix)>1: return None
        n,_,e=entries[0]; p=next(iter(prefix)) if prefix else 1
        total=n*p
        if prefix: e=f'{e} / {p}個セット'
    if (base_unit=='piece' and total>20000) or (base_unit=='g' and total>100000): return None
    return Quantity(total,base_unit,e,.99 if p>1 else .89,p)

def parse_weight_quantity(title: str):
    return _parse_quantity(title, 'kg|g', 'g')

BRANDS=[
 ('P&G','パンパース',['パンパース']),('花王','メリーズ',['メリーズ']),('ユニ・チャーム','ムーニー',['ムーニー','moony']),
 ('大王製紙','グーン',['グーン','goo.n','goon']),('王子ネピア','Genki!',['genki','ゲンキ']),('ピジョン','ピジョン',['ピジョン','pigeon']),
 ('レック','水99.9%',['水99.9','レック']),('明治','ほほえみ',['ほほえみ']),('森永乳業','はぐくみ',['はぐくみ']),
 ('アサヒグループ食品','和光堂 はいはい',['和光堂','はいはい']),('雪印メグミルク','ぴゅあ',['ぴゅあ']),('クリロン化成','BOS',['bos','ボス 防臭'])]

def identify_brand(title):
    k=norm(title).lower()
    for maker,brand,needles in BRANDS:
        if any(n.lower() in k for n in needles): return maker,brand
    return '',''

def diaper_type_mentions(t: str) -> set[str]:
    k=norm(t).lower()
    found=set()
    if 'パンツ' in k or re.search(r'(?<![a-z])pants?(?![a-z])', k): found.add('pants')
    if 'テープ' in k or re.search(r'(?<![a-z])tape(?![a-z])', k): found.add('tape')
    return found

def diaper_type(t):
    found=diaper_type_mentions(t)
    return next(iter(found)) if len(found)==1 else ''

_BIG_PLUS_RE=re.compile(
    r'(?:big|ビッグ|ビック)\s*(?:サイズ)?\s*より\s*大きい\s*(?:サイズ)?'
    r'|(?:big|ビッグ|ビック)\s*大(?=\s*\d*\s*枚|\b)'
    r'|スーパー\s*(?:big|ビッグ|ビック)'
    r'|xxl\s*(?:サイズ)?',
    re.I,
)

def diaper_size_mentions(t: str) -> set[str]:
    k=norm(t).lower()
    found=set()
    if _BIG_PLUS_RE.search(k):
        found.add('big_plus')
        k=_BIG_PLUS_RE.sub(' ', k)
    if re.search(r'(?<![a-z0-9])(?:big|xl)\s*(?:サイズ)?(?![a-z0-9])', k, re.I) or 'ビッグサイズ' in k or 'ビックサイズ' in k or re.search(r'ビッグ|ビック', k):
        found.add('big')
    # "出産準備 新生児" is contextual copy, not a size. Require a size-like form.
    if re.search(r'新生児\s*(?:用|サイズ|\d+\s*枚)', k) or re.search(r'(?<![a-z0-9])nb\s*(?:サイズ)?(?![a-z0-9])', k, re.I):
        found.add('newborn')
    if re.search(r'(?<![a-z0-9])m\s*(?:はいはい|たっち)', k, re.I) or re.search(r'(?:はいはい|たっち)\s*m(?![a-z0-9])', k, re.I):
        found.add('m')
    for s in ('s','m','l'):
        if f'{s}サイズ' in k or re.search(rf'(?:^|[\s・/／,(（:_]){s}(?=$|[\s・/／,)）:_])', k, re.I):
            found.add(s)
    return found

def diaper_size_count_mentions(t: str) -> set[str]:
    k=norm(t).lower()
    found=set()
    if re.search(
        r'(?:(?:big|ビッグ|ビック)\s*(?:サイズ)?\s*より\s*大きい\s*(?:サイズ)?|(?:big|ビッグ|ビック)\s*大|スーパー\s*(?:big|ビッグ|ビック)|xxl\s*(?:サイズ)?)'
        r'\s*[:：]?\s*(?:\([^)]{0,20}\)\s*)?\d+\s*枚',
        k,
        re.I,
    ):
        found.add('big_plus')
    if re.search(
        r'(?<!スーパー)(?:big|ビッグ|ビック)\s*(?:サイズ)?(?!\s*より\s*大きい|\s*大)'
        r'\s*[:：]?\s*(?:\([^)]{0,20}\)\s*)?\d+\s*枚',
        k,
        re.I,
    ):
        found.add('big')
    if re.search(r'新生児\s*(?:用|サイズ)?\s*[:：]?\s*(?:\([^)]{0,20}\)\s*)?\d+\s*枚', k):
        found.add('newborn')
    for s in ('s','m','l'):
        if re.search(
            rf'(?:^|[\s・/／,(（:_]){s}\s*(?:サイズ)?\s*[:：]?\s*(?:\([^)]{{0,20}}\)\s*)?\d+\s*枚',
            k,
            re.I,
        ):
            found.add(s)
    return found

def diaper_size(t):
    found=diaper_size_mentions(t)
    counted=diaper_size_count_mentions(t)
    if len(counted)==1:
        return next(iter(counted))
    return next(iter(found)) if len(found)==1 else ''

def _big_and_big_plus_are_separate_options(title: str) -> bool:
    counted=diaper_size_count_mentions(title)
    return 'big' in counted and 'big_plus' in counted

def _diaper_selection_issue(title: str, supplemental_text: str='') -> str:
    title_types=diaper_type_mentions(title)
    title_sizes=diaper_size_mentions(title)
    counted_sizes=diaper_size_count_mentions(title)
    if len(title_types)>1:
        return 'ambiguous_diaper_type'
    if len(title_sizes)>1:
        # Three or more explicit size labels are a product-variation list even if only
        # one trailing piece count is present (e.g. M/L/BIG/BIGより大きい 30枚).
        if len(title_sizes)>=3:
            return 'ambiguous_diaper_size'
        # With exactly two size words, a single size-specific piece count is strong
        # evidence for a fixed offer; the other word is often stray SEO/context copy.
        if len(counted_sizes)!=1:
            if title_sizes != {'big','big_plus'} or _big_and_big_plus_are_separate_options(title):
                return 'ambiguous_diaper_size'
    extra=norm(supplemental_text)
    combined=norm(f'{title} {extra}')
    size_choice = re.search(r'(?:サイズ).{0,12}(?:選択|選べ|えらべ|お選び|選ん)|(?:選択|選べ|えらべ|お選び|選ん).{0,12}(?:サイズ)', combined, re.I)
    type_choice = re.search(r'(?:タイプ|テープ|パンツ).{0,12}(?:選択|選べ|えらべ|お選び|選ん)|(?:選択|選べ|えらべ|お選び|選ん).{0,12}(?:タイプ|テープ|パンツ)', combined, re.I)
    combined_sizes=diaper_size_mentions(combined)
    combined_types=diaper_type_mentions(combined)
    if size_choice:
        return 'ambiguous_diaper_size_selection'
    if type_choice and len(combined_types)>1:
        return 'ambiguous_diaper_type_selection'
    if len(combined_sizes)>1 and re.search(r'バリエーション|各サイズ|サイズ展開', combined, re.I):
        return 'ambiguous_diaper_size_selection'
    return ''

def parse_for_segment_detailed(title: str, parser: str, segment: dict, supplemental_text: str=''):
    t=norm(title); low=t.lower()
    combined=norm(f'{t} {supplemental_text}')
    if re.search(r'定期(?:購入|便|コース)|初回(?:限定|価格)|初めての方限定|お試し|試供品|ふるさと納税|福袋',combined): return None,'conditional_offer'
    if re.search(r'(?:枚数|個数|パック数|容量|数量).{0,12}(?:選べ|選択|お選び)|(?:選べ|選択|お選び).{0,12}(?:枚数|個数|パック数|容量|数量)',combined): return None,'selectable_quantity'
    if any(x in low for x in ['介護','大人用','犬用','猫用','ペット用']): return None,'excluded_scope'
    maker,brand=identify_brand(t); attrs={}
    if parser=='diapers':
        if re.search(r'夜用|ぐっすり|水遊び|水あそび|トレーニング',t): return None,'special_diaper_variant'
        issue=_diaper_selection_issue(t, supplemental_text)
        if issue: return None,issue
        type_mentions=diaper_type_mentions(t); size_mentions=diaper_size_mentions(t); counted_sizes=diaper_size_count_mentions(t)
        exp_type=segment.get('type',''); exp_size=segment.get('size','')
        got_type=next(iter(type_mentions)) if len(type_mentions)==1 else ''
        if len(counted_sizes)==1:
            got_size=next(iter(counted_sizes))
        elif len(size_mentions)==1:
            got_size=next(iter(size_mentions))
        elif size_mentions == {'big','big_plus'}:
            got_size='big_plus'
        else:
            got_size=''
        if not got_type and exp_type=='tape' and got_size=='newborn': got_type='tape'
        if not got_type: return None,'missing_diaper_type'
        if not got_size: return None,'missing_diaper_size'
        if got_type!=exp_type: return None,'diaper_type_mismatch'
        if got_size!=exp_size: return None,'diaper_size_mismatch'
        q=parse_piece_quantity(t)
        stage='はいはい' if 'はいはい' in t else ('たっち' if 'たっち' in t else '')
        attrs={'type':got_type,'size':got_size,'fit_stage':stage}
    elif parser=='wipes':
        if 'おしりふき' not in t and 'おしり拭き' not in t: return None,'not_wipes'
        if any(x in t for x in ['手口','手・口','除菌','流せる']): return None,'excluded_wipes_variant'
        q=parse_piece_quantity(t); attrs={'variant':'thick' if '厚手' in t else 'unspecified'}
    elif parser=='formula':
        if not re.search(r'粉ミルク|乳児用(?:調整粉乳|ミルク)|ほほえみ|はぐくみ|はいはい|ぴゅあ|すこやか|E赤ちゃん|アイクレオ.*バランスミルク',t,re.I): return None,'not_formula'
        if any(x in low for x in ['液体','フォローアップ','ぐんぐん','チルミル','ステップ','たっち','アレルギー','特殊ミルク','治療用']): return None,'excluded_formula_variant'
        q=parse_weight_quantity(t); attrs={'stage':'infant','product_type':'powder','age_note':'対象月齢・調乳方法は販売ページとメーカー表示を確認'}
    elif parser=='diaper_bags':
        if not (('おむつ' in t or 'オムツ' in t) and any(x in t for x in ['袋','バッグ','bag','BAG'])): return None,'not_diaper_bag'
        if any(x in t for x in ['カセット','ゴミ箱本体','本体のみ']): return None,'excluded_diaper_bag_variant'
        if len(set(re.findall(r'(?<![A-Za-z])(?:SS|S|M|L|LL)\s*(?:サイズ)?(?=\s*\d+枚|サイズ)',t,re.I)))>1: return None,'selectable_bag_size'
        q=parse_piece_quantity(t)
    else: raise ValueError(parser)
    if not q: return None,'quantity_unparsed'
    return {'manufacturer':maker,'brand':brand,'attributes':attrs,'quantity':q.as_dict()},''

def parse_for_segment(title: str, parser: str, segment: dict, supplemental_text: str=''):
    parsed,_=parse_for_segment_detailed(title, parser, segment, supplemental_text=supplemental_text)
    return parsed

def unit_price(price_yen, metric, quantity):
    price=float(price_yen or 0); total=float(quantity.get('total') or 0)
    if not math.isfinite(price) or not math.isfinite(total) or price<=0 or total<=0: return None
    if metric=='per_piece' and quantity.get('base_unit')=='piece': return price/total
    if metric=='per_100g' and quantity.get('base_unit')=='g': return price/total*100
    return None
