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


(() => {
  const buttons = [...document.querySelectorAll('[data-compare-add]')];
  const dock = document.querySelector('[data-compare-dock]');
  const count = document.querySelector('[data-compare-count]');
  const open = document.querySelector('[data-compare-open]');
  const clear = document.querySelector('[data-compare-clear]');
  const modal = document.querySelector('[data-compare-modal]');
  const table = document.querySelector('[data-compare-table]');
  const closeButtons = [...document.querySelectorAll('[data-compare-close]')];
  if (!buttons.length || !dock || !count || !open || !modal || !table) return;

  const selected = new Map();
  const parse = (button) => ({
    id: button.dataset.compareId || button.dataset.compareName || String(Math.random()),
    name: button.dataset.compareName || '',
    unit: Number(button.dataset.compareUnit || 0),
    unitLabel: button.dataset.compareUnitLabel || '',
    price: Number(button.dataset.comparePrice || 0),
    quantity: button.dataset.compareQuantity || '',
    image: button.dataset.compareImage || '',
    rank: Number(button.dataset.compareRank || 0)
  });

  const sync = () => {
    buttons.forEach((button) => {
      const item = parse(button);
      const active = selected.has(item.id);
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
      button.innerHTML = active ? '<span>✓</span> 比較中' : '<span>＋</span> 比較に追加';
    });
    count.textContent = selected.size + '件選択';
    dock.hidden = selected.size === 0;
    open.disabled = selected.size < 2;
    open.textContent = selected.size < 2 ? 'もう1商品選ぶ' : '選んだ商品を比較';
  };

  const renderTable = () => {
    const items = [...selected.values()];
    const bestUnit = Math.min(...items.map((x) => x.unit || Infinity));
    table.innerHTML = items.map((item) => {
      const image = item.image
        ? '<div class="compare-cell-image"><img src="' + item.image.replace(/"/g,'&quot;') + '" alt="" loading="lazy"></div>'
        : '<div class="compare-cell-image compare-cell-image--empty">商品</div>';
      const best = Math.abs(item.unit - bestUnit) < 0.0001;
      return '<article class="compare-column' + (best ? ' is-best' : '') + '">' +
        '<div class="compare-column-badge">' + (best ? 'この中で最安' : item.rank + '位') + '</div>' +
        image +
        '<h3>' + item.name.replace(/[&<>"']/g,(m)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])) + '</h3>' +
        '<dl><div><dt>単価</dt><dd>¥' + (item.unit < 100 ? item.unit.toFixed(1) : Math.round(item.unit).toLocaleString('ja-JP')) + '<small> / ' + item.unitLabel + '</small></dd></div>' +
        '<div><dt>販売価格</dt><dd>¥' + Math.round(item.price).toLocaleString('ja-JP') + '</dd></div>' +
        '<div><dt>内容量</dt><dd>' + item.quantity + '</dd></div></dl></article>';
    }).join('');
  };

  buttons.forEach((button) => {
    button.setAttribute('aria-pressed','false');
    button.addEventListener('click', () => {
      const item = parse(button);
      if (selected.has(item.id)) {
        selected.delete(item.id);
      } else {
        if (selected.size >= 3) {
          dock.classList.remove('compare-dock-shake');
          void dock.offsetWidth;
          dock.classList.add('compare-dock-shake');
          count.textContent = '3商品までです';
          return;
        }
        selected.set(item.id, item);
        window.babyCostEvent?.('product_compare_select', {product_id:item.id, rank:String(item.rank)});
      }
      sync();
    });
  });

  open.addEventListener('click', () => {
    if (selected.size < 2) return;
    renderTable();
    modal.hidden = false;
    document.body.classList.add('compare-modal-open');
    modal.querySelector('.compare-close')?.focus();
    window.babyCostEvent?.('product_compare_open', {selected_count:String(selected.size)});
  });

  const closeModal = () => {
    modal.hidden = true;
    document.body.classList.remove('compare-modal-open');
    open.focus();
  };
  closeButtons.forEach((button) => button.addEventListener('click', closeModal));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !modal.hidden) closeModal();
  });
  clear?.addEventListener('click', () => {
    selected.clear();
    sync();
  });
  sync();
})();
