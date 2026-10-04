from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from .config import SITE_URL

API_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"
APP_ID = os.environ.get("RAKUTEN_APPLICATION_ID", "").strip()
ACCESS_KEY = os.environ.get("RAKUTEN_ACCESS_KEY", "").strip()
AFFILIATE_ID = os.environ.get("RAKUTEN_AFFILIATE_ID", "").strip()
_LAST_REQUEST_AT = 0.0


def _throttle(min_interval: float = 1.35):
    global _LAST_REQUEST_AT
    elapsed = time.monotonic() - _LAST_REQUEST_AT
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _LAST_REQUEST_AT = time.monotonic()


def _first_image(item: dict) -> str:
    for key in ("mediumImageUrls", "smallImageUrls"):
        value = item.get(key)
        if not value:
            continue
        row = value[0] if isinstance(value, list) and value else value
        if isinstance(row, dict):
            row = row.get("imageUrl") or row.get("url")
        if row:
            return str(row).replace("http://", "https://")
    return ""


def _normalize(raw: dict) -> dict | None:
    item = raw.get("Item", raw) if isinstance(raw, dict) else {}
    try:
        price = int(float(item.get("itemPrice") or 0))
    except (TypeError, ValueError):
        price = 0
    name = str(item.get("itemName") or "").strip()
    if not name or price <= 0:
        return None
    return {
        "source": "rakuten",
        "source_id": str(item.get("itemCode") or ""),
        "name": name,
        "catchcopy": str(item.get("catchcopy") or "").strip(),
        "caption": str(item.get("itemCaption") or "").strip(),
        "price_yen": price,
        "url": str(item.get("affiliateUrl") or item.get("itemUrl") or ""),
        "shop": str(item.get("shopName") or ""),
        "image": _first_image(item),
        "review_count": int(float(item.get("reviewCount") or 0)),
    }


def _http_error(exc: urllib.error.HTTPError) -> RuntimeError:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    # Rakuten error bodies contain parameter names/descriptions but not our secret values.
    if len(body) > 1000:
        body = body[:1000] + "..."
    return RuntimeError(f"Rakuten API HTTP {exc.code}: {body or exc.reason}")


def fetch_items(keyword: str, pages: int = 2) -> list[dict]:
    if not APP_ID or not ACCESS_KEY:
        raise RuntimeError("RAKUTEN_APPLICATION_ID / RAKUTEN_ACCESS_KEY are required")
    pages = max(1, min(int(pages), 3))
    items: list[dict] = []
    seen: set[str] = set()
    for page in range(1, pages + 1):
        if page > 1:
            time.sleep(1.05)
        params = {
            "applicationId": APP_ID,
            "keyword": keyword,
            "hits": 30,
            "page": page,
            "format": "json",
            "formatVersion": 2,
            "availability": 1,
            # Keep the MVP ranking honest: compare offers that the API can restrict to postage included/free shipping.
            "postageFlag": 1,
            # catchcopy/itemCaption are used only as quality evidence for selectable-size/type detection.
            "elements": "itemName,catchcopy,itemCaption,itemPrice,itemUrl,affiliateUrl,itemCode,shopName,mediumImageUrls,smallImageUrls,reviewCount",
        }
        if AFFILIATE_ID:
            params["affiliateId"] = AFFILIATE_ID
        _throttle()
        request = urllib.request.Request(
            API_URL + "?" + urllib.parse.urlencode(params),
            headers={
                "accessKey": ACCESS_KEY,
                "Origin": "https://stusaurus.github.io",
                "Referer": SITE_URL,
                "User-Agent": "baby-cost-jp/0.1",
            },
        )
        last_error = None
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                last_error = None
                break
            except urllib.error.HTTPError as exc:
                # Rakuten may briefly rate-limit otherwise valid scheduled builds.
                # Retry 429 and transient 5xx responses with conservative backoff;
                # deterministic auth/parameter errors still fail immediately.
                if exc.code == 429 or 500 <= exc.code < 600:
                    if attempt < max_attempts - 1:
                        retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                        try:
                            retry_after_seconds = float(retry_after)
                        except (TypeError, ValueError):
                            retry_after_seconds = 0.0
                        delay = max(retry_after_seconds, 1.5 * (attempt + 1))
                        time.sleep(delay)
                        _throttle(1.35)
                        continue
                last_error = _http_error(exc)
                break
            except Exception as exc:  # network/API transient errors are retried by scheduled build
                last_error = exc
                if attempt < max_attempts - 1:
                    time.sleep(1.5 * (attempt + 1))
        if last_error:
            raise last_error
        rows = payload.get("Items") or payload.get("items") or []
        for raw in rows:
            normalized = _normalize(raw)
            if not normalized:
                continue
            key = normalized["source_id"] or f'{normalized["name"]}|{normalized["price_yen"]}|{normalized["shop"]}'
            if key in seen:
                continue
            seen.add(key)
            items.append(normalized)
    return items
