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

def diaper_type(t):
    k=norm(t).lower()
    if 'パンツ' in k or 'pants' in k: return 'pants'
    if 'テープ' in k or 'tape' in k: return 'tape'
    return ''

def diaper_size(t):
    k=norm(t).lower()
    if 'bigより大きい' in k or 'ビッグより大きい' in k or re.search(r'\bxxl\b',k): return 'big_plus'
    if 'mはいはい' in k or 'm はいはい' in k or 'はいはい用' in k: return 'm'
    if 'mたっち' in k or 'm たっち' in k or 'たっち用' in k: return 'm'
    if re.search(r'(?:^|[^a-z])(?:big|ビッグ)(?:[^a-z]|$)',k) or re.search(r'\bxl\b',k): return 'big'
    if '新生児' in k or re.search(r'\bnb\b',k): return 'newborn'
    for s in ('s','m','l'):
        if re.search(rf'(?:^|[\s・/／,(（]){s}(?:サイズ)?(?:$|[\s・/／,)）])',k,re.I) or f'{s}サイズ' in k: return s
    return ''

def parse_for_segment(title: str, parser: str, segment: dict):
    t=norm(title); low=t.lower()
    if any(x in low for x in ['介護','大人用','犬用','猫用','ペット用']): return None
    maker,brand=identify_brand(t); attrs={}
    if parser=='diapers':
        got_type=diaper_type(t); exp_type=segment.get('type',''); exp_size=segment.get('size','')
        if not got_type and exp_type=='tape' and exp_size=='newborn': got_type='tape'
        got_size=diaper_size(t)
        if got_type!=exp_type or got_size!=exp_size: return None
        q=parse_piece_quantity(t)
        stage='はいはい' if 'はいはい' in t else ('たっち' if 'たっち' in t else '')
        attrs={'type':got_type,'size':got_size,'fit_stage':stage}
    elif parser=='wipes':
        if 'おしりふき' not in t and 'おしり拭き' not in t: return None
        if any(x in t for x in ['手口','手・口','除菌','トイレに流せる','流せるタイプ']): return None
        q=parse_piece_quantity(t); attrs={'variant':'standard'}
    elif parser=='formula':
        if 'ミルク' not in t and not brand: return None
        if any(x in low for x in ['液体','フォローアップ','ぐんぐん','チルミル','ステップ','たっち','アレルギー','特殊ミルク','治療用']): return None
        q=parse_weight_quantity(t); attrs={'stage':'infant'}
    elif parser=='diaper_bags':
        if not (('おむつ' in t or 'オムツ' in t) and any(x in t for x in ['袋','バッグ','bag','BAG'])): return None
        if any(x in t for x in ['カセット','ゴミ箱本体','本体のみ']): return None
        q=parse_piece_quantity(t)
    else: raise ValueError(parser)
    if not q: return None
    return {'manufacturer':maker,'brand':brand,'attributes':attrs,'quantity':q.as_dict()}

def unit_price(price_yen, metric, quantity):
    price=float(price_yen or 0); total=float(quantity.get('total') or 0)
    if price<=0 or total<=0: return None
    if metric=='per_piece' and quantity.get('base_unit')=='piece': return price/total
    if metric=='per_100g' and quantity.get('base_unit')=='g': return price/total*100
    return None
