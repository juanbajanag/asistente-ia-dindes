from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestAppFiles(unittest.TestCase):
    def test_app_syntax(self):
        path = ROOT / "app" / "app.py"
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")

    def test_cloud_entrypoint_syntax(self):
        path = ROOT / "streamlit_app.py"
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")

    def test_cloud_entrypoint_targets_main_app(self):
        text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
        self.assertIn('APP_PATH = PROJECT_ROOT / "app" / "app.py"', text)


if __name__ == "__main__":
    unittest.main()
