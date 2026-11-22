import json
import subprocess
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def read_json(name):
    with open(BASE / "data" / name, encoding="utf-8") as f:
        return json.load(f)


class TestPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = subprocess.run([sys.executable, str(BASE / "main.py")],
                                      capture_output=True, text=True)

    def test_pipeline_runs_without_error(self):
        self.assertEqual(self.pipeline.returncode, 0,
                         self.pipeline.stdout + self.pipeline.stderr)

    def test_collector_output_has_timestamp(self):
        self.assertIn("collected_at", read_json("collected_data.json"))

    def test_analyzer_uses_collector_output(self):
        collected = read_json("collected_data.json")
        analysis = read_json("analysis.json")
        self.assertEqual(analysis["collected_at"], collected["collected_at"])
        self.assertIsInstance(analysis["findings"], list)


if __name__ == "__main__":
    unittest.main()


