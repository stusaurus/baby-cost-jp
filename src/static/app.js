(() => {
  const root = window.BABY_COST?.root || '/baby-cost-jp/';
  document.querySelectorAll('#diaper-selector').forEach((box) => {
    let segments = [];
    try { segments = JSON.parse(box.dataset.segments || '[]'); } catch (_) {}
    const typeButtons = [...box.querySelectorAll('.type-chip')];
    const sizeBox = box.querySelector('.size-chips');
    const go = box.querySelector('#diaper-go');
    if (!typeButtons.length || !sizeBox || !go) return;

    const labels = {newborn:'新生児',s:'S',m:'M',l:'L',big:'BIG',big_plus:'BIGより大きい'};
    let selectedType = box.dataset.currentType || 'pants';
    let selectedSize = box.dataset.currentSize || '';

    if (!segments.some((x) => x.type === selectedType)) selectedType = segments[0]?.type || 'pants';

    const setTypeActive = () => {
      typeButtons.forEach((btn) => {
        const active = btn.dataset.value === selectedType;
        btn.classList.toggle('is-active', active);
        btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
    };

    const renderSizes = () => {
      const rows = segments.filter((x) => x.type === selectedType);
      if (!rows.some((x) => x.size === selectedSize)) selectedSize = rows[0]?.size || '';
      sizeBox.innerHTML = rows.map((x) =>
        '<button type="button" class="filter-chip size-chip' + (x.size === selectedSize ? ' is-active' : '') + '" data-value="' + x.size + '" aria-pressed="' + (x.size === selectedSize ? 'true' : 'false') + '">' + (labels[x.size] || x.size) + '</button>'
      ).join('');
      sizeBox.querySelectorAll('.size-chip').forEach((btn) => {
        btn.addEventListener('click', () => {
          selectedSize = btn.dataset.value || '';
          sizeBox.querySelectorAll('.size-chip').forEach((b) => {
            const active = b === btn;
            b.classList.toggle('is-active', active);
            b.setAttribute('aria-pressed', active ? 'true' : 'false');
          });
          window.babyCostEvent?.('comparison_filter_change', {category_id:'diapers', filter_name:'size', filter_value:selectedSize});
        });
      });
    };

    typeButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        selectedType = btn.dataset.value || 'pants';
        selectedSize = '';
        setTypeActive();
        renderSizes();
        window.babyCostEvent?.('comparison_filter_change', {category_id:'diapers', filter_name:'type', filter_value:selectedType});
      });
    });

    go.addEventListener('click', () => {
      const row = segments.find((x) => x.type === selectedType && x.size === selectedSize);
      if (!row) return;
      window.babyCostEvent?.('comparison_filter_submit', {category_id:'diapers', product_type:selectedType, size:selectedSize, conversion_source:'diaper_selector'});
      try { sessionStorage.setItem('baby_cost_feature_navigation_v1', JSON.stringify({source:'diaper_selector', target:new URL(row.url, location.href).pathname, at:Date.now()})); } catch (_) {}
      location.href = row.url || root + 'diapers/' + selectedType + '/' + selectedSize + '/';
    });

    setTypeActive();
    renderSizes();
  });
})();


(() => {
  const formatYen = (value) => {
    const n = Number(value || 0);
    return n < 100 ? '¥' + n.toFixed(1) : '¥' + Math.round(n).toLocaleString('ja-JP');
  };
  document.querySelectorAll('[data-savings-sim]').forEach((box) => {
    const best = Number(box.dataset.best || 0);
    const median = Number(box.dataset.median || 0);
    const result = box.querySelector('[data-savings-result]');
    const buttons = [...box.querySelectorAll('[data-usage]')];
    if (!result || !buttons.length || best <= 0 || median <= 0) return;
    const update = (usage) => {
      const diff = Math.max(0, median - best);
      result.textContent = formatYen(diff * usage * 30);
      buttons.forEach((b) => b.classList.toggle('is-active', Number(b.dataset.usage) === usage));
      window.babyCostEvent?.('savings_simulator_use', {category_id:'diapers', usage_per_day:String(usage)});
    };
    buttons.forEach((button) => button.addEventListener('click', () => update(Number(button.dataset.usage || 5))));
  });
})();
