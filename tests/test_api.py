from pathlib import Path
import shutil
import tempfile
import unittest

from fastapi.testclient import TestClient

from src import database
from src.api import app


class TestApi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old_path = database.DB_PATH
        database.DB_PATH = Path(self.tmp) / "test.db"
        database.init_db()
        self.client = TestClient(app)

    def tearDown(self):
        database.DB_PATH = self.old_path
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _create(self):
        body = {
            "overall_status": "CRITICAL",
            "findings": [
                {"area": "Backups", "severity": "HIGH", "message": "1 backup failed."}
            ],
        }
        return self.client.post("/runs", json=body)

    def test_create_and_get(self):
        r = self._create()
        self.assertEqual(r.status_code, 201)
        run_id = r.json()["run_id"]
        self.assertEqual(self.client.get(f"/runs/{run_id}").status_code, 200)

    def test_findings_returned(self):
        run_id = self._create().json()["run_id"]
        r = self.client.get(f"/runs/{run_id}/findings")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)
        self.assertEqual(r.json()[0]["area"], "Backups")

    def test_update_status(self):
        run_id = self._create().json()["run_id"]
        r = self.client.put(f"/runs/{run_id}/status", json={"overall_status": "WARNING"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get(f"/runs/{run_id}").json()["overall_status"], "WARNING")

    def test_delete_removes_run_and_findings(self):
        run_id = self._create().json()["run_id"]
        self.assertEqual(self.client.delete(f"/runs/{run_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/runs/{run_id}").status_code, 404)
        self.assertEqual(len(database.get_findings(run_id)), 0)

    def test_not_found(self):
        self.assertEqual(self.client.get("/runs/999").status_code, 404)

    def test_invalid_status_rejected(self):
        run_id = self._create().json()["run_id"]
        r = self.client.put(f"/runs/{run_id}/status", json={"overall_status": "BROKEN"})
        self.assertEqual(r.status_code, 422)

    def test_bad_limit_rejected(self):
        self.assertEqual(self.client.get("/runs?limit=500").status_code, 400)


if __name__ == "__main__":
    unittest.main()


    