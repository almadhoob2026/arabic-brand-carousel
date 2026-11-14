import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from assets import deck_assets, load_image
from critique import critique
from render import copy_assets, load_deck, make_html

SAMPLE = ROOT / 'examples' / 'demo-images.json'


class ImageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_deck(self, deck):
        f = self.dir / 'deck.json'
        f.write_text(json.dumps(deck, ensure_ascii=False), encoding='utf-8')
        return f

    def base_deck(self, image=None):
        slide = {'headline': 'عنوان أول', 'body': 'نص قصير'}
        if image:
            slide['image'] = image
        return {'brand': {'name': 'تجربة'}, 'slides': [slide, {'headline': 'عنوان ثانٍ'}]}

    def png(self, name, color, size=(1200, 1500)):
        Image.new('RGB', size, color).save(self.dir / name)
        return name

    def test_sample_deck_loads_and_embeds(self):
        deck = load_deck(SAMPLE)
        assets = deck_assets(deck, SAMPLE.parent)
        markup = make_html(deck, assets)
        self.assertIn('src="data:image/jpeg;base64,', markup)
        self.assertIn('src="data:image/svg+xml;base64,', markup)
        self.assertIn('img-background', markup)
        self.assertIn('img-top', markup)
        self.assertIn('img-side', markup)
        self.assertIn('alt="مكتب دراسة', markup)
        self.assertNotIn('assets/desk.jpg', markup)  # no file references left in HTML

    def test_rejects_remote_url(self):
        for src in ('https://example.com/a.jpg', '//cdn/x.png', 'data:image/png;base64,AAAA', 'file:///etc/passwd'):
            with self.subTest(src=src), self.assertRaises(ValueError):
                load_deck(self.write_deck(self.base_deck({'src': src, 'alt': 'وصف'})))

    def test_requires_alt_and_known_layout(self):
        with self.assertRaises(ValueError):
            load_deck(self.write_deck(self.base_deck({'src': 'a.png'})))
        with self.assertRaises(ValueError):
            load_deck(self.write_deck(self.base_deck({'src': 'a.png', 'alt': 'وصف', 'layout': 'collage'})))
        with self.assertRaises(ValueError):
            load_deck(self.write_deck(self.base_deck({'src': 'a.png', 'alt': 'وصف', 'overlay': 2})))
        with self.assertRaises(ValueError):
            load_deck(self.write_deck(self.base_deck({'src': 'a.png', 'alt': 'وصف', 'position': 'center;color:red'})))

    def test_type_checked_by_bytes(self):
        (self.dir / 'fake.png').write_text('not an image', encoding='utf-8')
        with self.assertRaises(ValueError):
            load_image('fake.png', self.dir)

    def test_rejects_scripted_svg(self):
        (self.dir / 'bad.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', encoding='utf-8')
        (self.dir / 'remote.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="https://x/y.png"/></svg>', encoding='utf-8')
        for name in ('bad.svg', 'remote.svg'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                load_image(name, self.dir)

    def test_missing_file(self):
        deck = load_deck(self.write_deck(self.base_deck({'src': 'missing.png', 'alt': 'وصف'})))
        with self.assertRaises(FileNotFoundError):
            deck_assets(deck, self.dir)
        codes = [f['code'] for f in critique(deck, self.dir)['findings']]
        self.assertIn('image-unreadable', codes)

    def test_bright_background_is_blocker(self):
        name = self.png('white.png', (255, 255, 255))
        deck = load_deck(self.write_deck(self.base_deck({'src': name, 'alt': 'وصف', 'overlay': 0.1, 'rights': 'owned'})))
        report = critique(deck, self.dir)
        self.assertIn('image-text-contrast', [f['code'] for f in report['findings']])
        self.assertFalse(report['passed_preflight'])

    def test_rights_and_resolution_warnings(self):
        name = self.png('small.png', (20, 20, 20), size=(300, 300))
        deck = load_deck(self.write_deck(self.base_deck({'src': name, 'alt': 'وصف'})))
        codes = [f['code'] for f in critique(deck, self.dir)['findings']]
        self.assertIn('image-rights', codes)
        self.assertIn('image-low-resolution', codes)

    def test_copy_assets_rewrites_paths(self):
        name = self.png('photo.png', (30, 30, 30))
        deck = load_deck(self.write_deck(self.base_deck({'src': name, 'alt': 'وصف', 'rights': 'owned'})))
        out = self.dir / 'out'
        out.mkdir()
        portable = copy_assets(deck, deck_assets(deck, self.dir), out)
        self.assertEqual(portable['slides'][0]['image']['src'], 'assets/slide-01-photo.png')
        self.assertTrue((out / 'assets' / 'slide-01-photo.png').is_file())
        self.assertEqual(deck['slides'][0]['image']['src'], name)  # original deck untouched


if __name__ == '__main__':
    unittest.main()
