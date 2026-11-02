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
  const api = {calculate};
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
  const summary = box.querySelector('[data-purchase-summary]');
  const error = box.querySelector('[data-purchase-error]');
  const cards = [...document.querySelectorAll('[data-purchase-product]')];
  const number = n => n.toLocaleString('ja-JP');
  const yen = n => '¥' + number(n);
  let state = null;
  const read = (input, optional = false) => {
    if (optional && input.value === '' && !input.validity.badInput) return null;
    return /^\d+$/.test(input.value) && input.checkValidity() ? Number(input.value) : NaN;
  };
  api.render = raw => {
    if (!state) return '<p class="purchase-unavailable">使用枚数・日数の入力を確認してください。</p>';
    let product;
    try { product = JSON.parse(raw); } catch (_) {}
    const {daily, days, sizeDays} = state;
    const r = api.calculate(product, daily, days, sizeDays);
    if (!r) return '<p class="purchase-unavailable">購入計算はできません。販売総枚数・価格・送料条件の確認が必要です。</p>';
    let warning = '';
    if (r.sizeSurplus > 0) {
      warning = '<p class="purchase-warning">サイズ変更までの予定' + number(sizeDays) + '日では、購入分のうち' + number(r.sizeSurplus) + '枚が余る計算です。短い期間や少量の商品も確認してください。</p>';
    } else if (sizeDays === null && r.surplus >= r.needed) {
      warning = '<p class="purchase-warning">今回の必要枚数以上に余ります。まとめ買い前に、今のサイズを使い切れるか確認してください。</p>';
    }
    return '<p class="purchase-context">1日' + number(daily) + '枚 × ' + number(days) + '日：必要' + number(r.needed) + '枚</p>' +
      '<dl class="purchase-metrics"><div><dt>必要購入セット数</dt><dd data-plan-sets>' + number(r.sets) + '<small>セット</small></dd></div>' +
      '<div class="purchase-payment"><dt>購入時の支払額（掲載条件）</dt><dd data-plan-payment>' + yen(r.payment) + '</dd></div>' +
      '<div><dt>1セットの総枚数</dt><dd>' + number(r.total) + '<small>枚</small></dd></div>' +
      '<div><dt>購入後に余る枚数</dt><dd data-plan-surplus>' + number(r.surplus) + '<small>枚</small></dd></div></dl>' +
      '<p class="purchase-equivalent">使用' + number(r.needed) + '枚分の費用相当額：約¥' + (r.costTenths / 10).toLocaleString('ja-JP', {minimumFractionDigits:1, maximumFractionDigits:1}) + '（按分・支払額とは別）</p>' + warning;
  };
  const update = () => {
    const daily = read(dailyInput), days = read(daysInput), sizeDays = read(sizeInput, true);
    state = Number.isFinite(daily) && Number.isFinite(days) && (sizeDays === null || Number.isFinite(sizeDays)) ? {daily, days, sizeDays} : null;
    [dailyInput, daysInput, sizeInput].forEach((input, i) => input.setAttribute('aria-invalid', Number.isNaN([daily, days, sizeDays][i]) ? 'true' : 'false'));
    error.hidden = !!state;
    error.textContent = state ? '' : '使用枚数は1〜30枚、対象期間は1〜90日、サイズの予定は空欄または1〜180日の整数で入力してください。';
    summary.innerHTML = state ? '1日' + number(daily) + '枚 × ' + number(days) + '日 ＝ <strong>必要' + number(daily * days) + '枚</strong>' : '入力を確認すると計算結果を表示します。';
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
  [dailyInput, daysInput, sizeInput].forEach((input, i) => {
    input.addEventListener('input', update);
    input.addEventListener('change', () => {update(); track(['daily_input','days_input','size_plan'][i]);});
  });
  update();
})();
