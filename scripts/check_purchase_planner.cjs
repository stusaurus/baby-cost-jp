// Read-only published-snapshot QA. Network analytics and purchase navigation are blocked.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {spawnSync}=require('node:child_process');
const assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base='https://stusaurus.github.io/baby-cost-jp/',route='diapers/pants/m/';
const output=process.env.PURCHASE_QA_OUTPUT||'purchase-planner-evidence';
async function published(file){
 if(process.env.PUBLISHED_SITE_DIR)return fs.readFileSync(path.join(process.env.PUBLISHED_SITE_DIR,file),'utf8');
 const r=await fetch(base+file);assert.equal(r.status,200);return r.text();
}
const money=n=>'¥'+n.toLocaleString('ja-JP');
(async()=>{
 fs.mkdirSync(output,{recursive:true});
 const original=await published(route+'index.html');
 const snapshot=JSON.parse(await published('data/latest.json'));
 assert.equal(snapshot.pricing_scope,'rakuten_postage_included_or_free_shipping');
 const originalDOM=new JSDOM(original),doc=originalDOM.window.document;
 const catalog=snapshot.categories['pants-m'].products;
 assert(catalog.length>=2);
 const buttons=[...doc.querySelectorAll('[data-compare-add]')];
 assert.equal(buttons.length,catalog.length);
 const products=catalog.map((p,i)=>{
  const b=buttons[i];assert.equal(b.dataset.compareId,p.source_id);
  assert.equal(Number(b.dataset.comparePrice),p.price_yen);
  assert.equal(b.dataset.compareUrl,p.affiliate_url);
  assert.equal(Number(b.dataset.compareUnit),p.unit_price);
  assert.equal(b.closest('.product').dataset.sortQuantity,Number(p.quantity.total).toFixed(6));
  // Pre-STEP81 published snapshots have a declared filtered-query scope but no
  // per-product field. That explicit historical provenance is used ONLY in QA.
  // Unknown provenance in application data is never filled by the calculator.
  return {...p,url:p.affiliate_url,image:b.dataset.compareImage,
   shipping_basis:Object.hasOwn(p,'shipping_basis')?p.shipping_basis:'rakuten_postage_filter'};
 });
 const imageCache=new Map();
 await Promise.all(products.map(async p=>{if(!p.image)return;try{const r=await fetch(p.image,{signal:AbortSignal.timeout(15000)});if(r.ok)imageCache.set(p.image,{body:Buffer.from(await r.arrayBuffer()),contentType:r.headers.get('content-type')||'image/jpeg'})}catch(_){}}));
 const render=spawnSync('python',['scripts/render_purchase_preview.py'],{input:JSON.stringify({products,generated_at:snapshot.generated_at}),encoding:'utf8'});
 assert.equal(render.status,0,render.stderr);
 const after=render.stdout,newDOM=new JSDOM(after);
 const seo=d=>({title:d.title,description:d.querySelector('meta[name=description]').content,
  canonical:d.querySelector('link[rel=canonical]').href,robots:d.querySelector('meta[name=robots]').content,
  h1:d.querySelector('h1').textContent,jsonld:[...d.querySelectorAll('script[type="application/ld+json"]')].map(x=>JSON.parse(x.textContent))});
 assert.deepEqual(seo(newDOM.window.document),seo(doc));
 const catalogDOM=d=>[...d.querySelectorAll('[data-compare-add]')].map(x=>({...x.dataset}));
 assert.deepEqual(catalogDOM(newDOM.window.document),catalogDOM(doc));
 fs.writeFileSync(output+'/before.html',original);fs.writeFileSync(output+'/after.html',after);
 const server=http.createServer((req,res)=>{
  const u=new URL(req.url,'http://localhost');let body,type='text/html; charset=utf-8';
  if(u.pathname==='/before/')body=original.replace(/<script\b[^>]*src=[^>]*><\/script>/g,'');
  else if(u.pathname==='/baby-cost-jp/'+route)body=after;
  else if(u.pathname.startsWith('/baby-cost-jp/static/')){
   const name=path.basename(u.pathname);const file=path.join('src/static',name);
   if(!fs.existsSync(file)){res.writeHead(404);res.end();return;}
   body=fs.readFileSync(file);type=name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':'image/webp';
  }else{
   const file=path.resolve('site','.'+u.pathname.replace('/baby-cost-jp','')+(u.pathname.endsWith('/')?'index.html':''));
   if(!file.startsWith(path.resolve('site')+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
   body=fs.readFileSync(file,'utf8');
  }
  if(typeof body==='string')body=body.replaceAll(base,origin+'/baby-cost-jp/');
  res.setHeader('Content-Type',type);res.end(body);
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin='http://127.0.0.1:'+server.address().port,url=origin+'/baby-cost-jp/'+route;
 const records=[];
 try{
  for(const [engine,type] of Object.entries({chromium,webkit})){
   const browser=await type.launch({headless:true});
   try{for(const width of [320,390,1440]){
    const context=await browser.newContext({viewport:{width,height:900},locale:'ja-JP'});
    // Only local content is served; synthetic events cannot reach GA4/Rakuten.
    await context.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():imageCache.has(r.request().url())?r.fulfill(imageCache.get(r.request().url())):r.abort());
    await context.addInitScript(()=>{window.__events=[];window.gtag=(...args)=>window.__events.push(args)});
    const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(origin+'/before/',{waitUntil:'networkidle'});
    await page.locator('.products').scrollIntoViewIfNeeded();await page.screenshot({path:output+'/'+engine+'-'+width+'-before.png'});
    await page.goto(url+'?test=1',{waitUntil:'networkidle'});
    assert.match(await page.locator('[data-purchase-summary]').innerText(),/必要150枚/);
    assert.equal(await page.locator('[data-purchase-product]').count(),products.length);
    async function verify(daily,days,sizeDays=null){
     const actual=await page.locator('.product').evaluateAll(xs=>xs.map(x=>({id:x.querySelector('[data-compare-id]').dataset.compareId,
      sets:x.querySelector('[data-plan-sets]')?.textContent,payment:x.querySelector('[data-plan-payment]')?.textContent,
      surplus:x.querySelector('[data-plan-surplus]')?.textContent,warning:x.querySelector('.purchase-warning')?.textContent||''})));
     for(const a of actual){const p=products.find(p=>p.source_id===a.id);
      const sets=Math.ceil(daily*days/p.quantity.total),surplus=sets*p.quantity.total-daily*days;
      assert.equal(a.sets,sets.toLocaleString('ja-JP')+'セット');assert.equal(a.payment,money(sets*p.price_yen));
      assert.equal(a.surplus,surplus.toLocaleString('ja-JP')+'枚');
      if(sizeDays!==null&&sets*p.quantity.total>daily*sizeDays)assert(a.warning.includes((sets*p.quantity.total-daily*sizeDays).toLocaleString('ja-JP')+'枚'));
     }
    }
    await verify(5,30);
    await page.locator('[data-purchase-planner]').evaluate(el=>el.scrollIntoView({block:'start'}));await page.locator('[data-purchase-planner]').screenshot({path:output+'/'+engine+'-'+width+'-planner.png'});
    await page.locator('[data-usage="8"]').click();await verify(8,30);
    await page.locator('[data-purchase-days-choice="7"]').click();await verify(8,7);
    await page.locator('[data-purchase-daily]').fill('7');await page.locator('[data-purchase-days]').fill('14');await verify(7,14);
    await page.locator('.purchase-size summary').click();await page.locator('[data-purchase-size-days]').fill('7');await verify(7,14,7);
    await page.locator('.product').first().scrollIntoViewIfNeeded();await page.locator('.product').first().screenshot({path:output+'/'+engine+'-'+width+'-product.png'});
    for(const value of ['','0','1.5','31']){await page.locator('[data-purchase-daily]').fill(value);assert.equal(await page.locator('[data-plan-payment]').count(),0);assert(await page.locator('[data-purchase-error]').isVisible())}
    await page.locator('[data-purchase-daily]').fill('5');await page.locator('[data-purchase-size-days]').fill('');await verify(5,14);
    const first=page.locator('[data-purchase-product]').first(),raw=await first.getAttribute('data-purchase-product');
    await first.evaluate(el=>el.dataset.purchaseProduct='null');await page.locator('[data-purchase-days]').fill('7');assert.equal(await first.locator('[data-plan-payment]').count(),0);
    await first.evaluate((el,raw)=>el.dataset.purchaseProduct=raw,raw);await page.locator('[data-purchase-days]').fill('30');await verify(5,30);
    await page.locator('[data-sort-mode=price]').click();assert.match(await page.locator('[data-result-sort-label]').innerText(),/1セット/);await verify(5,30);
    await page.locator('[data-sort-mode=quantity]').click();await verify(5,30);await page.locator('[data-sort-mode=unit]').click();
    await page.locator('[data-save-id]').first().click();await page.locator('[data-saved-only]').click();assert.equal(await page.locator('.product:visible').count(),1);await page.locator('[data-saved-only]').click();
    for(let i=0;i<3;i++)await page.locator('[data-compare-add]').nth(i).click();
    await page.locator('[data-compare-open]').click();assert.equal(await page.locator('.compare-column').count(),3);
    assert.equal(await page.locator('.compare-column [data-plan-payment]').first().textContent(),money(Math.ceil(150/products[0].quantity.total)*products[0].price_yen));
    await page.locator('.compare-column .purchase-card').first().scrollIntoViewIfNeeded();
    await page.screenshot({path:output+'/'+engine+'-'+width+'-tray.png'});
    await page.locator('[data-compare-share]').click();const link=await page.locator('[data-compare-share-url]').inputValue();assert(new URL(link).hash.startsWith('#compare='));
    assert.equal(new URL(link).search,'');assert(!link.includes('daily')&&!link.includes('sizeDays'));
    await page.locator('.compare-buy').first().evaluate(el=>{el.addEventListener('click',e=>e.preventDefault());el.click()});
    const sent=await page.evaluate(()=>window.__events);
    assert(sent.some(x=>x[1]==='purchase_planner_use'&&x[2].operator_test==='1'));
    assert.equal(sent.filter(x=>x[1]==='affiliate_click'&&x[2].operator_test==='1').length,1);assert(!sent.some(x=>x[1]==='purchase'));
    assert(!sent.filter(x=>x[1]==='purchase_planner_use').some(x=>'daily'in x[2]||'days'in x[2]||'value'in x[2]));
    await page.locator('.compare-close').click();
    await page.locator('#condition-change summary').click();await page.locator('[data-value=tape]').click();
    assert.equal(await page.locator('.size-chip').first().getAttribute('data-value'),'newborn');
    await page.locator('#diaper-go').click();await page.waitForURL('**/diapers/tape/newborn/');assert.equal(await page.locator('[data-purchase-planner]').count(),0);
    await page.goto(url+'?test=1'+new URL(link).hash,{waitUntil:'networkidle'});assert(await page.locator('[data-compare-modal]').isVisible());
    assert.equal(await page.locator('.compare-column').count(),3);assert.equal(await page.locator('.compare-column [data-plan-payment]').count(),3);
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2);assert.equal(overflow,false);assert.deepEqual(errors,[]);
    records.push({engine,width,products:products.length,overflow,errors,calculations:true,invalidCleared:true,sortingSavingAndTray:true,selector:true,attribution:true});
    await context.close();
   }}finally{await browser.close()}
  }
  if(process.env.LIGHTHOUSE_MODULE){
   const {default:lighthouse}=await import(process.env.LIGHTHOUSE_MODULE);
   const {launch}=await import(process.env.CHROME_LAUNCHER_MODULE);
   const chrome=await launch({chromePath:chromium.executablePath(),chromeFlags:['--headless','--no-sandbox']});
   try{for(const formFactor of ['mobile','desktop']){
    const settings=formFactor==='desktop'?{formFactor:'desktop',screenEmulation:{mobile:false,width:1440,height:900,deviceScaleFactor:1,disabled:false}}:{};
    const report=await lighthouse(url+'?test=1',{port:chrome.port,output:'json',logLevel:'error',onlyCategories:['performance','accessibility','best-practices','seo'],blockedUrlPatterns:['*google-analytics.com*','*googletagmanager.com*','*analytics.google.com*'],...settings});
    fs.writeFileSync(output+'/lighthouse-'+formFactor+'.json',report.report);records.push({lighthouse:formFactor,scores:Object.fromEntries(Object.entries(report.lhr.categories).map(([k,v])=>[k,v.score]))});
    assert(report.lhr.categories.seo.score>=.9);assert(report.lhr.categories.accessibility.score>=.9);
   }}finally{await chrome.kill()}
  }
  const result={publishedUrl:base+route,snapshotGeneratedAt:snapshot.generated_at,historicalQueryScope:snapshot.pricing_scope,productImagesCached:imageCache.size,seoAndCatalogUnchanged:true,records};
  fs.writeFileSync(output+'/report.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{server.close();originalDOM.window.close();newDOM.window.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
