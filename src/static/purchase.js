/* Integer yen and pieces only. No rounded unit-price or inner-pack arithmetic. */
((root) => {
  const positive = (n, max) => Number.isSafeInteger(n) && n > 0 && n <= max;
  const calculate = (product, daily, days, sizeDays = null) => {
    if (!positive(daily, 30) || !positive(days, 90) ||
        (sizeDays !== null && !positive(sizeDays, 180))) return null;
    if (!product || product.verified !== true || !positive(product.total, 20000) ||
        !positive(product.price, 999999999)) return null;
    const needed = daily * days;
    const sets = Math.ceil(needed / product.total);
    const purchased = sets * product.total;
    const payment = sets * product.price;
    // Round the final fraction once, half up, without binary fractional errors.
    const costTenths = Math.floor((product.price * needed * 20 + product.total) / (product.total * 2));
    return {needed, total: product.total, sets, payment, surplus: purchased - needed,
      costTenths, sizeSurplus: sizeDays === null ? null : Math.max(0, purchased - daily * sizeDays)};
  };
  const calculateWithStock = (product, daily, days, sizeDays = null, stock = 0) => {
    if (!Number.isSafeInteger(stock) || stock < 0 || stock > 10000 ||
        !positive(daily, 30) || !positive(days, 90) ||
        (sizeDays !== null && !positive(sizeDays, 180))) return null;
    const horizon = sizeDays === null ? days : Math.min(days, sizeDays);
    const needed = daily * horizon;
    const shortage = Math.max(0, needed - stock);
    if (shortage === 0) return {needed, shortage:0, stock, sets:0, payment:0, surplus:0, noBuy:true, sizeSurplus:0, costTenths:0};
    const base = calculate(product, daily, days, sizeDays);
    if (!base) return null;
    const sets = Math.ceil(shortage / product.total);
    return {...base, needed, shortage, stock, sets, payment:sets * product.price,
      surplus:sets * product.total - shortage,
      sizeSurplus:sizeDays === null ? null : Math.max(0, sets * product.total - shortage),
      costTenths:Math.floor((product.price * shortage * 20 + product.total)/(product.total * 2))};
  };
  const api = {calculate, calculateWithStock};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.babyCostPurchase = api;
})(typeof window === 'undefined' ? globalThis : window);

