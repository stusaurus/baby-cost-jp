"""Fail before deployment when discovery, links or live product quality break."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import math
import xml.etree.ElementTree as ET

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.canonical=[]; self.robots=''; self.links=[]; self.ids=set(); self.h1=0; self.json_blocks=[]; self.in_json=False
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get('id'): self.ids.add(a['id'])
        if tag=='h1': self.h1+=1
        if tag=='link' and a.get('rel')=='canonical': self.canonical.append(a.get('href'))
        if tag=='meta' and a.get('name')=='robots': self.robots=a.get('content','')
        if tag=='a' and a.get('href'): self.links.append(a['href'])
        if tag=='script' and a.get('type')=='application/ld+json': self.in_json=True
    def handle_endtag(self, tag):
        if tag=='script': self.in_json=False
    def handle_data(self, data):
        if self.in_json: self.json_blocks.append(json.loads(data))

def inspect_pages(site, site_url):
    result={}; errors=[]
    for path in site.rglob('*.html'):
        if path.name=='404.html' or path.name.startswith('google'): continue
        page=Page(path.read_text()); rel=path.relative_to(site).as_posix()
        url=site_url+('' if rel=='index.html' else rel[:-10] if rel.endswith('/index.html') else rel)
        result[url]=page
        if page.canonical!=[url]: errors.append(f'canonical: {rel}')
        if page.h1!=1: errors.append(f'H1: {rel}')
        if not page.json_blocks: errors.append(f'structured data: {rel}')
    for url,page in result.items():
        for link in page.links:
            if link.startswith('#'): target=url; fragment=link[1:]
            elif link.startswith(site_url): target=link.split('#')[0].split('?')[0]; fragment=urlsplit(link).fragment
            else: continue
            if target not in result: errors.append(f'broken internal link: {url} -> {link}')
            elif fragment and unquote(fragment) not in result[target].ids: errors.append(f'broken anchor: {url} -> {link}')
    return result, errors

def validate(site=Path('site'), previous=None, fixture=False):
    latest=json.loads((site/'data/latest.json').read_text()); base=latest['site_url']
    pages, errors=inspect_pages(site,base)
    ns='{http://www.sitemaps.org/schemas/sitemap/0.9}'
    urls=[n.text for n in ET.parse(site/'sitemap.xml').getroot().findall(f'{ns}url/{ns}loc')]
    expected={u for u,p in pages.items() if 'noindex' not in p.robots}
    if set(urls)!=expected or len(urls)!=len(set(urls)): errors.append('sitemap/indexable page mismatch')
    if f'Sitemap: {base}sitemap.xml' not in (site/'robots.txt').read_text(): errors.append('robots sitemap declaration')
    for required in ('','diapers/','method/'):
        if base+required not in pages: errors.append(f'missing page: {required}')
    category_counts={}
    from src.parsing import unit_price, parse_for_segment_detailed
    from src.config import load_categories
    categories=load_categories()
    for cid,category in categories.items():
        for seg in category['segments']:
            sid=seg['id']; row=latest['categories'].get(sid)
            if row is None: errors.append(f'missing segment: {sid}'); continue
            products=row['products']; category_counts[cid]=category_counts.get(cid,0)+len(products)
            old=((previous or {}).get('categories') or {}).get(sid,{}).get('products',[])
            if not fixture and len(old)>=2 and not products: errors.append(f'empty previously populated segment: {sid}')
            if not fixture and len(old)>=5 and len(products)<len(old)*.4: errors.append(f'sharp product count drop: {sid}')
            for p in products:
                calculated=unit_price(p['price_yen'],p['unit_metric'],p['quantity'])
                if calculated is None or not math.isfinite(p['unit_price']) or abs(calculated-p['unit_price'])>.00011: errors.append(f'unit calculation: {sid}/{p["source_id"]}')
                bounds=(.1,100) if cid=='wipes' else (50,5000) if cid=='formula' else (1,1000)
                if not bounds[0]<=p['unit_price']<=bounds[1]: errors.append(f'abnormal unit price: {sid}/{p["source_id"]}')
                parsed,reason=parse_for_segment_detailed(p['name'],category['parser'],seg)
                if not parsed: errors.append(f'classification: {sid}/{reason}')
                link=urlsplit(p['affiliate_url'])
                if not fixture and not (link.scheme=='https' and link.hostname=='hb.afl.rakuten.co.jp' and '/hgc/' in link.path): errors.append(f'affiliate URL: {sid}/{p["source_id"]}')
    if not fixture:
        for cid,count in category_counts.items():
            if count<2: errors.append(f'category has fewer than two products: {cid}')
    if errors: raise RuntimeError('\n'.join(errors))
    print(f'QUALITY_GATE passed: {len(pages)} pages, {len(urls)} indexable URLs; counts={category_counts}')
    return len(pages)

if __name__=='__main__':
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    validate(fixture='--fixture' in sys.argv)
