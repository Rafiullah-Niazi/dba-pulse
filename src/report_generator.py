import json
import os
import sys
from html import escape

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
COLORS = {
    "CRITICAL": "#c0392b",
    "HIGH": "#e67e22",
    "MEDIUM": "#d4ac0d",
    "LOW": "#27ae60",
}


def load_analysis(path):
    """Load and validate the analysis JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Analysis file not found: {path}. Run the analyzer first."
        )
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        raise ValueError(f"Analysis file is not valid JSON: {path}")

    if not isinstance(data, dict):
        raise ValueError("Invalid analysis file: expected a JSON object.")
    if "overall_status" not in data:
        raise ValueError("Invalid analysis file: 'overall_status' is missing.")
    if not isinstance(data.get("findings"), list):
        raise ValueError("Invalid analysis file: 'findings' list is missing.")
    return data


def sort_findings(findings):
    """Most severe findings first."""
    def rank(f):
        sev = str(f.get("severity", "LOW")).upper()
        return SEVERITY_ORDER.index(sev) if sev in SEVERITY_ORDER else len(SEVERITY_ORDER)
    return sorted(findings, key=rank)


def build_summary_cards(data):
    counts = data.get("finding_counts", {})
    cards = ""
    for sev in SEVERITY_ORDER:
        cards += (
            f"<div class='card' style='border-top:5px solid {COLORS[sev]}'>"
            f"<div class='num'>{int(counts.get(sev, 0))}</div>"
            f"<div>{sev}</div></div>"
        )
    return cards


def build_rows(findings):
    if not findings:
        return "<tr><td colspan='3'>No findings. Database looks healthy.</td></tr>"
    rows = ""
    for f in sort_findings(findings):
        sev = str(f.get("severity", "LOW")).upper()
        color = COLORS.get(sev, "#7f8c8d")
        rows += (
            "<tr>"
            f"<td style='color:{color};font-weight:bold'>{escape(sev)}</td>"
            f"<td>{escape(str(f.get('area', 'General')))}</td>"
            f"<td>{escape(str(f.get('message', '')))}</td>"
            "</tr>\n"
        )
    return rows


def build_html(data):
    status = str(data.get("overall_status", "UNKNOWN")).upper()
    status_color = COLORS.get(status, "#7f8c8d")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DBA-Pulse Report</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 30px; color: #2c3e50; }}
  h1 {{ margin-bottom: 5px; }}
  .meta {{ color: #7f8c8d; font-size: 14px; }}
  .status {{ font-size: 22px; font-weight: bold; color: {status_color}; margin: 15px 0; }}
  .cards {{ display: flex; gap: 15px; margin-bottom: 25px; }}
  .card {{ flex: 1; background: #f4f6f7; padding: 15px; text-align: center; border-radius: 6px; }}
  .num {{ font-size: 28px; font-weight: bold; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
  th {{ background: #2c3e50; color: #fff; }}
</style>
</head>
<body>
<h1>DBA-Pulse Daily Health Report</h1>
<p class="meta">Data collected: {escape(str(data.get('collected_at', 'N/A')))}
 | Analyzed: {escape(str(data.get('analyzed_at', 'N/A')))}</p>
<div class="status">Overall status: {escape(status)}</div>
<div class="cards">{build_summary_cards(data)}</div>
<table>
<tr><th>Severity</th><th>Area</th><th>Finding</th></tr>
{build_rows(data['findings'])}
</table>
</body>
</html>"""


def generate_report(analysis_path="data/analysis.json",
                    output_path="data/report.html"):
    data = load_analysis(analysis_path)
    html = build_html(data)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


if __name__ == "__main__":
    try:
        path = generate_report()
        print(f"Report saved to {path}")
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)