if (typeof document !== 'undefined') (() => {
  const box = document.querySelector('[data-purchase-planner]');
  if (!box) return;
  const api = window.babyCostPurchase;
  const dailyInput = box.querySelector('[data-purchase-daily]');
  const daysInput = box.querySelector('[data-purchase-days]');
  const sizeInput = box.querySelector('[data-purchase-size-days]');
  const stockInput = box.querySelector('[data-purchase-stock]');
  const summary = box.querySelector('[data-purchase-summary]');
  const error = box.querySelector('[data-purchase-error]');
  const cards = [...document.querySelectorAll('[data-purchase-product]')];
  const number = n => n.toLocaleString('ja-JP');
  const yen = n => '¥' + number(n);
  let state = null;
  // Provide the validated local inputs to the page sorter; never send them to analytics.
  api.currentPlan = () => state ? {...state} : null;
  const read = (input, optional = false) => {
    if (optional && input.value === '' && !input.validity.badInput) return null;
    return /^\d+$/.test(input.value) && input.checkValidity() ? Number(input.value) : NaN;
  };
  api.render = raw => {
    if (!state) return '<p class="purchase-unavailable">使用枚数・日数の入力を確認してください。</p>';
    let product;
    try { product = JSON.parse(raw); } catch (_) {}
    const {daily, days, sizeDays, stock} = state;
    const r = api.calculateWithStock(product, daily, days, sizeDays, stock);
    if (!r) return '<p class="purchase-unavailable">購入計算はできません。販売総枚数・価格・送料条件の確認が必要です。</p>';
    if (r.noBuy) return '<p class="purchase-context" data-purchase-no-buy>今は買い足し不要です。手持ちの' + number(stock) + '枚で、予定する' + number(r.needed) + '枚をまかなえます。</p>';
    let warning = '';
    if (r.sizeSurplus > 0) {
      warning = '<p class="purchase-warning">サイズ変更までの予定' + number(sizeDays) + '日では、購入分のうち' + number(r.sizeSurplus) + '枚が余る計算です。短い期間や少量の商品も確認してください。</p>';
    } else if (sizeDays === null && r.surplus >= r.needed) {
      warning = '<p class="purchase-warning">今回の必要枚数以上に余ります。まとめ買い前に、今のサイズを使い切れるか確認してください。</p>';
    }
    return '<p class="purchase-context">必要' + number(r.needed) + '枚 − 手持ち' + number(stock) + '枚 ＝ 不足' + number(r.shortage) + '枚</p>' +
      '<dl class="purchase-metrics"><div><dt>必要購入セット数</dt><dd data-plan-sets>' + number(r.sets) + '<small>セット</small></dd></div>' +
      '<div class="purchase-payment"><dt>購入時の支払額（掲載条件）</dt><dd data-plan-payment>' + yen(r.payment) + '</dd></div>' +
      '<div><dt>1セットの総枚数</dt><dd>' + number(r.total) + '<small>枚</small></dd></div>' +
      '<div><dt>購入後に余る枚数</dt><dd data-plan-surplus>' + number(r.surplus) + '<small>枚</small></dd></div></dl>' +
      '<p class="purchase-equivalent">使用' + number(r.needed) + '枚分の費用相当額：約¥' + (r.costTenths / 10).toLocaleString('ja-JP', {minimumFractionDigits:1, maximumFractionDigits:1}) + '（按分・支払額とは別）</p>' + warning;
  };
  const update = () => {
    const daily = read(dailyInput), days = read(daysInput), sizeDays = read(sizeInput, true), stock = read(stockInput);
    state = Number.isFinite(daily) && Number.isFinite(days) && Number.isSafeInteger(stock) && stock >= 0 && stock <= 10000 && (sizeDays === null || Number.isFinite(sizeDays)) ? {daily, days, sizeDays, stock} : null;
    [dailyInput, daysInput, sizeInput, stockInput].forEach((input, i) => input.setAttribute('aria-invalid', Number.isNaN([daily, days, sizeDays, stock][i]) || (i===3 && (!Number.isSafeInteger(stock) || stock<0 || stock>10000)) ? 'true' : 'false'));
    error.hidden = !!state;
    error.textContent = state ? '' : '使用枚数は1〜30枚、対象期間は1〜90日、サイズの予定は空欄または1〜180日、手持ちは0〜10000枚の整数で入力してください。';
    summary.innerHTML = state ? '予定' + number(daily * (sizeDays === null ? days : Math.min(days,sizeDays))) + '枚 − 手持ち' + number(stock) + '枚 ＝ <strong>不足' + number(Math.max(0,daily * (sizeDays === null ? days : Math.min(days,sizeDays)) - stock)) + '枚</strong>' : '入力を確認すると計算結果を表示します。';
    box.querySelectorAll('[data-usage]').forEach(b => {
      const active = Number(b.dataset.usage) === daily;
      b.classList.toggle('is-active', active); b.setAttribute('aria-pressed', String(active));
    });
    box.querySelectorAll('[data-purchase-days-choice]').forEach(b => {
      const active = Number(b.dataset.purchaseDaysChoice) === days;
      b.classList.toggle('is-active', active); b.setAttribute('aria-pressed', String(active));
    });
    const saving = box.querySelector('[data-savings-result]');
    box.querySelector('[data-savings-period]').textContent = state ? days + '日' : '入力した期間';
    saving.textContent = !state ? '—' : Number(box.dataset.savingsCount) < 2 ? '比較できる商品が不足しています' : '約¥' + (Math.max(0, Number(box.dataset.median) - Number(box.dataset.best)) * daily * days).toLocaleString('ja-JP', {minimumFractionDigits:1, maximumFractionDigits:1});
    cards.forEach(card => { card.querySelector('[data-purchase-result]').innerHTML = api.render(card.dataset.purchaseProduct); });
    document.dispatchEvent(new CustomEvent('purchase-plan-change'));
  };
  const track = action => {
    if (!state) return;
    // Record use, never raw household inputs, a purchase, or a purchase value.
    window.babyCostEvent?.('purchase_planner_use', {action, conversion_source:'diaper_purchase_planner'});
    if (action === 'daily_preset' || action === 'daily_input') window.babyCostEvent?.('savings_simulator_use', {conversion_source:'diaper_purchase_planner'});
  };
  box.querySelectorAll('[data-usage]').forEach(b => b.addEventListener('click', () => {dailyInput.value = b.dataset.usage; update(); track('daily_preset');}));
  box.querySelectorAll('[data-purchase-days-choice]').forEach(b => b.addEventListener('click', () => {daysInput.value = b.dataset.purchaseDaysChoice; update(); track('days_preset');}));
  [dailyInput, daysInput, sizeInput, stockInput].forEach((input, i) => {
    input.addEventListener('input', update);
    input.addEventListener('change', () => {update(); track(['daily_input','days_input','size_plan','stock_input'][i]);});
  });
  update();
})();
