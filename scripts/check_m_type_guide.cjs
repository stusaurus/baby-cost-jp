// Offline full-bundle M tape vs pants discovery and reader journey.
// Synthetic catalogs only; analytics, retailers and other origins blocked.
const assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process');
const http=require('node:http');
const fs=require('node:fs');
const path=require('node:path');
const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const source='https://stusaurus.github.io/baby-cost-jp/';
const base='/baby-cost-jp/';
const out=process.env.M_TYPE_GUIDE_QA_OUTPUT||'m-type-guide-qa-evidence';
fs.mkdirSync(out,{recursive:true});

const fixturePython = `
from datetime import datetime, timezone
import json
from src.config import load_categories
from src.render import render_diaper_index, render_comparison
from src.type_guide import render_m_diaper_type_guide
categories=load_categories()
segment_map={s['id']:s for s in categories['diapers']['segments']}
now=datetime(2026,11,23,22,0,tzinfo=timezone.utc)
def product(id,n,price,type):
 return dict(source_id='fixture:'+id,name=f'赤ちゃん用 {type} Mサイズ {n}枚',
             price_yen=price,unit_price=price/n,unit_metric='per_piece',
             quantity=dict(total=n,base_unit='piece',confidence=.99,
                           evidence=f'{n}枚',pack_count=1),
             shipping_basis='rakuten_postage_filter',
             url=('https://hb.afl.rakuten.co.jp/hgc/'+id+'/?'
                  'pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ffixture%2F'+id+'%2F'
                  '&m=http%3A%2F%2Fm.rakuten.co.jp%2Ffixture%2Fi%2F'+id+'%2F'),
             image='',brand='テスト用',manufacturer='テスト用',shop='テスト用店舗',attributes={})
snapshots={
 'tape-m': {'products':[product('tape-74',74,2680,'テープ'),
                        product('tape-248',248,6920,'テープ')]},
 'pants-m': {'products':[product('pants-50',50,2100,'パンツ'),
                         product('pants-180',180,6100,'パンツ')]}
}
pages={
  'diapers/':render_diaper_index(categories,now,snapshots),
  'guides/m-diapers-tape-vs-pants/':render_m_diaper_type_guide(snapshots,now),
}
for key,kind in [('tape-m','tape'),('pants-m','pants')]:
 pages[f'diapers/{kind}/m/']=render_comparison(
  categories,'diapers',categories['diapers'],segment_map[key],
  snapshots[key]['products'],now)
print(json.dumps(pages,ensure_ascii=False))
`;
const generated=spawnSync('python',['-c',fixturePython],{encoding:'utf8',maxBuffer:6*1024*1024});
assert.equal(generated.status,0,generated.stderr);
const pages=JSON.parse(generated.stdout);
const guideRoute='guides/m-diapers-tape-vs-pants/';

const server=http.createServer((req,res)=>{
 const u=new URL(req.url,'http://127.0.0.1');
 const origin='http://127.0.0.1:'+server.address().port;
 if(!u.pathname.startsWith(base)){res.writeHead(404);res.end();return;}
 const suffix=u.pathname.slice(base.length);
 if(Object.hasOwn(pages,suffix)){
  res.setHeader('Content-Type','text/html; charset=utf-8');
  res.end(pages[suffix].replaceAll(source,origin+base));return;
 }
 if(suffix.startsWith('static/')){
  const allowed=new Set(['styles.css','app.js','purchase.js','analytics.js','m_type_planner.js']);
  const name=path.basename(suffix);
  if(!allowed.has(name)){res.writeHead(404);res.end();return;}
  const file=path.resolve('src/static',name);
  res.setHeader('Content-Type',file.endsWith('.css')?'text/css':'text/javascript');
  res.end(fs.readFileSync(file));return;
 }
 res.writeHead(404);res.end();
});

