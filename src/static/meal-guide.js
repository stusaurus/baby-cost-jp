/* User-entered family-cost calculation; no inferred price, contract or nutrition. */
(() => {
  'use strict';
  const init = () => {
    const form = document.getElementById('tm-form');
    if (!form || form.dataset.ready === '1') return;
    form.dataset.ready = '1';
    const byId = id => document.getElementById(id);
    const result = byId('tm-results');
    const status = byId('tm-status');
    const formatYen = amount => Math.round(amount).toLocaleString('ja-JP') + '円';
    const formatUnit = amount => amount.toLocaleString('ja-JP', {
      maximumFractionDigits: 2, minimumFractionDigits: 0
    }) + '円';
    const fields = [
      ['tm-weekly', 1, 84],
      ['tm-bundle', 1, 200],
      ['tm-price', 0, 10000000],
      ['tm-shipping', 0, 1000000]
    ];

    form.addEventListener('submit', event => {
      event.preventDefault();
      result.hidden = true;
      const vals = Object.create(null);
      for (const [id, min, max] of fields) {
        const input = byId(id);
        const raw = input.value.trim();
        const n = Number(raw);
        if (!raw || !Number.isInteger(n) || n < min || n > max) {
          status.textContent = '食数は1以上の整数、価格と送料は0以上の整数で、すべての欄を入力してください。';
          return;
        }
        vals[id] = n;
      }
      const interval = Number(byId('tm-interval').value);
      if (![2, 3, 4].includes(interval)) {
        status.textContent = '配送周期は2・3・4週間から選んでください。';
        return;
      }
      // Twelve weeks divides exactly by each of the official delivery cycles.
      const deliveries = 12 / interval;
      const purchased = deliveries * vals['tm-bundle'];
      const needed = 12 * vals['tm-weekly'];
      const total = deliveries * (vals['tm-price'] + vals['tm-shipping']);
      const perMeal = total / purchased;
      if (![deliveries, purchased, needed, total, perMeal].every(Number.isFinite)) {
        status.textContent = '計算できませんでした。入力した値を確認してください。';
        return;
      }
      byId('tm-total').textContent = formatYen(total);
      byId('tm-average').textContent = formatYen(total / 3);
      byId('tm-deliveries').textContent = deliveries + '回';
      byId('tm-purchased').textContent = purchased + '食';
      byId('tm-needed').textContent = needed + '食';
      byId('tm-unit').textContent = formatUnit(perMeal);
      const balance = purchased - needed;
      byId('tm-balance').textContent = balance > 0
        ? '使う予定より' + balance + '食多く届く計算です。冷凍庫の容量・賞味期限と配送周期を確認してください。'
        : balance < 0
          ? '使う予定に対して' + (-balance) + '食不足する計算です。不足分は別途用意が必要です。'
          : '使う予定の食数と届く食数が一致します。';
      status.textContent = '入力した金額と配送条件から算出しました。実際の請求額は申込条件を確認してください。';
      result.hidden = false;
      window.babyCostEvent?.('meal_planner_use', {
        category_id: 'toddler_meals',
        delivery_interval_weeks: String(interval),
        balance_type: balance > 0 ? 'surplus' : balance < 0 ? 'shortage' : 'matched'
      });
    });

    const official = document.querySelector('#tm-mogumo-ad a[href^="https://px.a8.net/svt/ejp?"]');
    if (official) official.addEventListener('click', () => {
      window.babyCostEvent?.('affiliate_click', {
        affiliate: 'a8', category_id: 'toddler_meals',
        program: 'mogumo', conversion_source: 'toddler_meal_cost_planner',
        click_position: 'toddler_meal_sponsored_card'
      });
    });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
