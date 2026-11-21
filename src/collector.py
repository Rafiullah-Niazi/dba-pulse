"""
collector.py - DBA-Pulse Data Collector module (Phase 1, Day 5)

What it does
------------
Reads the four CSV files in data/ (backup, tablespace, sessions, error_log),
checks that they are valid, calculates simple health metrics from each one,
and saves everything into one clean JSON file (data/collected_data.json).
The next module (analyzer / AI summary) will read that JSON file.

Run it:
    python src/collector.py
"""
from datetime import datetime
import csv
import json
from datetime import datetime
from pathlib import Path

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_FILE = DATA_DIR / "collected_data.json"

# ---------- Thresholds (change here, not inside the functions) ----------
TABLESPACE_WARNING_PCT = 85
TABLESPACE_CRITICAL_PCT = 95

# Severity for common ORA- errors (used when error_log.csv has no severity column).
# Edit this table to match your own DBA judgement.
ERROR_SEVERITY = {
    "ORA-00600": "CRITICAL",  # internal error
    "ORA-07445": "CRITICAL",  # exception encountered (core dump)
    "ORA-00060": "HIGH",      # deadlock detected
    "ORA-03113": "HIGH",      # end-of-file on communication channel
    "ORA-01653": "HIGH",      # unable to extend table
    "ORA-01654": "HIGH",      # unable to extend index
    "ORA-01688": "HIGH",      # unable to extend table partition
    "ORA-04031": "HIGH",      # unable to allocate shared memory
    "ORA-12541": "HIGH",      # no listener
    "ORA-01555": "MEDIUM",    # snapshot too old
    "ORA-01017": "MEDIUM",    # invalid username/password
    "ORA-00054": "LOW",       # resource busy
}

# The four input files this module expects
INPUT_FILES = {
    "backup": "backup.csv",
    "tablespace": "tablespace.csv",
    "sessions": "sessions.csv",
    "error_log": "error_log.csv",
}


class CollectorError(Exception):
    """Raised when an input file is missing, empty or unreadable."""


# ---------- Helpers ----------
def load_csv(path):
    """Read a CSV file and return a list of rows (dicts).
    Column names are lower-cased and trimmed so 'Status ' and 'status' match."""
    path = Path(path)
    if not path.exists():
        raise CollectorError(f"File not found: {path}")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            for row in reader
        ]

    if not rows:
        raise CollectorError(f"File is empty: {path}")
    return rows


