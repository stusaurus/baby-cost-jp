const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require('jsdom');
const base='https://stusaurus.github.io/baby-cost-jp/';
function setup(path, storage={}, session={}) {
 const dom=new JSDOM(fs.readFileSync('site/'+path,'utf8'),{url:base+path.replace('index.html',''),runScripts:'outside-only'});
 const w=dom.window;const events=[];w.gtag=(...args)=>events.push(args);
 for(const [key,value] of Object.entries(storage))w.localStorage.setItem(key,value);
 for(const [key,value] of Object.entries(session))w.sessionStorage.setItem(key,value);
 w.eval(fs.readFileSync('src/static/analytics.js','utf8'));w.eval(fs.readFileSync('src/static/app.js','utf8'));
 return {dom,w,doc:w.document,events};
}
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
