# DBA-Pulse: Requirements and Development Plan

Part of the UNAI TECH Virtual Internship 2026 (AI & Automation). Author: Rafiullah Niazi.

## 1. Project requirements overview

**Problem.** A database administrator has to check backups, tablespace usage, sessions and error logs every day. Doing this by hand is slow, easy to forget, and the results are not stored anywhere, so trends are missed.

**Solution.** DBA-Pulse reads the daily data, checks it against clear rules, keeps a 7-day history, asks an AI model to write a short plain-English summary, and produces one HTML/PDF report.

**Scope.** The first version works on sample CSV files (backup, tablespace, sessions, error log). It runs on one computer, uses only free tools, and fits in 30 to 60 minutes of work per day.

**Out of scope.** A web dashboard, user login, a paid AI service, and a live connection to a production database (see Could Have in section 4).

## 2. Functional and non-functional requirements

### 2.1 Functional requirements

| ID | Requirement |
|----|-------------|
| FR1 | Read the four input tables (backup, tablespace, sessions, error log) from the data folder. |
| FR2 | Clean the data: remove empty rows, fix data types and dates, and stop with a clear message if a file or column is missing. |
| FR3 | Check every value against the thresholds in config.yaml and mark it OK, WARNING or CRITICAL. |
| FR4 | Let the user change thresholds in config.yaml without editing Python code. |
| FR5 | Save each day's result in SQLite and return the last 7 days as a trend. |
| FR6 | Draw a 7-day storage trend chart with matplotlib. |
| FR7 | Ask the Gemini API for a short plain-English summary of the findings, and use fallback text if the call fails. |
| FR8 | Build a report (findings table, chart, AI summary) from a Jinja2 template and save it as HTML and PDF in the output folder. |
| FR9 | Run the whole pipeline with one command (`python main.py`) and show a readable error if any step fails. |
| FR10 | Include automatic tests for the rules module (OK, WARNING and CRITICAL cases). |

### 2.2 Non-functional requirements

| ID | Area | Requirement |
|----|------|-------------|
| NFR1 | Cost | Every tool and service must be free (Python, Gemini free tier, SQLite, matplotlib, Jinja2, VS Code, Git, GitHub). |
| NFR2 | Security | The API key stays in a .env file that is ignored by Git. Only .env.example, with no secret, is committed. |
| NFR3 | Privacy | Only the short findings text (counts, statuses, percentages) goes to the AI. Raw tables and server names are never sent. |
| NFR4 | Reliability | If the AI call fails or times out, the report is still created with fallback text. |
| NFR5 | Performance | One full run on the sample data finishes in under 30 seconds (excluding the AI wait time). |
| NFR6 | Usability | The report is readable on one to two pages. A CRITICAL item is easy to see at a glance. |
| NFR7 | Maintainability | One module = one job. Thresholds live in config.yaml. Functions have short names and comments. |
| NFR8 | Portability | The project can be rebuilt from the README steps on a new computer. |
| NFR9 | Testability | The rules logic can be tested without internet or the AI. |

### 2.3 User requirements

| User | Expectation |
|------|-------------|
| Database administrator (main user) | Open one report each morning and see in under two minutes what needs attention. Wants clear OK / WARNING / CRITICAL labels, the reason for each warning, and a storage trend. |
| IT team lead or manager | Wants a short, plain-English summary without technical detail, and a PDF that can be sent or printed. |
| Developer / reviewer | Wants a simple setup (README), a clean folder structure, and tests that show the rules work. |

## 3. Feature and module breakdown

### 3.1 Features

| Feature | Purpose | Input | Processing | Output |
|---------|---------|-------|------------|--------|
| F1 Data collection and cleaning | Get reliable data to work with | data/backup.csv, tablespace.csv, sessions.csv, error_log.csv | Read with pandas, fix types and dates, drop bad rows, validate columns | Four clean tables |
| F2 Rule-based health check | Find problems automatically | Clean tables + thresholds | Compare each value with the WARNING and CRITICAL limits | Findings table (item, value, status, reason) |
| F3 Configurable thresholds | Change limits without coding | config/config.yaml | Load YAML into a settings dictionary | Settings used by the rules |
| F4 History and 7-day trend | Show change over time | Today's findings | Insert into SQLite (one row per day), query the last 7 days | History table and 7-day data |
| F5 Storage trend chart | Make the trend easy to see | 7-day storage data | Draw a line chart with matplotlib | PNG chart image |
| F6 AI summary | Explain results in simple words | Findings text (no raw data) | Send a short prompt to Gemini; on failure use fallback text | 3 to 5 line summary |
| F7 Report generation | Give one finished document | Findings, chart, summary | Fill the Jinja2 template, then convert HTML to PDF | report_DATE.html and .pdf |
| F8 Pipeline and error handling | Run everything automatically | Command: python main.py | Run modules in order, log steps, catch and explain errors | Finished report + clear console messages |
| F9 Automated tests | Prove the rules are correct | Small test values | pytest checks for OK, WARNING, CRITICAL and bad input | Pass / fail result |

