from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import shutil
import sys
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

    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)
    shutil.copytree(ROOT / "src" / "static", SITE_DIR / "static")

    snapshots = {}
    latest = {
        "schema_version": 1,
        "generated_at": updated_at.isoformat(),
        "site_url": SITE_URL,
        "pricing_scope": "rakuten_postage_included_or_free_shipping",
        "ranking_excludes": ["points", "coupons"],
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
            }
            for row in segment_audit:
                quality_audit["excluded_problem_products"].append({"segment_id": segment["id"], **row})
        quality_audit["categories"][category_id] = {"published_count": category_count}
        if category_id != "diapers":
            snapshots[category_id] = sorted(category_rows, key=lambda p: p["unit_price"])[:3]

    write_page(SITE_DIR / "index.html", render_home(categories, snapshots, updated_at))
    write_page(SITE_DIR / "diapers" / "index.html", render_diaper_index(categories, updated_at))
    write_page(SITE_DIR / "method" / "index.html", render_method())

    (SITE_DIR / "data").mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "data" / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8")
    (SITE_DIR / "data" / "quality-audit.json").write_text(json.dumps(quality_audit, ensure_ascii=False, indent=2), encoding="utf-8")
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
    for row in quality_audit["excluded_problem_products"]:
        print(f"QUALITY_EXCLUDED segment={row['segment_id']} reason={row['reason']} source_id={row['source_id']} name={row['name']}")
    print(f"Built {len(unique_urls)} indexable URLs at {SITE_DIR} ({'fixture' if fixture else 'live'})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", action="store_true", help="Build from local fixture data; no API access")
    parser.add_argument("--pages", type=int, default=2, help="Rakuten result pages per comparison segment (1-3)")
    args = parser.parse_args()
    main(fixture=args.fixture, pages=args.pages)
