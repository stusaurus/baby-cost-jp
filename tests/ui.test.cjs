const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require('jsdom');
const base='https://stusaurus.github.io/baby-cost-jp/';
function setup(path, storage={}, session={}, suffix='') {
 const dom=new JSDOM(fs.readFileSync('site/'+path,'utf8'),{url:base+path.replace('index.html','')+suffix,runScripts:'outside-only'});
 const w=dom.window;const events=[];w.gtag=(...args)=>events.push(args);
 w.matchMedia=()=>({matches:false});
 w.HTMLElement.prototype.scrollIntoView=()=>{};
 for(const [key,value] of Object.entries(storage))w.localStorage.setItem(key,value);
 for(const [key,value] of Object.entries(session))w.sessionStorage.setItem(key,value);
 w.eval(fs.readFileSync('src/static/purchase.js','utf8'));w.eval(fs.readFileSync('src/static/analytics.js','utf8'));w.eval(fs.readFileSync('src/static/app.js','utf8'));
 return {dom,w,doc:w.document,events};
}

test('M-pants comparison link restores only current page catalog data in a fresh session',async()=>{
 const a=setup('diapers/pants/m/index.html',{}, {}, '?test=1&unrelated=private');
 [...a.doc.querySelectorAll('[data-compare-add]')].slice(0,2).forEach(x=>x.click());
 a.doc.querySelector('[data-compare-open]').click();
 let copied='';Object.defineProperty(a.w.navigator,'clipboard',{value:{writeText:async text=>{copied=text;}}});
 a.doc.querySelector('[data-compare-share]').click();await new Promise(resolve=>setImmediate(resolve));
 assert(copied.startsWith(base+'diapers/pants/m/#compare='));
 assert.equal(new URL(copied).search,'');
 assert(!copied.includes('rakuten')&&!copied.includes('private'));
 assert.match(a.doc.querySelector('[data-compare-share-status]').textContent,/コピーしました/);
 const b=setup('diapers/pants/m/index.html',{}, {},new URL(copied).hash);
 assert.equal(b.doc.querySelector('[data-compare-modal]').hidden,false);
 assert.equal(b.doc.querySelectorAll('.compare-column').length,2);
 const original=[...a.doc.querySelectorAll('.compare-buy')].map(x=>[x.href,x.dataset.unitPrice]);
 assert.deepEqual([...b.doc.querySelectorAll('.compare-buy')].map(x=>[x.href,x.dataset.unitPrice]),original);
 const calls=b.events.filter(x=>x[1]==='affiliate_click');assert.equal(calls.length,0);
 a.w.close();b.w.close();
});
test('unavailable shared IDs are not fabricated and malformed/oversized lists are rejected',()=>{
 const initial=setup('diapers/pants/m/index.html');const id=initial.doc.querySelector('[data-compare-id]').dataset.compareId;initial.w.close();
 const hash=ids=>'#'+new URLSearchParams({compare:JSON.stringify(ids)}).toString();
 const a=setup('diapers/pants/m/index.html',{}, {},hash([id,'not-current']));
 assert.equal(a.doc.querySelector('[data-compare-modal]').hidden,true);
 assert.match(a.doc.querySelector('[data-compare-import-status]').textContent,/一部は現在掲載されていません/);
 assert.equal(a.doc.querySelectorAll('[data-compare-add][aria-pressed=true]').length,1);a.w.close();
 for(const ids of [[id,id],['<img src=x onerror=alert(1)>','x'],[id,'2','3','4'],{url:'https://example.com'}]){
  const b=setup('diapers/pants/m/index.html',{}, {},hash(ids));
  assert.equal(b.doc.querySelector('[data-compare-modal]').hidden,true);
  assert.equal(b.doc.querySelectorAll('.compare-column').length,0);
  assert.equal(b.doc.querySelector('img[src=x]'),null);b.w.close();
 }
});
test('clipboard denial leaves a selectable link and removing a candidate clears stale links',async()=>{
 const {w,doc}=setup('diapers/pants/m/index.html');
 [...doc.querySelectorAll('[data-compare-add]')].slice(0,2).forEach(x=>x.click());doc.querySelector('[data-compare-open]').click();
 Object.defineProperty(w.navigator,'clipboard',{value:{writeText:async()=>{throw new Error('denied');}}});
 doc.querySelector('[data-compare-share]').click();await new Promise(resolve=>setImmediate(resolve));
 const input=doc.querySelector('[data-compare-share-url]');assert(!input.hidden);assert.equal(doc.activeElement,input);assert.equal(input.selectionEnd,input.value.length);
 doc.querySelector('[data-compare-close]').click();doc.querySelector('[data-tray-remove]').click();
 assert.equal(input.value,'');assert(input.hidden);w.close();
});
test('share controls are limited to the M-pants all-brand page',()=>{
 const {w,doc}=setup('wipes/index.html');assert.equal(doc.querySelector('[data-compare-share]'),null);w.close();
});
test('type and size selection includes newborn only under tape',()=>{
 const {w,doc,events}=setup('index.html');
 doc.querySelector('[data-value=tape]').click();
 assert.equal(doc.querySelector('.size-chip').dataset.value,'newborn');
 doc.querySelector('[data-value=pants]').click();
 assert.equal(doc.querySelector('.size-chip').dataset.value,'s');
 assert(events.some(x=>x[1]==='comparison_filter_change'));w.close();
});
test('save survives reopening and saved-only filter restores full listing',()=>{
 const first=setup('diapers/pants/m/index.html');
 first.doc.querySelector('[data-save-id]').click();
 const saved=first.w.localStorage.getItem('baby_cost_saved_v1');first.w.close();
 const {w,doc,events}=setup('diapers/pants/m/index.html',{'baby_cost_saved_v1':saved});
 assert.equal(doc.querySelector('[data-save-id]').getAttribute('aria-pressed'),'true');
 doc.querySelector('[data-saved-only]').click();
 assert.equal([...doc.querySelectorAll('.product')].filter(x=>!x.hidden).length,1);
 doc.querySelector('[data-saved-only]').click();
 assert.equal([...doc.querySelectorAll('.product')].filter(x=>!x.hidden).length,2);w.close();
});
test('comparison dialog opens, offers Rakuten CTA, closes with Escape and restores focus',()=>{
 const {w,doc,events}=setup('diapers/pants/m/index.html');
 [...doc.querySelectorAll('[data-compare-add]')].forEach(x=>x.click());
 doc.querySelector('[data-compare-open]').click();
 assert.equal(doc.querySelector('[data-compare-modal]').hidden,false);
 assert.equal(doc.querySelectorAll('.compare-column').length,2);
 assert.equal(doc.querySelectorAll('.compare-buy[data-affiliate=rakuten]').length,2);
 const buy=doc.querySelector('.compare-buy[data-affiliate=rakuten]');buy.addEventListener('click',e=>e.preventDefault());buy.click();
 assert(events.some(x=>x[1]==='affiliate_click' && x[2].click_position==='compare_modal'));
 doc.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Escape'}));
 assert.equal(doc.querySelector('[data-compare-modal]').hidden,true);
 assert.equal(doc.activeElement,doc.querySelector('[data-compare-open]'));w.close();
});
test('affiliate event carries attribution and operator test, once per click',()=>{
 const {w,doc,events}=setup('diapers/pants/m/index.html',{'baby_cost_operator_test_v1':'1'});
 const a=doc.querySelector('[data-affiliate]');a.addEventListener('click',e=>e.preventDefault());a.click();
 const sent=events.filter(x=>x[1]==='affiliate_click');assert.equal(sent.length,1);
 assert.equal(sent[0][2].operator_test,'1');assert.equal(sent[0][2].category_id,'diapers');assert.equal(sent[0][2].conversion_source,'comparison_result');
 w.close();
});
test('guided growth selection reveals needs and is tracked',()=>{
 const {w,doc,events}=setup('index.html');const button=doc.querySelector('[data-growth-stage-button=newborn]');button.click();
 assert.equal(button.getAttribute('aria-pressed'),'true');
 assert.equal(doc.querySelector('[data-growth-panel=newborn]').hidden,false);
 assert(events.some(x=>x[1]==='growth_stage_select' && x[2].growth_stage==='newborn'));w.close();
});
test('growth origin survives the category and selector journey, with save context',()=>{
 const key='baby_cost_feature_navigation_v1';
 const first=setup('diapers/index.html',{}, {[key]:JSON.stringify({source:'growth_early',target:'/baby-cost-jp/diapers/',at:Date.now()})});
 first.w.babyCostNavigation('diaper_selector',base+'diapers/pants/m/');
 const nav=first.w.sessionStorage.getItem(key);first.w.close();
 const {w,doc,events}=setup('diapers/pants/m/index.html',{}, {[key]:nav});
 assert.equal(w.sessionStorage.getItem(key),null);
 doc.querySelector('[data-save-id]').click();
 const a=doc.querySelector('[data-affiliate]');a.addEventListener('click',e=>e.preventDefault());a.click();
 const click=events.find(x=>x[1]==='affiliate_click')[2];
 assert.equal(click.conversion_source,'diaper_selector');assert.equal(click.journey_origin,'growth_early');assert.equal(click.growth_stage,'early');
 const save=events.find(x=>x[1]==='product_save')[2];assert.equal(save.category_id,'diapers');assert.equal(save.size,'m');
 w.close();
});
test('expired, future and wrong-target attribution does not contaminate direct visits',()=>{
 for(const nav of [{at:Date.now()-1800001,target:'/baby-cost-jp/diapers/pants/m/'},{at:Date.now()+10000,target:'/baby-cost-jp/diapers/pants/m/'},{at:Date.now(),target:'/baby-cost-jp/wipes/'}]){
  const {w,events}=setup('diapers/pants/m/index.html',{}, {'baby_cost_feature_navigation_v1':JSON.stringify({...nav,source:'growth_early'})});
  assert.equal(events.find(x=>x[1]==='comparison_view')[2].growth_stage,undefined);w.close();
 }
});

