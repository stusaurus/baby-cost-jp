(() => {
  const root = window.BABY_COST?.root || '/baby-cost-jp/';
  document.querySelectorAll('#diaper-selector').forEach((box) => {
    let segments = [];
    try { segments = JSON.parse(box.dataset.segments || '[]'); } catch (_) {}
    const type = box.querySelector('#diaper-type');
    const size = box.querySelector('#diaper-size');
    const go = box.querySelector('#diaper-go');
    if (!type || !size || !go) return;
    const currentType = box.dataset.currentType || '';
    const currentSize = box.dataset.currentSize || '';
    const labels = {newborn:'新生児',s:'S',m:'M',l:'L',big:'BIG',big_plus:'BIGより大きい'};
    const sync = () => {
      const rows = segments.filter((x) => x.type === type.value);
      size.innerHTML = rows.map((x) => `<option value="${x.size}">${labels[x.size] || x.size}</option>`).join('');
      if (currentSize && rows.some((x) => x.size === currentSize)) size.value = currentSize;
    };
    if (currentType && segments.some((x) => x.type === currentType)) type.value = currentType;
    type.addEventListener('change', () => { sync(); window.babyCostEvent?.('comparison_filter_change', {category_id:'diapers', filter_name:'type', filter_value:type.value}); });
    size.addEventListener('change', () => window.babyCostEvent?.('comparison_filter_change', {category_id:'diapers', filter_name:'size', filter_value:size.value}));
    go.addEventListener('click', () => {
      const row = segments.find((x) => x.type === type.value && x.size === size.value);
      if (!row) return;
      window.babyCostEvent?.('comparison_filter_submit', {category_id:'diapers', product_type:type.value, size:size.value, conversion_source:'diaper_selector'});
      try { sessionStorage.setItem('baby_cost_feature_navigation_v1', JSON.stringify({source:'diaper_selector', target:new URL(row.url, location.href).pathname, at:Date.now()})); } catch (_) {}
      location.href = row.url || `${root}diapers/${type.value}/${size.value}/`;
    });
    sync();
  });
})();
