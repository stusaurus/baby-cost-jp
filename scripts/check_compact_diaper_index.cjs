// Verify compact diaper index -> 5 calculators and price table, no mock links.
// Five validated synthetic SKU categories; blocks every off-origin request.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const {spawnSync} = require("node:child_process");
const {chromium,webkit} = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const python = `
from src.config import load_categories
from src.render import render_comparison,render_diaper_index
from datetime import datetime,timezone
import json
categories=load_categories(); cat=categories['diapers']
now=datetime(2026,11,23,tzinfo=timezone.utc)
types=[
 ('tape-newborn','tape','newborn',10,14),
 ('tape-s','tape','s',8,14),
 ('tape-m','tape','m',6,14),
 ('pants-s','pants','s',5,30),
 ('pants-m','pants','m',5,30),
 ('pants-l','pants','l',5,14),
 ('pants-big','pants','big',5,14),
]
def product(id,kind,size,qty,price):
 return dict(
   source_id=id,name=f'ベビー用 おむつ {kind} {size} {qty}枚',
   price_yen=price,unit_price=price/qty,unit_metric='per_piece',
   quantity=dict(total=qty,base_unit='piece',confidence=.99,
                 pack_count=1,evidence=f'{qty}枚'),
   shipping_basis='rakuten_postage_filter',
   url='https://hb.afl.rakuten.co.jp/hgc/'+id,
   image='',manufacturer='テスト用',brand='テスト用',shop='テスト用店舗',
   attributes={},
 )
snapshots={}
pages={}
for key,kind,size,daily,days in types:
 seg=next(seg for seg in cat['segments'] if seg['id']==key)
 rows=[product(key+'-80',kind,size,80,2800),
       product(key+'-160',kind,size,160,5100)]
 snapshots[key]=dict(products=rows)
 pages[f'diapers/{kind}/{size}/']=render_comparison(
     categories,'diapers',cat,seg,rows,now)
pages['diapers/']=render_diaper_index(categories,now,snapshots)
print(json.dumps(dict(pages=pages),ensure_ascii=False))
`;
const proc=spawnSync("python",["-c",python],{encoding:"utf8",maxBuffer:6*1024*1024});
assert.equal(proc.status,0,proc.stderr);
const rendered=JSON.parse(proc.stdout).pages;
const source="https://stusaurus.github.io/baby-cost-jp/";
const base="/baby-cost-jp/";
const folder=process.env.DIAPER_HUB_QA_OUTPUT || "diaper-hub-qa-evidence";
fs.mkdirSync(folder,{recursive:true});