const {calculate}=require('../src/static/purchase.js');
const offer=(total=192,price=4480)=>({total,price,verified:true});
test('purchase math: one set, exact boundary, multiple sets and large surplus',()=>{
 assert.deepEqual(calculate(offer(),5,30),{needed:150,total:192,sets:1,payment:4480,surplus:42,costTenths:35000,sizeSurplus:null});
 assert.equal(calculate(offer(150),5,30).surplus,0);
 assert.deepEqual(calculate(offer(),8,30),{needed:240,total:192,sets:2,payment:8960,surplus:144,costTenths:56000,sizeSurplus:null});
 assert.equal(calculate(offer(420,9980),5,7).surplus,385);
 assert.equal(calculate(offer(420,9980),5,7,14).sizeSurplus,350);
 assert.equal(calculate(offer(70,1500),5,14,14).sizeSurplus,0);
});
test('purchase math rejects invalid inputs and unknown prices, quantities or shipping',()=>{
 for(const n of [0,-1,1.1,31,NaN,Infinity,'5',null,undefined])assert.equal(calculate(offer(),n,30),null);
 for(const n of [0,-1,1.1,91,NaN,Infinity,'30',null])assert.equal(calculate(offer(),5,n),null);
 for(const n of [0,-1,1.1,181,NaN,Infinity,'14'])assert.equal(calculate(offer(),5,30,n),null);
 for(const p of [null,{},offer(0),offer(1.5),offer(20001),offer(192,0),offer(192,1.5),{...offer(),verified:false},{...offer(),price:'4480'}])assert.equal(calculate(p,5,30),null);
});
test('fractional equivalent rounds once, using integers even at allowed maximum',()=>{
 assert.equal(calculate(offer(200,201),1,10).costTenths,101); // 10.05 -> 10.1, no binary error
 assert.equal(calculate(offer(3,100),1,1).costTenths,333);
 assert.equal(calculate(offer(3,100),1,3).payment,100);
 const r=calculate(offer(1,999999999),30,90);
 assert.equal(r.payment,2699999997300);assert.equal(r.costTenths,26999999973000);
 for(let total=1;total<=250;total++)for(const needed of [1,28,150,240,2700]){
  const daily=needed===2700?30:1,days=needed/daily;
  if(days>90)continue;
  const r=calculate(offer(total,3211),daily,days);
  assert(r.sets*total>=needed&&(r.sets-1)*total<needed);
  assert(r.surplus>=0&&r.surplus<total);
 }
});
function change(a,selector,value,type='input'){
 const input=a.doc.querySelector(selector);input.value=value;input.dispatchEvent(new a.w.Event(type,{bubbles:true}));
}
test('daily presets, manual input, days and savings share one state with cards and tray',()=>{
 const a=setup('diapers/pants/m/index.html');
 assert.match(a.doc.querySelector('[data-purchase-summary]').textContent,/必要150枚/);
 a.doc.querySelector('[data-usage="8"]').click();
 assert.match(a.doc.querySelector('[data-plan-sets]').textContent,/2セット/);
 assert.match(a.doc.querySelector('[data-plan-payment]').textContent,/8,960/);
 a.doc.querySelector('[data-purchase-days-choice="7"]').click();
 assert.match(a.doc.querySelector('[data-purchase-summary]').textContent,/必要56枚/);
 change(a,'[data-purchase-daily]','7');change(a,'[data-purchase-days]','14');
 assert.equal(a.doc.querySelector('[data-savings-period]').textContent,'14日');
 assert.match(a.doc.querySelector('[data-purchase-summary]').textContent,/必要98枚/);
 [...a.doc.querySelectorAll('[data-compare-add]')].forEach(b=>b.click());a.doc.querySelector('[data-compare-open]').click();
 assert.equal(a.doc.querySelectorAll('.compare-column [data-plan-payment]').length,2);
 assert.equal(a.doc.querySelector('.compare-column [data-plan-payment]').textContent,a.doc.querySelector('.product [data-plan-payment]').textContent);
 assert.match(a.doc.querySelector('.compare-column .purchase-context').textContent,/必要98枚/);
 change(a,'[data-purchase-days]','30');
 assert.match(a.doc.querySelector('.compare-column .purchase-context').textContent,/必要210枚/);
 a.w.close();
});
test('invalid input clears stale amounts and recovers; size advice uses only entered duration',()=>{
 const a=setup('diapers/pants/m/index.html');
 for(const value of ['', '0','-1','1.5','31']){
  change(a,'[data-purchase-daily]',value);
  assert.equal(a.doc.querySelectorAll('[data-plan-payment]').length,0);
  assert.equal(a.doc.querySelector('[data-purchase-error]').hidden,false);
 }
 change(a,'[data-purchase-daily]','5');change(a,'[data-purchase-size-days]','7');
 assert.match(a.doc.querySelector('[data-purchase-summary]').textContent,/必要35枚/);
 assert.equal(a.doc.querySelector('[data-savings-period]').textContent,'7日');
 assert.match(a.doc.querySelector('.purchase-warning').textContent,/余る計算です/);
 change(a,'[data-purchase-size-days]','');assert.equal(a.doc.querySelector('.purchase-warning'),null);
 change(a,'[data-purchase-size-days]','181');assert.equal(a.doc.querySelectorAll('[data-plan-payment]').length,0);
 change(a,'[data-purchase-size-days]','180');assert.equal(a.doc.querySelector('[data-purchase-error]').hidden,true);
 const card=a.doc.querySelector('[data-purchase-product]');card.dataset.purchaseProduct='null';
 change(a,'[data-purchase-days]','7');assert.match(card.textContent,/購入計算はできません/);assert.equal(card.querySelector('[data-plan-payment]'),null);
 card.dataset.purchaseProduct='{bad';change(a,'[data-purchase-days]','14');assert.equal(card.querySelector('[data-plan-payment]'),null);
 a.w.close();
});
test('planner tracks explicit use only, preserves operator boundary, never sends household input or purchase',()=>{
 for(const suffix of ['','?test=1']){
  const a=setup('diapers/pants/m/index.html',{}, {},suffix);
  assert.equal(a.events.filter(e=>e[1]==='purchase_planner_use').length,0);
  a.doc.querySelector('[data-usage="6"]').click();
  change(a,'[data-purchase-size-days]','14','change');
  const sent=a.events.filter(e=>e[1]==='purchase_planner_use');assert.equal(sent.length,2);
  for(const [, ,payload] of sent){
   assert.equal(payload.operator_test,suffix?'1':undefined);
   for(const key of ['usage_per_day','daily','days','size_days','value','revenue'])assert(!(key in payload));
  }
  assert(!a.events.some(e=>e[1]==='purchase'||e[1]==='affiliate_click'));
  const link=a.doc.querySelector('.product a[data-affiliate]');link.addEventListener('click',e=>e.preventDefault());link.click();
  const clicks=a.events.filter(e=>e[1]==='affiliate_click');assert.equal(clicks.length,1);assert.equal(clicks[0][2].operator_test,suffix?'1':undefined);
  a.w.close();
 }
});


