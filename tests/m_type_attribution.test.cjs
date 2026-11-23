const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require('jsdom');
const script = fs.readFileSync(require.resolve('../src/static/analytics.js'), 'utf8');
const SITE = 'https://stusaurus.github.io/baby-cost-jp/';
const NAV_KEY = 'baby_cost_feature_navigation_v1';

function setup({explicit = true, prior = true} = {}) {
  const path = '/baby-cost-jp/guides/m-diapers-tape-vs-pants/';
  const attr = explicit ? 'data-conversion-source="m_type_personal_planner"' : '';
  const dom = new JSDOM(`<!doctype html><a id="buy" data-affiliate="rakuten"
    data-category-id="diapers" data-product-id="shop:123" data-product-name="テープM 64枚"
    data-size="m" data-product-type="tape" data-unit-metric="per_piece"
    data-unit-price="42.9688" data-click-position="m_type_personal_result" ${attr}
    href="https://hb.afl.rakuten.co.jp/hgc/verified/">商品を見る</a>`,
    {url: SITE+'guides/m-diapers-tape-vs-pants/',runScripts:'outside-only'});
  const {window} = dom;
  const observed = [];
  window.gtag = (...args) => observed.push(args);
  if (prior) {
    window.sessionStorage.setItem(NAV_KEY, JSON.stringify({
      source:'diaper_index_m_type_guide', target:path, at:Date.now(),
      journey_origin:'diaper_index_m_type_guide'
    }));
  }
  window.eval(script);
  return {dom, window, observed, link:window.document.querySelector('#buy')};
}

test('explicit M-type planner attribution overrides previous internal navigation', () => {
  const x = setup();
  x.link.dispatchEvent(new x.window.MouseEvent('click', {bubbles:true, cancelable:true}));
  const events = x.observed.filter(([type]) => type === 'event');
  assert.deepEqual(events.map(row=>row[1]), ['product_result_click', 'affiliate_click']);
  const [, , data] = events[1];
  assert.equal(data.conversion_source, 'm_type_personal_planner');
  assert.equal(data.journey_origin, 'diaper_index_m_type_guide');
  assert.equal(data.click_position, 'm_type_personal_result');
  assert.equal(data.product_id, 'shop:123');
  assert.equal(data.product_type, 'tape');
  assert.equal(data.size, 'm');
  assert.equal(data.link_url, 'https://hb.afl.rakuten.co.jp/hgc/verified/');
  assert.equal(data.operator_test, undefined);
  assert.equal(Object.hasOwn(data, 'stock'), false);
  assert.equal(Object.hasOwn(data, 'days'), false);
  assert.equal(Object.hasOwn(data, 'payment'), false);
  assert.deepEqual(events[0][2], events[1][2]);
  x.window.close();
});

test('unlabeled existing product links preserve inherited attribution', () => {
  const x=setup({explicit:false});
  x.link.dispatchEvent(new x.window.MouseEvent('click', {bubbles:true, cancelable:true}));
  const affiliate=x.observed.find(([type,name])=>type==='event'&&name==='affiliate_click');
  assert.equal(affiliate[2].conversion_source, 'diaper_index_m_type_guide');
  x.window.close();
});

test('direct entrance attributes M-type shopping CTA to its own feature', () => {
  const x=setup({prior:false});
  x.link.dispatchEvent(new x.window.MouseEvent('click', {bubbles:true, cancelable:true}));
  const affiliate=x.observed.find(([type,name])=>type==='event'&&name==='affiliate_click');
  assert.equal(affiliate[2].conversion_source, 'm_type_personal_planner');
  x.window.close();
});
