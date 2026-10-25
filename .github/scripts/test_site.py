"""Dependency-free smoke checks for the static site and gallery generator."""

import importlib.util
import re
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag not in {"a", "img", "script", "link", "source"}:
            return
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.urls.append(value)


class SiteSmokeTests(unittest.TestCase):
    def test_local_page_assets_exist(self):
        for relative_page in ("index.html", "404.html", "photo-gallery/gallery.html"):
            page = ROOT / relative_page
            self.assertTrue(page.is_file(), f"Missing page: {relative_page}")
            parser = References()
            parser.feed(page.read_text(encoding="utf-8"))
            for url in parser.urls:
                parts = urlsplit(url)
                if parts.scheme or parts.netloc or not parts.path:
                    continue
                path = unquote(parts.path)
                if path.startswith("/"):
                    target = ROOT / path.lstrip("/")
                else:
                    target = page.parent / path
                if target.is_dir():
                    target = target / "index.html"
                with self.subTest(page=relative_page, url=url):
                    self.assertTrue(target.is_file(), f"Missing local asset: {target}")

    def test_gallery_references_every_photo(self):
        photo_dir = ROOT / "photo-gallery" / "photos"
        photos = sorted(path.name for path in photo_dir.glob("*.jpg"))
        self.assertGreater(len(photos), 0)
        html = (ROOT / "photo-gallery" / "gallery.html").read_text(encoding="utf-8")
        referenced = re.findall(r'<a href="photos/([^"]+\.jpg)" class="image">', html)
        self.assertCountEqual(photos, referenced)

    def test_gallery_generator_works_without_third_party_packages(self):
        spec = importlib.util.spec_from_file_location("create_gallery", ROOT / "create_gallery.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            module.CURRENT_DIR = Path(folder)
            photo_dir = Path(folder) / "photo-gallery" / "photos"
            photo_dir.mkdir(parents=True)
            old = "TEST-PHOTO-240101-120000-0001.jpg"
            new = "TEST-PHOTO-250101-120000-0002.jpg"
            (photo_dir / old).touch()
            (photo_dir / new).touch()
            module.run()
            generated = (photo_dir.parent / "gallery.html").read_text(encoding="utf-8")
            self.assertIn("photos/" + old, generated)
            self.assertIn("photos/" + new, generated)
            self.assertLess(generated.index("photos/" + new), generated.index("photos/" + old))
            self.assertIn("jquery.poptrox.min.js", generated)


if __name__ == "__main__":
    unittest.main()
