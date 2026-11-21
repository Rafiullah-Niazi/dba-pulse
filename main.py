"""DBA-Pulse - runs the full pipeline: Collector -> Analyzer."""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"


def run(script):
    print(f"\n>>> Running {script}")
    return subprocess.run([sys.executable, str(SRC / script)]).returncode


if __name__ == "__main__":
    print("DBA-Pulse is ready")
    for step in ("collector.py", "analyzer.py"):
        if run(step) != 0:
            print(f"Pipeline stopped: {step} failed.")
            sys.exit(1)
    print("\nPipeline finished: data/collected_data.json -> data/analysis.json")

    