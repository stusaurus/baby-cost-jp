// Offline browser QA for the new indexable tape-s tape purchase planner.
// No external retailer links or real analytics requests are made.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const {chromium,webkit} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const python = `
from datetime import datetime,timezone
from src.config import load_categories
from src.render import render_comparison,render_diaper_index
import json
cats=load_categories();cat=cats['diapers']
segment=next(s for s in cat['segments'] if s['id']=='tape-s')
def p(item, price, count):
  return dict(name=f'赤ちゃん用 テープ Sサイズ {count}枚',source_id=item,
      price_yen=price,unit_price=price/count,unit_metric='per_piece',
      quantity=dict(total=count,base_unit='piece',pack_count=1,
                    confidence=.99,evidence=f'{count}枚'),
      shipping_basis='rakuten_postage_filter',
      url='https://hb.afl.rakuten.co.jp/hgc/'+item,image='',
      brand='テスト用',manufacturer='テスト用',shop='テスト店舗',
      attributes={})
offers=[p('tape-s-74',2680,74),p('tape-s-248',6920,248)]
now=datetime(2026,11,22,tzinfo=timezone.utc)
print(json.dumps({'page':render_comparison(cats,'diapers',cat,segment,offers,now),
                  'hub':render_diaper_index(cats,now,{'tape-s':{'products':offers}})},ensure_ascii=False))
