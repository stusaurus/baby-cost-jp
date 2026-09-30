from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import shutil
import sys
from urllib.request import Request, urlopen
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DATA_DIR, SITE_DIR, SITE_URL, load_categories  # noqa: E402
from src.parsing import norm, parse_for_segment_detailed, unit_price  # noqa: E402
from src.rakuten import fetch_items  # noqa: E402
from src.render import (  # noqa: E402
    render_comparison,
    render_diaper_index,
    render_home,
    render_method,
    segment_url,
    write_page,
)

QUALITY_AUDIT_REASONS = {
    "ambiguous_diaper_size",
    "ambiguous_diaper_size_selection",
    "ambiguous_diaper_type",
    "ambiguous_diaper_type_selection",
    "duplicate_equivalent_name",
}


def load_fixtures() -> dict:
    return json.loads((DATA_DIR / "fixtures.json").read_text(encoding="utf-8"))


def load_previous_latest(fixture: bool = False) -> dict:
    if fixture:
        return {}
    try:
        request = Request(f"{SITE_URL}data/latest.json", headers={"User-Agent": "baby-cost-jp-builder/1.0"})
        with urlopen(request, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"PRICE_HISTORY previous snapshot unavailable: {exc}")
        return {}


def load_previous_history(fixture: bool = False) -> dict:
    if fixture:
        return {}
    try:
        request = Request(f"{SITE_URL}data/price-history.json", headers={"User-Agent": "baby-cost-jp-builder/1.0"})
        with urlopen(request, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"PRICE_HISTORY archive unavailable: {exc}")
        return {}


def _same_quantity(current: dict, previous: dict) -> bool:
    current_q = current.get("quantity") or {}
    previous_q = previous.get("quantity") or {}
    if current_q.get("base_unit") != previous_q.get("base_unit"):
        return False
    try:
        return abs(float(current_q.get("total", 0)) - float(previous_q.get("total", 0))) <= 1e-9
    except (TypeError, ValueError):
        return False


def attach_price_history(
    products: list[dict],
    segment_id: str,
    previous_history: dict,
    previous_segment: dict | None,
    previous_generated_at: str | None,
    generated_at: str,
) -> dict:
    old_segment = ((previous_history.get("segments") or {}).get(segment_id) or {})
    old_products = old_segment.get("products") or {}
    previous_products = {
        p.get("source_id"): p
        for p in (previous_segment or {}).get("products", [])
        if p.get("source_id")
    }
    new_products = {}

    for product in products:
        source_id = product.get("source_id")
        if not source_id:
            continue

        points = []
        old_entry = old_products.get(source_id)
        if old_entry and _same_quantity(product, old_entry):
            points = list(old_entry.get("points") or [])[-13:]
        else:
            previous = previous_products.get(source_id)
            if previous and previous_generated_at and _same_quantity(product, previous):
                points = [{
                    "at": previous_generated_at,
                    "price_yen": int(previous.get("price_yen", 0)),
                    "unit_price": float(previous.get("unit_price", 0)),
                }]

        current_point = {
            "at": generated_at,
            "price_yen": int(product.get("price_yen", 0)),
            "unit_price": float(product.get("unit_price", 0)),
        }
        if not points or points[-1].get("at") != generated_at:
            points.append(current_point)
        points = points[-14:]

        if len(points) >= 2:
            product["price_history"] = points

        quantity = product.get("quantity") or {}
        new_products[source_id] = {
            "name": product.get("name", ""),
            "base_unit": quantity.get("base_unit"),
            "total": quantity.get("total"),
            "points": points,
        }

    return {"products": new_products}


