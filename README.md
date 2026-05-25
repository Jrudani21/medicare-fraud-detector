# 🏥 Catching Phantom Billers: Medicare Cross-Country Fraud Detection

> **Can SQL alone identify providers submitting Medicare claims from two countries at the same time?**  
> Overlap detection, risk scoring, and charge benchmarking across 9,976 synthetic CMS claims — with a live Streamlit dashboard.

![Dashboard](figures/dashboard_preview.png)

---

## 📋 Table of Contents
- [Problem](#problem)
- [Data](#data)
- [Methods](#methods)
- [Key Results](#key-results)
- [Business Insights](#business-insights)
- [How to Reproduce](#how-to-reproduce)
- [What I'd Do Next](#what-id-do-next)

---

## Problem

Medicare fraud costs the US government an estimated **$60 billion per year**. One documented scheme — investigated by the CMS Office of Inspector General (OIG) — involves providers billing from a US address and a foreign country during overlapping date windows. A provider cannot physically be in two countries at the same time.

This project detects that pattern by:

1. Identifying NPIs with overlapping US and foreign claim windows (phantom billing signal)
2. Scoring every flagged provider by severity — pairs, overlap days, charge ratio, payment volume
3. Benchmarking foreign charges against US specialty averages for the same procedure codes
4. Surfacing findings in an interactive 5-tab Streamlit dashboard

---

## Data

| Property | Detail |
|---|---|
| **Source** | CMS Medicare Physician & Other Practitioners by Provider and Service (PUF) |
| **Real data URL** | [data.cms.gov](https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider-and-service) |
| **Included dataset** | Synthetic — 9,976 claims, 2,000 NPIs (`data/claims.csv`) |
| **Generator** | `data/generate.py` — real HCPCS codes, NPI format, CMS-benchmarked payment amounts |
| **Storage** | SQLite (`data/claims.db`) |

### Key Variables

| Column | Type | Description |
|---|---|---|
| `rndrng_npi` | text | National Provider Identifier |
| `rndrng_prvdr_cntry` | text | Country of provider address |
| `rndrng_prvdr_state_abrvtn` | text | US state (when domestic) |
| `hcpcs_cd` | text | Procedure code billed |
| `avg_mdcr_pymt_amt` | numeric | Average Medicare payment ($) |
| `avg_sbmtd_chrg` | numeric | Average submitted charge ($) |
| `rndrng_prvdr_type` | text | Provider specialty |

> The schema in `queries/01_schema.sql` mirrors exact CMS PUF column names — swap in the real CSV to run on live data with no code changes.

---

## Methods

### SQL Pipeline (`queries/`)

| File | What It Does |
|---|---|
| `01_schema.sql` | Create `cms_claims` table with CMS column names and indexes |
| `02_overlap_detection.sql` | Self-join to find NPIs with overlapping US + foreign claim date windows |
| `03_risk_scoring.sql` | Score each flagged provider: overlap pairs, overlap days, charge ratio, payment volume → HIGH / MEDIUM / LOW |
| `04_country_pair_summary.sql` | Aggregate fraud signals by foreign country |
| `05_specialty_benchmark.sql` | Compare foreign payments to US average for same HCPCS + specialty |

**Core fraud query logic (`02_overlap_detection.sql`)**

```sql
-- Self-join: same NPI, one US claim, one foreign claim, overlapping dates
SELECT a.rndrng_npi, a.rndrng_prvdr_cntry AS us_country,
       b.rndrng_prvdr_cntry AS foreign_country, ...
FROM cms_claims a
JOIN cms_claims b ON a.rndrng_npi = b.rndrng_npi
WHERE a.rndrng_prvdr_cntry = 'US'
  AND b.rndrng_prvdr_cntry != 'US'
  AND a.date_range overlaps b.date_range
```

### Streamlit Dashboard (`app.py`)

| Tab | Content |
|---|---|
| 🌍 Foreign Country Risk | Bar charts — flagged providers and charge inflation by country |
| 👤 Flagged Providers | Filterable NPI-level risk table with score and risk level |
| 📋 Claim Pairs | Overlapping US ↔ foreign claim pairs with per-NPI timeline |
| 📊 Charge Benchmarks | Foreign payments vs US specialty benchmark — flags inflated claims |
| 📈 Risk Distribution | Pie + histogram + specialty breakdown |

---

## Key Results

### Fraud Detection Summary (Synthetic Data)

| Metric | Result |
|---|---|
| **Providers flagged** | 18 out of 2,000 NPIs (0.9%) |
| **Suspicious Medicare payments** | $46,000+ |
| **Highest-risk countries** | Mexico, India, Philippines |
| **Max charge inflation** | 5–6× the allowed Medicare amount |
| **Benchmark threshold** | Foreign claims ≥ 2× US specialty average flagged |

### Risk Score Distribution

| Risk Level | Criteria |
|---|---|
| **HIGH** | Multiple overlap pairs + high payment volume + charge ratio > 3× |
| **MEDIUM** | At least one overlap pair + moderate charge inflation |
| **LOW** | Single overlap, low payment, minimal charge difference |

### Top Foreign Countries by Charge Inflation

| Country | Avg Charge Ratio (Foreign / US) |
|---|---|
| Mexico | ~5.8× |
| India | ~5.2× |
| Philippines | ~4.9× |

---

## Business Insights

| Finding | Implication |
|---|---|
| Overlap detection requires only a self-join | No ML needed — pure SQL is interpretable and auditable |
| Charge inflation varies by country | Country-level benchmarks help prioritise investigations |
| Specialty matters for benchmarking | A neurosurgeon and a GP billing the same HCPCS code have different US baselines |
| Risk scoring enables triage | Investigators can sort by HIGH risk and work down — no manual filtering |
| Schema mirrors real CMS PUF | Swap synthetic CSV for real data — zero code changes needed |

---

## How to Reproduce

### Setup
```bash
pip install -r requirements.txt
```

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

### Launch the dashboard
```bash
streamlit run app.py
```

### Use real CMS data
1. Download the CMS PUF CSV from [data.cms.gov](https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider-and-service)
2. Replace `data/claims.csv` with the real file
3. Re-run the SQLite import — all queries and visualisations work unchanged

---

## What I'd Do Next
- Add **date parsing** to the synthetic generator to enable true temporal overlap detection across multi-year CMS data
- Layer in a **logistic regression or random forest** classifier trained on the SQL-derived risk features
- Connect to **real CMS PUF data** and validate flagged NPIs against published OIG exclusion lists
- Add a **geospatial tab** mapping flagged providers by country and US state
- Export flagged NPIs as a **PDF investigation report** directly from the dashboard

---

*Fraud pattern documented in: CMS Office of Inspector General enforcement reports. Data structure: CMS Medicare Physician & Other Practitioners PUF.*
