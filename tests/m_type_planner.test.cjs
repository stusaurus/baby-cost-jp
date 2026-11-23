const test = require('node:test');
const assert = require('node:assert/strict');
const {checkout, compare} = require('../src/static/m_type_planner.js');

const catalog = {
  tape: [
    {id:'tape-74', name:'テープ74枚', price:2680, total:74, verified:true},
    {id:'tape-248', name:'テープ248枚', price:6920, total:248, verified:true}
  ],
  pants: [
    {id:'pants-50', name:'パンツ50枚', price:2100, total:50, verified:true},
    {id:'pants-180', name:'パンツ180枚', price:6100, total:180, verified:true}
  ]
};

test('7 / 14 / 30 days compare whole checkout sets, not unit cost', () => {
  const a = compare(catalog, 6, 7, 0, 0);
  assert.equal(a.needed, 42);
  assert.deepEqual([a.tape.payment, a.pants.payment, a.winner, a.difference], [2680, 2100, 'pants', 580]);
  const b = compare(catalog, 6, 14, 0, 0);
  assert.deepEqual([b.tape.sets, b.tape.payment, b.tape.surplus], [2, 5360, 64]);
  assert.deepEqual([b.pants.sets, b.pants.payment, b.pants.surplus], [2, 4200, 16]);
  const c = compare(catalog, 6, 30, 0, 0);
  assert.deepEqual([c.tape.sets, c.tape.payment, c.tape.surplus], [1, 6920, 68]);
  assert.deepEqual([c.pants.sets, c.pants.payment, c.pants.surplus], [1, 6100, 0]);
});

test('inventory is type-specific and purchase is zero when the type stock is sufficient', () => {
  const a = compare(catalog, 6, 14, 84, 0);
  assert.deepEqual([a.tape.payment, a.tape.sets, a.tape.surplus, a.tape.noBuy], [0, 0, 0, true]);
  assert.equal(a.pants.payment, 4200);
  assert.equal(a.winner, 'tape');
  const b = compare(catalog, 6, 14, 0, 100);
  assert.deepEqual([b.pants.payment, b.pants.sets, b.pants.surplus], [0, 0, 16]);
  assert.equal(b.tape.payment, 5360);
  const both = compare(catalog, 6, 14, 100, 90);
  assert.deepEqual([both.tape.payment, both.pants.payment, both.winner], [0, 0, 'same']);
  assert.equal(both.tape.surplus, 16);
});

test('stock is subtracted before rounding whole purchase sets', () => {
  const x = checkout(catalog.tape, 6, 14, 20);
  assert.deepEqual([x.needed, x.shortage, x.sets, x.bought, x.surplus, x.payment], [84, 64, 1, 74, 10, 2680]);
});

test('invalid and unsafe catalogs or household inputs never generate prices', () => {
  for (const changed of [
    {...catalog, tape: []}, {...catalog, tape: catalog.tape.slice(0, 1)},
    {...catalog, tape:[catalog.tape[0], {...catalog.tape[1], verified:false}]},
    {...catalog, tape:[catalog.tape[0], {...catalog.tape[1], price:0}]},
    {...catalog, pants:[catalog.pants[0], {...catalog.pants[1], total:1.5}]}
  ]) assert.equal(compare(changed, 6, 14, 0, 0), null);
  for (const args of [[0,14,0,0],[31,14,0,0],[6,0,0,0],[6,91,0,0],
    [6,14,-1,0],[6,14,10001,0],[6,14,0,0.5],[NaN,14,0,0]]) {
    assert.equal(compare(catalog, ...args), null);
  }
});

test('no input data leaves the local algorithm and output never links to a product', () => {
  assert.equal(typeof compare(catalog,6,14,0,0).pants.name, 'string');
  assert.equal('url' in compare(catalog,6,14,0,0).pants, false);
});