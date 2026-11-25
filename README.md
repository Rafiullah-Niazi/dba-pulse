
# DBA-Pulse

Automated daily database health report with an AI-written summary.

DBA-Pulse reads database health data (backup, tablespace, sessions and error log), checks it against simple rules, asks the Gemini API (free tier) to write a short plain-English summary, and builds a daily report as HTML and PDF.

Built as part of the UNAI TECH Virtual Internship 2026 (AI & Automation).

## Current Status (Phase 1, Day 8)

| Step | Module | Board tasks | Status |
|------|--------|-------------|--------|
| 1 | Setup, repository, sample data | T1 to T3 | Done |
| 2 | `collector.py` | T4 | Done (Day 5) |
| 3 | `analyzer.py` (risk rules) and tests | T5, T6 | Done (Day 6) |
| 4 | `report_generator.py` (HTML report) and tests | T10 (first version) | Done (Day 8) |
| 5 | `history.py` | T7 | Planned |
| 6 | `ai_summary.py` | T8, T9 | Planned |
| 7 | `charts.py` and final report template | T11 | Planned |
| 8 | PDF export | T12 | Planned |

**What works today:** the collector, the analyzer and the report generator are connected by `main.py`. Running it produces `data/collected_data.json`, `data/analysis.json` and `data/report.html`. All automated tests pass.

**Not built yet:** history tracking, AI summary, charts, PDF export.

## Architecture

![DBA-Pulse architecture](docs/architecture.png)

```mermaid
flowchart LR
&#x20;   A["data/*.csv"] --> B[collector.py]
&#x20;   B --> C[analyzer.py]
&#x20;   CFG[config.yaml] --> C
&#x20;   C --> D[history.py]
&#x20;   C --> E[ai_summary.py]
&#x20;   KEY[".env API key"] --> E
&#x20;   D --> F[charts.py]
&#x20;   C --> G[report_generator.py]
&#x20;   E --> G
&#x20;   F --> G
&#x20;   G --> H["HTML + PDF report"]
&#x20;   M[main.py] -.runs each step.-> B
```

`main.py` calls each module in order. Each step saves its result as a JSON file that the next step reads. Only `ai_summary.py` will talk to the internet, and if the AI call fails a fallback text will be used so the report is still produced.

## Requirements and Planning

Full requirements, feature and module breakdown, priorities and task list: [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md)

| Priority | Features |
|----------|----------|
| Must Have | Collector, rules + config, AI summary (with fallback), HTML report, main.py pipeline |
| Should Have | History and 7-day trend, storage chart, PDF export, tests, daily scheduling |
| Could Have | Email or Telegram alerts, live Oracle connection, web page for past reports |

## Modules

| Module | File | Responsibility |
|--------|------|----------------|
| Orchestrator | `main.py` | Runs the pipeline in order and reports errors clearly |
| Collector | `src/collector.py` | Reads the four data tables and cleans them |
| Analyzer (risk rules) | `src/analyzer.py` | Finds the risks in the collected data, gives each a severity, saves `data/analysis.json` |
| Report generator | `src/report_generator.py` | Reads `data/analysis.json`, validates it and builds `data/report.html` with a status, severity cards and a sorted findings table |
| History store | `src/history.py` | Saves daily results in SQLite and returns the 7-day trend (planned) |
| AI summary | `src/ai_summary.py` | Calls the Gemini API for a short summary, with fallback text (planned) |
| Chart generator | `src/charts.py` | Draws the storage chart with matplotlib (planned) |

## Folder structure

```
dba-pulse/
├── config/
│   └── config.yaml          thresholds for the rules
├── data/                    sample data and generated JSON/HTML files
├── docs/
│   └── architecture.png     architecture diagram
├── scripts/
│   └── make_sample_data.py  creates the sample data
├── src/
│   ├── collector.py
│   ├── analyzer.py
│   └── report_generator.py
├── templates/
├── tests/
│   ├── test_collector.py
│   ├── test_analyzer.py
│   ├── test_pipeline.py
│   └── test_report_generator.py
├── .env.example
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

## Setup

```powershell
git clone https://github.com/Rafiullah-Niazi/dba-pulse.git
cd dba-pulse
python -m venv venv
venvScriptsActivate.ps1
pip install -r requirements.txt
python scripts/make_sample_data.py
```

Run the commands from the project root. To use the AI summary later, copy `.env.example` to `.env` and add your own Gemini API key. The `.env` file is ignored by Git and must never be uploaded.

## How to run

1. Activate the virtual environment:
&#x20;  ```
&#x20;  venvScriptsactivate
&#x20;  ```
2. Run the full pipeline (collector, analyzer, report):
&#x20;  ```
&#x20;  python main.py
&#x20;  ```
3. Open `data/report.html` in your browser to see the report.
4. Run only the report generator (after the analyzer has run):
&#x20;  ```
&#x20;  python src/report_generator.py
&#x20;  ```
5. Run the tests:
&#x20;  ```
&#x20;  python -m unittest discover -s tests -p "test_*.py" -v
&#x20;  ```

## Progress log

- Day 5: Data Collector done
- Day 6: Analyzer done and connected to the collector through `main.py`
- Day 8: Report Generator done (HTML report) and connected to the pipeline
- Next: AI summary with the Gemini API

## Database

DBA-Pulse stores each analysis run in SQLite (`data/dba_pulse.db`) using
`src/database.py` (tables: `runs`, `findings`; full CRUD). The database is
filled automatically by `python main.py`.

- Schema and operations: [docs/database.md](docs/database.md)
- Demo of Create/Read/Update/Delete: `python scripts/db_demo.py`
- Tests: `python -m unittest discover -s tests -p "test_*.py" -v`




## Tools

Python, SQLite, Gemini API (free tier), Jinja2, matplotlib, ReportLab. Everything used in this project is free.

## Author

Rafiullah Niazi, Kabul, Afghanistan
