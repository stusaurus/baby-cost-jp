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
      buttons.forEach((b) => {b.classList.toggle('is-active', Number(b.dataset.usage) === usage);b.setAttribute('aria-pressed',Number(b.dataset.usage)===usage?'true':'false');});
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
  const traySlots = dock.querySelector('[data-tray-slots]');
  const storageKey = 'baby_cost_tray_v1:' + location.pathname;
  const escapeHtml = value => String(value || '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
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
      button.closest('.product')?.classList.toggle('is-selected', active);
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
      button.innerHTML = active ? '<span>✓</span> トレーに入りました' : '<span>＋</span> 比較トレーに入れる';
    });
    count.textContent = selected.size + ' / 3商品を選択';
    const remaining = dock.querySelector('[data-compare-remaining]');
    if (remaining) remaining.textContent = selected.size < 3 ? 'あと' + (3-selected.size) + '商品選べます' : '3商品を比較できます';
    dock.hidden = selected.size === 0;
    open.disabled = selected.size < 2;
    open.textContent = selected.size < 2 ? 'もう1つ選ぶ' : 'くらべてみる';
    if (traySlots) {
      const items = [...selected.values()];
      traySlots.innerHTML = [0,1,2].map(index => {
        const item = items[index];
        return item ? '<button type="button" class="tray-slot is-filled" data-tray-remove="' + escapeHtml(item.id) + '" aria-label="' + escapeHtml(item.name) + 'をトレーから外す">' + (item.image ? '<img src="' + escapeHtml(item.image) + '" alt="">' : '<span>' + escapeHtml(item.unitLabel) + '</span>') + '<span class="tray-remove" aria-hidden="true">×</span></button>' : '<span class="tray-slot" aria-hidden="true">' + (index+1) + '</span>';
      }).join('');
      traySlots.querySelectorAll('[data-tray-remove]').forEach((button, index) => button.addEventListener('click', () => {
        const id = button.dataset.trayRemove;
        selected.delete(id);
        sync();
        const remainingSlots = [...traySlots.querySelectorAll('[data-tray-remove]')];
        const next = remainingSlots[Math.min(index, remainingSlots.length - 1)]
          || buttons.find(button => parse(button).id === id);
        next?.focus({preventScroll: true});
      }));
    }
    try { sessionStorage.setItem(storageKey, JSON.stringify([...selected.keys()])); } catch (_) {}
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

  try {
    const saved = JSON.parse(sessionStorage.getItem(storageKey) || '[]');
    if (Array.isArray(saved)) saved.slice(0,3).forEach(id => {const button=buttons.find(b => parse(b).id===id);if(button)selected.set(id,parse(button));});
  } catch (_) {}

  let background = [];
  open.addEventListener('click', () => {
    if (selected.size < 2) return;
    renderTable();
    modal.hidden = false;
    document.body.classList.add('compare-modal-open');
    modal.querySelector('.compare-close')?.focus();
    background = [];
    for (let branch = modal; branch.parentElement && branch !== document.body; branch = branch.parentElement) {
      [...branch.parentElement.children].forEach(element => {
        if (element !== branch) {
          background.push({element, inert: element.inert});
          element.inert = true;
        }
      });
    }
    window.babyCostEvent?.('product_compare_open', {selected_count:String(selected.size)});
  });

  const closeModal = () => {
    modal.hidden = true;
    document.body.classList.remove('compare-modal-open');
    background.forEach(({element, inert}) => {element.inert = inert;});
    background = [];
    open.focus();
  };
  closeButtons.forEach((button) => button.addEventListener('click', closeModal));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !modal.hidden) closeModal();
    if (event.key === 'Tab' && !modal.hidden) {
      const focusable = [...modal.querySelectorAll('button:not([disabled]),a[href]')];
      const first = focusable[0], last = focusable[focusable.length-1];
      if (event.shiftKey && document.activeElement === first) {event.preventDefault(); last?.focus();}
      else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first?.focus();}
    }
  });
  clear?.addEventListener('click', () => {
    const firstId = selected.keys().next().value;
    selected.clear();
    sync();
    buttons.find(button => parse(button).id === firstId)?.focus({preventScroll: true});
  });
  sync();
})();


