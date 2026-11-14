"""Offline visual editor smoke test. Browser required only for the optional integration test."""
import re
import unittest
from pathlib import Path

EDITOR = Path(__file__).resolve().parents[1] / 'editor' / 'index.html'


class EditorStaticTests(unittest.TestCase):
    def test_editor_is_self_contained(self):
        doc = EDITOR.read_text(encoding='utf-8')
        self.assertIn('<html lang="ar" dir="rtl">', doc)
        self.assertIn('const EXAMPLE=', doc)
        self.assertIn('function drawSlide(', doc)
        self.assertIn('canvas.toBlob(', doc)
        self.assertNotRegex(doc, r'<script[^>]+src=')
        self.assertNotRegex(doc, r'<link[^>]+href=["\']https?://')
        self.assertIn('function validate(', doc)

    def test_output_size(self):
        doc = EDITOR.read_text(encoding='utf-8')
        self.assertIn('canvas.width=1080', doc)
        self.assertIn('canvas.height=1350', doc)


if __name__ == '__main__':
    unittest.main()