`;
const result=spawnSync('python',['-c',python],{encoding:'utf8'});
assert.equal(result.status,0,result.stderr);
const {page:html,hub:hubHtml}=JSON.parse(result.stdout);
assert(html.includes('id="purchase-planner"'));
assert(html.includes('テープSのおむつ何枚必要？'));
assert(hubHtml.includes('data-nav-source="diaper_index_tape_s_planner"'));
const source='https://stusaurus.github.io/baby-cost-jp/';
const base='/baby-cost-jp/';
const route=base+'diapers/tape/s/';
const hubRoute=base+'diapers/';
const folder=process.env.TAPE_S_QA_OUTPUT || 'tape-s-qa-evidence';
fs.mkdirSync(folder,{recursive:true});
const server=http.createServer((req,res)=>{
  const u=new URL(req.url,'http://localhost');
  const origin='http://127.0.0.1:'+server.address().port;
  if(u.pathname===route || u.pathname===hubRoute){
    res.setHeader('Content-Type','text/html; charset=utf-8');
    res.end((u.pathname===route ? html : hubHtml).replaceAll(source,origin+base));
    return;
  }
  if(u.pathname.startsWith(base+'static/')){
    const name=path.basename(u.pathname);
    const dir=path.resolve('src/static');
    const file=path.resolve(dir,name);
    if(!file.startsWith(dir+path.sep) || !fs.existsSync(file)){
      res.statusCode=404;res.end('not found');return;
    }
    res.setHeader('Content-Type',name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':'image/webp');
    res.end(fs.readFileSync(file));return;
  }
  res.statusCode=404;res.end('not found');
});
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const origin='http://127.0.0.1:'+server.address().port;
  const checked=[];
  try{
    for(const [engine,driver] of Object.entries({chromium,webkit})){
      const browser=await driver.launch({headless:true});
      try{
        for(const width of [320,390,1440]){
          const context=await browser.newContext({viewport:{width,height:900},locale:'ja-JP'});
          await context.route('**/*',request=>{
            const u=new URL(request.request().url());
            return u.origin===origin?request.continue():request.abort();
          });
          await context.addInitScript(()=>{
            window.__events=[];
            window.gtag=(...args)=>window.__events.push(args);
          });
          const p=await context.newPage();const errors=[];
          p.on('pageerror',e=>errors.push(e.message));
          await p.goto(origin+hubRoute,{waitUntil:'networkidle'});
          const entry=p.locator('a[data-nav-source="diaper_index_tape_s_planner"]');
          assert.equal(await entry.count(),1);
          assert.equal(await entry.getAttribute('href'),origin+route+'#purchase-planner');
          assert((await entry.evaluate(el=>el.getBoundingClientRect().height))>=44,engine+'/'+width+' hub touch target');
          assert((await p.evaluate(()=>document.documentElement.scrollWidth))<=width+1,engine+'/'+width+' hub overflow');
          await entry.click();
          await p.waitForURL('**/diapers/tape/s/#purchase-planner');
          assert.equal(await p.locator('meta[name="robots"]').getAttribute('content'),'index,follow');
          assert.equal(await p.locator('.product').count(),2);
          assert.equal(await p.locator('[data-purchase-planner]').count(),1);
          assert.equal(await p.locator('[data-purchase-daily]').inputValue(),'8');
          assert.equal(await p.locator('[data-purchase-days]').inputValue(),'14');
          assert.equal(await p.locator('[data-purchase-stock]').inputValue(),'0');
          assert.match(await p.locator('[data-purchase-summary]').innerText(),/不足112枚/);
          const assertSKU=async(id,sets,payment,surplus)=>{
            const card=p.locator('.product').filter({has:p.locator('[data-compare-id="'+id+'"]')});
            assert.equal(await card.locator('[data-plan-sets]').innerText(),sets+'セット');
            assert.equal(await card.locator('[data-plan-payment]').innerText(),'¥'+payment.toLocaleString('ja-JP'));
            assert.equal(await card.locator('[data-plan-surplus]').innerText(),surplus+'枚');
            const link=card.locator('.product-actions .cta');
            assert.match(await link.getAttribute('href'),/^https:\/\/hb\.afl\.rakuten\.co\.jp\/hgc\//);
            assert.match(await link.getAttribute('rel'),/nofollow sponsored noopener/);
            assert.equal(await link.getAttribute('data-size'),'s');
            assert.equal(await link.getAttribute('data-product-type'),'tape');
          };
          await assertSKU('tape-s-74',2,5360,36);
          await assertSKU('tape-s-248',1,6920,136);
          await p.locator('[data-purchase-stock]').fill('20');
          assert.match(await p.locator('[data-purchase-summary]').innerText(),/不足92枚/);
          await assertSKU('tape-s-74',2,5360,56);
          await assertSKU('tape-s-248',1,6920,156);
          await p.locator('[data-purchase-days-choice="7"]').click();
          assert.match(await p.locator('[data-purchase-summary]').innerText(),/不足36枚/);
          await assertSKU('tape-s-74',1,2680,38);
          await assertSKU('tape-s-248',1,6920,212);
          await p.locator('[data-usage="10"]').click();
          assert.match(await p.locator('[data-purchase-summary]').innerText(),/不足50枚/);
          await assertSKU('tape-s-74',1,2680,24);
          await p.locator('[data-purchase-stock]').fill('500');
          assert.match(await p.locator('[data-purchase-summary]').innerText(),/不足0枚/);
          assert.equal(await p.locator('[data-plan-payment]').count(),0);
          assert.equal(await p.locator('.product-actions .cta:visible').count(),0);
          await p.locator('[data-purchase-daily]').fill('1.5');
          assert.equal(await p.locator('[data-purchase-error]').isVisible(),true);
          assert.equal(await p.locator('[data-plan-payment]').count(),0);
          await p.locator('[data-purchase-daily]').fill('10');
          assert.equal(await p.locator('[data-purchase-error]').isVisible(),false);
          const scroll=await p.evaluate(()=>({screen:innerWidth,document:document.documentElement.scrollWidth}));
          assert(scroll.document<=scroll.screen+1,engine+'/'+width+' '+JSON.stringify(scroll));
          assert.deepEqual(errors,[]);
          const events=await p.evaluate(()=>window.__events);
          assert(!events.some(e=>['purchase','affiliate_click'].includes(e[1])));
          assert(!events.some(e=>e[2] && ['daily','days','stock','quantity','price','payment'].some(key=>Object.hasOwn(e[2],key))));
          if(width===390)await p.screenshot({path:path.join(folder,engine+'-390-tape-s.png'),fullPage:true});
          checked.push({engine,width,entry:true,correctMath:true,linksSafe:true,privacy:true,noOverflow:true});
          await context.close();
        }
      }finally{await browser.close();}
    }
    fs.writeFileSync(path.join(folder,'results.json'),JSON.stringify({success:true,checked},null,2));
    console.log('TAPE_S_QA '+JSON.stringify(checked));
  }finally{server.close();}
})().catch(error=>{console.error(error);process.exitCode=1;server.close();});
