"""Publish a deliberately small, curated Pinterest RSS pilot.

Stable item IDs and historical comparison dates prevent daily product refreshes
from generating duplicate or misleading Pins. No Pinterest credentials required.
"""
from pathlib import Path
import argparse
import subprocess
import tempfile
import xml.etree.ElementTree as ET

BASE = "https://stusaurus.github.io/baby-cost-jp/"
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
PATH = "diapers/pants/l/"
IMAGE = "pinterest/p01.png"
GUID = BASE + "pinterest/p01"
TITLE = "おむつLを70枚だけ買い足すなら？ 単価と支払総額"
DESC = ("パンツLを70枚買い足す場合の比較例。2026年11月24日取得の楽天掲載条件では、"
        "324枚11,800円と132枚5,850円。支払額の差は5,950円。"
        "価格・在庫・送料は購入時に確認してください。必要枚数と手持ち在庫から購入総額を計算できます。"
        "リンク先には広告を含みます。")
SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1500" viewBox="0 0 1000 1500">
<rect width="1000" height="1500" fill="#faf4e9"/>
<g font-family="Noto Sans CJK JP, sans-serif" fill="#203b3c">
<text x="70" y="105" font-size="36" font-weight="bold">ベビー用品比較</text>
<path d="M70 143H930" stroke="#aac7bb" stroke-width="4"/>
<text x="70" y="236" font-size="68" font-weight="bold">おむつLを</text>
<text x="70" y="330" font-size="82" font-weight="bold">70枚だけ買うなら？</text>
<text x="70" y="409" font-size="38">単価最安と支払最少は違うことも。</text>
<rect x="64" y="470" width="420" height="480" rx="28" fill="#fff"/>
<rect x="516" y="470" width="420" height="480" rx="28" fill="#e2efe5"/>
<g text-anchor="middle">
<text x="274" y="546" font-size="34" font-weight="bold">単価が安い例</text>
<text x="726" y="546" font-size="34" font-weight="bold">支払額が少ない例</text>
<text x="274" y="645" font-size="58" font-weight="bold">324枚</text>
<text x="726" y="645" font-size="58" font-weight="bold">132枚</text>
<text x="274" y="713" font-size="32">36.42円 / 枚</text>
<text x="726" y="713" font-size="32">44.32円 / 枚</text>
<text x="274" y="814" font-size="55" font-weight="bold">11,800円</text>
<text x="726" y="814" font-size="55" font-weight="bold">5,850円</text>
<text x="274" y="900" font-size="32">254枚余る</text>
<text x="726" y="900" font-size="32">62枚余る</text>
<text x="500" y="1036" font-size="37">この比較例での支払額の差</text>
<text x="500" y="1150" font-size="100" fill="#ac4a35" font-weight="bold">5,950円</text>
</g>
<rect x="64" y="1205" width="872" height="100" rx="28" fill="#203b3c"/>
<text x="500" y="1268" fill="#fff" font-size="40" text-anchor="middle" font-weight="bold">必要枚数から購入総額を計算</text>
<g font-size="26" fill="#40585a">
<text x="70" y="1365">2026年11月24日取得の楽天掲載条件による比較例。</text>
<text x="70" y="1406">価格・在庫・送料は購入時に確認してください。</text>
<text x="70" y="1447">リンク先には広告を含みます。</text>
</g></g></svg>"""


def make_feed(site: Path, render=True):
    # Only promote the existing indexable landing page with a functioning planner.
    sitemap = ET.parse(site / "sitemap.xml")
    urls = {e.text for e in sitemap.findall(f".//{NS}loc")}
    page = site / PATH / "index.html"
    eligible = BASE + PATH in urls and page.is_file() and 'id="purchase-planner"' in page.read_text(encoding="utf-8")
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "ベビー用品比較｜お買い物のヒント"
    ET.SubElement(channel, "link").text = BASE
    ET.SubElement(channel, "description").text = "必要な数量と支払総額を比較する買い物のヒント"
    ET.SubElement(channel, "language").text = "ja"
    image = site / IMAGE
    if eligible and render:
        image.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as folder:
            svg = Path(folder) / "p01.svg"
            svg.write_text(SVG, encoding="utf-8")
            subprocess.run(["rsvg-convert", "--format", "png", "--output", str(image), str(svg)], check=True)
        import struct
        header = image.read_bytes()[:24]
        if header[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", header[16:24]) != (1000, 1500):
            raise ValueError("Pinterest image must be a 1000x1500 PNG")
    if eligible:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = TITLE
        ET.SubElement(item, "description").text = DESC
        ET.SubElement(item, "link").text = BASE + PATH + "?utm_source=pinterest&utm_medium=organic_social&utm_campaign=diaper_checkout_p01#purchase-planner"
        ET.SubElement(item, "guid", isPermaLink="false").text = GUID
        ET.SubElement(item, "pubDate").text = "Wed, 25 Nov 2026 11:16:00 GMT"
        ET.SubElement(item, "enclosure", url=BASE + IMAGE, type="image/png", length=str(image.stat().st_size if render else 0))
    elif image.exists():
        image.unlink()
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(site / "pinterest-feed.xml", encoding="utf-8", xml_declaration=True)
    print(f"PINTEREST_RSS items={int(eligible)} stable_id=p01")
    return eligible


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, default=Path("site"))
    args = parser.parse_args()
    make_feed(args.site)
