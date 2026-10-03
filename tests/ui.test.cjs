const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require('jsdom');
const base='https://stusaurus.github.io/baby-cost-jp/';
function setup(path, storage={}) {
 const dom=new JSDOM(fs.readFileSync('site/'+path,'utf8'),{url:base+path.replace('index.html',''),runScripts:'outside-only'});
 const w=dom.window;const events=[];w.gtag=(...args)=>events.push(args);
 for(const [key,value] of Object.entries(storage))w.localStorage.setItem(key,value);
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
test('comparison dialog opens, closes with Escape and restores focus',()=>{
 const {w,doc}=setup('diapers/pants/m/index.html');
 [...doc.querySelectorAll('[data-compare-add]')].forEach(x=>x.click());
 doc.querySelector('[data-compare-open]').click();
 assert.equal(doc.querySelector('[data-compare-modal]').hidden,false);
 assert.equal(doc.querySelectorAll('.compare-column').length,2);
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
test('growth selection tracked on disclosure open',()=>{
 const {w,doc,events}=setup('index.html');const details=doc.querySelector('[data-growth-stage]');details.open=true;details.dispatchEvent(new w.Event('toggle'));
 assert(events.some(x=>x[1]==='growth_stage_select' && x[2].growth_stage==='newborn'));w.close();
});
