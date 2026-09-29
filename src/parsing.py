from __future__ import annotations
from dataclasses import asdict, dataclass
import re, unicodedata

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
    t=norm(title)
    m=re.search(r'(\d+(?:\.\d+)?)\s*枚\s*[×xX]\s*(\d+)\s*(?:個|袋|パック|箱|セット)?',t)
    if m:
        a,b=float(m[1]),int(m[2]); return Quantity(a*b,'piece',m[0],.99,b)
    m=re.search(r'(\d+(?:\.\d+)?)\s*枚.{0,10}?(\d+)\s*(?:個|袋|パック|箱)\s*(?:セット|組)?',t)
    if m and int(m[2])>1:
        a,b=float(m[1]),int(m[2]); return Quantity(a*b,'piece',m[0],.96,b)
    vals=[(float(m[1]),m[0]) for m in re.finditer(r'(\d+(?:\.\d+)?)\s*枚',t)]
    if vals:
        n,e=max(vals,key=lambda x:x[0]); return Quantity(n,'piece',e,.89)
    return None

def parse_weight_quantity(title: str):
    t=norm(title)
    m=re.search(r'(\d+(?:\.\d+)?)\s*(kg|g)\s*[×xX]\s*(\d+)\s*(?:個|缶|袋|箱|パック|セット)?',t,re.I)
    if m:
        n=float(m[1])*(1000 if m[2].lower()=='kg' else 1); p=int(m[3]); return Quantity(n*p,'g',m[0],.99,p)
    m=re.search(r'(\d+(?:\.\d+)?)\s*(kg|g).{0,10}?(\d+)\s*(?:個|缶|袋|箱|パック)',t,re.I)
    if m and int(m[3])>1:
        n=float(m[1])*(1000 if m[2].lower()=='kg' else 1); p=int(m[3]); return Quantity(n*p,'g',m[0],.96,p)
    vals=[]
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(kg|g)',t,re.I):
        n=float(m[1])*(1000 if m[2].lower()=='kg' else 1); vals.append((n,m[0]))
    if vals:
        n,e=max(vals,key=lambda x:x[0]); return Quantity(n,'g',e,.89)
    return None

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

_BIG_PLUS_RE=re.compile(r'(?:big|ビッグ)\s*(?:サイズ)?\s*より\s*大きい|xxl\s*(?:サイズ)?', re.I)

def diaper_size_mentions(t: str) -> set[str]:
    k=norm(t).lower()
    found=set()
    if _BIG_PLUS_RE.search(k):
        found.add('big_plus')
        k=_BIG_PLUS_RE.sub(' ', k)
    if re.search(r'(?<![a-z0-9])(?:big|xl)\s*(?:サイズ)?(?![a-z0-9])', k, re.I) or 'ビッグサイズ' in k or re.search(r'ビッグ(?!\s*より\s*大きい)', k):
        found.add('big')
    if '新生児' in k or re.search(r'(?<![a-z0-9])nb\s*(?:サイズ)?(?![a-z0-9])', k, re.I):
        found.add('newborn')
    if re.search(r'(?<![a-z0-9])m\s*(?:はいはい|たっち)', k, re.I):
        found.add('m')
    for s in ('s','m','l'):
        if re.search(rf'(?<![a-z0-9]){s}\s*サイズ(?![a-z0-9])', k, re.I) or re.search(rf'(?<![a-z0-9]){s}(?![a-z0-9])', k, re.I):
            found.add(s)
    return found

def diaper_size(t):
    found=diaper_size_mentions(t)
    return next(iter(found)) if len(found)==1 else ''

def _diaper_selection_issue(title: str, supplemental_text: str='') -> str:
    title_types=diaper_type_mentions(title)
    title_sizes=diaper_size_mentions(title)
    if len(title_types)>1:
        return 'ambiguous_diaper_type'
    if len(title_sizes)>1:
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
    if any(x in low for x in ['介護','大人用','犬用','猫用','ペット用']): return None,'excluded_scope'
    maker,brand=identify_brand(t); attrs={}
    if parser=='diapers':
        issue=_diaper_selection_issue(t, supplemental_text)
        if issue: return None,issue
        type_mentions=diaper_type_mentions(t); size_mentions=diaper_size_mentions(t)
        exp_type=segment.get('type',''); exp_size=segment.get('size','')
        got_type=next(iter(type_mentions)) if len(type_mentions)==1 else ''
        got_size=next(iter(size_mentions)) if len(size_mentions)==1 else ''
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
        if any(x in t for x in ['手口','手・口','除菌','トイレに流せる','流せるタイプ']): return None,'excluded_wipes_variant'
        q=parse_piece_quantity(t); attrs={'variant':'standard'}
    elif parser=='formula':
        if 'ミルク' not in t and not brand: return None,'not_formula'
        if any(x in low for x in ['液体','フォローアップ','ぐんぐん','チルミル','ステップ','たっち','アレルギー','特殊ミルク','治療用']): return None,'excluded_formula_variant'
        q=parse_weight_quantity(t); attrs={'stage':'infant'}
    elif parser=='diaper_bags':
        if not (('おむつ' in t or 'オムツ' in t) and any(x in t for x in ['袋','バッグ','bag','BAG'])): return None,'not_diaper_bag'
        if any(x in t for x in ['カセット','ゴミ箱本体','本体のみ']): return None,'excluded_diaper_bag_variant'
        q=parse_piece_quantity(t)
    else: raise ValueError(parser)
    if not q: return None,'quantity_unparsed'
    return {'manufacturer':maker,'brand':brand,'attributes':attrs,'quantity':q.as_dict()},''

def parse_for_segment(title: str, parser: str, segment: dict, supplemental_text: str=''):
    parsed,_=parse_for_segment_detailed(title, parser, segment, supplemental_text=supplemental_text)
    return parsed

def unit_price(price_yen, metric, quantity):
    price=float(price_yen or 0); total=float(quantity.get('total') or 0)
    if price<=0 or total<=0: return None
    if metric=='per_piece' and quantity.get('base_unit')=='piece': return price/total
    if metric=='per_100g' and quantity.get('base_unit')=='g': return price/total*100
    return None
