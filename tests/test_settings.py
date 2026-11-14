import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from render import clean_generated
from settings import DEFAULTS, deck_fields, load, save, summary, validate

EX = ROOT / 'examples'


class SettingsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.file = Path(self.tmp.name) / '.carousel' / 'settings.json'

    def tearDown(self):
        self.tmp.cleanup()

    def test_defaults_and_validation(self):
        self.assertEqual(validate({}), DEFAULTS)
        bad = [{'slides': 11}, {'slides': '7'}, {'pdf': 'yes'}, {'register': 'egyptian'},
               {'direction': 'retro'}, {'images': 'stock'}, {'formats': ['reel']},
               {'brand_profile': 'https://x.com/b.json'}, {'colour': 'red'}]
        for s in bad:
            with self.subTest(s=s), self.assertRaises(ValueError):
                validate(s)

    def test_save_merges_and_round_trips(self):
        self.assertIsNone(load(self.file))
        save({'formats': ['story', 'portrait'], 'slides': 5, 'register': 'gulf'}, self.file)
        s = save({'direction': 'bold', 'slides': None}, self.file)  # None keeps the saved value
        self.assertEqual(s['formats'], ['portrait', 'story'])
        self.assertEqual(s['slides'], 5)
        self.assertEqual(s['direction'], 'bold')
        raw = json.loads(self.file.read_text(encoding='utf-8'))
        self.assertEqual(raw['version'], 1)
        self.assertEqual(load(self.file), s)

    def test_deck_fields_and_summary(self):
        s = validate({'formats': ['square'], 'direction': 'luxury', 'brand_profile': 'brands/a.json', 'pdf': True})
        self.assertEqual(deck_fields(s), {'formats': ['square'], 'design': {'direction': 'luxury'},
                                          'brand_profile': 'brands/a.json'})
        self.assertNotIn('brand_profile', deck_fields(validate({})))
        self.assertIn('+ PDF', summary(s))
        self.assertIn('فصحى', summary(s))


class SettingsDocsTest(unittest.TestCase):
    def test_cards_respect_tool_limits(self):
        text = (ROOT / 'references' / 'settings.md').read_text(encoding='utf-8')
        for card in text.split('## Card ')[1:]:
            rows = [r for r in card.splitlines() if r.startswith('| ') and not r.startswith('| header') and '---' not in r]
            self.assertLessEqual(len(rows), 4, 'AskUserQuestion allows at most 4 questions per card')
            for r in rows:
                header = r.split('|')[1].strip()
                self.assertLessEqual(len(header), 12, header)
                self.assertLessEqual(len(r.split('|')[3].split('·')), 4, r)

    def test_commands_run_settings_first(self):
        carousel = (ROOT / 'commands' / 'carousel.md').read_text(encoding='utf-8')
        self.assertIn('settings.py show', carousel)
        self.assertIn('AskUserQuestion', carousel)
        self.assertIn('--quick', carousel)
        self.assertLess(carousel.index('Settings first'), carousel.index('follow the skill'))
        settings_cmd = (ROOT / 'commands' / 'carousel-settings.md').read_text(encoding='utf-8')
        self.assertIn('settings.py set', settings_cmd)
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertLess(skill.index('## Stage 0'), skill.index('## Stage 1 '))


class OutputHygieneTest(unittest.TestCase):
    def test_clean_generated_only_touches_generated_names(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for name in ('slide-01.png', 'slide-07.png', 'contact-sheet.png', 'caption.txt', 'audit.json',
                         'slide-final.png', 'my-notes.txt', 'slide-1.png'):
                (d / name).write_text('x', encoding='utf-8')
            (d / 'assets').mkdir()
            clean_generated(d)
            self.assertEqual(sorted(f.name for f in d.iterdir()),
                             ['assets', 'my-notes.txt', 'slide-1.png', 'slide-final.png'])

    def test_refuses_to_overwrite_source_deck(self):
        from render import render
        with tempfile.TemporaryDirectory() as d:
            shutil.copyfile(EX / 'demo.json', Path(d) / 'deck.json')
            with self.assertRaises(ValueError):
                render(Path(d) / 'deck.json', d)
            (Path(d) / 'story').mkdir()
            shutil.copyfile(EX / 'demo.json', Path(d) / 'story' / 'deck.json')
            with self.assertRaises(ValueError):
                render(Path(d) / 'story' / 'deck.json', d)


class AuditManifestIntegrationTest(unittest.TestCase):
    """Real renders; skipped without Chromium."""

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
        except Exception as exc:  # pragma: no cover
            raise unittest.SkipTest(f'Chromium unavailable: {exc}')
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_story_only_deck_passes_audit(self):
        from audit import audit
        from render import render
        deck = json.loads((EX / 'demo.json').read_text(encoding='utf-8'))
        deck['formats'] = ['story']
        f = self.dir / 'story-only.json'
        f.write_text(json.dumps(deck, ensure_ascii=False), encoding='utf-8')
        out = self.dir / 'story-out'
        render(f, out)
        self.assertEqual(audit(out, f), 0)
        manifest = json.loads((out / 'render.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['formats'], {'story': 'story'})
        report = json.loads((out / 'story' / 'audit.json').read_text(encoding='utf-8'))
        self.assertEqual(report['format'], 'story')

    def test_rerender_removes_stale_slides_and_ignores_old_formats(self):
        from audit import audit
        from render import render
        out = self.dir / 'rerender'
        render(EX / 'demo.json', out, 'portrait,square')  # 7 slides, two formats
        (out / 'keep-me.txt').write_text('user file', encoding='utf-8')
        render(EX / 'demo-profile.json', out, 'portrait')  # 3 slides, one format
        self.assertEqual(sorted(p.name for p in out.glob('slide-*.png')),
                         ['slide-01.png', 'slide-02.png', 'slide-03.png'])
        self.assertTrue((out / 'keep-me.txt').exists())
        self.assertEqual(audit(out, EX / 'demo-profile.json'), 0)


if __name__ == '__main__':
    unittest.main()
