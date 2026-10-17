# ARCHITECTURE - medicare-fraud-detector

## Overview
The application detects Medicare fraud by identifying providers billing from both US and foreign countries with overlapping date windows. It consists of four layers: data, query, application, and synthetic data generation.

## Data Layer
- SQLite database (`data/claims.db`) containing a single table `cms_claims` that mirrors the CMS Medicare Physician & Other Practitioners by Provider and Service PUF.
- The table is loaded from a CSV file (`data/claims.csv`) using the schema defined in `queries/01_schema.sql`.
- Indexes on `rndrng_npi`, `rndrng_prvdr_cntry`, and (`clm_from_dt`, `clm_thru_dt`) for query performance.

## Query Layer
- Five predefined SQL queries in the `queries/` directory:
  1. `01_schema.sql`: Table creation and indexes.
  2. `02_overlap_detection.sql`: Self-join to find NPIs with overlapping US and foreign claim windows.
  3. `03_risk_scoring.sql`: Computes risk scores (HIGH/MEDIUM/LOW) for flagged providers.
  4. `04_country_pair_summary.sql`: Aggregates fraud metrics by foreign country.
  5. `05_specialty_benchmark.sql`: Compares foreign payments to US specialty benchmarks.
- Queries are static files read and executed by the application.

## Application Layer
- Streamlit dashboard (`app.py`) that:
  - Loads the SQLite connection and caches it.
  - Reads and executes each query, caching the results.
  - Loads the raw claims data for timelines.
  - Applies sidebar filters (risk level, specialty, minimum overlap days) to the risk and pairs dataframes.
  - Displays results across five tabs using Plotly Express and dataframes.
  - Uses custom CSS for risk-level coloring and metric styling.

## Synthetic Data Generation
- Script `data/generate.py` creates a synthetic dataset matching CMS structure and column names.
- Generates 9,976 claims across 2,000 NPIs with a known fraud pattern (18 flagged providers).
- Used for development and testing when real CMS data is not available.

## Data Flow
1. CSV → SQLite (via import) → SQL queries → DataFrames → Streamlit UI.
2. Filters are applied post-query in Python (pandas) for interactivity.
3. No external APIs or services; all processing is local.

## Verified against
- app.py
- data/generate.py
- queries/01_schema.sql
- queries/02_overlap_detection.sql
- queries/03_risk_scoring.sql
- queries/04_country_pair_summary.sql
- queries/05_specialty_benchmark.sql