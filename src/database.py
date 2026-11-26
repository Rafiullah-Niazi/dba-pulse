"""SQLite storage for DBA-Pulse analysis runs and findings."""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dba_pulse.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    run_time       TEXT    NOT NULL,
    overall_status TEXT    NOT NULL,
    finding_count  INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS findings (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id    INTEGER NOT NULL,
    area      TEXT,
    severity  TEXT    NOT NULL,
    message   TEXT    NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);
"""


def get_connection(db_path=None):
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


# CREATE
def save_run(analysis, db_path=None):
    findings = analysis.get("findings", [])
    run_time = analysis.get("analyzed_at") or datetime.now().isoformat(timespec="seconds")
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO runs (run_time, overall_status, finding_count) VALUES (?, ?, ?)",
            (run_time, analysis.get("overall_status", "UNKNOWN"), len(findings)),
        )
        run_id = cur.lastrowid
        for f in findings:
            conn.execute(
                "INSERT INTO findings (run_id, area, severity, message) VALUES (?, ?, ?, ?)",
                (run_id, f.get("area"), f.get("severity", "UNKNOWN"), f.get("message", "")),
            )
        conn.commit()
        return run_id
    finally:
        conn.close()


# READ
def list_runs(limit=10, db_path=None):
    conn = get_connection(db_path)
    try:
        return conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    finally:
        conn.close()


def get_findings(run_id, db_path=None):
    conn = get_connection(db_path)
    try:
        return conn.execute(
            "SELECT * FROM findings WHERE run_id = ?", (run_id,)).fetchall()
    finally:
        conn.close()

def get_run(run_id, db_path=None):
    """Return one run as a sqlite3.Row, or None if it does not exist."""
    conn = get_connection(db_path)
    try:
        return conn.execute(
            "SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    finally:
        conn.close()
        


# UPDATE
def update_run_status(run_id, new_status, db_path=None):
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "UPDATE runs SET overall_status = ? WHERE id = ?", (new_status, run_id))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


# DELETE (findings are removed too, via ON DELETE CASCADE)
def delete_run(run_id, db_path=None):
    conn = get_connection(db_path)
    try:
        cur = conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()

        