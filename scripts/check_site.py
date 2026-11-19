import json
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1] / "site"


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.fragments = []
        self.assets = []
        self.controlled_ids = []
        self.has_main = False
        self.has_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if attrs.get("aria-controls"):
            self.controlled_ids.extend(attrs["aria-controls"].split())
        if tag == "main":
            self.has_main = True
        if tag == "title":
            self.has_title = True
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.fragments.append(attrs["href"][1:])
        if tag == "script" and attrs.get("src"):
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("rel") in {"stylesheet", "icon"}:
            self.assets.append(attrs.get("href", ""))


def main():
    parser = SiteParser()
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    parser.feed(html)
    assert parser.has_main and parser.has_title, "index needs a title and main landmark"
    assert '<details class="mobile-nav">' in html and 'href="#how">How it works</a>' in html and 'href="#privacy">Privacy</a>' in html, "mobile section navigation is missing"
    assert 'http-equiv="Content-Security-Policy"' in html, "the static page needs a restrictive content policy"
    assert 'property="og:title"' in html and 'name="twitter:card"' in html, "social preview metadata is missing"
    assert 'type="application/ld+json"' in html, "software structured data is missing"
    assert all(fragment in parser.ids for fragment in parser.fragments), "broken in-page link"
    assert all(controlled_id in parser.ids for controlled_id in parser.controlled_ids), "broken aria-controls reference"
    assert {"sample-rows-toggle", "sample-rows", "sample-copy", "sample-copy-status"} <= parser.ids, "sample sheet preview controls are missing"
    assert "mailto:eatitall.founder@gmail.com" in html, "paid setup contact path is missing"
    assert "Don’t email passwords, OAuth tokens" in html, "contact safety guidance is missing"
    assert all((ROOT / asset).is_file() for asset in parser.assets), "missing local asset"
    assert not any(asset.startswith(("http://", "https://")) for asset in parser.assets), "remote runtime asset"
    ElementTree.parse(ROOT / "sitemap.xml")
    vercel = json.loads((ROOT.parent / "vercel.json").read_text(encoding="utf-8"))
    assert vercel["outputDirectory"] == "site", "Vercel must publish only the static product site"
    headers = {header["key"].lower(): header["value"] for rule in vercel["headers"] for header in rule["headers"]}
    assert {"content-security-policy", "strict-transport-security", "x-content-type-options", "x-frame-options", "referrer-policy"} <= headers.keys(), "Vercel response security headers are incomplete"
    print("JobMail site checks passed.")


if __name__ == "__main__":
    main()