def to_float(value, default=0.0):
    """Convert text to a number. Bad or empty values become the default."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def pick(row, *names, default=""):
    """Return the first column that exists, so small column-name
    differences (e.g. 'status' vs 'backup_status') do not break the code."""
    for name in names:
        if name in row and row[name] != "":
            return row[name]
    return default


# ---------- One function per data source ----------
def collect_backups(rows):
    """Count successful / failed backups and find the latest successful one."""
    ok_words = {"success", "successful", "completed", "ok", "passed"}
    success, failed = [], []

    for r in rows:
        status = pick(r, "status", "backup_status").lower()
        (success if status in ok_words else failed).append(r)

    latest = ""
    if success:
        latest = max(
            pick(r, "backup_date", "date", "start_time", "end_time") for r in success
        )

    return {
        "total": len(rows),
        "successful": len(success),
        "failed": len(failed),
        "last_successful_backup": latest,
        "failed_backups": [
            {
                "date": pick(r, "backup_date", "date", "start_time"),
                "type": pick(r, "backup_type", "type"),
                "status": pick(r, "status", "backup_status"),
            }
            for r in failed
        ],
    }


def collect_tablespaces(rows):
    """Work out the used % for each tablespace (latest date only) and flag risky ones."""
    latest = {}  # tablespace name -> (date, item); later rows / later dates win
    for r in rows:
        used_pct = to_float(pick(r, "used_pct", "used_percent", "pct_used"), -1)
        if used_pct < 0:  # not in the file, calculate it
            total = to_float(pick(r, "total_gb", "total_mb", "size_gb"))
            used = to_float(pick(r, "used_gb", "used_mb"))
            used_pct = round(used / total * 100, 2) if total else 0.0

        if used_pct >= TABLESPACE_CRITICAL_PCT:
            level = "CRITICAL"
        elif used_pct >= TABLESPACE_WARNING_PCT:
            level = "WARNING"
        else:
            level = "OK"

        name = pick(r, "tablespace_name", "tablespace", "name")
        date = pick(r, "date", "snapshot_date", "collected_date")
        if name not in latest or date >= latest[name][0]:
            latest[name] = (date, {"name": name, "date": date,
                                   "used_pct": used_pct, "level": level})

    items = [v[1] for v in latest.values()]
    return {
        "total_tablespaces": len(items),
        "critical": [i for i in items if i["level"] == "CRITICAL"],
        "warning": [i for i in items if i["level"] == "WARNING"],
        "highest_usage": max(items, key=lambda i: i["used_pct"]) if items else None,
    }


def collect_sessions(rows):
    """Summarise session counts: average, peak, limit and blocking."""
    active = [to_float(pick(r, "active_sessions", "active")) for r in rows]
    blocked = sum(to_float(pick(r, "blocked_sessions", "blocked")) for r in rows)
    max_sessions = max(
        (to_float(pick(r, "max_sessions", "session_limit")) for r in rows), default=0
    )
    peak = max(active) if active else 0
    return {
        "snapshots": len(rows),
        "average_active": round(sum(active) / len(active), 1) if active else 0,
        "peak_active": int(peak),
        "max_sessions": int(max_sessions),
        "peak_pct_of_max": round(peak / max_sessions * 100, 1) if max_sessions else None,
        "total_blocked": int(blocked),
        "has_blocking": blocked > 0,
    }


def collect_errors(rows):
    """Count errors by severity and list the ORA- codes seen.
    Severity comes from the file if it has one, otherwise from ERROR_SEVERITY."""
    by_severity = {}
    by_code = {}
    for r in rows:
        code = pick(r, "error_code", "ora_code", "code").upper()
        sev = pick(r, "severity", "level").upper()
        if not sev:
            sev = ERROR_SEVERITY.get(code, "UNKNOWN")
        by_severity[sev] = by_severity.get(sev, 0) + 1
        if code:
            by_code[code] = by_code.get(code, 0) + 1
    return {
        "total_errors": len(rows),
        "by_severity": by_severity,
        "by_code": by_code,
        "error_codes": sorted(by_code),
    }


# ---------- Main workflow ----------
def collect_all(data_dir=DATA_DIR):
    """Load every file, collect metrics, and return one combined dict."""
    data_dir = Path(data_dir)
    collectors = {
        "backup": collect_backups,
        "tablespace": collect_tablespaces,
        "sessions": collect_sessions,
        "error_log": collect_errors,
    }

    result = {"collected_at": datetime.now().isoformat(timespec="seconds")}
    problems = []

    for key, func in collectors.items():
        try:
            rows = load_csv(data_dir / INPUT_FILES[key])
            result[key] = func(rows)
        except CollectorError as e:
            problems.append(str(e))
            result[key] = None  # keep going, report the problem at the end

    result["problems"] = problems

    result["collected_at"] = datetime.now().isoformat(timespec="seconds")
    return result


def save_json(data, path=OUTPUT_FILE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def print_summary(data):
    print("=" * 50)
    print("DBA-Pulse - Collector summary")
    print("=" * 50)
    b, t, s, e = data["backup"], data["tablespace"], data["sessions"], data["error_log"]
    if b:
        print(f"Backups     : {b['successful']}/{b['total']} successful, "
              f"{b['failed']} failed (last OK: {b['last_successful_backup']})")
    if t:
        top = t["highest_usage"]
        print(f"Tablespaces : {t['total_tablespaces']} checked, {len(t['critical'])} critical, "
              f"{len(t['warning'])} warning (highest: {top['name']} {top['used_pct']}%)")
    if s:
        print(f"Sessions    : avg {s['average_active']} active, peak {s['peak_active']}"
              f"/{s['max_sessions']} ({s['peak_pct_of_max']}%), {s['total_blocked']} blocked")
    if e:
        print(f"Errors      : {e['total_errors']} total {e['by_severity']}")
    for p in data["problems"]:
        print(f"[PROBLEM] {p}")


def main():
    data = collect_all()
    out = save_json(data)
    print_summary(data)
    print(f"\nSaved to: {out}")


if __name__ == "__main__":
    main()
