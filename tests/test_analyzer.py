import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import analyzer

TODAY = date(2026, 11, 11)


def sample(**changes):
    """Collected data shaped like the real collected_data.json."""
    data = {
        "backup": {"failed": 0, "last_successful_backup": "2026-11-10"},
        "tablespace": {
            "critical": [],
            "warning": [{"name": "USERS_DATA", "used_pct": 91.0, "level": "WARNING"}],
        },
        "sessions": {"peak_pct_of_max": 50, "total_blocked": 0},
        "error_log": {"by_severity": {"LOW": 2}},
    }
    data.update(changes)
    return data


class TestAnalyzer(unittest.TestCase):
    def test_healthy_data_gives_ok(self):
        data = sample(tablespace={"critical": [], "warning": []})
        self.assertEqual(analyzer.analyze(data, TODAY)["overall_status"], "OK")

    def test_failed_backup_is_high(self):
        data = sample(backup={"failed": 1, "last_successful_backup": "2026-11-10"})
        result = analyzer.analyze(data, TODAY)
        severities = [f["severity"] for f in result["findings"] if f["area"] == "Backups"]
        self.assertIn("HIGH", severities)

    def test_old_backup_is_critical(self):
        data = sample(backup={"failed": 0, "last_successful_backup": "2026-11-01"})
        self.assertEqual(analyzer.analyze(data, TODAY)["overall_status"], "CRITICAL")

    def test_tablespace_warning_is_medium(self):
        result = analyzer.analyze(sample(), TODAY)
        self.assertEqual(result["findings"][0]["severity"], "MEDIUM")

    def test_session_peak_and_blocked(self):
        data = sample(sessions={"peak_pct_of_max": 95.7, "total_blocked": 7})
        result = analyzer.analyze(data, TODAY)
        text = " ".join(f["message"] for f in result["findings"])
        self.assertIn("95.7%", text)
        self.assertIn("7 blocked", text)

    def test_findings_sorted_worst_first(self):
        data = sample(error_log={"by_severity": {"CRITICAL": 1}})
        result = analyzer.analyze(data, TODAY)
        self.assertEqual(result["findings"][0]["severity"], "CRITICAL")

    def test_missing_input_file_raises(self):
        with self.assertRaises(analyzer.AnalyzerError):
            analyzer.load_collected("no_such_file.json")


if __name__ == "__main__":
    unittest.main()
