import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.generate_pinterest_feed import BASE, PATH, GUID, make_feed


class PinterestFeedTest(unittest.TestCase):
    def prepare(self, site, listed=True, planner=True):
        root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        if listed:
            ET.SubElement(ET.SubElement(root, "url"), "loc").text = BASE + PATH
        ET.ElementTree(root).write(site / "sitemap.xml", encoding="utf-8")
        page = site / PATH / "index.html"
        page.parent.mkdir(parents=True)
        page.write_text('<section id="purchase-planner"></section>' if planner else "<p>Unavailable</p>", encoding="utf-8")

    def test_stable_curated_item(self):
        with tempfile.TemporaryDirectory() as folder:
            site = Path(folder)
            self.prepare(site)
            self.assertTrue(make_feed(site, render=False))
            path = site / "pinterest-feed.xml"
            before = path.read_bytes()
            self.assertTrue(make_feed(site, render=False))
            self.assertEqual(before, path.read_bytes())
            root = ET.parse(path).getroot()
            self.assertEqual(root.attrib["version"], "2.0")
            items = root.findall("./channel/item")
            self.assertEqual(len(items), 1)
            item = items[0]
            self.assertEqual(item.findtext("guid"), GUID)
            self.assertEqual(item.find("guid").attrib["isPermaLink"], "false")
            self.assertTrue(item.findtext("link").startswith(BASE + PATH + "?utm_source=pinterest&"))
            self.assertTrue(item.findtext("link").endswith("#purchase-planner"))
            self.assertIn("2026年11月24日", item.findtext("description"))
            self.assertEqual(item.find("enclosure").attrib["type"], "image/png")

    def test_missing_indexable_target_or_planner_suppresses_item(self):
        for listed, planner in [(False, True), (True, False)]:
            with self.subTest(listed=listed, planner=planner), tempfile.TemporaryDirectory() as folder:
                site = Path(folder)
                self.prepare(site, listed, planner)
                self.assertFalse(make_feed(site, render=False))
                self.assertEqual(ET.parse(site / "pinterest-feed.xml").findall("./channel/item"), [])
