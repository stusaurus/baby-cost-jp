(() => {
  const ROOT = '/baby-cost-jp/';
  const TEST_KEY = 'baby_cost_operator_test_v1';
  const SITE_ID = window.BABY_COST?.siteId || 'baby_cost_jp';
  const NAV_KEY = 'baby_cost_feature_navigation_v1';
  const params = new URLSearchParams(location.search);
  let inheritedSource = '';
  try {
    const nav = JSON.parse(sessionStorage.getItem(NAV_KEY) || 'null');
    sessionStorage.removeItem(NAV_KEY);
    if (nav && nav.target === location.pathname && Date.now() - Number(nav.at || 0) < 30 * 60 * 1000) inheritedSource = String(nav.source || '');
  } catch (_) {}
  let operator = window.BABY_COST_OPERATOR_TEST === true;
  if (!operator) { try { operator = localStorage.getItem(TEST_KEY) === '1'; } catch (_) {} }
  if (params.get('test') === '1' || params.get('test') === '0') {
    operator = params.get('test') === '1';
    try { operator ? localStorage.setItem(TEST_KEY,'1') : localStorage.removeItem(TEST_KEY); } catch (_) {}
    const u = new URL(location.href); u.searchParams.delete('test');
    try { history.replaceState(history.state,'',u.href); } catch (_) {}
  }
  const send = (name, data = {}) => {
    if (typeof window.gtag !== 'function') return;
    const payload = {site_id:SITE_ID, ...data};
    if (operator) payload.operator_test = '1';
    window.gtag('event', name, payload);
  };
  window.babyCostEvent = send;
  if (operator && typeof window.gtag === 'function') window.gtag('set', {operator_test:'1', site_id:SITE_ID});

  document.querySelectorAll('[data-comparison]').forEach((node) => send('comparison_view', {
    category_id: node.dataset.categoryId || '', size: node.dataset.size || '', product_type: node.dataset.productType || '',
    result_count: Number(node.dataset.resultCount || 0), page_path: location.pathname
  }));

  document.addEventListener('click', (event) => {
    const target = event.target?.closest ? event.target : event.target?.parentElement;
    const link = target?.closest('a[data-nav-source]');
    if (!link) return;
    const source = link.dataset.navSource || '';
    try {
      const url = new URL(link.href, location.href);
      if (url.origin === location.origin) {
        sessionStorage.setItem(NAV_KEY, JSON.stringify({source, target:url.pathname, at:Date.now()}));
      }
    } catch (_) {}
    if (link.dataset.categoryId) send('category_select', {
      category_id: link.dataset.categoryId, conversion_source: source, page_path: location.pathname
    });
  }, true);

  document.addEventListener('toggle', (event) => {
    const stage = event.target;
    if(stage.matches?.('[data-growth-stage]') && stage.open) send('growth_stage_select', {growth_stage:stage.dataset.growthStage, page_path:location.pathname});
  }, true);

  function affiliate(event) {
    if (event.type === 'auxclick' && event.button !== 1) return;
    const target = event.target?.closest ? event.target : event.target?.parentElement;
    const link = target?.closest('a[data-affiliate]');
    if (!link) return;
    const data = {
      affiliate: link.dataset.affiliate || '', conversion_source: inheritedSource || 'comparison_result', category_id: link.dataset.categoryId || '',
      product_name: (link.dataset.productName || '').slice(0,100), product_id: link.dataset.productId || '',
      size: link.dataset.size || '', product_type: link.dataset.productType || '', unit_metric: link.dataset.unitMetric || '',
      unit_price: Number(link.dataset.unitPrice || 0), rank: Number(link.closest('.product')?.querySelector('.rank')?.textContent || link.dataset.rank || 0), click_position: link.dataset.clickPosition || '',
      link_url: link.href, page_path: location.pathname, transport_type:'beacon'
    };
    send('product_result_click', data);
    send('affiliate_click', data);
  }
  document.addEventListener('click', affiliate);
  document.addEventListener('auxclick', affiliate);
})();