(async()=>{
 await new Promise(done=>server.listen(0,'127.0.0.1',done));
 const origin='http://127.0.0.1:'+server.address().port;
 const observations=[];
 try{
  for(const [engine,driver] of Object.entries({chromium,webkit})){
   const browser=await driver.launch({headless:true});
   try{
    for(const width of [320,390,1440]){
     const context=await browser.newContext({viewport:{width,height:860},locale:'ja-JP'});
     await context.route('**/*',request=>new URL(request.request().url()).origin===origin?request.continue():request.abort());
     const page=await context.newPage();
     await page.addInitScript(() => {
       // Capture GA events offline; never send the user's data to GA.
       window.dataLayer = [];
       window.gtag = (...args) => window.dataLayer.push(args);
     });
     const events=()=>page.evaluate(()=>Array.from(window.dataLayer||[])
       .filter(row=>row[0]==='event').map(row=>({name:row[1],data:row[2]})));
     const errors=[];page.on('pageerror',e=>errors.push(e.message));
     await page.goto(origin+base+'diapers/',{waitUntil:'networkidle'});
     const route=page.locator('[data-nav-source="diaper_index_m_type_guide"]');
     assert.equal(await route.count(),1);
     assert((await route.evaluate(el=>el.getBoundingClientRect().height))>=44,engine+'/'+width+' hub tap');
     await route.click();
     await page.waitForURL('**/'+guideRoute);
     assert.equal(await page.locator('meta[name="robots"]').getAttribute('content'),'index,follow');
     assert.equal(await page.locator('.m-type-table tbody tr').count(),3);
     assert.equal(await page.locator('.m-type-table').innerText().then(s=>s.includes('¥5,360')),true);
     assert.equal(await page.locator('.m-type-table').innerText().then(s=>s.includes('¥4,200')),true);
     assert.equal(await page.locator('.m-type-table').innerText().then(s=>s.includes('¥6,920')),true);
     assert.equal(await page.locator('.m-type-scroll').getAttribute('tabindex'),'0');
     const daily=page.locator('[data-m-type-input="daily"]');
     const days=page.locator('[data-m-type-input="days"]');
     const tapeStock=page.locator('[data-m-type-input="tape-stock"]');
     const pantsStock=page.locator('[data-m-type-input="pants-stock"]');
     const payment=type=>page.locator('[data-m-type-card="'+type+'"] [data-m-type-field="payment"]');
     assert.equal(await daily.inputValue(),'6');
     assert.equal(await days.inputValue(),'14');
     assert.equal(await payment('tape').innerText(),'¥5,360');
     assert.equal(await payment('pants').innerText(),'¥4,200');
     const buy=type=>page.locator('[data-m-type-card="'+type+'"] [data-m-type-buy]');
     assert.equal(await buy('tape').isVisible(),true);
     assert.equal(await buy('pants').isVisible(),true);
     assert.equal(await buy('tape').getAttribute('data-product-id'),'fixture:tape-74');
     assert.equal(await buy('pants').getAttribute('data-product-id'),'fixture:pants-50');
     assert.equal(await buy('tape').getAttribute('target'),'_blank');
     assert((await buy('tape').getAttribute('rel')).includes('sponsored'));
     assert((await buy('tape').getAttribute('href')).includes('/hgc/tape-74/'));
     assert((await buy('pants').getAttribute('href')).includes('/hgc/pants-50/'));
     assert.equal(await buy('pants').getAttribute('data-click-position'),'m_type_personal_result');
     assert.equal((await events()).filter(e=>e.name==='purchase_planner_use').length,0);
     // Link should count as exactly one affiliate click even after navigation
     // from the diaper index. Preserve its original journey separately.
     await page.evaluate(()=>document.addEventListener('click',e=>{
       if(e.target.closest?.('[data-m-type-buy]'))e.preventDefault();
     },true));
     await buy('tape').click();
     const clicks=(await events()).filter(e=>e.name==='affiliate_click');
     assert.equal(clicks.length,1);
     assert.equal(clicks[0].data.conversion_source,'m_type_personal_planner');
     assert.equal(clicks[0].data.journey_origin,'diaper_index_m_type_guide');
     assert.equal(clicks[0].data.product_id,'fixture:tape-74');
     assert.equal(clicks[0].data.click_position,'m_type_personal_result');
     assert.equal((await events()).filter(e=>e.name==='product_result_click').length,1);
     await tapeStock.fill('84');
     assert.equal(await payment('tape').innerText(),'¥0');
     assert.equal(await payment('pants').innerText(),'¥4,200');
     assert.equal(await buy('tape').isVisible(),false);
     assert.equal(await buy('tape').getAttribute('href'),null);
     assert.equal(await buy('pants').isVisible(),true);
     assert.equal(await page.locator('[data-m-type-field="stock-note"]').innerText()
       .then(s=>s.includes('手持ち枚数が異なる')),true);
     await tapeStock.fill('0');
     await pantsStock.fill('84');
     assert.equal(await payment('pants').innerText(),'¥0');
     assert.equal(await buy('pants').isVisible(),false);
     assert.equal(await buy('pants').getAttribute('href'),null);
     await pantsStock.fill('0');
     await page.locator('[data-m-type-days-choice="30"]').click();
     assert.equal(await days.inputValue(),'30');
     const uses=(await events()).filter(e=>e.name==='purchase_planner_use');
     assert(uses.length>=1);
     const latestUse=uses.at(-1).data;
     assert.equal(latestUse.conversion_source,'m_type_personal_planner');
     assert.equal(latestUse.action,'days_preset');
     assert.equal(latestUse.category_id,'diapers');
     assert.equal(latestUse.size,'m');
     assert.equal(latestUse.stock,undefined);
     assert.equal(latestUse.days,undefined);
     assert.equal(latestUse.payment,undefined);
     assert.equal(await payment('tape').innerText(),'¥6,920');
     assert.equal(await payment('pants').innerText(),'¥6,100');
     assert.equal(await buy('tape').getAttribute('data-product-id'),'fixture:tape-248');
     assert.equal(await buy('pants').getAttribute('data-product-id'),'fixture:pants-180');
     assert((await buy('tape').getAttribute('href')).includes('/hgc/tape-248/'));
     assert((await buy('pants').getAttribute('href')).includes('/hgc/pants-180/'));
     await daily.fill('0');
     assert.equal(await page.locator('[data-m-type-error]').isVisible(),true);
     assert.equal(await page.locator('[data-m-type-live]').isVisible(),false);
     assert.equal(await buy('tape').getAttribute('href'),null);
     assert.equal(await buy('pants').getAttribute('href'),null);
     await daily.fill('6');
     await page.locator('[data-m-type-days-choice="14"]').click();
     assert.equal(await payment('tape').innerText(),'¥5,360');
     assert.equal(await page.locator('[data-nav-source="m_type_tape_planner"]').count(),1);
     assert.equal(await page.locator('[data-nav-source="m_type_pants_planner"]').count(),1);
     assert((await page.evaluate(()=>document.documentElement.scrollWidth))<=width+1,engine+'/'+width+' guide overflow');
     if(width===390)await page.screenshot({path:path.join(out,engine+'-390-m-type-guide.png'),fullPage:true});
     for(const type of ['tape','pants']){
      await page.goto(origin+base+guideRoute,{waitUntil:'networkidle'});
      const cta=page.locator('[data-nav-source="m_type_'+type+'_planner"]');
      assert((await cta.evaluate(el=>el.getBoundingClientRect().height))>=44,engine+'/'+width+' '+type+' tap');
      await cta.click();
      await page.waitForURL('**/diapers/'+type+'/m/#purchase-planner');
      assert.equal(await page.locator('#purchase-planner').count(),1);
      assert.equal(await page.locator('[data-purchase-days]').inputValue(),type==='tape'?'14':'30');
      assert.equal(await page.locator('[data-nav-source="m_type_guide_from_comparison"]').count(),1);
      assert((await page.evaluate(()=>document.documentElement.scrollWidth))<=width+1,engine+'/'+width+'/'+type+' overflow');
     }
     assert.deepEqual(errors,[],engine+'/'+width+' page errors');
     observations.push({engine,width,mHub:true,guideIndexable:true,threeScenarios:true,personalizedPlanner:true,exactProductAffiliate:true,correctGA4Source:true,interactionOnlyEvent:true,noBuyLinkSuppressed:true,independentStock:true,invalidInputBlocked:true,twoPlannerLinks:true,noOverflow:true,noPageErrors:true});
     await context.close();
    }
   }finally{await browser.close();}
  }
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({success:true,observations},null,2));
  console.log('M_TYPE_GUIDE_QA '+JSON.stringify(observations));
 }finally{server.close();}
})().catch(err=>{console.error(err);process.exitCode=1;server.close();});
