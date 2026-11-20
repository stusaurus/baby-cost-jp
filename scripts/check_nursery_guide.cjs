// Dedicated Playwright QA for the nursery diaper purchase calculator.
// Serves only locally generated fixture pages and synthetic verified offers.
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const assert = require("node:assert/strict");
const { chromium, webkit } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const root = path.resolve("site");
const out = process.env.NURSERY_QA_OUTPUT || "nursery-qa-evidence";
const expectedRoute = "/baby-cost-jp/guides/nursery-diapers/";
const fakeOffers = [
  {id:"synthetic-100",name:"テスト用 おむつ パンツM 100枚",price:3000,pieces:100,url:"https://hb.afl.rakuten.co.jp/hgc/synthetic-100"},
  {id:"synthetic-120",name:"テスト用 おむつ パンツM 120枚",price:2800,pieces:120,url:"https://hb.afl.rakuten.co.jp/hgc/synthetic-120"}
];
function htmlWithProducts(src) {
  const tag=/<script type="application\/json" id="nursery-catalog">[\s\S]*?<\/script>/;
  assert.match(src,tag);
  return src.replace(tag,'<script type="application/json" id="nursery-catalog">'+JSON.stringify(fakeOffers)+'</script>');
}
const body = htmlWithProducts(fs.readFileSync(path.join(root,"guides/nursery-diapers/index.html"),"utf8"));
fs.mkdirSync(out,{recursive:true});
const local = http.createServer((req,res) => {
  const u = new URL(req.url,"http://localhost");
  const suffix = u.pathname.replace(/^\/baby-cost-jp\//,"");
  let rel = suffix.endsWith("/") ? suffix + "index.html" : suffix;
  if (u.pathname === expectedRoute) {
    res.setHeader("Content-Type","text/html; charset=utf-8");
    res.end(body.replaceAll("https://stusaurus.github.io/baby-cost-jp/", "http://127.0.0.1:"+local.address().port+"/baby-cost-jp/"));
    return;
  }
  const target = path.resolve(root,rel);
  if (!target.startsWith(root+path.sep) || !fs.existsSync(target)) {
    res.statusCode=404;res.end("not found");return;
  }
  const type = target.endsWith(".js")?"text/javascript":target.endsWith(".css")?"text/css":target.endsWith(".webp")?"image/webp":"text/html";
  res.setHeader("Content-Type",type);
  res.end(fs.readFileSync(target));
});
(async()=>{
  await new Promise(resolve=>local.listen(0,"127.0.0.1",resolve));
  const origin = "http://127.0.0.1:"+local.address().port;
  const results = [];
  try {
    for (const [engine,driver] of Object.entries({chromium,webkit})) {
      const browser = await driver.launch({headless:true});
      try {
        for (const width of [320,390,1440]) {
          const context=await browser.newContext({viewport:{width,height:900},locale:"ja-JP"});
          await context.route("**/*",route=>{
            const url = new URL(route.request().url());
            return url.origin===origin?route.continue():route.abort();
          });
          await context.addInitScript(()=>{
            window.__events=[];
            window.gtag=(...args)=>window.__events.push(args);
          });
          const page=await context.newPage();
          const errors=[];
          page.on("pageerror",e=>errors.push(e.message));
          await page.goto(origin+expectedRoute,{waitUntil:"networkidle"});
          await page.locator("[data-nursery-form] button[type=submit]").click();
          const result=page.locator("[data-nursery-output]");
          assert.equal(await result.isVisible(),true);
          const initial=await result.innerText();
          for(const expected of ["54枚","55枚","109枚","89枚"]) assert(initial.includes(expected),expected+" not in "+initial.slice(0,900));
          assert.equal(await page.locator('[name="productSize"]').inputValue(),"other");
          assert.equal(await page.locator(".nursery-offer").count(),0);
          assert(initial.includes("必要枚数のみを計算しました"),"The unconfirmed size must not offer M-size products");
          assert.equal(await page.locator(".nursery-size-link").count(),1);
          const fallback = page.locator(".nursery-size-link");
          assert.equal(await fallback.getAttribute("data-nav-source"),"nursery_unconfirmed_size");
          assert.equal(await fallback.getAttribute("data-category-id"),"diapers");
          assert.equal((await page.evaluate(()=>window.__events)).filter(e=>e[1]==="affiliate_click").length,0);
          await page.locator('[name="productSize"]').selectOption("pants-m");
          await page.locator("[data-nursery-form] button[type=submit]").click();
          const text=await result.innerText();
          for(const expected of ["54枚","55枚","109枚","89枚","¥2,800","¥3,000","20枚"]) assert(text.includes(expected),expected+" not in "+text.slice(0,900));
          assert.equal(await page.locator(".nursery-offer").count(),2);
          const links=page.locator(".nursery-offer a[data-affiliate=rakuten]");
          assert.equal(await links.count(),2);
          for(let i=0;i<2;i++){
            assert((await links.nth(i).getAttribute("href")).startsWith("https://hb.afl.rakuten.co.jp/hgc/"));
            assert.match(await links.nth(i).getAttribute("rel"),/sponsored/);
          }
          // The offers are added after page load. Verify delegated GA4 click
          // events, the direct-landing source label, and payload privacy.
          assert.equal(await links.first().getAttribute("data-conversion-source"),"nursery_plan_offer");
          await links.first().evaluate(el => {
            const event = new MouseEvent("click",{bubbles:true,cancelable:true,button:0});
            event.preventDefault(); // Avoid opening the synthetic affiliate URL.
            el.dispatchEvent(event);
          });
          const sent = await page.evaluate(()=>window.__events);
          const purchases = sent.filter(e=>e[1]==="product_result_click");
          const affiliates = sent.filter(e=>e[1]==="affiliate_click");
          assert.equal(purchases.length,1,engine+"/"+width+" product_result_click");
          assert.equal(affiliates.length,1,engine+"/"+width+" affiliate_click");
          assert.equal(purchases[0][2].conversion_source,"nursery_plan_offer");
          assert.equal(affiliates[0][2].conversion_source,"nursery_plan_offer");
          assert.equal(affiliates[0][2].click_position,"nursery_plan_offer");
          assert.equal(affiliates[0][2].product_id,await links.first().getAttribute("data-product-id"));
          assert.equal(affiliates[0][2].page_path,"/baby-cost-jp/guides/nursery-diapers/");
          for(const e of [...purchases,...affiliates]){
            for(const forbidden of ["attend","stock","nurseryDaily","homeAttend","period","shortage","mode","needed","productSize"]) {
              assert(!Object.hasOwn(e[2],forbidden), "Unexpected private data field: "+forbidden);
            }
          }
          const events=await page.evaluate(()=>window.__events);
          const planEvents=events.filter(ev=>ev[1]==="nursery_plan_complete");
          assert.equal(planEvents.length,2);
          const payload=planEvents[0][2];
          assert.deepEqual(Object.keys(payload).sort(),["calculator_type","page_path","site_id"].sort());
          // No individual values, attendance pattern or nursery status in events.
          for (const unsafe of ["attend","stock","nurseryDaily","homeAttend","period","shortage","mode","needed","productSize"]) {
            assert(!Object.hasOwn(payload,unsafe));
          }
          const overflow = await page.evaluate(() => ({
            documentWidth: document.documentElement.scrollWidth,
            viewportWidth: innerWidth,
            elements: [...document.querySelectorAll("body *")].filter((el) => {
              const rect = el.getBoundingClientRect();
              return rect.width > 0 && (rect.right > innerWidth + 1 || rect.left < -1);
            }).slice(0, 12).map((el) => ({
              tag: el.tagName, className: String(el.className).slice(0, 65),
              width: Math.round(el.getBoundingClientRect().width),
              right: Math.round(el.getBoundingClientRect().right)
            }))
          }));
          assert(overflow.documentWidth <= overflow.viewportWidth,engine+"/"+width+" horizontal overflow "+JSON.stringify(overflow));
          if(width===390)await page.screenshot({path:path.join(out,engine+"-"+width+"-bring.png"),fullPage:true});

          await page.locator('[name="mode"]').selectOption("subscription");
          assert.equal(await page.locator("[data-nursery-bring]:visible").count(),0);
          await page.locator("[data-nursery-form] button[type=submit]").click();
          const subscription=await result.innerText();
          assert(subscription.includes("54枚") && subscription.includes("34枚"));
          assert(subscription.includes("サブスク費用"));
          await page.locator('[name="mode"]').selectOption("bring");
          assert.equal(await page.locator("[data-nursery-bring]:visible").count(),2);

          await page.locator('[name="stock"]').fill("1000");
          await page.locator("[data-nursery-form] button[type=submit]").click();
          assert((await result.innerText()).includes("追加購入は0セット"));
          assert.equal(await page.locator(".nursery-offer").count(),0);

          await page.locator('[name="stock"]').fill("20");
          await page.locator('[name="attend"]').fill("15");
          await page.locator("[data-nursery-form] button[type=submit]").click();
          assert.equal(await page.locator("[data-nursery-error]").isVisible(),true);
          assert.equal(await result.isVisible(),false);

          await page.locator('[name="attend"]').fill("0");
          await page.locator("[data-nursery-form] button[type=submit]").click();
          assert.equal(await page.locator("[data-nursery-error]").isVisible(),false);
          // With no attendance, the nursery reserve cannot be charged.
          const zeroAttendance=await result.innerText();
          assert(zeroAttendance.includes("84枚") && zeroAttendance.includes("64枚"),zeroAttendance.slice(0,500));

          await page.locator('[name="attend"]').fill("10");
          await page.locator('[name="homeAttend"]').fill("1.5");
          await page.locator("[data-nursery-form] button[type=submit]").click();
          assert.equal(await page.locator("[data-nursery-error]").isVisible(),true);
          assert.equal(await result.isVisible(),false);
          assert.deepEqual(errors,[],engine+"/"+width+" JS errors");
          results.push({engine,width,default:true,subscription:true,zeroPurchase:true,invalid:true,zeroAttendance:true,analyticsSafe:true,externalRequestsBlocked:true});
          await context.close();
        }
      }finally{await browser.close();}
    }
    fs.writeFileSync(path.join(out,"results.json"),JSON.stringify({ok:true,results},null,2));
    console.log("NURSERY_QA passed "+JSON.stringify(results));
  }finally{local.close();}
})().catch(e=>{console.error(e);process.exitCode=1;local.close();});
