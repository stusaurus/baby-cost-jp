(() => {
  "use strict";
  const form = document.querySelector("[data-nursery-form]");
  const output = document.querySelector("[data-nursery-output]");
  const error = document.querySelector("[data-nursery-error]");
  const catalogElement = document.getElementById("nursery-catalog");
  if (!form || !output || !error || !catalogElement) return;
  let catalog = [];
  try { catalog = JSON.parse(catalogElement.textContent || "[]"); } catch (_) {}
  if (!Array.isArray(catalog)) catalog = [];
  const input = (key) => form.elements.namedItem(key);
  const yen = (n) => "¥" + n.toLocaleString("ja-JP");
  const pieces = (n) => n.toLocaleString("ja-JP") + "枚";
  const add = (parent, tag, text, cls) => {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    el.textContent = text;
    parent.appendChild(el);
    return el;
  };
  function validInteger(key, maximum) {
    const value = input(key)?.value;
    if (value == null || value.trim() === "") throw new Error("空欄があるため計算できません。すべての項目を入力してください。");
    const n = Number(value);
    if (!Number.isInteger(n) || n < 0 || n > maximum) {
      throw new Error("枚数・日数は、指定した範囲内の整数で入力してください。");
    }
    return n;
  }
  function recalculate() {
    const period = validInteger("period", 30);
    if (![7, 14, 30].includes(period)) throw new Error("計算期間を選び直してください。");
    const attend = validInteger("attend", period);
    const homeAttend = validInteger("homeAttend", 30);
    const homeOff = validInteger("homeOff", 30);
    const mode = input("mode").value;
    if (!["bring", "subscription"].includes(mode)) throw new Error("園のおむつの用意方法を選んでください。");
    const nurseryDaily = mode === "bring" ? validInteger("nurseryDaily", 30) : 0;
    const reserve = mode === "bring" && attend > 0 ? validInteger("reserve", 100) : 0;
    const stock = validInteger("stock", 1000);
    const home = attend * homeAttend + (period - attend) * homeOff;
    const nursery = mode === "bring" ? attend * nurseryDaily + reserve : 0;
    const needed = home + nursery;
    const shortage = Math.max(0, needed - stock);
    return { period, attend, home, nursery, needed, stock, shortage, mode };
  }
  function offerSelection(shortage) {
    return catalog.filter((p) => {
      if (!p || typeof p !== "object") return false;
      if (!(Number.isSafeInteger(p.price) && p.price > 0 && Number.isSafeInteger(p.pieces) && p.pieces > 0)) return false;
      try {
        const u = new URL(p.url);
        return u.protocol === "https:" && u.hostname === "hb.afl.rakuten.co.jp" && u.pathname.startsWith("/hgc/");
      } catch (_) { return false; }
    }).map((p) => {
      const sets = Math.ceil(shortage / p.pieces);
      return { ...p, sets, payment: sets * p.price, excess: sets * p.pieces - shortage };
    });
  }
  function optionCard(parent, heading, p) {
    const box = add(parent, "article", "", "nursery-offer");
    add(box, "h3", heading);
    add(box, "p", p.name, "nursery-offer-name");
    const dl = document.createElement("dl");
    box.appendChild(dl);
    const row = (label, value) => {
      const div = document.createElement("div");
      add(div, "dt", label);
      add(div, "dd", value);
      dl.appendChild(div);
    };
    row("購入セット数", p.sets + "セット／計" + pieces(p.sets * p.pieces));
    row("今回の支払額（掲載条件）", yen(p.payment));
    row("購入後の余り", pieces(p.excess));
    const link = document.createElement("a");
    link.href = p.url;
    link.target = "_blank";
    link.rel = "nofollow sponsored noopener";
    link.dataset.affiliate = "rakuten";
    link.dataset.categoryId = "diapers";
    link.dataset.productName = String(p.name || "").slice(0, 100);
    link.dataset.productId = String(p.id || "");
    link.dataset.size = "m";
    link.dataset.productType = "pants";
    link.dataset.unitMetric = "per_piece";
    link.dataset.unitPrice = String(p.price / p.pieces);
    link.dataset.clickPosition = "nursery_plan_offer";
    // Preserve source attribution for direct Google landings on the guide.
    // A prior same-tab navigation source still takes precedence in analytics.js.
    link.dataset.conversionSource = "nursery_plan_offer";
    link.textContent = "楽天で最新の価格・数量を確認する →";
    box.appendChild(link);
  }
  function show(result) {
    output.replaceChildren();
    output.hidden = false;
    const heading = add(output, "h2", "必要なおむつの計算結果");
    heading.tabIndex = -1;
    const grid = add(output, "div", "", "nursery-totals");
    const metric = (label, value) => {
      const el = add(grid, "div", "", "nursery-total");
      add(el, "span", label);
      add(el, "strong", pieces(value));
    };
    metric("家庭で使う分", result.home);
    metric(result.mode === "bring" ? "園への持参分（予備含む）" : "園分の家庭購入", result.nursery);
    metric("合計確保したい枚数", result.needed);
    metric("手持ちを引いた不足", result.shortage);
    if (result.mode === "subscription") {
      add(output, "p", "園への持参が不要な前提です。サブスク費用・契約条件は含めていません。", "nursery-disclaimer");
    }
    if (result.shortage === 0) {
      add(output, "p", "この計算条件なら追加購入は0セットです。手持ち在庫だけで足りるため、買い足しは不要です。", "nursery-no-buy");
      return heading;
    }
    // A generic nursery shortage is not evidence the child wears pants-M.
    // Never display M-size affiliate offers unless the guardian explicitly
    // selects the currently used size on this submission.
    if (input("productSize")?.value !== "pants-m") {
      add(output, "p", "必要枚数のみを計算しました。パンツMを現在使用中と確認できた場合だけ、このページで商品と購入セット数を比較できます。ほかのサイズはタイプ・サイズ別の比較一覧をご利用ください。", "nursery-disclaimer");
      const link = document.createElement("a");
      link.href = "/baby-cost-jp/diapers/";
      link.textContent = "自分に合うタイプ・サイズの比較へ進む →";
      link.className = "nursery-size-link";
      link.dataset.navSource = "nursery_unconfirmed_size";
      link.dataset.categoryId = "diapers";
      output.appendChild(link);
      return heading;
    }
    const offers = offerSelection(result.shortage);
    if (offers.length === 0) {
      add(output, "p", "現在、数量と価格を確認できたパンツMの商品がありません。必要枚数のみを表示します。", "nursery-disclaimer");
      return heading;
    }
    add(output, "h3", "パンツMを使用中の場合の買い方比較");
    add(output, "p", "現在掲載しているパンツMの検証済み" + offers.length + "商品の中から、この不足枚数に必要な販売セット数で比較しています。");
    const cheapest = [...offers].sort((a, b) => a.payment - b.payment || a.excess - b.excess || a.id.localeCompare(b.id))[0];
    const smallest = [...offers].sort((a, b) => a.excess - b.excess || a.payment - b.payment || a.id.localeCompare(b.id))[0];
    const cards = add(output, "div", "", "nursery-offer-grid");
    optionCard(cards, "支払額が少ない商品", cheapest);
    if (smallest.id !== cheapest.id) {
      optionCard(cards, "余りが少ない商品", smallest);
      add(output, "p", "今回の掲載条件では、" + yen(smallest.payment - cheapest.payment) + "多く支払うと、余りを" + pieces(cheapest.excess - smallest.excess) + "減らせます。", "nursery-tradeoff");
    } else add(output, "p", "支払額と余りが最小の候補は同じ商品です。", "nursery-tradeoff");
    add(output, "p", "パンツM以外のサイズには、この商品候補は適用できません。園の指定メーカー・サイズと現在のフィットを確認してください。楽天全商品の最安値ではありません。配送先別送料・在庫・注文制限・サブスク料金は購入前に別途確認してください。", "nursery-disclaimer");
    return heading;
  }
  function updateMode() {
    const disabled = input("mode").value !== "bring";
    form.querySelectorAll("[data-nursery-bring]").forEach((el) => {
      el.hidden = disabled;
      const control = el.querySelector("input");
      if (control) control.disabled = disabled;
    });
  }
  input("mode").addEventListener("change", updateMode);
  updateMode();
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    try {
      const result = recalculate();
      error.hidden = true;
      const heading = show(result);
      heading.focus({ preventScroll: false });
      // Only the completion event is measured; no diary, stock, daycare,
      // health, attendance, or numeric raw values are ever sent to GA4.
      if (typeof window.babyCostEvent === "function") {
        window.babyCostEvent("nursery_plan_complete", { calculator_type: "home_and_nursery" });
      }
    } catch (e) {
      output.replaceChildren();
      output.hidden = true;
      error.textContent = e.message || "入力内容を確認してください。";
      error.hidden = false;
      error.focus?.();
    }
  });
})();
