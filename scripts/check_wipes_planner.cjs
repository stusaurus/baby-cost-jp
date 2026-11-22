// Browser QA: monthly wipes buying calculation, genuine checkout totals,
// affiliate attribution, malformed input, and both Chromium and WebKit at 3 widths.
// All price data is synthetic; no live retailer or analytics request is made.
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const assert = require("node:assert/strict");
const { chromium, webkit } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const root = path.resolve("site");
const evidence = process.env.WIPES_QA_OUTPUT || "wipes-qa-evidence";
const routePath = "/baby-cost-jp/wipes/";
const source = "https://stusaurus.github.io/baby-cost-jp/";
const synthetic = [
  {id:"test-640",name:"テスト おしりふき 640枚",price:1417,pieces:640,rank:1,url:"https://hb.afl.rakuten.co.jp/hgc/synthetic-640"},
  {id:"test-450",name:"テスト おしりふき 450枚",price:1500,pieces:450,rank:2,url:"https://hb.afl.rakuten.co.jp/hgc/synthetic-450"},
  {id:"test-1200",name:"テスト おしりふき 1200枚",price:3000,pieces:1200,rank:3,url:"https://hb.afl.rakuten.co.jp/hgc/synthetic-1200"},
  {id:"test-unsafe",name:"悪質なURL",price:100,pieces:450,rank:4,url:"https://hb.afl.rakuten.co.jp.attacker.example/hgc/unsafe"}
];
let pageHTML = fs.readFileSync(path.join(root,"wipes/index.html"),"utf8");
const replaceCatalog = /<script type="application\/json" id="wipes-plan-catalog">[\s\S]*?<\/script>/;
assert.match(pageHTML, replaceCatalog);
pageHTML = pageHTML.replace(replaceCatalog,'<script type="application/json" id="wipes-plan-catalog">'+JSON.stringify(synthetic)+'</script>');
fs.mkdirSync(evidence,{recursive:true});

let server;
function localGet(req,res) {
  const addr = "http://127.0.0.1:" + server.address().port;
  const requested = new URL(req.url,addr);
  if (requested.pathname === routePath) {
    res.setHeader("Content-Type","text/html; charset=utf-8");
    res.end(pageHTML.replaceAll(source,addr+"/baby-cost-jp/"));
    return;
  }
  if (!requested.pathname.startsWith("/baby-cost-jp/")) {
    res.statusCode=404;res.end("no such route");return;
  }
  const suffix = requested.pathname.substring("/baby-cost-jp/".length);
  const safePath = path.resolve(root,(!suffix || suffix.endsWith("/"))?suffix+"index.html":suffix);
  if (!safePath.startsWith(root+path.sep) || !fs.existsSync(safePath)) {
    res.statusCode=404;res.end("not found");return;
  }
  res.setHeader("Content-Type",safePath.endsWith(".js")?"text/javascript":safePath.endsWith(".css")?"text/css":"text/html");
  const contents=fs.readFileSync(safePath);
  // Localize the generated homepage's absolute GitHub Pages links as well as
  // the wipes page itself. Test real navigation without leaving the fixture.
  res.end(safePath.endsWith(".html")
    ?contents.toString("utf8").replaceAll(source,addr+"/baby-cost-jp/")
    :contents);
}
server=http.createServer(localGet);

