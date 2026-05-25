#🌍 Medicare Cross-Country Provider Fraud Detector

Detects providers (NPIs) submitting Medicare claims from a **US address and a foreign country simultaneously** — a documented phantom billing scheme investigated by the CMS Office of Inspector General (OIG).

## Fraud Pattern

The same NPI appears in two billing records with **overlapping date windows** but different countries. A provider cannot physically be in two countries at the same time — overlapping cross-border billing is a strong indicator of fabricated foreign claims.

This pattern is documented in CMS OIG enforcement reports and is one of the primary signals used in Medicare fraud investigations.

## Data Source

**CMS Medicare Physician & Other Practitioners by Provider and Service (PUF)**  
https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider-and-service

The schema in `queries/01_schema.sql` uses exact CMS column names (`rndrng_npi`, `rndrng_prvdr_cntry`, `hcpcs_cd`, `avg_mdcr_pymt_amt`, etc.). Download the real CSV and load it to run this project on live data.

The included `data/claims.csv` is a **synthetic dataset** generated with `data/generate.py` using real HCPCS codes, NPI format, provider types, state codes, and CMS-benchmarked payment amounts.

## Project Structure

```
medicare-fraud-detector/
├── data/
│   ├── generate.py          # synthetic data generator (CMS structure)
│   ├── claims.csv           # generated dataset  (9,976 claims, 2,000 NPIs)
│   └── claims.db            # SQLite database
├── queries/
│   ├── 01_schema.sql        # table definition — mirrors CMS PUF columns
│   ├── 02_overlap_detection.sql   # core fraud query: overlapping cross-country billing
│   ├── 03_risk_scoring.sql        # risk score every flagged NPI (HIGH/MEDIUM/LOW)
│   ├── 04_country_pair_summary.sql # which foreign countries appear most
│   └── 05_specialty_benchmark.sql  # foreign charges vs US specialty peers
├── app.py                   # Streamlit dashboard (5 tabs)
└── requirements.txt
```

## SQL Queries

| File | What it does |
|------|-------------|
| `01_schema.sql` | Create `cms_claims` table with CMS column names and indexes |
| `02_overlap_detection.sql` | Self-join to find NPI pairs with overlapping US + foreign claim windows |
| `03_risk_scoring.sql` | Score each flagged provider: pairs, overlap days, charge ratio, payment volume |
| `04_country_pair_summary.sql` | Aggregate fraud signals by foreign country |
| `05_specialty_benchmark.sql` | Compare foreign payments to US average for same HCPCS + specialty |

### Load data into SQLite

```bash
sqlite3 data/claims.db
.mode csv
.import data/claims.csv cms_claims
.quit
```

### Run a query

```bash
sqlite3 data/claims.db < queries/02_overlap_detection.sql
```

## Streamlit Dashboard

5 tabs:

| Tab | Content |
|-----|---------|
| 🌍 Foreign Country Risk | Bar charts — flagged providers and charge inflation by country |
| 👤 Flagged Providers | Filterable NPI-level risk table with score and risk level |
| 📋 Claim Pairs | Drill into overlapping US ↔ foreign claim pairs; per-NPI timeline |
| 📊 Charge Benchmarks | Foreign payments vs US specialty benchmark — flags inflated claims |
| 📈 Risk Distribution | Pie + histogram + specialty breakdown |

### Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Key Findings (synthetic data)

- **18 flagged NPIs** out of 2,000 providers (0.9%)
- **$46,000+ Medicare payments** flagged as suspicious
- **Mexico, India, Philippines** show the highest charge inflation ratios (5–6× allowed amount)
- Query 5 identifies foreign claims billed at **2× or more** the US specialty average for the same HCPCS code

## To Use With Real CMS Data

1. Download the CMS PUF CSV from the link above
2. Replace `data/claims.csv` with the real file
3. Re-run the SQLite import
4. Launch the dashboard — all queries and visualisations work unchanged
