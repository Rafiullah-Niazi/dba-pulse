import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import report_generator as rg

SAMPLE = {
    "analyzed_at": "2026-11-24T09:36:41",
    "collected_at": "2026-11-24T09:36:41",
    "overall_status": "CRITICAL",
    "finding_counts": {"CRITICAL": 1, "HIGH": 1, "MEDIUM": 1},
    "findings": [
        {"area": "Tablespace", "severity": "MEDIUM", "message": "USERS_DATA is 91.0% full."},
        {"area": "Backups", "severity": "CRITICAL", "message": "Last successful backup is 14 days old."},
        {"area": "Sessions", "severity": "HIGH", "message": "7 blocked sessions recorded."},
    ],
}


class TestReportGenerator(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.analysis = os.path.join(self.tmp.name, "analysis.json")
        self.output = os.path.join(self.tmp.name, "report.html")

    def tearDown(self):
        self.tmp.cleanup()

    def write_json(self, data):
        with open(self.analysis, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def test_valid_analysis_creates_report(self):
        self.write_json(SAMPLE)
        rg.generate_report(self.analysis, self.output)
        self.assertTrue(os.path.exists(self.output))

    def test_report_contains_status_and_findings(self):
        html = rg.build_html(SAMPLE)
        self.assertIn("CRITICAL", html)
        self.assertIn("USERS_DATA is 91.0% full.", html)
        self.assertIn("Backups", html)

    def test_findings_sorted_by_severity(self):
        ordered = rg.sort_findings(SAMPLE["findings"])
        self.assertEqual([f["severity"] for f in ordered],
                         ["CRITICAL", "HIGH", "MEDIUM"])

    def test_empty_findings_shows_healthy_message(self):
        data = dict(SAMPLE, findings=[], finding_counts={})
        self.assertIn("No findings", rg.build_html(data))

    def test_missing_file_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            rg.load_analysis(os.path.join(self.tmp.name, "nope.json"))

    def test_missing_findings_raises_error(self):
        self.write_json({"overall_status": "OK"})
        with self.assertRaises(ValueError):
            rg.load_analysis(self.analysis)

    def test_invalid_json_raises_error(self):
        with open(self.analysis, "w") as f:
            f.write("{ not valid json")
        with self.assertRaises(ValueError):
            rg.load_analysis(self.analysis)

    def test_html_is_escaped(self):
        data = dict(SAMPLE, findings=[
            {"area": "X", "severity": "LOW", "message": "<script>alert(1)</script>"}])
        html = rg.build_html(data)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)


if __name__ == "__main__":
    unittest.main() 

    