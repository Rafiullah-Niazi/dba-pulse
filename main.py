"""DBA-Pulse - runs the full pipeline: Collector -> Analyzer -> Database -> Report."""
import json
import subprocess
import sys
from pathlib import Path

from src import database

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
ANALYSIS_FILE = ROOT / "data" / "analysis.json"


def run(script):
    print(f"\n>>> Running {script}")
    return subprocess.run([sys.executable, str(SRC / script)]).returncode


def save_to_database():
    print("\n>>> Saving analysis to database")
    database.init_db()
    with open(ANALYSIS_FILE, encoding="utf-8") as f:
        run_id = database.save_run(json.load(f))
    print(f"Analysis saved to database (run id {run_id})")


if __name__ == "__main__":
    print("DBA-Pulse is ready")

    for step in ("collector.py", "analyzer.py"):
        if run(step) != 0:
            print(f"Pipeline stopped: {step} failed.")
            sys.exit(1)

    save_to_database()

    if run("report_generator.py") != 0:
        print("Pipeline stopped: report_generator.py failed.")
        sys.exit(1)

    print("\nPipeline finished: data/collected_data.json -> data/analysis.json "
          "-> data/dba_pulse.db -> data/report.html")

    