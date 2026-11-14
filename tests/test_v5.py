import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from brand import build_palette, contrast, init_profile, logo_colours, merge_profile
from eval_triggers import invoked_skill, run_error
from formats import FORMATS, parse_formats
from publish import build_pack, normalise_tags, validate_publish
from render import load_deck, make_html

EX = ROOT / 'examples'


class FormatTest(unittest.TestCase):
    def test_parse_formats(self):
        self.assertEqual(parse_formats(None), ('portrait',))
        self.assertEqual(parse_formats('story,portrait,story'), ('portrait', 'story'))
        self.assertEqual(parse_formats(['square']), ('square',))
        for bad in ('reel', ['portrait', 'a4'], []):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_formats(bad)

    def test_format_css(self):
        deck = load_deck(EX / 'demo-layouts.json')
        story = make_html(deck, fmt='story')
        self.assertIn('class="fmt-story"', story)
        self.assertIn('@page{size:1080px 1920px', story)
        self.assertIn('.slide{height:1920px}', story)
        scale = lambda m: float(re.search(r'--headline-scale:([\d.]+)', m).group(1))
        self.assertLess(scale(make_html(deck, fmt='square')), scale(make_html(deck)))

    def test_deck_formats_validated(self):
        with tempfile.TemporaryDirectory() as d:
            deck = json.loads((EX / 'demo.json').read_text(encoding='utf-8'))
            deck['formats'] = ['portrait', 'tiktok']
            f = Path(d) / 'deck.json'
            f.write_text(json.dumps(deck), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_deck(f)


class PublishTest(unittest.TestCase):
    def test_validation(self):
        validate_publish({'caption': 'نص', 'hashtags': ['#تسويق', 'content_ai'], 'first_comment': 'سؤال'})
        bad = [{'caption': 'x' * 2201}, {'hashtags': ['a'] * 31}, {'hashtags': ['two words']},
               {'hashtags': ['#bad-tag']}, {'link': 'x'}, {'hashtags': 'notalist'}]
        for pub in bad:
            with self.subTest(pub=pub), self.assertRaises(ValueError):
                validate_publish(pub)

    def test_tags_normalised(self):
        self.assertEqual(normalise_tags(['تسويق', '#تسويق', '#AI', 'ai']), ['#تسويق', '#AI'])

    def test_pack(self):
        deck = load_deck(EX / 'demo-profile.json')
        pack = build_pack(deck)
        self.assertTrue(pack['caption_with_hashtags'].endswith('#كتابة_المحتوى #تسويق_رقمي'))
        self.assertEqual(len(pack['alt_text']), len(deck['slides']))
        self.assertTrue(pack['alt_text'][1]['authored'])
        self.assertTrue(pack['alt_text'][0]['alt'].startswith('الشريحة 1 من 3: ثلاث خطوات لفكرة أوضح.'))
        self.assertEqual(pack['warnings'], [])
        self.assertIn('No caption', build_pack(load_deck(EX / 'demo.json'))['warnings'][0])

    def test_slide_alt_validated(self):
        with tempfile.TemporaryDirectory() as d:
            deck = {'brand': {'name': 'ت'}, 'slides': [{'headline': 'أ', 'alt': ''}, {'headline': 'ب'}]}
            f = Path(d) / 'deck.json'
            f.write_text(json.dumps(deck, ensure_ascii=False), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_deck(f)


class BrandProfileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_sample_profile_merge(self):
        deck = load_deck(EX / 'demo-profile.json')
        self.assertNotIn('brand_profile', deck)
        self.assertEqual(deck['brand']['category'], 'نصائح سريعة')       # deck overrides profile
        self.assertEqual(deck['brand']['name'], 'مساحة معرفة')            # profile value kept
        self.assertTrue(Path(deck['brand']['logo']).is_absolute())       # profile-relative → absolute
        self.assertTrue(Path(deck['brand']['logo']).is_file())
        self.assertEqual(deck['publish']['hashtags'], ['كتابة_المحتوى', 'تسويق_رقمي'])

    def test_profile_rejections(self):
        (self.dir / 'p.json').write_text(json.dumps({'brand': {'name': 'x'}, 'colors': {}}), encoding='utf-8')
        for ref in ('https://example.com/p.json', 'p.json', 'missing.json'):
            with self.subTest(ref=ref), self.assertRaises((ValueError, FileNotFoundError)):
                merge_profile({'brand_profile': ref, 'slides': []}, self.dir / 'deck.json')

    def test_palette_contrast(self):
        for accent in [(220, 30, 60), (20, 90, 200), (250, 230, 40), (30, 160, 90), (128, 128, 128)]:
            for theme in ('dark', 'light'):
                with self.subTest(accent=accent, theme=theme):
                    _, r = build_palette(accent, theme)
                    self.assertGreaterEqual(r['foreground/background'], 7)
                    self.assertGreaterEqual(r['muted/background'], 4.5)
                    self.assertGreaterEqual(r['accent/background'], 3)

    def test_logo_colours(self):
        svg = logo_colours(EX / 'assets' / 'logo.svg')
        self.assertIn((243, 201, 105), [c for c, _ in svg])
        img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        img.paste((200, 20, 40, 255), (20, 20, 80, 80))
        img.save(self.dir / 'logo.png')
        self.assertTrue(any(contrast(c, (200, 20, 40)) < 1.2 for c, _ in logo_colours(self.dir / 'logo.png')))

    def test_init_profile_relative_logo(self):
        img = Image.new('RGB', (64, 64), (20, 90, 200))
        (self.dir / 'assets').mkdir()
        img.save(self.dir / 'assets' / 'logo.png')
        profile, _ = init_profile(self.dir / 'assets' / 'logo.png', 'علامة', self.dir / 'brands' / 'b.json', '@b')
        self.assertEqual(profile['brand']['logo'], '../assets/logo.png')
        saved = json.loads((self.dir / 'brands' / 'b.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['brand']['handle'], '@b')


class PluginPackagingTest(unittest.TestCase):
    def test_manifests(self):
        plugin = json.loads((ROOT / '.claude-plugin' / 'plugin.json').read_text(encoding='utf-8'))
        market = json.loads((ROOT / '.claude-plugin' / 'marketplace.json').read_text(encoding='utf-8'))
        self.assertEqual(plugin['name'], 'arabic-brand-carousel')
        self.assertEqual(plugin['skills'], ['./'])
        entry = next(p for p in market['plugins'] if p['name'] == plugin['name'])
        self.assertEqual(entry['source'], './')
        self.assertEqual(entry['version'], plugin['version'])
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertRegex(skill, r'^---\nname: arabic-brand-carousel\n')

    def test_commands(self):
        files = sorted((ROOT / 'commands').glob('*.md'), key=lambda f: f.stem)
        self.assertEqual([f.stem for f in files], ['carousel', 'carousel-brand', 'carousel-review', 'carousel-settings'])
        for f in files:
            text = f.read_text(encoding='utf-8')
            self.assertRegex(text, r'^---\ndescription: .+\nargument-hint: .+\n---\n', f.name)
            self.assertIn('$ARGUMENTS', text)
            self.assertIn('arabic-brand-carousel', text)


class TriggerEvalTest(unittest.TestCase):
    def test_cases_file(self):
        spec = json.loads((ROOT / 'evals' / 'triggers.json').read_text(encoding='utf-8'))
        ids = [c['id'] for c in spec['cases']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(any(c['should_trigger'] for c in spec['cases']))
        self.assertTrue(any(not c['should_trigger'] for c in spec['cases']))

    def test_stream_parsing(self):
        fired = json.dumps({'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'arabic-brand-carousel:arabic-brand-carousel'}}]}})
        other = json.dumps({'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'content-engine-v3:carousel-creator'}}]}})
        auth = json.dumps({'type': 'assistant', 'message': {'model': '<synthetic>', 'content': [
            {'type': 'text', 'text': 'Failed to authenticate'}]}})
        self.assertTrue(invoked_skill([fired], 'arabic-brand-carousel'))
        self.assertFalse(invoked_skill([other, 'not json'], 'arabic-brand-carousel'))
        self.assertEqual(run_error([auth]), 'Failed to authenticate')
        self.assertEqual(run_error([fired]), '')


class V5IntegrationTest(unittest.TestCase):
    """Real Chromium renders; skipped without a browser."""

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

    def test_all_formats_and_pdf(self):
        from audit import audit
        from render import render
        out = self.dir / 'layouts'
        render(EX / 'demo-layouts.json', out, 'portrait,square,story', pdf=True)
        self.assertEqual(audit(out, EX / 'demo-layouts.json'), 0)
        for fmt, spec in FORMATS.items():
            folder = out / spec['folder'] if spec['folder'] else out
            with Image.open(folder / 'slide-01.png') as im:
                self.assertEqual(im.size, spec['size'])
            pdf = (folder / 'carousel.pdf').read_bytes()
            self.assertEqual(len(re.findall(rb'/Type\s*/Page(?![a-zA-Z])', pdf)), 10, fmt)
            geo = json.loads((folder / 'geometry.json').read_text(encoding='utf-8'))
            self.assertEqual(geo['format'], fmt)
            self.assertTrue(all(not s['issues'] for s in geo['slides']), fmt)

    def test_profile_deck_outputs(self):
        from audit import audit
        from render import render
        out = self.dir / 'profile'
        render(EX / 'demo-profile.json', out)  # formats come from the deck: portrait + story
        self.assertEqual(audit(out, EX / 'demo-profile.json'), 0)
        self.assertTrue((out / 'story' / 'slide-03.png').is_file())
        self.assertFalse((out / 'square').exists())
        self.assertIn('#تسويق_رقمي', (out / 'caption.txt').read_text(encoding='utf-8'))
        portable = json.loads((out / 'deck.json').read_text(encoding='utf-8'))
        self.assertEqual(portable['brand']['logo'], 'assets/logo-logo.svg')
        self.assertTrue((out / 'assets' / 'logo-logo.svg').is_file())


if __name__ == '__main__':
    unittest.main()
