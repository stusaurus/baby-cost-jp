// Exercise the new controls against the published, independently accepted catalog.
// This preview never fetches Rakuten, publishes a page, or follows a purchase link.
const fs=require('node:fs'), http=require('node:http'), path=require('node:path');
const assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const publicBase='https://stusaurus.github.io/baby-cost-jp/';
const route='diapers/pants/m/';
const output='shared-comparison-evidence';
const block=['*google-analytics.com*','*googletagmanager.com*','*analytics.google.com*'];
(async()=>{
 fs.mkdirSync(output,{recursive:true});
 const response=await fetch(publicBase+route);assert.equal(response.status,200);
 const original=await response.text();
 const source=new JSDOM(original), preview=new JSDOM(fs.readFileSync('site/'+route+'index.html','utf8'));
 const before=source.window.document, injected=preview.window.document;
 assert.equal(before.querySelector('link[rel=canonical]').href,publicBase+route);
 const data=doc=>[...doc.querySelectorAll('[data-compare-add]')].map(x=>({...x.dataset}));
 const catalog=data(before);assert(catalog.length>=2);
 const meta=doc=>[doc.title,doc.querySelector('meta[name=description]').content,doc.querySelector('h1').textContent];
 const oldMeta=meta(before);
 before.querySelector('[data-compare-modal]').replaceWith(before.importNode(injected.querySelector('[data-compare-modal]'),true));
 before.querySelector('[data-comparison]').append(before.importNode(injected.querySelector('[data-compare-import-status]'),true));
 assert.deepEqual(data(before),catalog);assert.deepEqual(meta(before),oldMeta);
 const server=http.createServer((req,res)=>{
  const u=new URL(req.url,'http://localhost');
  if(u.pathname==='/baby-cost-jp/'+route){res.setHeader('Content-Type','text/html; charset=utf-8');res.end(source.serialize().replaceAll(publicBase,origin+'/baby-cost-jp/'));return;}
  const name=u.pathname.replace('/baby-cost-jp/static/','');
  if(['app.js','analytics.js','styles.css','shop-mobile.webp','shop-wide.webp'].includes(name)){
   res.setHeader('Content-Type',name.endsWith('.js')?'application/javascript':name.endsWith('.css')?'text/css':'image/webp');res.end(fs.readFileSync(path.join('src/static',name)));return;
  }
  res.writeHead(404);res.end();
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const origin='http://127.0.0.1:'+server.address().port;
 const url=origin+'/baby-cost-jp/'+route;
 const browser=await chromium.launch({headless:true});
 const records=[];
 try {
  for(const width of [320,390,1440]){
   const context=await browser.newContext({viewport:{width,height:900},locale:'ja-JP'});
   await context.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com/,r=>r.abort());
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(url+'?test=1',{waitUntil:'networkidle'});
   assert.equal(await page.locator('[data-compare-share]').count(),1);
   await page.locator('[data-compare-add]').nth(0).click();await page.locator('[data-compare-add]').nth(1).click();
   await page.locator('[data-compare-open]').click();
   await page.locator('[data-compare-share]').click();
   const link=await page.locator('[data-compare-share-url]').inputValue();
   assert.equal(new URL(link).search,'');assert(link.includes('#compare='));
   const actual=await page.locator('.compare-buy').evaluateAll(xs=>xs.map(x=>({href:x.href,unit:x.dataset.unitPrice})));
   assert.equal(actual.length,2);assert(actual.every(x=>new URL(x.href).hostname==='hb.afl.rakuten.co.jp'));
   await page.screenshot({path:output+'/share-'+width+'.png'});
   const other=await browser.newContext({viewport:{width,height:900},locale:'ja-JP'});
   await other.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com/,r=>r.abort());
   const opened=await other.newPage();opened.on('pageerror',e=>errors.push(e.message));
   await opened.goto(url+'?test=1'+new URL(link).hash,{waitUntil:'networkidle'});
   assert(await opened.locator('[data-compare-modal]').isVisible());
   assert.deepEqual(await opened.locator('.compare-buy').evaluateAll(xs=>xs.map(x=>({href:x.href,unit:x.dataset.unitPrice}))),actual);
   const overflow=await opened.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2);
   assert.equal(overflow,false);assert.deepEqual(errors,[]);
   await opened.screenshot({path:output+'/received-'+width+'.png'});
   records.push({width,restored:actual.length,overflow,errors,purchaseLinksValidated:true});
   await other.close();await context.close();
  }
  const {default:lighthouse}=await import(process.env.LIGHTHOUSE_MODULE || 'lighthouse');
  const {launch}=await import(process.env.CHROME_LAUNCHER_MODULE || 'chrome-launcher');
  const chrome=await launch({chromePath:chromium.executablePath(),chromeFlags:['--headless','--no-sandbox']});
  try{
   for(const formFactor of ['mobile','desktop']){
    const settings=formFactor==='desktop'?{formFactor:'desktop',screenEmulation:{mobile:false,width:1440,height:900,deviceScaleFactor:1,disabled:false}}:{};
    const report=await lighthouse(url+'?test=1',{port:chrome.port,output:'json',logLevel:'error',onlyCategories:['performance','accessibility','best-practices','seo'],blockedUrlPatterns:block,...settings});
    fs.writeFileSync(output+'/lighthouse-'+formFactor+'.json',report.report);
    records.push({lighthouse:formFactor,scores:Object.fromEntries(Object.entries(report.lhr.categories).map(([k,v])=>[k,v.score]))});
    assert(report.lhr.categories.seo.score>=.9);assert(report.lhr.categories.accessibility.score>=.9);
   }
  }finally{await chrome.kill();}
  fs.writeFileSync(output+'/report.json',JSON.stringify({publicUrl:publicBase+route,catalogSize:catalog.length,catalogAndMetadataUnchanged:true,records},null,2));
  console.log(JSON.stringify(records));
 }finally{await browser.close();server.close();source.window.close();preview.window.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
