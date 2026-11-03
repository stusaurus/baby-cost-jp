// Local-only browser regression for the toddler meal planner and provided A8 ad.
// Blocks all external tracking and purchase navigation; no synthetic A8 clicks.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium, webkit } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const output = 'toddler-meal-evidence';
const site = path.resolve('site');
const prefix = '/baby-cost-jp/';
const urlPath = prefix + 'guides/toddler-meals/';
const creative = 'https://px.a8.net/svt/ejp?a8mat=4BGCF1+9W19AY+5CLW+5YJRM';
const pixel = 'https://www16.a8.net/0.gif?a8mat=4BGCF1+9W19AY+5CLW+5YJRM';

(async () => {
  fs.mkdirSync(output, { recursive:true });
  const source = fs.readFileSync(path.join(site,'guides/toddler-meals/index.html'),'utf8');
  assert(source.includes('<link rel="canonical" href="https://stusaurus.github.io/baby-cost-jp/guides/toddler-meals/">'));
  assert(source.includes('href="'+creative+'" rel="nofollow"'));
  assert(source.includes('src="'+pixel+'"'));

  let origin = '';
  const server = http.createServer((req,res) => {
    const u = new URL(req.url, 'http://127.0.0.1');
    if (!u.pathname.startsWith(prefix)) {
      res.writeHead(404); res.end(); return;
    }
    let relative = decodeURIComponent(u.pathname.slice(prefix.length));
    if (!relative || relative.endsWith('/')) relative += 'index.html';
    const file = path.resolve(site,relative);
    if (!file.startsWith(site + path.sep) || !fs.existsSync(file)) {
      res.writeHead(404); res.end(); return;
    }
    const ext = path.extname(file).toLowerCase();
    let body = fs.readFileSync(file);
    const type = ext === '.js' ? 'application/javascript' :
      ext === '.css' ? 'text/css' :
      ext === '.webp' ? 'image/webp' :
      ext === '.svg' ? 'image/svg+xml' : 'text/html; charset=utf-8';
    if (ext === '.html') {
      body = Buffer.from(body.toString('utf8').replaceAll(
        'https://stusaurus.github.io/baby-cost-jp/', origin + prefix
      ));
    }
    res.setHeader('Content-Type', type);
    res.end(body);
  });
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  origin = 'http://127.0.0.1:' + server.address().port;
  const url = origin + urlPath;
  const evidence = [];

  try {
    for (const [name, engine] of Object.entries({chromium,webkit})) {
      const browser = await engine.launch({headless:true});
      try {
        for (const width of [320,390,1440]) {
          const context = await browser.newContext({viewport:{width,height:900},locale:'ja-JP'});
          await context.route('**/*', route => {
            const parsed = new URL(route.request().url());
            return parsed.origin === origin ? route.continue() : route.abort();
          });
          await context.addInitScript(() => {
            window.__guideEvents = [];
            window.gtag = (...args) => window.__guideEvents.push(args);
          });
          const page = await context.newPage();
          const errors = [];
          page.on('pageerror', error => errors.push(error.message));
          await page.goto(url + '?test=1', {waitUntil:'networkidle'});

          assert.equal(await page.locator('[data-toddler-meal-planner]').count(),1);
          const a = page.locator('#tm-mogumo-ad a[href^="https://px.a8.net"]');
          assert.equal(await a.getAttribute('href'),creative);
          assert.equal(await a.getAttribute('rel'),'nofollow');
          assert.equal(await page.locator('#tm-mogumo-ad img').getAttribute('src'),pixel);

          await page.locator('#tm-weekly').fill('4');
          await page.locator('#tm-bundle').fill('12');
          await page.locator('#tm-price').fill('7000');
          await page.locator('#tm-shipping').fill('1000');
          await page.locator('#tm-interval').selectOption('3');
          await page.locator('#tm-form button[type=submit]').click();
          assert.equal(await page.locator('#tm-total').textContent(),'32,000円');
          assert.equal(await page.locator('#tm-average').textContent(),'10,667円');
          assert.equal(await page.locator('#tm-purchased').textContent(),'48食');
          assert.equal(await page.locator('#tm-needed').textContent(),'48食');
          assert.equal(await page.locator('#tm-results').isVisible(),true);

          await page.locator('#tm-weekly').fill('9');
          await page.locator('#tm-form button[type=submit]').click();
          assert.match(await page.locator('#tm-balance').textContent(),/60食不足/);

          const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2);
          assert.equal(overflow,false,'Page overflows at width '+width+' in '+name);
          assert.deepEqual(errors,[],'Runtime errors at width '+width+' in '+name);
          await page.screenshot({path:output+'/toddler-'+name+'-'+width+'.png',fullPage:true});
          evidence.push({engine:name,width,overflow,calculated:true,officialA8:true,pageErrors:errors});
          await context.close();
        }
      } finally { await browser.close(); }
    }
    fs.writeFileSync(output+'/report.json',JSON.stringify({page:urlPath,evidence},null,2));
    console.log(JSON.stringify(evidence));
  } finally { server.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
