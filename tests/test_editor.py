"""Offline visual editor tests.

Static checks always run. The integration tests drive editor/index.html in headless
Chromium (via Playwright, already a renderer dependency) and are skipped when no
browser is available.
"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITOR = ROOT / 'editor' / 'index.html'
RENDER = ROOT / 'scripts' / 'render.py'
ASSETS = ROOT / 'scripts' / 'assets.py'
EXAMPLES = ROOT / 'examples'


def tuple_of(source, name):
    """Read a module-level tuple of string literals from Python source without importing it."""
    m = re.search(rf"^{name}\s*=\s*\(([^)]*)\)", source, re.M)
    return re.findall(r"'([^']+)'", m.group(1))


def js_array(doc, name):
    m = re.search(rf"\b{name}=\[([^\]]*)\]", doc)
    return re.findall(r"'([^']+)'", m.group(1))


class EditorStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = EDITOR.read_text(encoding='utf-8')
        cls.render_src = RENDER.read_text(encoding='utf-8')
        cls.assets_src = ASSETS.read_text(encoding='utf-8')

    def test_editor_is_self_contained(self):
        doc = self.doc
        self.assertIn('<html lang="ar" dir="rtl">', doc)
        self.assertIn('const EXAMPLE=', doc)
        self.assertIn('function drawSlide(', doc)
        self.assertIn('canvas.toBlob(', doc)
        self.assertNotRegex(doc, r'<script[^>]+src=')
        self.assertNotRegex(doc, r'<link[^>]+href=["\']https?://')
        self.assertIn('function validate(', doc)

    def test_output_size(self):
        self.assertIn('canvas.width=1080', self.doc)
        self.assertIn('canvas.height=1350', self.doc)

    def test_no_network_apis_or_remote_urls(self):
        for api in ('fetch(', 'XMLHttpRequest', 'WebSocket', 'EventSource', 'sendBeacon', 'importScripts'):
            self.assertNotIn(api, self.doc)
        self.assertNotRegex(self.doc, r'https?://')

    def test_images_are_read_locally_as_data_uris(self):
        self.assertIn("inp.type='file'", self.doc)
        self.assertIn("inp.accept='image/png,image/jpeg,image/webp,image/svg+xml'", self.doc)
        self.assertIn('new FileReader()', self.doc)
        self.assertIn('readAsDataURL(file)', self.doc)

    def test_image_enums_match_renderer(self):
        for js, py in (('IMAGE_LAYOUTS', 'IMAGE_LAYOUTS'), ('IMAGE_FITS', 'IMAGE_FITS'), ('IMAGE_RIGHTS', 'IMAGE_RIGHTS')):
            self.assertEqual(js_array(self.doc, js), tuple_of(self.assets_src, py), js)
        allowed = re.search(r"set\(img\) - \{([^}]*)\}", self.render_src).group(1)
        self.assertEqual(sorted(js_array(self.doc, 'IMAGE_KEYS')), sorted(re.findall(r"'([^']+)'", allowed)))

    def test_image_limits_match_renderer(self):
        self.assertIn("img.get('overlay', 0.62)", self.render_src)
        self.assertIn('0 <= ov <= 0.95', self.render_src)
        self.assertIn('OVERLAY_DEFAULT=0.62,OVERLAY_MAX=0.95,ALT_MAX=300,CREDIT_MAX=120', self.doc)
        self.assertIn("len(img['alt']) > 300", self.render_src)
        self.assertIn("len(str(img.get('credit', ''))) > 120", self.render_src)
        py_position = re.search(r"re\.fullmatch\(r'([^']+)', str\(img\['position'\]\)\)", self.render_src).group(1)
        self.assertIn('const POSITION_RE=/^' + py_position + '$/;', self.doc)
        self.assertIn('MAX_IMAGE_BYTES=10*1024*1024,MAX_TOTAL_BYTES=40*1024*1024', self.doc)
        self.assertIn('MAX_BYTES = 10 * 1024 * 1024', self.assets_src)
        self.assertIn('MAX_TOTAL_BYTES = 40 * 1024 * 1024', self.assets_src)

    def test_layout_geometry_matches_renderer_css(self):
        rect = {k: tuple(map(int, v)) for k, *v in re.findall(
            r"(\w+):\{x:(\d+),y:(\d+),w:(\d+),h:(\d+),r:(\d+)\}", re.search(r'const MEDIA_RECT=\{(.*?)\};', self.doc).group(1))}
        css = self.render_src
        top = re.search(r'\.img-top \.media\{top:(\d+)px;left:(\d+)px;right:(\d+)px;height:(\d+)px;border-radius:(\d+)px\}', css)
        t, l, r, h, rad = map(int, top.groups())
        self.assertEqual(rect['top'], (l, t, 1080 - l - r, h, rad))
        side = re.search(r'\.img-side \.media\{top:(\d+)px;bottom:(\d+)px;left:(\d+)px;width:(\d+)px;border-radius:(\d+)px\}', css)
        t, b, l, w, rad = map(int, side.groups())
        self.assertEqual(rect['side'], (l, t, w, 1350 - t - b, rad))
        self.assertEqual(rect['background'], (0, 0, 1080, 1350, 0))
        text_left = int(re.search(r'\.img-side \.content,[^{]*\{left:(\d+)px;right:85px\}', css).group(1))
        self.assertIn(f'side:{{right:995,width:{995 - text_left},', self.doc)
        top_text = int(re.search(r'\.img-top \.content\{top:(\d+)px', css).group(1))
        self.assertIn(f'top:{{right:995,width:910,top:{top_text},', self.doc)
        self.assertIn('LOGO_H=56,LOGO_MAX_W=220', self.doc)
        self.assertIn('.logo{height:56px;max-width:220px', css)

    def test_svg_and_reference_rules_match_renderer(self):
        self.assertIn('<(?:script|foreignObject)|', self.doc)
        self.assertIn("<script|<foreignObject|", self.assets_src)
        self.assertIn(r'const SCHEME_RE=/^[A-Za-z][A-Za-z0-9+.-]+:/;', self.doc)
        self.assertIn(r"SCHEME = re.compile(r'^[A-Za-z][A-Za-z0-9+.-]+:')", self.assets_src)


def _browser():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        return None
    sys.path.insert(0, str(ROOT / 'scripts'))
    import render
    return render.browser_executable()


@unittest.skipUnless(_browser(), 'Playwright with a local Chromium/Chrome is required')
class EditorBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path=_browser())

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1400, 'height': 1000}, accept_downloads=True)
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.on('requestfailed', lambda r: self.errors.append('request ' + r.url[:60]))
        self.requests = []
        self.page.on('request', lambda r: self.requests.append(r.url[:40]))
        self.page.goto(EDITOR.as_uri())
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)

    def tearDown(self):
        self.page.close()
        self.tmp.cleanup()
        self.assertEqual(self.errors, [])
        self.assertEqual([u for u in self.requests if not u.startswith(('file:', 'data:'))], [])

    def attach(self, label, path):
        self.page.locator(f'input[aria-label="{label}"]').set_input_files(str(path))
        self.page.wait_for_timeout(300)

    def import_json(self, path):
        self.page.set_input_files('#import-json', str(path))
        self.page.wait_for_timeout(200)

    def download(self, button):
        with self.page.expect_download() as info:
            self.page.click(button)
        target = self.out / info.value.suggested_filename
        info.value.save_as(target)
        return target

    def test_import_demo_with_paths_shows_reattach_placeholders(self):
        self.import_json(EXAMPLES / 'demo-images.json')
        self.assertTrue(self.page.is_hidden('#errors'))
        self.assertIn('أعد إرفاق', self.page.inner_text('#status'))
        info = ' '.join(self.page.locator('.srcinfo').all_inner_texts())
        self.assertIn('assets/logo.svg', info)
        self.assertIn('assets/desk.jpg', info)
        self.assertEqual(self.page.locator('input[aria-label="إعادة إرفاق الصورة"]').count(), 1)
        # Re-attaching desk.jpg once fills all three slides that referenced assets/desk.jpg.
        self.attach('إعادة إرفاق الصورة', EXAMPLES / 'assets' / 'desk.jpg')
        self.assertIn('3', self.page.inner_text('#status'))
        self.attach('إعادة إرفاق الشعار', EXAMPLES / 'assets' / 'logo.svg')
        exported = json.loads(self.download('#save-json').read_text(encoding='utf-8'))
        original = json.loads((EXAMPLES / 'demo-images.json').read_text(encoding='utf-8'))
        self.assertEqual(exported, original)  # paths kept, no data: URIs

    def test_attach_images_preview_layouts_and_export_for_renderer(self):
        self.attach('إرفاق شعار', EXAMPLES / 'assets' / 'logo.svg')
        self.attach('إرفاق صورة', EXAMPLES / 'assets' / 'desk.jpg')
        self.assertIn('alt', self.page.inner_text('#errors'))  # alt is required before export
        self.assertTrue(self.page.is_disabled('#save-json'))
        self.page.locator('.imgbox textarea').fill('مكتب دراسة بإضاءة دافئة')
        self.page.locator('.imgbox select').nth(2).select_option('owned')
        self.assertTrue(self.page.is_enabled('#save-json'))
        png = self.download('#export-png')
        from PIL import Image
        with Image.open(png) as im:
            self.assertEqual(im.size, (1080, 1350))
        for layout in ('top', 'side'):
            self.page.click('#next')
            self.attach('إرفاق صورة', EXAMPLES / 'assets' / 'chart.png')
            self.page.locator('.imgbox textarea').fill('رسم أعمدة متصاعدة')
            self.page.locator('.imgbox select').first.select_option(layout)
        self.assertTrue(self.page.is_hidden('#errors'))
        note = self.page.inner_text('#export-note')
        self.assertIn('carousel-slide-01-desk.jpg', note)
        self.assertIn('carousel-logo-logo.svg', note)
        downloads = []
        self.page.on('download', lambda d: downloads.append(d))
        self.page.click('#save-json')
        self.page.wait_for_timeout(1500)
        for d in downloads:
            d.save_as(self.out / d.suggested_filename)
        names = sorted(d.suggested_filename for d in downloads)
        self.assertEqual(names, ['carousel-deck.json', 'carousel-logo-logo.svg',
                                 'carousel-slide-01-desk.jpg', 'carousel-slide-02-chart.png'])
        sys.path.insert(0, str(ROOT / 'scripts'))
        from render import load_deck
        from assets import deck_assets
        deck_path = self.out / 'carousel-deck.json'
        deck = load_deck(deck_path)
        self.assertEqual([(s.get('image') or {}).get('layout') for s in deck['slides'][:3]], ['background', 'top', 'side'])
        self.assertEqual(deck['slides'][2]['image']['src'], 'carousel-slide-02-chart.png')  # same bytes → one file
        found = deck_assets(deck, deck_path.parent)
        self.assertEqual(found['logo']['mime'], 'image/svg+xml')
        self.assertGreater(found['slides'][0]['width'], 0)
        # Embedded export re-imports in the editor; render.py rejects data: URIs by design.
        embedded = self.download('#save-json-embedded')
        self.assertIn('data:image/jpeg;base64,', embedded.read_text(encoding='utf-8'))
        with self.assertRaises(ValueError):
            load_deck(embedded)
        self.page.goto(EDITOR.as_uri())  # fresh page: nothing cached from the attachments
        self.import_json(embedded)
        self.assertTrue(self.page.is_hidden('#errors'))
        self.assertIn('مضمّنة في JSON', ' '.join(self.page.locator('.srcinfo').all_inner_texts()))

    def test_v4_layout_fields_round_trip_unchanged(self):
        deck = json.loads((EXAMPLES / 'demo-layouts.json').read_text(encoding='utf-8'))
        deck['brand']['font_file'] = '../fonts/Cairo-Variable.ttf'
        path = self.out / 'layouts.json'
        path.write_text(json.dumps(deck, ensure_ascii=False), encoding='utf-8')
        self.import_json(path)
        self.assertTrue(self.page.is_hidden('#errors'))
        for button in ('#save-json', '#save-json-embedded'):
            exported = json.loads(self.download(button).read_text(encoding='utf-8'))
            exported_design = exported.pop('design', None)
            expected = dict(deck)
            expected_design = expected.pop('design', None)
            self.assertEqual(exported, expected)
            if expected_design is not None:
                self.assertEqual(exported_design, expected_design)
        deck['brand']['font_file'] = 'https://example.com/font.ttf'
        path.write_text(json.dumps(deck, ensure_ascii=False), encoding='utf-8')
        self.import_json(path)
        self.assertIn('brand.font_file', self.page.inner_text('#errors'))

    def test_rejects_unsafe_or_unsupported_files(self):
        evil = self.out / 'evil.svg'
        evil.write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', encoding='utf-8')
        self.attach('إرفاق شعار', evil)
        self.assertIn('SVG', self.page.inner_text('#errors'))
        text = self.out / 'notes.png'
        text.write_text('not an image', encoding='utf-8')
        self.attach('إرفاق صورة', text)
        self.assertIn('notes.png', self.page.inner_text('#errors'))
        self.assertEqual(self.page.locator('.srcinfo').count(), 0)  # nothing was attached

    def test_import_rejects_invalid_image_fields_like_load_deck(self):
        bad = json.loads((EXAMPLES / 'demo-images.json').read_text(encoding='utf-8'))
        bad['brand']['logo'] = 'https://example.com/logo.png'
        bad['slides'][0]['image'].update(alt=' ', overlay=1.2)
        bad['slides'][1]['image'].update(layout='left', fit='fill', position='middle', rights='free', extra=1)
        path = self.out / 'bad.json'
        path.write_text(json.dumps(bad, ensure_ascii=False), encoding='utf-8')
        self.import_json(path)
        errors = self.page.inner_text('#errors')
        for needle in ('brand.logo', '.alt', '.overlay', '.layout', '.fit', '.position', '.rights', 'extra'):
            self.assertIn(needle, errors)
        sys.path.insert(0, str(ROOT / 'scripts'))
        from render import load_deck
        with self.assertRaises(ValueError):
            load_deck(path)


if __name__ == '__main__':
    unittest.main()
