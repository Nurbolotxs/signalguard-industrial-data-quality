# 📡 SignalGuard — Industrial Data Quality Monitoring

An interactive **industrial telemetry data-quality system** built with **Python, SQL, SQLite, Streamlit, Plotly, and pytest**. Designed as a portfolio project for Data Quality / Data Engineering internships.

## Features
- Generates **12,000 reproducible synthetic telemetry records** from 30 sensors at three plants
- SQL-based checks for **nulls, out-of-range readings, unknown sensors, duplicate event IDs, and future timestamps**
- Interactive dark-mode dashboard with **quality KPIs, rule breakdown, pass/fail donut, daily trend, plant comparison, and flagged-record explorer**
- Filter and download flagged records as CSV
- Export JSON quality report and flagged CSV from CLI
- **10 automated tests** and GitHub Actions CI
- SQL examples: **JOIN, GROUP BY, HAVING, CTE, window functions**

## Quick start (Windows PowerShell)
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m src.cli --rows 12000
python -m streamlit run app.py
```
Open the local URL shown in your terminal (usually http://localhost:8501).

## Quick start (macOS / Linux)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
python -m src.cli
python -m streamlit run app.py
```

## Architecture
```text
Synthetic sensor readings → SQLite tables → SQL validation rules
                                              ├── KPI dashboard
                                              ├── Interactive charts
                                              ├── Flagged-record explorer
                                              └── JSON + CSV reports
```

## Project structure
```text
app.py                     Streamlit / Plotly dashboard
src/core.py                Schema, deterministic generator, SQL quality rules
src/cli.py                 CLI + report export
sql/quality_checks.sql     Standalone SQL examples
tests/test_core.py         Automated regression tests
.github/workflows/tests.yml  CI
```

## Run tests
```bash
python -m pytest -q
```

## Important design notes
- **SQLite is used instead of PostgreSQL** so the entire project runs locally without a database server. SQL checks and schema are explicit and portable in concept, but some SQL syntax will need adaptation for PostgreSQL.
- A row can violate **multiple rules**. The overall invalid count counts each flagged row once; individual rule counts overlap.
- Unknown sensor IDs are intentionally retained to demonstrate referential-integrity checks; the schema does not enforce a foreign key on the raw ingestion table.
- The 'future timestamp' cutoff is a **fixed demo reference date** (2026-11-19), not the computer's current clock.
- Data is **synthetic**. No industrial data or real-time sensors are connected.
- Regenerating the demo dataset resets the local database.

## Suggested CV entry
**SignalGuard — Industrial Data Quality Monitoring | Python, SQL, SQLite, Streamlit, pytest**  
Built an interactive data-quality monitoring system for 12,000 synthetic sensor readings, implementing five SQL-based validation rules, automated tests, and visual dashboards for quality trends and anomaly investigation.


## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub (keep `app.py`, `requirements.txt`, and `src/` in the repository root).
2. Open [Streamlit Community Cloud](https://share.streamlit.io/), sign in with GitHub, and choose **Create app** / **Deploy an app**.
3. Select your repository, the `main` branch, and the entrypoint `app.py`.
4. In advanced settings, choose Python **3.13** if available, then deploy.
5. The first visitor automatically initializes a synthetic SQLite demo database in the system temporary directory. No database credentials or external services are needed.

**Demo limitations:** The SQLite database is ephemeral on hosted environments; it can reset when the instance restarts. Regenerate resets it to the deterministic demo data. This app is a portfolio demonstration, not persistent production monitoring.