def attach_price_changes(products: list[dict], previous_segment: dict | None) -> list[dict]:
    if not previous_segment:
        return []
    previous_by_id = {
        p.get("source_id"): p
        for p in previous_segment.get("products", [])
        if p.get("source_id")
    }
    drops = []
    for product in products:
        source_id = product.get("source_id")
        previous = previous_by_id.get(source_id)
        if not previous:
            continue
        if not _same_quantity(product, previous):
            continue
        try:
            current_price = int(product.get("price_yen", 0))
            previous_price = int(previous.get("price_yen", 0))
            current_unit = float(product.get("unit_price", 0))
            previous_unit = float(previous.get("unit_price", 0))
        except (TypeError, ValueError):
            continue
        delta_price = current_price - previous_price
        delta_unit = current_unit - previous_unit
        status = "down" if delta_price < 0 else ("up" if delta_price > 0 else "same")
        change = {
            "status": status,
            "previous_price_yen": previous_price,
            "price_delta_yen": delta_price,
            "previous_unit_price": previous_unit,
            "unit_delta": round(delta_unit, 4),
        }
        product["price_change"] = change
        if delta_price < 0 and previous_price > 0:
            drops.append({
                "product": product,
                "drop_yen": -delta_price,
                "drop_percent": round((-delta_price / previous_price) * 100, 1),
            })
    return drops


def featured_candidate(products: list[dict], category_id: str, category: dict, segment: dict) -> dict | None:
    if len(products) < 2:
        return None
    values = sorted(float(p["unit_price"]) for p in products)
    n = len(values)
    median = values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2
    best = min(products, key=lambda p: (p["unit_price"], -int(p.get("review_count") or 0)))
    if median <= 0:
        return None
    gap = max(0.0, median - float(best["unit_price"]))
    pct = gap / median * 100
    return {
        "category_id": category_id,
        "category_label": category["name"],
        "segment_id": segment["id"],
        "segment_label": segment["label"],
        "url": segment_url(category, segment),
        "metric": category["metric"],
        "unit_price": float(best["unit_price"]),
        "median_unit_price": round(median, 4),
        "gap_percent": round(pct, 1),
        "product": best,
    }


def _canonical_product_name(name: str) -> str:
    text = norm(name).lower()
    return re.sub(r"[^0-9a-zぁ-んァ-ヶ一-龯]+", "", text)


def _audit_append(audit: list[dict] | None, reason: str, item: dict):
    if audit is None or reason not in QUALITY_AUDIT_REASONS:
        return
    audit.append({
        "reason": reason,
        "source_id": item.get("source_id", ""),
        "name": item.get("name", ""),
        "shop": item.get("shop", ""),
        "price_yen": item.get("price_yen", 0),
    })


def normalize_products(raw_items: list[dict], category_id: str, category: dict, segment: dict, audit: list[dict] | None = None) -> list[dict]:
    candidates = []
    seen_source = set()
    for item in raw_items:
        source_key = item.get("source_id") or f'{item.get("name")}|{item.get("price_yen")}|{item.get("shop")}'
        if source_key in seen_source:
            continue
        seen_source.add(source_key)

        supplemental = " ".join(x for x in [item.get("catchcopy", ""), item.get("caption", "")] if x)
        parsed, reject_reason = parse_for_segment_detailed(
            item.get("name", ""), category["parser"], segment, supplemental_text=supplemental
        )
        if not parsed:
            _audit_append(audit, reject_reason, item)
            continue
        price = unit_price(item.get("price_yen", 0), category["metric"], parsed["quantity"])
        if price is None or parsed["quantity"]["confidence"] < 0.88:
            continue
        candidates.append({
            **item,
            "category_id": category_id,
            "segment_id": segment["id"],
            **parsed,
            "unit_metric": category["metric"],
            "unit_price": round(price, 4),
        })

    # Sort before title-level dedupe so equivalent listings keep the cheapest valid offer.
    candidates.sort(key=lambda p: (p["unit_price"], -int(p.get("review_count") or 0), p["name"]))
    rows = []
    seen_names = set()
    for row in candidates:
        name_key = _canonical_product_name(row.get("name", ""))
        if name_key and name_key in seen_names:
            _audit_append(audit, "duplicate_equivalent_name", row)
            continue
        if name_key:
            seen_names.add(name_key)
        rows.append(row)
    return rows[:10]


def output_path(category: dict, segment: dict) -> Path:
    if category["parser"] == "diapers":
        return SITE_DIR / "diapers" / segment["type"] / segment["size"] / "index.html"
    return SITE_DIR / category["path"] / "index.html"