### 3.2 Modules and dependencies

| Module | Responsibility | Features | Depends on |
|--------|----------------|----------|------------|
| collector (src/collector.py) | Read and clean the four tables | F1 | data/ folder only |
| rules (src/rules.py) | Mark each item OK / WARNING / CRITICAL | F2, F3 | collector output, config.yaml |
| history (src/history.py) | Save daily results in SQLite, return 7-day trend | F4 | rules output |
| charts (src/charts.py) | Draw the storage trend chart | F5 | history output |
| ai_summary (src/ai_summary.py) | Write the summary with Gemini, with fallback text | F6 | rules output, .env (API key) |
| report (src/report.py) | Build the HTML and PDF report | F7 | rules, charts, ai_summary, template |
| main (main.py) | Run all steps in order and handle errors | F8 | all other modules |
| tests (tests/) | Test the rules and the cleaning | F9 | rules, collector |

Dependency flow: collector, then rules; rules feeds history, ai_summary and report; history feeds charts; charts and ai_summary feed report; main runs them all.

## 4. Feature prioritization

| Priority | Features | Why |
|----------|----------|-----|
| **Must Have** | F1 Data collection and cleaning; F2 Rule-based health check; F3 Configurable thresholds; F6 AI summary (with fallback text); F7 Report generation (HTML first); F8 Pipeline run with main.py and error messages | Without these there is no report, and without F6 the project is not an AI & Automation project. The fallback text keeps the report working if the AI is down. |
| **Should Have** | F4 History and 7-day trend; F5 Storage trend chart; PDF export; F9 Tests for rules; Daily run with Windows Task Scheduler | These make the report much more useful and the project more professional, but a basic report still works without them. |
| **Could Have** | Email the report automatically; Telegram or Teams alert for CRITICAL items; Live Oracle connection instead of CSV files; Simple web page to view past reports; More checks (invalid objects, long-running jobs) | Nice extras, only if the Must and Should items are finished and time is left. |

## 5. Development task list

Each task is small enough for one session of 30 to 60 minutes and can be tested on its own. Tasks are in build order.

**1. collector (Must)**
1. Write a function that reads one CSV file safely
2. Check that the required columns exist
3. Fix data types and dates, remove empty rows
4. Return the four clean tables and test with sample data

**2. rules + config (Must)**
1. Create config.yaml with WARNING and CRITICAL limits
2. Write a loader for config.yaml
3. Write rule functions for backup, tablespace, sessions and error log
4. Combine results into one findings table with a reason for each
5. Write tests in tests/test_rules.py (OK, WARNING, CRITICAL, bad input)

**3. history (Should)**
1. Create the SQLite table
2. Save today's result (replace if run twice in one day)
3. Return the last 7 days
4. Test with fake dates

**4. charts (Should)**
1. Draw the storage line chart from 7-day data
2. Add title, labels and a threshold line
3. Save as PNG in output/

**5. ai_summary (Must)**
1. Store the API key in .env and load it
2. Write the prompt (findings text only)
3. Call Gemini and read the answer
4. Add timeout and fallback text
5. Test with the key missing

**6. report (Must for HTML, Should for PDF)**
1. Design report.html.j2 (header, findings table, chart, summary)
2. Fill the template with real data
3. Colour the OK / WARNING / CRITICAL rows
4. Export to PDF
5. Check the file names report_DATE.html and .pdf

**7. main (Must)**
1. Call all modules in order
2. Add simple logging for each step
3. Show clear error messages
4. Test the full run from a clean clone of the repository

**8. Automation and finish (Should)**
1. Schedule the daily run with Windows Task Scheduler
2. Update the README with final screenshots
3. Record a short demo and final notes