const server=http.createServer((req,res)=>{
  const u=new URL(req.url,"http://127.0.0.1");
  const origin="http://127.0.0.1:"+server.address().port;
  if(!u.pathname.startsWith(base)){res.statusCode=404;res.end("not found");return;}
  const suffix=u.pathname.slice(base.length);
  if(Object.prototype.hasOwnProperty.call(rendered,suffix)){
    res.setHeader("Content-Type","text/html; charset=utf-8");
    res.end(rendered[suffix].replaceAll(source,origin+base));
    return;
  }
  if(suffix.startsWith("static/")){
    const root=path.resolve("src/static");
    const file=path.resolve(root,path.basename(suffix));
    if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.statusCode=404;res.end("missing");return;}
    res.setHeader("Content-Type",file.endsWith(".js")?"text/javascript":file.endsWith(".css")?"text/css":"image/webp");
    res.end(fs.readFileSync(file));return;
  }
  res.statusCode=404;res.end("not found");
});
(async()=>{
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  const origin="http://127.0.0.1:"+server.address().port;
  const homes=origin+base+"diapers/";
  const cases=[
    ["tape","newborn","10","14"],
    ["tape","s","8","14"],
    ["tape","m","6","14"],
    ["pants","s","5","30"],
    ["pants","m","5","30"],
    ["pants","l","5","14"],
    ["pants","big","5","14"],
  ];
  const records=[];
  try{
    for(const [engine,driver] of Object.entries({chromium,webkit})){
      const browser=await driver.launch({headless:true});
      try{
        for(const width of [320,390,1440]){
          const ctx=await browser.newContext({locale:"ja-JP",viewport:{width,height:850}});
          await ctx.route("**/*",r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());
          const p=await ctx.newPage();let errors=[];
          p.on("pageerror",err=>errors.push(err.message));
          await p.goto(homes,{waitUntil:"networkidle"});
          assert.equal(await p.locator("nav.home-purchase-path-grid").count(),1);
          assert.equal(await p.locator('nav.home-purchase-path-grid a.home-purchase-path').count(),7);
          assert.equal(await p.locator('table.seo-data-table tbody tr').count(),9);
          assert.equal(await p.locator('.choices').count(),0);
          assert.equal(await p.locator('aside.diaper-hub-nursery:not(.m-type-hub-entry)').count(),1);
          assert.equal(await p.locator('aside.m-type-hub-entry').count(),1);
          assert.equal(await p.locator('a[data-nav-source="diaper_index_price_jump"]').getAttribute('href'),'#diaper-price-by-size');
          assert.equal(await p.locator(".home-purchase-path-count").count(),7);
          const jumping=p.locator('[data-nav-source="diaper_index_purchase_jump"]');
          assert.equal(await jumping.count(),1);
          assert.equal(await jumping.getAttribute("href"),"#diaper-purchase-paths");
          assert((await jumping.evaluate(el=>el.getBoundingClientRect().height))>=44,engine+"/"+width+" planner jump tap");
          assert((await p.evaluate(()=>document.documentElement.scrollWidth))<=width+1,engine+"/"+width+" diaper index overflow");
          await jumping.click();
          await p.waitForURL("**/diapers/#diaper-purchase-paths");
          assert.equal(await p.locator("#diaper-purchase-paths").count(),1);
          if(width===390)await p.screenshot({path:path.join(folder,engine+"-390-diaper-index.png"),fullPage:true});
          await p.locator('[data-nav-source="diaper_index_type_size_jump"]').click();
          await p.waitForURL('**/diapers/#diaper-selector');
          assert.equal(await p.locator('#diaper-selector').count(),1);
          await p.locator('[data-nav-source="diaper_index_price_jump"]').click();
          await p.waitForURL('**/diapers/#diaper-price-by-size');
          assert.equal(await p.locator('#diaper-price-by-size').count(),1);
          for(const [kind,size,daily,days] of cases){
            await p.goto(homes,{waitUntil:"networkidle"});
            const locator=p.locator('a.home-purchase-path[data-product-type="'+kind+'"][data-size="'+size+'"]');
            assert.equal(await locator.count(),1,engine+"/"+width+"/"+kind+size+" unique");
            assert.equal(await locator.getAttribute("href"),origin+base+"diapers/"+kind+"/"+size+"/#purchase-planner");
            assert((await locator.evaluate(el=>el.getBoundingClientRect().height))>=44,engine+"/"+width+"/"+kind+size+" touch");
            await locator.click();
            await p.waitForURL("**/diapers/"+kind+"/"+size+"/#purchase-planner");
            assert.equal(await p.locator('[data-purchase-planner]').count(),1);
            assert.equal(await p.locator('[data-purchase-daily]').inputValue(),daily);
            assert.equal(await p.locator('[data-purchase-days]').inputValue(),days);
            assert.equal(await p.locator(".product").count(),2);
            assert.equal(await p.locator('meta[name="robots"]').getAttribute("content"),"index,follow");
            assert((await p.evaluate(()=>document.documentElement.scrollWidth))<=width+1,engine+"/"+width+"/"+kind+size+" page overflow");
          }
          assert.deepEqual(errors,[],engine+"/"+width+" page errors");
          records.push({engine,width,allSevenLinks:true,verifiedOffers:true,correctInputs:true,noOverflow:true,keyboardSizedTapTargets:true});
          await ctx.close();
        }
      }finally{await browser.close();}
    }
    fs.writeFileSync(path.join(folder,"results.json"),JSON.stringify({success:true,records},null,2));
    console.log("DIAPER_HUB_QA "+JSON.stringify(records));
  }finally{server.close();}
})().catch(err=>{console.error(err);process.exitCode=1;server.close();});