(async()=>{
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  const origin = "http://127.0.0.1:"+server.address().port;
  const results = [];
  try {
    for (const [engine,driver] of Object.entries({chromium,webkit})) {
      const browser = await driver.launch({headless:true});
      try {
        for (const width of [320,390,1440]) {
          const context=await browser.newContext({viewport:{width,height:900},locale:"ja-JP"});
          // Never contact real retailer or Google: verify events in a local stub.
          await context.route("**/*",request=>{
            try {
              return new URL(request.request().url()).origin===origin
                ?request.continue():request.abort();
            } catch (_) { return request.abort(); }
          });
          await context.addInitScript(()=>{
            window.__events=[];
            window.gtag=(...params)=>window.__events.push(params);
          });
          const p=await context.newPage();
          const pageErrors=[];
          p.on("pageerror",err=>pageErrors.push(err.message));
          await p.goto(origin+routePath,{waitUntil:"networkidle"});
          assert.equal(await p.locator("[data-wipes-plan-form]").count(),1);
          assert.equal(await p.locator(".wipes-plan-offer").count(),0);
          await p.locator(".wipes-plan-submit").click();
          const result=p.locator("[data-wipes-plan-output]");
          assert.equal(await result.isVisible(),true);
          const output=await result.innerText();
          for (const fragment of ["600枚","200枚","400枚","640枚","¥1,417","240枚","450枚","¥1,500","50枚","¥83"]) {
            assert(output.includes(fragment),engine+"/"+width+" missing "+fragment+" in "+output.slice(0,700));
          }
          assert.equal(await p.locator(".wipes-plan-offer").count(),2);
          const links=p.locator(".wipes-plan-buy");
          assert.equal(await links.count(),2);
          const ids=[];
          for(let i=0;i<2;i++){
            const el=links.nth(i);
            assert.match(await el.getAttribute("href"),/^https:\/\/hb\.afl\.rakuten\.co\.jp\/hgc\//);
            assert.match(await el.getAttribute("rel"),/nofollow sponsored noopener/);
            assert.equal(await el.getAttribute("data-conversion-source"),"wipes_plan_offer");
            assert.equal(await el.getAttribute("data-click-position"),"wipes_plan_offer");
            ids.push(await el.getAttribute("data-product-id"));
          }
          assert.deepEqual(ids,["test-640","test-450"]);
          const before=await p.evaluate(()=>window.__events);
          assert.equal(before.filter(e=>e[1]==="wipes_plan_complete").length,1);
          assert.equal(before.filter(e=>e[1]==="affiliate_click").length,0);
          assert.deepEqual(Object.keys(before.filter(e=>e[1]==="wipes_plan_complete")[0][2]).sort(),
            ["calculator_type","category_id","page_path","product_type","site_id","size"].sort());
          await links.first().evaluate(a=>{
            const click=new MouseEvent("click",{bubbles:true,cancelable:true,button:0});
            click.preventDefault();
            a.dispatchEvent(click);
          });
          const recorded=await p.evaluate(()=>window.__events);
          for (const name of ["product_result_click","affiliate_click"]) {
            const events=recorded.filter(e=>e[1]===name);
            assert.equal(events.length,1,engine+"/"+width+" "+name);
            assert.equal(events[0][2].conversion_source,"wipes_plan_offer");
            assert.equal(events[0][2].click_position,"wipes_plan_offer");
            assert.equal(events[0][2].product_id,"test-640");
            assert.equal(events[0][2].category_id,"wipes");
            assert.equal(events[0][2].page_path,routePath);
            for (const secret of ["daily","period","stock","need","deficit","days","pieces","usage"]) {
              assert(!Object.hasOwn(events[0][2],secret), "private calculator input leaked: "+secret);
            }
          }
          const overflow=await p.evaluate(()=>({
            documentWidth:document.documentElement.scrollWidth,screenWidth:innerWidth,
            elements:[...document.querySelectorAll("body *")].filter(el=>{
              const b=el.getBoundingClientRect();
              return b.width>0 && (b.right>innerWidth+1 || b.left< -1);
            }).slice(0,8).map(el=>({tag:el.tagName,cls:String(el.className).slice(0,50),right:Math.round(el.getBoundingClientRect().right)}))
          }));
          assert(overflow.documentWidth<=overflow.screenWidth,engine+"/"+width+" horizontal overflow "+JSON.stringify(overflow));
          if(width===390)await p.screenshot({path:path.join(evidence,engine+"-"+width+"-example.png"),fullPage:true});

          await p.locator('[name="stock"]').fill("8000");
          await p.locator(".wipes-plan-submit").click();
          assert((await result.innerText()).includes("追加購入は0セット"));
          assert.equal(await p.locator(".wipes-plan-offer").count(),0);

          await p.locator('[name="stock"]').fill("0");
          await p.locator('[name="daily"]').fill("3");
          await p.locator('[name="period"]').selectOption("7");
          await p.locator(".wipes-plan-submit").click();
          const short=await result.innerText();
          assert(short.includes("21枚") && short.includes("7日分"),engine+"/"+width+" seven-day "+short.slice(0,200));

          await p.locator('[name="daily"]').fill("1.5");
          await p.locator(".wipes-plan-submit").click();
          assert.equal(await p.locator("[data-wipes-plan-error]").isVisible(),true);
          assert.equal(await result.isVisible(),false);

          await p.locator('[name="daily"]').fill("-1");
          await p.locator(".wipes-plan-submit").click();
          assert.equal(await p.locator("[data-wipes-plan-error]").isVisible(),true);
          assert.equal(await result.isVisible(),false);

          await p.locator('[name="daily"]').fill("0");
          await p.locator(".wipes-plan-submit").click();
          assert.equal(await p.locator("[data-wipes-plan-error]").isVisible(),false);
          assert((await result.innerText()).includes("追加購入は0セット"));
          assert.deepEqual(pageErrors,[],engine+"/"+width+" browser errors");
          // Real rendered homepage, not a mocked anchor. Follow the new
          // content-based discovery link to the existing wipes calculator.
          await p.goto(origin+"/baby-cost-jp/",{waitUntil:"networkidle"});
          const entry=p.locator('a[data-nav-source="home_wipes_planner"]');
          assert.equal(await entry.count(),1);
          assert.equal(await entry.getAttribute("href"),origin+"/baby-cost-jp/wipes/#wipes-plan");
          assert((await entry.evaluate(el=>el.getBoundingClientRect().height))>=44,
            engine+"/"+width+" home wipes touch target below 44px");
          const homeWidth=await p.evaluate(()=>document.documentElement.scrollWidth);
          assert(homeWidth<=width+1,engine+"/"+width+" home horizontal overflow "+homeWidth);
          if(width===390)await p.screenshot({path:path.join(evidence,engine+"-"+width+"-home-entry.png"),fullPage:true});
          await entry.click();
          await p.waitForURL("**/baby-cost-jp/wipes/#wipes-plan");
          assert.equal(await p.locator("#wipes-plan").count(),1);
          assert.equal(await p.locator("[data-wipes-plan-form]").count(),1);
          assert((await p.evaluate(()=>document.documentElement.scrollWidth))<=width+1);
          assert.deepEqual(pageErrors,[],engine+"/"+width+" navigation browser errors");
          results.push({engine,width,correctMath:true,checkoutVsWaste:true,validAffiliate:true,analyticsSafe:true,invalidRejected:true,zeroPurchase:true,noOverflow:true});
          await context.close();
        }
      } finally { await browser.close(); }
    }
    fs.writeFileSync(path.join(evidence,"results.json"),JSON.stringify({success:true,results},null,2));
    console.log("WIPES_QA "+JSON.stringify(results));
  } finally { server.close(); }
})().catch(err=>{console.error(err);process.exitCode=1;server.close();});
