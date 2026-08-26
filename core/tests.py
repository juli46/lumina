from pathlib import Path

from django.test import SimpleTestCase


class TestFormJavaScriptTests(SimpleTestCase):
    def test_add_option_script_uses_result_selects(self):
        js_path = Path(__file__).resolve().parent / "static" / "js" / "test.js"
        content = js_path.read_text(encoding="utf-8")

        self.assertIn('class="form-control resultado-select"', content)
        self.assertIn('name="resultado_${idPregunta}[]"', content)

