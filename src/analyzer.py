
"""DBA-Pulse - Module 2: Analyzer
Reads data/collected_data.json, decides which findings are risks,
and saves data/analysis.json for the AI summary module."""

import json
from datetime import date, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "collected_data.json"
OUTPUT_FILE = BASE_DIR / "data" / "analysis.json"

# Limits in one place so they are easy to change
BACKUP_MAX_AGE_DAYS = 1
SESSION_PEAK_WARNING_PCT = 80
SESSION_PEAK_HIGH_PCT = 90
BLOCKED_WARNING = 1
BLOCKED_HIGH = 5

RANK = {"OK": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


class AnalyzerError(Exception):
    """Raised when the collected data cannot be read."""


def g(data, *names, default=None):
    """Return the first key found (same idea as pick() in the collector)."""
    if isinstance(data, dict):
        for name in names:
            if name in data and data[name] is not None:
                return data[name]
    return default


def finding(area, severity, message):
    return {"area": area, "severity": severity, "message": message}


def load_collected(path=INPUT_FILE):
    path = Path(path)
    if not path.exists():
        raise AnalyzerError(f"Collected data not found: {path}. Run collector.py first.")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise AnalyzerError(f"Collected data is not valid JSON: {exc}")


def analyze_backups(data, today=None):
    today = today or date.today()
    out = []
    failed = g(data, "failed", "failed_count", default=0) or 0
    last_ok = g(data, "last_successful_backup", "last successful" , "last_successful_date", "last_ok")
    if failed:
        out.append(finding("Backups", "HIGH", f"{failed} backup(s) failed."))
    if not last_ok:
        out.append(finding("Backups", "CRITICAL", "No successful backup found."))
    else:
        try:
            age = (today - datetime.strptime(str(last_ok)[:10], "%Y-%m-%d").date()).days
            if age > BACKUP_MAX_AGE_DAYS:
                sev = "CRITICAL" if age > 3 else "HIGH"
                out.append(finding("Backups", sev, f"Last successful backup is {age} days old ({last_ok})."))
        except ValueError:
            out.append(finding("Backups", "LOW", f"Could not read backup date: {last_ok}"))
    return out


def analyze_tablespaces(data):
    out = []
    for ts in g(data, "critical", default=[]) or []:
        name = g(ts, "name", default="?")
        pct = g(ts, "used_pct", default=0)
        out.append(finding("Tablespace", "CRITICAL", f"{name} is {pct}% full."))
    for ts in g(data, "warning", default=[]) or []:
        name = g(ts, "name", default="?")
        pct = g(ts, "used_pct", default=0)
        out.append(finding("Tablespace", "MEDIUM", f"{name} is {pct}% full."))
    return out


def analyze_sessions(data):
    out = []
    peak_pct = g(data, "peak_pct_of_max" , "peak_pct" , "peak_percent" , default=0) or 0
    blocked = g(data, "blocked_total", "total_blocked", "blocked", default=0) or 0
    if peak_pct >= SESSION_PEAK_HIGH_PCT:
        out.append(finding("Sessions", "HIGH", f"Peak sessions reached {peak_pct}% of the limit."))
    elif peak_pct >= SESSION_PEAK_WARNING_PCT:
        out.append(finding("Sessions", "MEDIUM", f"Peak sessions reached {peak_pct}% of the limit."))
    if blocked >= BLOCKED_HIGH:
        out.append(finding("Sessions", "HIGH", f"{blocked} blocked sessions recorded."))
    elif blocked >= BLOCKED_WARNING:
        out.append(finding("Sessions", "MEDIUM", f"{blocked} blocked session(s) recorded."))
    return out


def analyze_errors(data):
    out = []
    by_sev = g(data, "by_severity", "severity_counts", default={}) or {}
    for sev in ("CRITICAL", "HIGH"):
        count = by_sev.get(sev, 0)
        if count:
            out.append(finding("Errors", sev, f"{count} {sev} error(s) in the error log."))
    return out


def analyze(collected, today=None):
    findings = []
    findings += analyze_backups(g(collected, "backups", "backup", default={}), today)
    findings += analyze_tablespaces(g(collected, "tablespaces", "tablespace", default={}))
    findings += analyze_sessions(g(collected, "sessions", default={}))
    findings += analyze_errors(g(collected, "errors", "error_log", default={}))
    findings.sort(key=lambda f: RANK[f["severity"]], reverse=True)

    overall = findings[0]["severity"] if findings else "OK"
    counts = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    return {
        "analyzed_at": datetime.now().isoformat(timespec="seconds"),
        "collected_at": g(collected, "collected_at"),
        "overall_status": overall,
        "finding_counts": counts,
        "findings": findings,
    }


def save_json(result, path=OUTPUT_FILE):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)


def print_summary(result):
    print("=" * 50)
    print("DBA-Pulse - Analyzer summary")
    print("=" * 50)
    print(f"Overall status : {result['overall_status']}")
    print(f"Findings       : {len(result['findings'])} {result['finding_counts']}")
    for f in result["findings"]:
        print(f"  [{f['severity']:<8}] {f['area']}: {f['message']}")
    print(f"\nSaved to: {OUTPUT_FILE}")


def main():
    try:
        result = analyze(load_collected())
    except AnalyzerError as exc:
        print(f"ERROR: {exc}")
        return 1
    save_json(result)
    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
