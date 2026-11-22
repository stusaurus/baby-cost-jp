// Real-browser QA for the existing pants-S renderer with synthetic, verified offers.
// No retail requests, no real analytics, no changes to the production catalog.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const {chromium, webkit} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const python = `
from datetime import datetime, timezone
import sys
from src.config import load_categories
from src.render import render_comparison
category = load_categories()['diapers']
segment = next(s for s in category['segments'] if s['id']=='pants-s')
def product(name, source_id, price, pieces):
    return dict(name=name, source_id=source_id, price_yen=price,
        unit_price=price/pieces, unit_metric='per_piece',
        quantity=dict(total=pieces, base_unit='piece', pack_count=1,
                      confidence=.99, evidence=str(pieces)+'枚'),
        shipping_basis='rakuten_postage_filter',
        url='https://hb.afl.rakuten.co.jp/hgc/'+source_id,
        image='', brand='テスト用', manufacturer='テスト用',
        shop='テスト用店舗', attributes={})
products = [product('赤ちゃん用 パンツ S 156枚','s-156',5070,156),
            product('赤ちゃん用 パンツ S 62枚','s-62',2840,62)]
print(render_comparison({'diapers': category},'diapers',category,segment,
                        products[:1] if len(sys.argv) > 1 else products,
                        datetime(2026,11,22,0,0,tzinfo=timezone.utc)))
