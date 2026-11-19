# Run from C:\dba-pulse with the venv active:  .\setup_day3.ps1
# Creates the Day 3 folder structure with small placeholder files so GitHub shows every folder.

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path config, docs, output, scripts, src, templates, tests | Out-Null

# Move the sample data generator and keep its Git history
if (Test-Path "make_sample_data.py") {
    git mv make_sample_data.py scripts/make_sample_data.py
}

$files = [ordered]@{
    "src\__init__.py"          = '"""DBA-Pulse source package."""'
    "src\collector.py"         = '"""collector.py - reads and cleans the database health data (T4)."""'
    "src\rules.py"             = '"""rules.py - checks values against thresholds (T5)."""'
    "src\history.py"           = '"""history.py - daily history and 7-day trend in SQLite (T7)."""'
    "src\ai_summary.py"        = '"""ai_summary.py - Gemini summary with fallback text (T9)."""'
    "src\charts.py"            = '"""charts.py - matplotlib storage chart (T11)."""'
    "src\report.py"            = '"""report.py - HTML template and PDF export (T10, T12)."""'
    "tests\test_rules.py"      = '"""test_rules.py - tests for rules.py (T6)."""'
    "config\config.yaml"       = '# Thresholds for the rules go here (T5)'
    "templates\report.html.j2" = '<!-- Jinja2 report template (T10) -->'
    "output\.gitkeep"          = ''
    ".env.example"             = 'GEMINI_API_KEY=your_key_here'
}

foreach ($f in $files.Keys) {
    if (-not (Test-Path $f)) {
        Set-Content -Path $f -Value $files[$f]
    }
}

Write-Host "Done. Now copy architecture.png into docs\ and replace README.md, then check .gitignore."
