from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote
from html.parser import HTMLParser

class RobotsParser(HTMLParser):
    noindex=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=="meta" and a.get("name", "").lower()=="robots" and "noindex" in a.get("content", "").lower(): self.noindex=True
import xml.etree.ElementTree as ET

SITE_DIR = Path("site")
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/") + "/"

if not SITE_URL.strip("/"):
    raise SystemExit("SITE_URL is required")
if not SITE_DIR.exists():
    raise SystemExit("site directory does not exist")

urls = []
for html in sorted(SITE_DIR.rglob("*.html")):
    rel = html.relative_to(SITE_DIR).as_posix()
    parser=RobotsParser()
    parser.feed(html.read_text(encoding="utf-8"))
    if parser.noindex or html.name.startswith("google") or rel == "404.html":
        continue
    if rel == "index.html":
        path = ""
    elif rel.endswith("/index.html"):
        path = rel[:-10]
    else:
        path = rel
    urls.append(SITE_URL + quote(path, safe="/-._~"))

xml = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for url in urls:
    # lastmod is omitted: rebuilding a page does not prove a significant content change.
    xml.append(f"  <url><loc>{url}</loc></url>")
xml.append("</urlset>")
(SITE_DIR / "sitemap.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
robots = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n"
(SITE_DIR / "robots.txt").write_text(robots, encoding="utf-8")

root = ET.parse(SITE_DIR / "sitemap.xml").getroot()
ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
parsed_urls = [node.text for node in root.findall(f"{ns}url/{ns}loc")]
if parsed_urls != urls:
    raise SystemExit("sitemap.xml validation failed: generated URL list differs from parsed XML")
if not urls or len(set(urls)) != len(urls):
    raise SystemExit("sitemap.xml validation failed: empty or duplicate URLs")
expected_sitemap_line = f"Sitemap: {SITE_URL}sitemap.xml"
if expected_sitemap_line not in robots.splitlines():
    raise SystemExit("robots.txt validation failed: sitemap declaration missing")
print(f"Generated and validated sitemap.xml with {len(urls)} URLs and robots.txt")
