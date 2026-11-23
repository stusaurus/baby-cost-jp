/* Local-only, whole-sale-set comparison for M tape and pants. No network, storage or personal-input analytics. */
((root) => {
  const integer = (n, min, max) => Number.isSafeInteger(n) && n >= min && n <= max;
  const valid = (offer) => offer && offer.verified === true &&
    integer(offer.total, 1, 20000) && integer(offer.price, 1, 999999999) &&
    typeof offer.id === 'string' && typeof offer.name === 'string';
  const checkout = (offers, daily, days, stock) => {
    if (!Array.isArray(offers) || offers.length < 2 ||
        !offers.every(valid) || !integer(daily, 1, 30) ||
        !integer(days, 1, 90) || !integer(stock, 0, 10000)) return null;
    const needed = daily * days;
    const shortage = Math.max(0, needed - stock);
    if (shortage === 0) return {
      needed, stock, shortage, sets: 0, bought: 0, payment: 0,
      surplus: stock - needed, noBuy: true, name: '買い足し不要'
    };
    const choices = offers.map(offer => {
      const sets = Math.ceil(shortage / offer.total);
      return {
        needed, stock, shortage, sets, bought: sets * offer.total,
        payment: sets * offer.price, surplus: stock + sets * offer.total - needed,
        noBuy: false, name: offer.name, id: offer.id,
        unitPrice: offer.price / offer.total, url: offer.url || ''
      };
    });
    choices.sort((a, b) => a.payment - b.payment ||
      a.surplus - b.surplus || a.id.localeCompare(b.id));
    return choices[0];
  };
  const compare = (data, daily, days, tapeStock, pantsStock) => {
    if (!data || !Array.isArray(data.tape) || !Array.isArray(data.pants)) return null;
    const tape = checkout(data.tape, daily, days, tapeStock);
    const pants = checkout(data.pants, daily, days, pantsStock);
    if (!tape || !pants) return null;
    return {tape, pants, needed: daily * days,
      winner: tape.payment === pants.payment ? 'same' :
        tape.payment < pants.payment ? 'tape' : 'pants',
      difference: Math.abs(tape.payment - pants.payment)};
  };
  const api = {checkout, compare};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.babyCostMTypePlanner = api;
})(typeof window === 'undefined' ? globalThis : window);

if (typeof document !== 'undefined') (() => {
  const box = document.querySelector('[data-m-type-planner]');
  if (!box || !window.babyCostMTypePlanner) return;
  const api = window.babyCostMTypePlanner;
  let data;
  try { data = JSON.parse(box.querySelector('[data-m-type-snapshot]').textContent); }
  catch (_) { return; }
  const inputs = {
    daily: box.querySelector('[data-m-type-input="daily"]'),
    days: box.querySelector('[data-m-type-input="days"]'),
    tapeStock: box.querySelector('[data-m-type-input="tape-stock"]'),
    pantsStock: box.querySelector('[data-m-type-input="pants-stock"]')
  };
  const result = box.querySelector('[data-m-type-live]');
  const error = box.querySelector('[data-m-type-error]');
  const number = value => value.toLocaleString('ja-JP');
  const yen = value => '¥' + number(value);
  const isRakuten = raw => {
    if (typeof raw !== 'string' || !raw) return false;
    try {
      const url = new URL(raw);
      return url.protocol === 'https:' && url.host === 'hb.afl.rakuten.co.jp' &&
        url.pathname.startsWith('/hgc/') && url.pathname.length > 5;
    } catch (_) { return false; }
  };
  const clearBuy = parent => {
    const buy = parent.querySelector('[data-m-type-buy]');
    const fallback = parent.querySelector('[data-m-type-fallback]');
    buy.hidden = true; buy.removeAttribute('href');
    ['productId', 'productName', 'unitPrice'].forEach(key => delete buy.dataset[key]);
    fallback.hidden = true;
  };
  const read = input => /^\d+$/.test(input.value) && input.checkValidity() &&
    Number.isSafeInteger(Number(input.value)) ? Number(input.value) : null;
  const set = (parent, key, value) => { parent.querySelector('[data-m-type-field="' + key + '"]').textContent = value; };
  const drawCard = (name, value) => {
    const parent = box.querySelector('[data-m-type-card="' + name + '"]');
    set(parent, 'payment', yen(value.payment));
    set(parent, 'shortage', number(value.shortage) + '枚');
    set(parent, 'sets', value.noBuy ? '0セット（購入不要）' : number(value.sets) + 'セット');
    set(parent, 'bought', number(value.bought) + '枚');
    set(parent, 'surplus', number(value.surplus) + '枚');
    set(parent, 'name', value.name);
    const buy = parent.querySelector('[data-m-type-buy]');
    const fallback = parent.querySelector('[data-m-type-fallback]');
    clearBuy(parent);
    if (!value.noBuy) {
      if (isRakuten(value.url) && typeof value.id === 'string' && value.id) {
        // Link and event metadata come from the *same selected* SKU.
        buy.href = value.url;
        buy.dataset.productId = value.id;
        buy.dataset.productName = value.name;
        buy.dataset.unitPrice = value.unitPrice.toFixed(4);
        buy.hidden = false;
      } else {
        // Never substitute a different retailer product or guessed URL.
        fallback.hidden = false;
      }
    }
    parent.classList.toggle('m-type-plan-card--no-buy', value.noBuy);
  };
  const update = () => {
    const raw = Object.fromEntries(Object.entries(inputs).map(([key, el]) => [key, read(el)]));
    for (const [key, el] of Object.entries(inputs)) {
      el.setAttribute('aria-invalid', String(raw[key] === null));
    }
    const value = Object.values(raw).every(v => v !== null) ?
      api.compare(data, raw.daily, raw.days, raw.tapeStock, raw.pantsStock) : null;
    error.hidden = Boolean(value);
    result.hidden = !value;
    if (!value) {
      ['tape', 'pants'].forEach(type => clearBuy(box.querySelector('[data-m-type-card="' + type + '"]')));
      error.textContent = '1日の枚数は1〜30枚、日数は1〜90日、各タイプの手持ちは0〜10000枚の整数で入力してください。';
      return;
    }
    error.textContent = '';
    set(result, 'needed', number(value.needed) + '枚');
    drawCard('tape', value.tape);
    drawCard('pants', value.pants);
    const verdict = value.winner === 'same' ? 'この条件では両タイプの買い足し支払額は同じです。' :
      (value.winner === 'tape' ? 'テープM' : 'パンツM') +
      'の掲載候補が ' + yen(value.difference) + ' 少ない見込みです。';
    set(result, 'verdict', verdict);
    set(result, 'stock-note', raw.tapeStock === raw.pantsStock ?
      '手持ち枚数は両タイプとも同じ条件です。' :
      '手持ち枚数が異なるため、この差額は商品の価格差だけではなく、保有在庫による買い足し額の差も含みます。');
    box.querySelectorAll('[data-m-type-days-choice]').forEach(button => {
      const pressed = Number(button.dataset.mTypeDaysChoice) === raw.days;
      button.classList.toggle('is-active', pressed);
      button.setAttribute('aria-pressed', String(pressed));
    });
  };
  box.querySelectorAll('[data-m-type-days-choice]').forEach(button => {
    button.addEventListener('click', () => {
      inputs.days.value = button.dataset.mTypeDaysChoice;
      update();
    });
  });
  Object.values(inputs).forEach(input => {
    input.addEventListener('input', update);
    input.addEventListener('change', update);
  });
  update();
})();