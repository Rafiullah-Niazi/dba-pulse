# Data Collector (Day 5)

Module: src/collector.py

## What it does
Reads backup.csv, tablespace.csv, sessions.csv and error_log.csv from data/,
calculates health metrics, and saves them to data/collected_data.json.

## Metrics
- Backups: successful vs failed, last successful backup
- Tablespaces: latest used %, WARNING at 85%, CRITICAL at 95%
- Sessions: average, peak, peak % of session limit, blocked sessions
- Errors: count by severity (looked up from the ORA code) and by code

## How to run
python src/collector.py
python -m unittest discover tests -v

## Findings from sample data
- 6 of 7 backups successful, 1 failed
- USERS_DATA tablespace at 91.0% (warning)
- Peak sessions 287 of 300 (95.7%), 7 blocked sessions
