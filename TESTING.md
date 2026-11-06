# TESTING - medicare-fraud-detector

## Overview
`python tests/check.py` runs the SQL pipeline against `data/claims.db` and asserts that the database matches the CSV, that overlap days are real day counts, that the overlap rule flags exactly the planted providers, and that the peer-outlier screen keeps its precision. The older notes below predate it.

## Test Files
- No files matching `test*.py`, `*_test.py`, or similar patterns were found.
- No `tests/` directory or test-related configuration (e.g., `pytest.ini`, `tox.ini`, `conftest.py`) exists.

## Test Commands
- The README does not include any test commands (e.g., `pytest`, `python -m unittest`).
- The `requirements.txt` lists only runtime dependencies (streamlit, pandas, plotly); no test dependencies are present.
- No scripts in the repository are intended for testing (e.g., no `run_tests.sh`, `test.py`, or Makefile test targets).

## What Was Not Run
Since no test commands or test files exist, no tests were run. The project is verified by manual inspection of the code and by reading the documentation and SQL queries.

## Verification Approach
The correctness of the project was assessed by:
1. Reading the source code (`app.py`, `data/generate.py`).
2. Reviewing the SQL queries in the `queries/` directory.
3. Checking the README for usage instructions.
4. Confirming the presence of the synthetic data and database schema.

No dynamic execution (e.g., running the app, importing data, executing queries) was performed as part of this documentation task, per the instructions to avoid running code.

## Verified against
- app.py
- data/generate.py
- queries/01_schema.sql
- queries/02_overlap_detection.sql
- queries/03_risk_scoring.sql
- queries/04_country_pair_summary.sql
- queries/05_specialty_benchmark.sql
- README.md
- requirements.txt