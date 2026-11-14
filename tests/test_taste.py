import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from taste import taste_profile, css_tokens, suggest_layouts
from critique import critique, contrast
from render import load_deck, make_html

SAMPLE = Path(__file__).resolve().parents[1] / 'examples' / 'demo.json'

class TasteTest(unittest.TestCase):
    def setUp(self): self.deck = load_deck(SAMPLE)
    def test_default_backward_compatible(self):
        self.deck.pop('design', None)
        profile = taste_profile(self.deck)
        self.assertEqual(profile['direction'], 'editorial')
        self.assertIn('--headline-scale', make_html(self.deck))
    def test_valid_override(self):
        self.deck['design'] = {'direction':'educational','visual_density':9}
        self.assertEqual(taste_profile(self.deck)['visual_density'],9)
    def test_reject_css_injection(self):
        self.deck['design']={'direction':'bold','decoration_level':'1; color:red'}
        with self.assertRaises(ValueError): taste_profile(self.deck)
    def test_reject_bool(self):
        self.deck['design']={'visual_density':True}
        with self.assertRaises(ValueError): taste_profile(self.deck)
    def test_no_brand_palette_overwrite(self):
        self.deck['design']={'direction':'heritage'}
        self.assertIn(self.deck['brand']['accent'],make_html(self.deck))
    def test_contrast(self):
        self.assertEqual(contrast('#000000','#FFFFFF'),21)
    def test_detect_contrast_blocker(self):
        self.deck['brand']['foreground']='#222222'
        report=critique(self.deck)
        self.assertTrue(any(x['code']=='contrast-primary' for x in report['findings']))
        self.assertFalse(report['passed_preflight'])
    def test_detect_duplicate(self):
        self.deck['slides'][2]['headline']=self.deck['slides'][1]['headline']
        self.assertTrue(any(x['code']=='repeated-headline' for x in critique(self.deck)['findings']))
    def test_preserves_authored_kinds(self):
        result=suggest_layouts(self.deck)
        self.assertEqual(result[0]['current_kind'],'cover')
        self.assertEqual(len(result),len(self.deck['slides']))

if __name__=='__main__':unittest.main()
