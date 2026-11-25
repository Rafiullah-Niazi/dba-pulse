import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import database as db

SAMPLE = {
    "overall_status": "CRITICAL",
    "findings": [
        {"area": "Backups", "severity": "HIGH", "message": "a"},
        {"area": "Sessions", "severity": "MEDIUM", "message": "b"},
    ],
}


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "test.db"
        db.init_db(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_read(self):
        rid = db.save_run(SAMPLE, self.path)
        self.assertEqual(len(db.get_findings(rid, self.path)), 2)
        self.assertEqual(db.list_runs(1, self.path)[0]["finding_count"], 2)

    def test_update(self):
        rid = db.save_run(SAMPLE, self.path)
        self.assertEqual(db.update_run_status(rid, "OK", self.path), 1)
        self.assertEqual(db.list_runs(1, self.path)[0]["overall_status"], "OK")

    def test_delete_cascades(self):
        rid = db.save_run(SAMPLE, self.path)
        self.assertEqual(db.delete_run(rid, self.path), 1)
        self.assertEqual(db.get_findings(rid, self.path), [])

