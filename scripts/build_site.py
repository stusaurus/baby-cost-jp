from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DATA_DIR, SITE_DIR, SITE_URL, load_categories  # noqa: E402
from src.parsing import parse_for_segment, unit_price  # noqa: E402
from src.rakuten import fetch_items  # noqa: E402
from src.render import (  # noqa: E402
    render_comparison,
    render_diaper_index,
    render_home,
    render_method,
    segment_url,
    write_page,
)


def load_fixtures() -> dict:
    return json.loads((DATA_DIR / "fixtures.json").read_text(encoding="utf-8"))


def normalize_products(raw_items: list[dict], category_id: str, category: dict, segment: dict) -> list[dict]:
    rows = []
    seen = set()
    for item in raw_items:
        parsed = parse_for_segment(item.get("name", ""), category["parser"], segment)
        if not parsed:
            continue
        price = unit_price(item.get("price_yen", 0), category["metric"], parsed["quantity"])
        if price is None or parsed["quantity"]["confidence"] < 0.88:
            continue
        key = item.get("source_id") or f'{item.get("name")}|{item.get("price_yen")}|{item.get("shop")}'
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            **item,
            "category_id": category_id,
            "segment_id": segment["id"],
            **parsed,
            "unit_metric": category["metric"],
            "unit_price": round(price, 4),
        })
    rows.sort(key=lambda p: (p["unit_price"], -int(p.get("review_count") or 0), p["name"]))
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
    sitemap_urls = [SITE_URL, f"{SITE_URL}diapers/", f"{SITE_URL}method/"]

    for category_id, category in categories.items():
        category_rows = []
        for segment in category["segments"]:
            if fixture:
                raw = fixtures.get(segment["id"], [])
            else:
                raw = []
                queries = segment.get("queries") or [segment["query"]]
                for query in queries:
                    raw.extend(fetch_items(query, pages=pages))
            products = normalize_products(raw, category_id, category, segment)
            category_rows.extend(products)
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
        if category_id != "diapers":
            snapshots[category_id] = sorted(category_rows, key=lambda p: p["unit_price"])[:3]

    write_page(SITE_DIR / "index.html", render_home(categories, snapshots, updated_at))
    write_page(SITE_DIR / "diapers" / "index.html", render_diaper_index(categories, updated_at))
    write_page(SITE_DIR / "method" / "index.html", render_method())

    (SITE_DIR / "data").mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "data" / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8")
    (SITE_DIR / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    unique_urls = list(dict.fromkeys(sitemap_urls))
    lastmod = updated_at.date().isoformat()
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(
        f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>" for url in unique_urls
    ) + "\n</urlset>\n"
    (SITE_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"Built {len(unique_urls)} indexable URLs at {SITE_DIR} ({'fixture' if fixture else 'live'})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", action="store_true", help="Build from local fixture data; no API access")
    parser.add_argument("--pages", type=int, default=2, help="Rakuten result pages per comparison segment (1-3)")
    args = parser.parse_args()
    main(fixture=args.fixture, pages=args.pages)
