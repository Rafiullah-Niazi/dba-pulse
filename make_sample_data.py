import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "sample.db"
DAYS = 7


def build_tables():
    today = date.today()
    days = [today - timedelta(days=i) for i in range(DAYS - 1, -1, -1)]  # oldest -> today

    # 1. Backup: one FAILED day (day index 3) to test Critical later
    backup_rows = []
    for i, d in enumerate(days):
        if i == 3:
            backup_rows.append((d.isoformat(), "PRODDB", f"{d} 01:30:00", f"{d} 01:42:00", "FAILED", 0.0))
        else:
            backup_rows.append((d.isoformat(), "PRODDB", f"{d} 01:30:00", f"{d} 02:10:00", "COMPLETED", round(48.0 + i * 0.3, 1)))
    backup = pd.DataFrame(backup_rows, columns=["date", "db_name", "start_time", "end_time", "status", "size_gb"])

    # 2. Tablespace: USERS_DATA grows 88% -> 91% (Warning today)
    users_pct = [88.0, 88.5, 89.0, 89.5, 90.0, 90.5, 91.0]
    ts_rows = []
    for i, d in enumerate(days):
        ts_rows.append((d.isoformat(), "SYSTEM", 10.0, 4.5))
        ts_rows.append((d.isoformat(), "SYSAUX", 20.0, 12.0))
        ts_rows.append((d.isoformat(), "USERS_DATA", 100.0, users_pct[i]))
        ts_rows.append((d.isoformat(), "TEMP", 50.0, 15.0))
    tablespace = pd.DataFrame(ts_rows, columns=["date", "name", "total_gb", "used_gb"])
    tablespace["pct_used"] = (tablespace["used_gb"] / tablespace["total_gb"] * 100).round(1)

    # 3. Sessions: spike on day index 4 to test the rules later
    active = [118, 125, 131, 129, 287, 140, 142]
    blocked = [0, 0, 1, 0, 6, 0, 0]
    sessions = pd.DataFrame({
        "date": [d.isoformat() for d in days],
        "active": active,
        "max_sessions": [300] * DAYS,
        "blocked": blocked,
    })

    # 4. Error log: a few ORA- lines, 3 of them today
    error_log = pd.DataFrame([
        (f"{days[2]} 22:15:00", "ORA-00060", "Deadlock detected"),
        (f"{days[4]} 14:05:00", "ORA-03113", "End-of-file on communication channel"),
        (f"{days[6]} 03:12:00", "ORA-01653", "Unable to extend table in tablespace USERS_DATA"),
        (f"{days[6]} 05:40:00", "ORA-00060", "Deadlock detected"),
        (f"{days[6]} 06:02:00", "ORA-03113", "End-of-file on communication channel"),
    ], columns=["timestamp", "code", "message"])

    return {"backup": backup, "tablespace": tablespace, "sessions": sessions, "error_log": error_log}


def main():
    DATA_DIR.mkdir(exist_ok=True)
    tables = build_tables()
    conn = sqlite3.connect(DB_PATH)
    for name, df in tables.items():
        df.to_sql(name, conn, if_exists="replace", index=False)
        df.to_csv(DATA_DIR / f"{name}.csv", index=False)
        print(f"{name}: {len(df)} rows")
    conn.close()
    print(f"Sample data created in {DATA_DIR}/")


if __name__ == "__main__":
    main()


    