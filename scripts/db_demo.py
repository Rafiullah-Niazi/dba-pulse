import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import database as db

db.init_db()
conn = db.get_connection()
tables = [r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
conn.close()
print("Connected to SQLite:", db.DB_PATH.name, "| tables:", tables)

demo = {"overall_status": "CRITICAL",
        "findings": [{"area": "Backups", "severity": "HIGH", "message": "Demo finding"}]}
rid = db.save_run(demo)
print("CREATE -> run id", rid)
print("READ   ->", [dict(r) for r in db.list_runs(3)])
print("UPDATE -> rows changed:", db.update_run_status(rid, "WARNING"))
print("READ   ->", dict(db.list_runs(1)[0]))
print("DELETE -> rows removed:", db.delete_run(rid))