`;
const generated = spawnSync('python',['-c',python], {encoding:'utf8'});
assert.equal(generated.status,0,generated.stderr);
const onlyOne = spawnSync('python',['-c',python,'single'],{encoding:'utf8'});
assert.equal(onlyOne.status,0,onlyOne.stderr);
const singleHtml=onlyOne.stdout;
assert(singleHtml.includes('id="purchase-planner"'));
assert(singleHtml.includes('検証できたパンツSは1商品だけ'));
assert(singleHtml.includes('content="noindex,follow"'));
const source='https://stusaurus.github.io/baby-cost-jp/';
const html=generated.stdout;
assert(html.includes('id="purchase-planner"') && html.includes('パンツSをあと14日'));
const route='/baby-cost-jp/diapers/pants/s/';
const output=process.env.PANTS_S_QA_OUTPUT||'pants-s-qa-evidence';
fs.mkdirSync(output,{recursive:true});
let server;
server=http.createServer((req,res)=>{
    const u=new URL(req.url,'http://localhost');
    if(u.pathname===route){
        const origin='http://127.0.0.1:'+server.address().port;
        res.setHeader('Content-Type','text/html; charset=utf-8');
        res.end((u.searchParams.has('single') ? singleHtml : html).replaceAll(source,origin+'/baby-cost-jp/'));return;
    }
    if(u.pathname.startsWith('/baby-cost-jp/static/')){
        const file=path.basename(u.pathname);
        const abs=path.resolve('src/static',file);
        if(!abs.startsWith(path.resolve('src/static')+path.sep)||!fs.existsSync(abs)){
            res.statusCode=404;res.end('not found');return;
        }
        res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':'image/webp');
        res.end(fs.readFileSync(abs));return;
    }
    res.statusCode=404;res.end('not found');
});

(async()=>{
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
    const origin='http://127.0.0.1:'+server.address().port;
    const result=[];
    try {
        for(const [engine,driver] of Object.entries({chromium,webkit})){
            const browser=await driver.launch({headless:true});
            try{
                for(const width of [320,390,1440]){
                    const context=await browser.newContext({viewport:{width,height:900},locale:'ja-JP'});
                    await context.route('**/*',request=>{
                        const url=new URL(request.request().url());
                        return url.origin===origin?request.continue():request.abort();
                    });
                    await context.addInitScript(()=>{
                        window.__events=[];
                        window.gtag=(...a)=>window.__events.push(a);
                    });
                    const page=await context.newPage();
                    const errors=[];
                    page.on('pageerror',e=>errors.push(e.message));
                    await page.goto(origin+route+'?operator_test=1',{waitUntil:'networkidle'});
                    assert.equal(await page.locator('[data-purchase-planner]').count(),1);
                    assert.equal(await page.locator('.product').count(),2);
                    assert.equal(await page.locator('[data-purchase-entry]').getAttribute('href'),'#purchase-planner');
                    const summary=page.locator('[data-purchase-summary]');
                    assert.match(await summary.innerText(),/不足150枚/);
                    async function check(id,sets,payment,surplus){
                        const card=page.locator('.product').filter({has:page.locator('[data-compare-id="'+id+'"]')});
                        assert.equal(await card.locator('[data-plan-sets]').innerText(),sets+'セット');
                        assert.equal(await card.locator('[data-plan-payment]').innerText(),'¥'+payment.toLocaleString('ja-JP'));
                        assert.equal(await card.locator('[data-plan-surplus]').innerText(),surplus+'枚');
                        const link=card.locator('.product-actions .cta');
                        assert.match(await link.getAttribute('href'),/^https:\/\/hb\.afl\.rakuten\.co\.jp\/hgc\/s-/);
                        assert.match(await link.getAttribute('rel'),/nofollow sponsored noopener/);
                        assert.equal(await link.getAttribute('data-size'),'s');
                        assert.equal(await link.getAttribute('data-product-type'),'pants');
                    }
                    await check('s-156',1,5070,6);
                    await check('s-62',3,8520,36);
                    // Size-review horizon and stock reduce actual needed sets; no prediction.
                    await page.locator('[data-purchase-days-choice="30"]').click();
                    await page.locator('.purchase-size summary').click();
                    await page.locator('[data-purchase-size-choice="7"]').click();
                    await page.locator('[data-purchase-stock]').fill('20');
                    assert.match(await summary.innerText(),/不足15枚/);
                    await check('s-156',1,5070,141);
                    await check('s-62',1,2840,47);
                    await page.locator('[data-sort-mode="price"]').click();
                    assert.match(await page.locator('[data-result-sort-label]').innerText(),/必要枚数分の購入額/);
                    assert.equal(await page.locator('.product').first().locator('[data-compare-id]').getAttribute('data-compare-id'),'s-62');
                    if(width===390){
                        await page.locator('[data-purchase-planner]').screenshot({path:path.join(output,engine+'-390-planner.png')});
                        await page.screenshot({path:path.join(output,engine+'-390-full.png'),fullPage:true});
                    }
                    await page.locator('[data-purchase-stock]').fill('100');
                    assert.match(await summary.innerText(),/不足0枚/);
                    assert.equal(await page.locator('[data-plan-payment]').count(),0);
                    assert.equal(await page.locator('.product-actions .cta:visible').count(),0);
                    await page.locator('[data-purchase-daily]').fill('1.5');
                    assert.equal(await page.locator('[data-purchase-error]').isVisible(),true);
                    assert.equal(await page.locator('[data-plan-payment]').count(),0);
                    await page.locator('[data-purchase-daily]').fill('5');
                    assert.equal(await page.locator('[data-purchase-error]').isVisible(),false);
                    const overflow=await page.evaluate(()=>({
                        document:document.documentElement.scrollWidth,screen:innerWidth
                    }));
                    assert(overflow.document<=overflow.screen+1,JSON.stringify({engine,width,overflow}));
                    assert.deepEqual(errors,[]);
                    const events=await page.evaluate(()=>window.__events);
                    assert(!events.some(e=>(e[1]==='purchase'||e[1]==='affiliate_click')));
                    assert(!events.some(e=>e[2]&&(
                        'daily' in e[2]||'stock' in e[2]||
                        'days' in e[2]||'sizeDays' in e[2])));
                    // Live-equivalent one-offer state: retain calculator without
                    // suggesting multiple retailers or claiming indexability.
                    await page.goto(origin+route+'?single=1',{waitUntil:'networkidle'});
                    assert.equal(await page.locator('.product').count(),1);
                    assert.equal(await page.locator('[data-purchase-planner]').count(),1);
                    assert.equal(await page.locator('meta[name="robots"]').getAttribute('content'),'noindex,follow');
                    assert.match(await page.locator('.neutral-note').last().innerText(),/1商品だけ/);
                    assert.equal(await page.locator('[data-plan-sets]').innerText(),'1セット');
                    assert.equal(await page.locator('[data-plan-payment]').innerText(),'¥5,070');
                    assert.equal(await page.locator('[data-plan-surplus]').innerText(),'6枚');
                    assert.equal(await page.locator('.product-actions .cta').count(),1);
                    assert.equal(await page.locator('[data-purchase-planner]').isVisible(),true);
                    if(width===390){
                        await page.locator('[data-purchase-planner]').screenshot({path:path.join(output,engine+'-390-single-offer.png')});
                    }
                    const singleOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
                    assert.equal(singleOverflow,false);
                    result.push({engine,width,correctSets:true,checkout:true,sizeReview:true,verifiedLinks:true,
                        badInputRejected:true,noBuy:true,noOverflow:true,eventsSafe:true});
                    await context.close();
                }
            }finally{await browser.close();}
        }
        fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({success:true,result},null,2));
        console.log('PANTS_S_QA '+JSON.stringify(result));
    }finally{server.close();}
})().catch(error=>{console.error(error);process.exitCode=1;server.close();});
