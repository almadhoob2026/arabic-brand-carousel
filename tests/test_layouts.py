import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from layouts import infer_kind, slide_text, NEW_KINDS
from critique import critique
from render import load_deck, make_html, BUNDLED_FONT

SAMPLE = ROOT / 'examples' / 'demo-layouts.json'


def deck_with(*slides):
    return {'brand': {'name': 'تجربة'}, 'slides': list(slides)}


class LayoutUnitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def load(self, deck):
        f = self.dir / 'deck.json'
        f.write_text(json.dumps(deck, ensure_ascii=False), encoding='utf-8')
        return load_deck(f)

    def test_infer_kind_from_fields(self):
        cases = {
            'metric': {'metric': {'value': '٥٠٪'}},
            'comparison': {'compare': {'columns': [{'points': ['أ']}, {'points': ['ب']}]}},
            'quote': {'quote': {'text': 'نص'}},
            'timeline': {'timeline': [{'label': '١', 'text': 'أ'}, {'label': '٢', 'text': 'ب'}]},
            'grid': {'cards': [{'title': 'أ'}, {'title': 'ب'}]},
            'qa': {'answer': 'جواب'},
            'steps': {'bullets': ['أ']},
        }
        for kind, fields in cases.items():
            with self.subTest(kind=kind):
                self.assertEqual(infer_kind({'headline': 'ع', **fields}, 3, 5), kind)
        self.assertEqual(infer_kind({'headline': 'ع'}, 1, 5), 'cover')
        self.assertEqual(infer_kind({'headline': 'ع', 'cta': 'ابدأ'}, 5, 5), 'cta')
        self.assertEqual(infer_kind({'headline': 'ع'}, 3, 5), 'statement')

    def test_explicit_and_legacy_kinds(self):
        self.assertEqual(infer_kind({'kind': 'checklist', 'bullets': ['أ']}, 2, 5), 'checklist')
        self.assertEqual(infer_kind({'kind': 'Before-After', 'compare': {}}, 2, 5), 'before-after')
        self.assertEqual(infer_kind({'kind': 'hero', 'metric': {'value': '١'}}, 2, 5), 'statement')

    def test_validation_errors(self):
        bad = [
            {'headline': 'ع', 'compare': {'columns': [{'points': ['أ']}] * 3}},
            {'headline': 'ع', 'compare': {'columns': [{'points': []}, {'points': ['ب']}]}},
            {'headline': 'ع', 'kind': 'metric'},
            {'headline': 'ع', 'timeline': [{'label': '١', 'text': 'أ'}]},
            {'headline': 'ع', 'cards': [{'title': str(i)} for i in range(5)]},
            {'headline': 'ع', 'quote': {'text': 'نص', 'source_url': 'x'}},
            {'headline': 'ع', 'metric': {'value': '١' * 30}},
            {'headline': 'ع', 'answer': ''},
        ]
        for slide in bad:
            with self.subTest(slide=slide), self.assertRaises(ValueError):
                self.load(deck_with(slide, {'headline': 'ثانية'}))

    def test_sample_renders_all_new_layouts(self):
        markup = make_html(load_deck(SAMPLE))
        for kind in NEW_KINDS:
            self.assertIn(f'data-kind="{kind}"', markup)
        self.assertIn('«الوضوح احترام لوقت القارئ.»', markup)
        self.assertIn('>قبل<', markup)  # before-after default column titles
        self.assertNotIn('<script', markup)

    def test_escapes_new_fields(self):
        deck = self.load(deck_with({'headline': 'ع', 'quote': {'text': '<img src=x onerror=alert(1)>'}},
                                   {'headline': 'ب', 'cards': [{'title': '<b>x</b>'}, {'title': 'y'}]}))
        markup = make_html(deck)
        self.assertNotIn('<img src=x', markup)
        self.assertNotIn('<b>x</b>', markup)

    def test_bundled_font_embedded(self):
        self.assertTrue(BUNDLED_FONT.is_file())
        self.assertIn("font-family:'Cairo';src:url(data:font/ttf;base64,", make_html(load_deck(SAMPLE)))
        deck = load_deck(SAMPLE)
        deck['brand']['font_family'] = 'Tahoma, sans-serif'
        self.assertNotIn('@font-face', make_html(deck))

    def test_brand_font_file(self):
        from assets import deck_assets
        shutil.copyfile(BUNDLED_FONT, self.dir / 'brand.ttf')
        deck = self.load({**deck_with({'headline': 'ع'}, {'headline': 'ب'}),
                          'brand': {'name': 'تجربة', 'font_file': 'brand.ttf'}})
        markup = make_html(deck, deck_assets(deck, self.dir))
        self.assertIn("font-family:'BrandFont'", markup)
        self.assertIn("--arabic-font:'BrandFont', ", markup)
        (self.dir / 'fake.ttf').write_text('nope', encoding='utf-8')
        deck['brand']['font_file'] = 'fake.ttf'
        with self.assertRaises(ValueError):
            make_html(deck, deck_assets(deck, self.dir))
        with self.assertRaises(ValueError):
            self.load({**deck_with({'headline': 'ع'}, {'headline': 'ب'}),
                       'brand': {'name': 'تجربة', 'font_file': 'https://fonts.example/x.ttf'}})

    def test_slide_text_counts_structured_copy(self):
        s = {'headline': 'عنوان', 'compare': {'columns': [{'title': 'أ', 'points': ['واحد اثنان']}, {'points': ['ثلاثة']}]}}
        self.assertEqual(len(slide_text(s).split()), 5)

    def test_repetitive_layout_advice(self):
        deck = load_deck(SAMPLE)
        deck['slides'] = [deck['slides'][0]] + [{'headline': f'فكرة {i}'} for i in range(4)] + [deck['slides'][-1]]
        codes = [f['code'] for f in critique(deck)['findings']]
        self.assertIn('repetitive-layout', codes)
        self.assertNotIn('repetitive-layout', [f['code'] for f in critique(load_deck(SAMPLE))['findings']])


