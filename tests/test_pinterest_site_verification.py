import unittest
from html.parser import HTMLParser
from src.render import shell, SITE_URL

class VerificationParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_head = False
        self.tokens = []
    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.in_head = True
        if tag == "meta" and self.in_head:
            attrs = dict(attrs)
            if attrs.get("name") == "p:domain_verify":
                self.tokens.append(attrs.get("content"))
    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False

class PinterestSiteVerificationTest(unittest.TestCase):
    def test_only_canonical_home_has_verification_tag(self):
        for url, expected in [(SITE_URL, ["2545be02fd314581021e48540d8d479f"]), (SITE_URL + "method/", [])]:
            with self.subTest(url=url):
                parser = VerificationParser()
                parser.feed(shell("test", "test", "<h1>test</h1>", url))
                self.assertEqual(parser.tokens, expected)
