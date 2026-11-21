"""Tests for src/collector.py  -  run with:  python -m unittest discover tests -v"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import collector  # noqa: E402


def write_csv(folder, name, text):
    (Path(folder) / name).write_text(text.strip() + "\n", encoding="utf-8")


class TestCollector(unittest.TestCase):
    def test_backup_counts(self):
        rows = [
            {"backup_date": "2026-11-01", "status": "SUCCESS"},
            {"backup_date": "2026-11-02", "status": "FAILED"},
            {"backup_date": "2026-11-03", "status": "COMPLETED"},
        ]
        r = collector.collect_backups(rows)
        self.assertEqual(r["successful"], 2)
        self.assertEqual(r["failed"], 1)
        self.assertEqual(r["last_successful_backup"], "2026-11-03")

    def test_tablespace_levels(self):
        rows = [
            {"tablespace_name": "USERS", "used_pct": "50"},
            {"tablespace_name": "DATA", "used_pct": "90"},
            {"tablespace_name": "SYSTEM", "total_gb": "10", "used_gb": "9.8"},
        ]
        r = collector.collect_tablespaces(rows)
        self.assertEqual(len(r["warning"]), 1)
        self.assertEqual(len(r["critical"]), 1)
        self.assertEqual(r["highest_usage"]["name"], "SYSTEM")

    def test_tablespace_uses_latest_date_only(self):
        rows = [
            {"date": "2026-11-04", "name": "USERS", "pct_used": "90"},
            {"date": "2026-11-05", "name": "USERS", "pct_used": "50"},
        ]
        r = collector.collect_tablespaces(rows)
        self.assertEqual(r["total_tablespaces"], 1)
        self.assertEqual(len(r["warning"]), 0)

    def test_sessions_average_and_peak(self):
        rows = [
            {"date": "2026-11-04", "active": "100", "max_sessions": "300", "blocked": "0"},
            {"date": "2026-11-05", "active": "200", "max_sessions": "300", "blocked": "1"},
        ]
        r = collector.collect_sessions(rows)
        self.assertEqual(r["average_active"], 150.0)
        self.assertEqual(r["peak_active"], 200)
        self.assertEqual(r["peak_pct_of_max"], 66.7)
        self.assertTrue(r["has_blocking"])

    def test_error_severity_from_code_when_no_severity_column(self):
        rows = [
            {"timestamp": "2026-11-06 22:15:00", "code": "ORA-00060", "message": "Deadlock"},
            {"timestamp": "2026-11-08 14:05:00", "code": "ORA-03113", "message": "EOF"},
            {"timestamp": "2026-11-09 10:00:00", "code": "ORA-99999", "message": "other"},
        ]
        r = collector.collect_errors(rows)
        self.assertEqual(r["by_severity"], {"HIGH": 2, "UNKNOWN": 1})
        self.assertEqual(r["by_code"]["ORA-00060"], 1)

    def test_missing_file_is_reported_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            result = collector.collect_all(d)
            self.assertEqual(len(result["problems"]), 4)
            self.assertIsNone(result["backup"])

    def test_empty_file_raises(self):
        with tempfile.TemporaryDirectory() as d:
            write_csv(d, "x.csv", "a,b")
            with self.assertRaises(collector.CollectorError):
                collector.load_csv(Path(d) / "x.csv")

    def test_bad_number_becomes_default(self):
        self.assertEqual(collector.to_float("abc"), 0.0)
        self.assertEqual(collector.to_float("12.5"), 12.5)

    def test_full_run_with_sample_files(self):
        with tempfile.TemporaryDirectory() as d:
            write_csv(d, "backup.csv", "backup_date,backup_type,status\n2026-11-01,FULL,SUCCESS\n2026-11-02,INCR,FAILED")
            write_csv(d, "tablespace.csv", "tablespace_name,used_pct\nUSERS,40\nDATA,97")
            write_csv(d, "sessions.csv", "active_sessions,blocked_sessions\n12,0\n15,2")
            write_csv(d, "error_log.csv", "error_code,severity\nORA-00600,HIGH\nORA-01555,MEDIUM")
            result = collector.collect_all(d)
            self.assertEqual(result["problems"], [])
            self.assertTrue(result["sessions"]["has_blocking"])
            self.assertEqual(result["error_log"]["total_errors"], 2)


if __name__ == "__main__":
    unittest.main()
