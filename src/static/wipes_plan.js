(() => {
  "use strict";
  const form = document.querySelector("[data-wipes-plan-form]");
  const output = document.querySelector("[data-wipes-plan-output]");
  const error = document.querySelector("[data-wipes-plan-error]");
  const payload = document.getElementById("wipes-plan-catalog");
  if (!form || !output || !error || !payload) return;

  let catalog = [];
  try { catalog = JSON.parse(payload.textContent || "[]"); } catch (_) {}
  if (!Array.isArray(catalog)) catalog = [];

  const get = (name) => form.elements.namedItem(name);
  const yen = (n) => "¥" + n.toLocaleString("ja-JP");
  const sheets = (n) => n.toLocaleString("ja-JP") + "枚";
  function add(parent, tag, text, className) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = text;
    parent.appendChild(el);
    return el;
  }
  function integerField(name, maximum) {
    const raw = get(name)?.value;
    if (typeof raw !== "string" || raw.trim() === "") {
      throw new Error("空欄があります。すべての項目を入力してください。");
    }
    const n = Number(raw);
    if (!Number.isSafeInteger(n) || n < 0 || n > maximum) {
      throw new Error("日数・枚数は指定された範囲内の整数で入力してください。");
    }
    return n;
  }
  function safeOffer(item) {
    if (!item || typeof item !== "object" ||
        !Number.isSafeInteger(item.price) || item.price <= 0 ||
        !Number.isSafeInteger(item.pieces) || item.pieces <= 0 ||
        !Number.isSafeInteger(item.rank) || item.rank < 1) return false;
    try {
      const url = new URL(item.url);
      return url.protocol === "https:" && url.hostname === "hb.afl.rakuten.co.jp" &&
             url.pathname.startsWith("/hgc/") && !url.username && !url.password;
    } catch (_) { return false; }
  }
  function offerCard(parent, label, row) {
    const card = add(parent, "article", "", "wipes-plan-offer");
    add(card, "h4", label);
    add(card, "p", String(row.name || ""), "wipes-plan-offer-name");
    const dl = document.createElement("dl");
    for (const [title, value] of [
      ["買うセット数", row.sets + "セット（合計" + sheets(row.sets * row.pieces) + "）"],
      ["掲載条件での支払総額", yen(row.payment)],
      ["購入後に余る枚数", sheets(row.excess)]
    ]) {
      const div = document.createElement("div");
      add(div, "dt", title);
      add(div, "dd", value);
      dl.appendChild(div);
    }
    card.appendChild(dl);
    const detail = document.createElement("a");
    detail.href = "#rank-" + row.rank;
    detail.textContent = "一覧で仕様・厚さも確認する ↓";
    detail.className = "wipes-plan-detail";
    card.appendChild(detail);
    const buy = document.createElement("a");
    buy.href = row.url;
    buy.target = "_blank";
    buy.rel = "nofollow sponsored noopener";
    buy.dataset.affiliate = "rakuten";
    buy.dataset.categoryId = "wipes";
    buy.dataset.productId = String(row.id || "");
    buy.dataset.productName = String(row.name || "").slice(0, 100);
    buy.dataset.unitMetric = "per_piece";
    buy.dataset.unitPrice = String(row.price / row.pieces);
    buy.dataset.rank = String(row.rank);
    buy.dataset.clickPosition = "wipes_plan_offer";
    buy.dataset.conversionSource = "wipes_plan_offer";
    buy.className = "wipes-plan-buy";
    buy.textContent = "楽天で最新の価格・枚数を確認 →";
    card.appendChild(buy);
  }
  function renderResult(need, stock, deficit, period) {
    output.replaceChildren();
    output.hidden = false;
    const title = add(output, "h3", "買い足し計算の結果");
    title.tabIndex = -1;
    const stats = add(output, "div", "", "wipes-plan-stats");
    const metric = (label, value) => {
      const row = add(stats, "div", "", "wipes-plan-stat");
      add(row, "span", label);
      add(row, "strong", sheets(value));
    };
    metric(period + "日分に必要", need);
    metric("今ある枚数", stock);
    metric("買い足しが必要", deficit);
    if (deficit === 0) {
      add(output, "p", "この条件では追加購入は0セットです。まだ十分あるため、買い足しは不要です。", "wipes-plan-no-buy");
      return title;
    }
    const results = catalog.filter(safeOffer).map(row => {
      const sets = Math.ceil(deficit / row.pieces);
      return { ...row, sets, payment: row.price * sets, excess: row.pieces * sets - deficit };
    }).filter(row => Number.isSafeInteger(row.payment) && row.payment > 0);
    if (!results.length) {
      add(output, "p", "現在、掲載価格・枚数・送料条件の根拠がそろった商品がないため、買い足し枚数のみを表示します。", "wipes-plan-caveat");
      return title;
    }
    const leastPayment = [...results].sort((a,b) =>
      a.payment - b.payment || a.excess - b.excess || a.rank - b.rank)[0];
    const leastWaste = [...results].sort((a,b) =>
      a.excess - b.excess || a.payment - b.payment || a.rank - b.rank)[0];
    add(output, "p", "販売単位に切り上げ、現在の検証済み" + results.length + "商品の中で比較した結果です。");
    const grid = add(output, "div", "", "wipes-plan-offers");
    offerCard(grid, "支払総額が小さい候補", leastPayment);
    if (leastWaste.rank !== leastPayment.rank) {
      offerCard(grid, "余りが少ない候補", leastWaste);
      const extraCost = leastWaste.payment - leastPayment.payment;
      const lessWaste = leastPayment.excess - leastWaste.excess;
      add(output, "p", "この例では" + yen(extraCost) + "多く払うと、余りを" + sheets(lessWaste) + "減らせます。", "wipes-plan-tradeoff");
    } else {
      add(output, "p", "今回の条件では、支払額も余りも小さい候補は同じです。", "wipes-plan-tradeoff");
    }
    add(output, "p", "掲載されている商品の中での結果です。使用感やシート寸法は価格から判定できません。肌に合うかを確認し、初めて使う種類の大量購入は慎重に判断してください。", "wipes-plan-caveat");
    return title;
  }
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    try {
      const daily = integerField("daily", 200);
      const period = integerField("period", 30);
      if (![7, 14, 30].includes(period)) throw new Error("計算日数を選び直してください。");
      const stock = integerField("stock", 30000);
      const need = daily * period;
      const deficit = Math.max(0, need - stock);
      error.hidden = true;
      const title = renderResult(need, stock, deficit, period);
      title.focus({ preventScroll:false });
      // Do not send usage frequency, stock, period, or shortage to GA4.
      if (typeof window.babyCostEvent === "function") {
        window.babyCostEvent("wipes_plan_complete", { calculator_type:"wipes_usage_and_stock" });
      }
    } catch (e) {
      output.replaceChildren();
      output.hidden = true;
      error.textContent = e.message || "入力内容を確認してください。";
      error.hidden = false;
    }
  });
})();
