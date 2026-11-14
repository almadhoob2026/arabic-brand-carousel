import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from render import load_deck, make_html

class DeckTest(unittest.TestCase):
    def setUp(self):
        self.example=Path(__file__).resolve().parents[1]/'examples'/'demo.json'

    def test_valid_sample(self):
        deck=load_deck(self.example)
        self.assertEqual(len(deck['slides']),7)
        self.assertIn('dir="rtl"',make_html(deck))
        self.assertIn('1080px',make_html(deck))

    def test_rejects_bad_color(self):
        deck=json.loads(self.example.read_text(encoding='utf-8'))
        deck['brand']['accent']='red; background: url(http://evil)'
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'bad.json';f.write_text(json.dumps(deck),encoding='utf-8')
            with self.assertRaises(ValueError):load_deck(f)

    def test_escapes_html(self):
        deck=load_deck(self.example)
        deck['slides'][0]['headline']='<script>alert(1)</script>'
        result=make_html(deck)
        self.assertIn('&lt;script&gt;',result)
        self.assertNotIn('<script>alert(1)</script>',result)

    def test_css_tokens_single_prefix(self):
        markup=make_html(load_deck(self.example))
        self.assertIn(';--headline-scale:',markup)
        self.assertNotIn('----',markup)

    def test_brand_handle_isolated(self):
        self.assertIn('<bdi>@yourbrand</bdi>',make_html(load_deck(self.example)))

if __name__=='__main__':unittest.main()