def main(fixture: bool = False, pages: int = 2):
    categories = load_categories()
    fixtures = load_fixtures() if fixture else {}
    updated_at = datetime.now(ZoneInfo("Asia/Tokyo"))
    previous_latest = load_previous_latest(fixture=fixture)
    previous_history = load_previous_history(fixture=fixture)
    previous_generated_at = previous_latest.get("generated_at")

    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)
    shutil.copytree(ROOT / "src" / "static", SITE_DIR / "static")

    snapshots = {}
    featured_candidates = []
    price_drop_candidates = []
    history_segments = {}
    latest = {
        "schema_version": 1,
        "generated_at": updated_at.isoformat(),
        "site_url": SITE_URL,
        "pricing_scope": "rakuten_postage_included_or_free_shipping",
        "ranking_excludes": ["points", "coupons"],
        "previous_generated_at": previous_generated_at,
        "categories": {},
    }
    quality_audit = {
        "generated_at": updated_at.isoformat(),
        "segments": {},
        "categories": {},
        "excluded_problem_products": [],
    }
    sitemap_urls = [SITE_URL, f"{SITE_URL}diapers/", f"{SITE_URL}method/"]

    for category_id, category in categories.items():
        category_rows = []
        category_count = 0
        for segment in category["segments"]:
            if fixture:
                raw = fixtures.get(segment["id"], [])
            else:
                raw = []
                queries = segment.get("queries") or [segment["query"]]
                for query in queries:
                    raw.extend(fetch_items(query, pages=pages))
            segment_audit: list[dict] = []
            products = normalize_products(raw, category_id, category, segment, audit=segment_audit)
            previous_segment = (previous_latest.get("categories") or {}).get(segment["id"])
            segment_drops = attach_price_changes(products, previous_segment)
            history_segments[segment["id"]] = attach_price_history(
                products,
                segment["id"],
                previous_history,
                previous_segment,
                previous_generated_at,
                updated_at.isoformat(),
            )
            for row in segment_drops:
                row.update({
                    "category_id": category_id,
                    "category_label": category["name"],
                    "segment_id": segment["id"],
                    "segment_label": segment["label"],
                    "url": segment_url(category, segment),
                })
                price_drop_candidates.append(row)
            candidate = featured_candidate(products, category_id, category, segment)
            if candidate:
                featured_candidates.append(candidate)
            category_rows.extend(products)
            category_count += len(products)
            url = segment_url(category, segment)
            write_page(output_path(category, segment), render_comparison(categories, category_id, category, segment, products, updated_at))
            if len(products) >= 2:
                sitemap_urls.append(url)
            latest["categories"][segment["id"]] = {
                "category_id": category_id,
                "label": segment["label"],
                "query": segment["query"], "queries": segment.get("queries") or [segment["query"]],
                "result_count": len(products),
                "indexable": len(products) >= 2,
                "products": [
                    {
                        "source": p.get("source", ""), "source_id": p.get("source_id", ""), "name": p["name"],
                        "price_yen": p["price_yen"], "shop": p.get("shop", ""), "affiliate_url": p.get("url", ""),
                        "unit_price": p["unit_price"], "unit_metric": p["unit_metric"], "quantity": p["quantity"],
                        "manufacturer": p["manufacturer"], "brand": p["brand"], "attributes": p["attributes"],
                        "price_change": p.get("price_change"),
                        "history_points": len(p.get("price_history") or []),
                    } for p in products
                ],
            }
            reason_counts = dict(Counter(row["reason"] for row in segment_audit))
            quality_audit["segments"][segment["id"]] = {
                "category_id": category_id,
                "label": segment["label"],
                "raw_candidates": len(raw),
                "published_count": len(products),
                "problem_exclusions": reason_counts,
                "published_products": [
                    {"source_id": p.get("source_id", ""), "name": p.get("name", "")}
                    for p in products
                ],
            }
            for row in segment_audit:
                quality_audit["excluded_problem_products"].append({"segment_id": segment["id"], **row})
        quality_audit["categories"][category_id] = {"published_count": category_count}
        if category_id != "diapers":
            snapshots[category_id] = sorted(category_rows, key=lambda p: p["unit_price"])[:3]

    featured_deals = []
    for category_id in categories:
        rows = [row for row in featured_candidates if row["category_id"] == category_id]
        if rows:
            featured_deals.append(max(rows, key=lambda row: (row["gap_percent"], -row["unit_price"])))
    featured_deals.sort(key=lambda row: row["gap_percent"], reverse=True)
    latest["featured_deals"] = [
        {
            "category_id": row["category_id"],
            "segment_id": row["segment_id"],
            "segment_label": row["segment_label"],
            "unit_price": row["unit_price"],
            "median_unit_price": row["median_unit_price"],
            "gap_percent": row["gap_percent"],
            "source_id": row["product"].get("source_id", ""),
        }
        for row in featured_deals
    ]

    price_drop_candidates.sort(key=lambda row: (row["drop_percent"], row["drop_yen"]), reverse=True)
    price_drops = price_drop_candidates[:4]
    latest["price_drop_count"] = len(price_drop_candidates)

    write_page(SITE_DIR / "index.html", render_home(categories, snapshots, featured_deals, price_drops, updated_at))
    write_page(SITE_DIR / "diapers" / "index.html", render_diaper_index(categories, updated_at))
    write_page(SITE_DIR / "method" / "index.html", render_method())

    (SITE_DIR / "data").mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "data" / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8")
    (SITE_DIR / "data" / "quality-audit.json").write_text(json.dumps(quality_audit, ensure_ascii=False, indent=2), encoding="utf-8")
    price_changes = {
        "generated_at": updated_at.isoformat(),
        "previous_generated_at": previous_generated_at,
        "drop_count": len(price_drop_candidates),
        "drops": [
            {
                "category_id": row["category_id"],
                "segment_id": row["segment_id"],
                "source_id": row["product"].get("source_id", ""),
                "name": row["product"].get("name", ""),
                "drop_yen": row["drop_yen"],
                "drop_percent": row["drop_percent"],
                "current_price_yen": row["product"].get("price_yen", 0),
                "previous_price_yen": row["product"].get("price_change", {}).get("previous_price_yen", 0),
            }
            for row in price_drop_candidates
        ],
    }
    (SITE_DIR / "data" / "price-changes.json").write_text(json.dumps(price_changes, ensure_ascii=False, indent=2), encoding="utf-8")
    price_history = {
        "schema_version": 1,
        "generated_at": updated_at.isoformat(),
        "max_points": 14,
        "segments": history_segments,
    }
    (SITE_DIR / "data" / "price-history.json").write_text(json.dumps(price_history, ensure_ascii=False, indent=2), encoding="utf-8")
    (SITE_DIR / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    unique_urls = list(dict.fromkeys(sitemap_urls))
    lastmod = updated_at.date().isoformat()
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(
        f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>" for url in unique_urls
    ) + "\n</urlset>\n"
    (SITE_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    print("QUALITY_AUDIT_COUNTS")
    for segment_id, stats in quality_audit["segments"].items():
        print(f"QUALITY segment={segment_id} published={stats['published_count']} raw={stats['raw_candidates']} exclusions={json.dumps(stats['problem_exclusions'], ensure_ascii=False, sort_keys=True)}")
    for category_id, stats in quality_audit["categories"].items():
        print(f"QUALITY category={category_id} published={stats['published_count']}")
    for segment_id, stats in quality_audit["segments"].items():
        for row in stats.get("published_products", []):
            print(f"QUALITY_PUBLISHED segment={segment_id} source_id={row['source_id']} name={row['name']}")
    for row in quality_audit["excluded_problem_products"]:
        print(f"QUALITY_EXCLUDED segment={row['segment_id']} reason={row['reason']} source_id={row['source_id']} name={row['name']}")
    print(f"Built {len(unique_urls)} indexable URLs at {SITE_DIR} ({'fixture' if fixture else 'live'})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", action="store_true", help="Build from local fixture data; no API access")
    parser.add_argument("--pages", type=int, default=2, help="Rakuten result pages per comparison segment (1-3)")
    args = parser.parse_args()
    main(fixture=args.fixture, pages=args.pages)