(() => {
  document.querySelectorAll('[data-view-switcher]').forEach((switcher) => {
    const comparison = switcher.closest('.comparison');
    const list = comparison?.querySelector('[data-sortable-products]');
    const label = comparison?.querySelector('[data-result-sort-label]');
    const buttons = [...switcher.querySelectorAll('[data-sort-mode]')];
    if (!list || !buttons.length || !label) return;

    const labels = {
      unit: '単価が安い順',
      price: '支払総額が安い順',
      quantity: '大容量順'
    };

    const apply = (mode) => {
      const cards = [...list.querySelectorAll('.product')];
      const get = (card) => Number(
        mode === 'unit' ? card.dataset.sortUnit :
        mode === 'price' ? card.dataset.sortPrice :
        card.dataset.sortQuantity
      ) || 0;

      cards.sort((a,b) => {
        const av=get(a), bv=get(b);
        if (mode === 'quantity') return bv-av || Number(a.dataset.originalRank||0)-Number(b.dataset.originalRank||0);
        return av-bv || Number(a.dataset.originalRank||0)-Number(b.dataset.originalRank||0);
      });

      cards.forEach((card,index) => {
        list.appendChild(card);
        const rank=index+1;
        const rankEl=card.querySelector('.rank');
        const badge=card.querySelector('.rank-badge');
        if (rankEl) {
          rankEl.textContent=String(rank);
          rankEl.className='rank rank-' + rank;
        }
        card.classList.remove(...[...card.classList].filter((x)=>/^product-rank-\d+$/.test(x)));
        card.classList.add('product-rank-' + rank);
        if (badge) {
          badge.textContent =
            mode === 'unit' ? (rank === 1 ? '最安' : rank + '位') :
            mode === 'price' ? (rank === 1 ? '総額最安' : '総額 ' + rank + '位') :
            (rank === 1 ? '最大容量' : '容量 ' + rank + '位');
        }
      });

      buttons.forEach((button) => {
        const active=button.dataset.sortMode===mode;
        button.classList.toggle('is-active',active);
        button.setAttribute('aria-pressed',active?'true':'false');
      });
      label.textContent=labels[mode] || labels.unit;
      window.babyCostEvent?.('comparison_sort', {
        category_id: comparison?.dataset.categoryId || '',
        sort_mode: mode
      });
    };

    buttons.forEach((button) => {button.setAttribute('aria-pressed',button.classList.contains('is-active')?'true':'false'); button.addEventListener('click', () => apply(button.dataset.sortMode || 'unit'));});
  });
})();


(() => {
  document.querySelectorAll('[data-buying-guide]').forEach((guide) => {
    const comparison = guide.closest('.comparison');
    const result = guide.querySelector('[data-buy-guide-result]');
    const buttons = [...guide.querySelectorAll('[data-buy-goal]')];
    if (!comparison || !result || !buttons.length) return;

    const copy = {
      unit: ['単価重視で並べます','1枚・100gあたりが安い順に切り替えました。'],
      price: ['支払総額重視で並べます','販売価格そのものが安い順に切り替えました。'],
      quantity: ['まとめ買い重視で並べます','内容量が多い順に切り替えました。']
    };

    buttons.forEach((button) => {
      button.addEventListener('click', () => {
        const goal = button.dataset.buyGoal || 'unit';
        buttons.forEach((b) => {b.classList.toggle('is-active', b === button);b.setAttribute('aria-pressed',b===button?'true':'false');});
        const sortButton = comparison.querySelector('[data-sort-mode="' + goal + '"]');
        sortButton?.click();

        const [title, text] = copy[goal] || copy.unit;
        result.hidden = false;
        const strong = result.querySelector('strong');
        const span = result.querySelector('span');
        if (strong) strong.textContent = title;
        if (span) span.textContent = text;

        window.babyCostEvent?.('buying_guide_select', {
          category_id: comparison.dataset.categoryId || '',
          goal
        });

        comparison.querySelector('[data-result-sort-label]')?.scrollIntoView({
          behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
          block: 'center'
        });
      });
    });
  });
})();


(() => {
  document.querySelectorAll('[data-brand-compare]').forEach((section) => {
    const comparison = section.closest('.comparison');
    const products = [...(comparison?.querySelectorAll('[data-sortable-products] .product') || [])];
    const buttons = [...section.querySelectorAll('[data-brand-filter]')];
    const clear = section.querySelector('[data-brand-filter-clear]');
    if (!comparison || !products.length || !buttons.length || !clear) return;

    const apply = (brand) => {
      products.forEach((card) => {
        card.hidden = !!brand && card.dataset.brand !== brand;
      });
      buttons.forEach((button) => {button.classList.toggle('is-active', button.dataset.brandFilter === brand);button.setAttribute('aria-pressed',button.dataset.brandFilter === brand?'true':'false');});
      clear.hidden = !brand;
      if (brand) {
        window.babyCostEvent?.('brand_filter_select', {
          category_id: comparison.dataset.categoryId || '',
          brand
        });
        comparison.querySelector('[data-sortable-products]')?.scrollIntoView({
          behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
          block: 'start'
        });
      }
    };

    buttons.forEach((button) => button.addEventListener('click', () => {
      const brand = button.dataset.brandFilter || '';
      apply(button.classList.contains('is-active') ? '' : brand);
    }));
    clear.addEventListener('click', () => apply(''));
  });
})();

// Expand the nearby condition selector before following its page link.
document.querySelectorAll('a[href="#condition-change"]').forEach(link => link.addEventListener('click',()=>{const box=document.getElementById('condition-change');if(box)box.open=true;}));
