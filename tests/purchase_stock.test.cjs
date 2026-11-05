const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {calculateWithStock}=require('../src/static/purchase.js');
const p={verified:true,total:60,price:980};
test('stock exactly covers need, no purchase',()=>{
  const r=calculateWithStock(p,5,30,null,150);
  assert.equal(r.noBuy,true);assert.equal(r.payment,0);assert.equal(r.sets,0);
});
test('stock is subtracted before rounding sets',()=>{
  const r=calculateWithStock(p,5,30,null,30);
  assert.equal(r.shortage,120);assert.equal(r.sets,2);assert.equal(r.payment,1960);
});
test('size review also bounds a zero-stock order',()=>{
  const r=calculateWithStock(p,5,30,10,0);
  assert.equal(r.needed,50);
  assert.equal(r.shortage,50);
  assert.equal(r.sets,1);
  assert.equal(r.payment,980);
  assert.equal(r.surplus,10);
});
test('size review horizon bounds purchase quantity',()=>{
  const r=calculateWithStock(p,5,30,10,5);
  assert.equal(r.needed,50);assert.equal(r.shortage,45);assert.equal(r.sets,1);assert.equal(r.surplus,15);
});
test('missing evidence cannot produce payment when purchase needed',()=>{
  assert.equal(calculateWithStock({},5,30,null,0),null);
});
test('invalid stock rejected',()=>{
  for(const n of [-1,1.5,10001,NaN])assert.equal(calculateWithStock(p,5,30,null,n),null);
});
test('sorting and markup both use stock',()=>{
  const app=fs.readFileSync('src/static/app.js','utf8');
  const render=fs.readFileSync('src/render.py','utf8');
  assert.match(app,/calculateWithStock\(/);
  assert.match(render,/data-purchase-stock/);
});