class GeometryIntegrationTest(unittest.TestCase):
    """Renders in a real Chromium; skipped when no browser is available."""

    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
            from render import browser_executable
            with sync_playwright() as p:
                args = {'headless': True}
                if browser_executable():
                    args['executable_path'] = browser_executable()
                p.chromium.launch(**args).close()
        except Exception as exc:  # pragma: no cover - environment dependent
            raise unittest.SkipTest(f'Chromium unavailable: {exc}')
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def render(self, deck_path, name):
        from render import render
        from audit import audit
        out = self.dir / name
        render(deck_path, out)
        code = audit(out, deck_path)
        return code, json.loads((out / 'geometry.json').read_text(encoding='utf-8')), json.loads((out / 'audit.json').read_text(encoding='utf-8'))

    def test_examples_pass_geometry(self):
        for example in ('demo.json', 'demo-images.json', 'demo-layouts.json'):
            with self.subTest(example=example):
                code, geo, report = self.render(ROOT / 'examples' / example, example)
                self.assertEqual(code, 0, report['errors'])
                self.assertTrue(all(not s['issues'] for s in geo['slides']))
                self.assertTrue(all(s['min_font_px'] >= geo['min_font_px'] for s in geo['slides']))

    def test_overflow_is_reported(self):
        long_point = 'نص طويل جدًا يتكرر ليملأ المساحة ' * 5
        deck = deck_with({'headline': 'عنوان', 'body': long_point * 3, 'bullets': [long_point[:170]] * 5},
                         {'headline': 'ثانية'})
        f = self.dir / 'overflow.json'
        f.write_text(json.dumps(deck, ensure_ascii=False), encoding='utf-8')
        code, geo, report = self.render(f, 'overflow')
        self.assertEqual(code, 1)
        self.assertIn('content-overflow', [i['code'] for i in geo['slides'][0]['issues']])
        self.assertTrue(any('content-overflow' in e for e in report['errors']))


if __name__ == '__main__':
    unittest.main()