test('Mogumo twelve-week planner computes true checkout totals, supply balance, and average without assumed prices',()=>{
 const s=setup('guides/toddler-meals/index.html', {}, {}, '?test=1');
 const {w,doc,events}=s;
 try {
   w.eval(fs.readFileSync('src/static/meal-guide.js','utf8'));
   doc.dispatchEvent(new w.Event('DOMContentLoaded'));
   const set=(id,value)=>{doc.getElementById(id).value=String(value)};
   set('tm-weekly',4);set('tm-bundle',12);set('tm-price',7000);set('tm-shipping',1000);set('tm-interval',3);
   doc.getElementById('tm-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
   assert.equal(doc.getElementById('tm-results').hidden,false);
   assert.equal(doc.getElementById('tm-total').textContent,'32,000円');
   assert.equal(doc.getElementById('tm-average').textContent,'10,667円');
   assert.equal(doc.getElementById('tm-deliveries').textContent,'4回');
   assert.equal(doc.getElementById('tm-unit').textContent,'666.67円');
   assert.equal(doc.getElementById('tm-purchased').textContent,'48食');
   assert.equal(doc.getElementById('tm-needed').textContent,'48食');
   assert.match(doc.getElementById('tm-balance').textContent,/一致/);
   const calc=events.filter(e=>e[1]==='meal_planner_use');
   assert.equal(calc.length,1);
   assert.equal(calc[0][2].operator_test,'1');
   assert.equal(calc[0][2].balance_type,'matched');
   assert.equal(calc[0][2].delivery_interval_weeks,'3');
   assert.equal(calc[0][2].price_yen,undefined);
   // Changing delivery interval can cause a shortage even if bundle price stays same.
   set('tm-weekly',5);set('tm-bundle',8);set('tm-interval',2);
   doc.getElementById('tm-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
   assert.equal(doc.getElementById('tm-total').textContent,'48,000円');
   assert.match(doc.getElementById('tm-balance').textContent,/12食不足/);
   assert.equal(doc.getElementById('tm-deliveries').textContent,'6回');
 } finally {w.close()}
});

test('Mogumo ad link and impression pixel stay unchanged and A8 click is tracked through baby site GA4',()=>{
 const s=setup('guides/toddler-meals/index.html',{}, {},'?test=1');
 const {w,doc,events}=s;
 try {
   w.eval(fs.readFileSync('src/static/meal-guide.js','utf8'));
   doc.dispatchEvent(new w.Event('DOMContentLoaded'));
   const box=doc.querySelector('#tm-mogumo-ad');
   assert.ok(box.textContent.includes('広告｜A8.netアフィリエイト'));
   const link=box.querySelector('a[href^="https://px.a8.net/"]');
   const pixel=box.querySelector('img');
   assert.equal(link.getAttribute('href'),'https://px.a8.net/svt/ejp?a8mat=4BGCF1+9W19AY+5CLW+5YJRM');
   assert.equal(link.getAttribute('rel'),'nofollow');
   assert.equal(link.textContent,'【子どもお墨付き】冷凍幼児食モグモ ');
   assert.equal(pixel.getAttribute('src'),'https://www16.a8.net/0.gif?a8mat=4BGCF1+9W19AY+5CLW+5YJRM');
   assert.equal(pixel.getAttribute('width'),'1');
   assert.equal(pixel.getAttribute('height'),'1');
   link.addEventListener('click',e=>e.preventDefault());
   link.dispatchEvent(new w.MouseEvent('click',{bubbles:true,cancelable:true}));
   const clicks=events.filter(e=>e[1]==='affiliate_click' && e[2]?.affiliate==='a8');
   assert.equal(clicks.length,1);
   assert.equal(clicks[0][2].site_id,'baby_cost_jp');
   assert.equal(clicks[0][2].operator_test,'1');
   assert.equal(clicks[0][2].category_id,'toddler_meals');
   assert.equal(clicks[0][2].conversion_source,'toddler_meal_cost_planner');
 } finally {w.close()}
});

test('Mogumo planner invalid/missing inputs never show a fabricated result',()=>{
 const s=setup('guides/toddler-meals/index.html');
 const {w,doc}=s;
 try {
   w.eval(fs.readFileSync('src/static/meal-guide.js','utf8'));
   doc.dispatchEvent(new w.Event('DOMContentLoaded'));
   const submit=()=>doc.getElementById('tm-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
   submit();
   assert.equal(doc.getElementById('tm-results').hidden,true);
   assert.match(doc.getElementById('tm-status').textContent,/すべての欄/);
   for(const [id,n] of Object.entries({'tm-weekly':4,'tm-bundle':12,'tm-price':9000,'tm-shipping':0}))doc.getElementById(id).value=String(n);
   doc.getElementById('tm-interval').value='4';
   submit();
   assert.equal(doc.getElementById('tm-results').hidden,false);
   doc.getElementById('tm-bundle').value='0';
   submit();
   assert.equal(doc.getElementById('tm-results').hidden,true);
 } finally {w.close()}
});

test('stock-aware page avoids showing imaginary savings when no diapers need buying',()=>{
 const a=setup('diapers/pants/m/index.html');
 try{
  change(a,'[data-purchase-stock]','150');
  assert.match(a.doc.querySelector('[data-purchase-summary]').textContent,/不足0枚/);
  assert.match(a.doc.querySelector('.product [data-purchase-no-buy]').textContent,/今は買い足し不要/);
  assert.equal(a.doc.querySelectorAll('.product [data-plan-payment]').length,0);
  assert.match(a.doc.querySelector('[data-savings-result]').textContent,/約¥0\.0/);
  change(a,'[data-purchase-stock]','30');
  assert.match(a.doc.querySelector('.product .purchase-equivalent').textContent,/今回買い足す120枚分/);
  assert.match(a.doc.querySelector('[data-purchase-summary]').textContent,/不足120枚/);
  assert.equal(a.doc.querySelector('[data-purchase-error]').hidden,true);
 }finally{a.w.close();}
});
