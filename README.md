# [🏥 Medicare Cross-Country Provider Fraud Detector](https://medicare-fraud-detector.streamlit.app/)

> **Can SQL alone identify providers billing Medicare from two countries at the same time?**  
> Overlap detection, risk scoring, and charge benchmarking across 9,936 synthetic CMS claims surfaced in a live Streamlit dashboard.

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

Medicare fraud costs the US government an estimated **$60 billion per year**. One documented scheme   investigated by the CMS Office of Inspector General (OIG)   involves providers submitting claims from a US address and a foreign country during **overlapping date windows**. A provider cannot physically be in two countries at the same time, making this a strong indicator of phantom billing.

This project detects that pattern end-to-end:

1. Flag every NPI with overlapping US and foreign billing windows (SQL self-join)
2. Score each flagged provider on severity   overlap pairs, overlap days, charge inflation, payment volume
3. Benchmark foreign charges against the US average for the same HCPCS code and specialty
4. Surface all findings in an interactive 5-tab Streamlit dashboard with Plotly charts

---

## Data

| Property | Detail |
|---|---|
| **Source** | [CMS Medicare Physician & Other Practitioners by Provider and Service (PUF)](https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider-and-service) |
| **Included dataset** | Synthetic   9,936 claims · 2,000 NPIs (`data/claims.csv`) |
| **Generator** | `data/generate.py`   real HCPCS codes, NPI format, CMS-benchmarked payment amounts |
| **Storage** | SQLite (`data/claims.db`) |
| **Drop-in compatible** | Schema mirrors exact CMS PUF column names   swap the real CSV and all queries run unchanged |

### Schema (`queries/01_schema.sql`)

| Column | Type | Description |
|---|---|---|
| `rndrng_npi` | TEXT | 10-digit National Provider Identifier |
| `rndrng_prvdr_cntry` | TEXT | Country of provider address (US or ISO code) |
| `rndrng_prvdr_state_abrvtn` | TEXT | US state (blank for foreign claims) |
| `rndrng_prvdr_type` | TEXT | Provider specialty |
| `hcpcs_cd` | TEXT | Procedure code billed |
| `clm_from_dt` / `clm_thru_dt` | DATE | Claim date window |
| `avg_sbmtd_chrg` | REAL | Average submitted charge ($) |
| `avg_mdcr_alowd_amt` | REAL | Average Medicare allowed amount ($) |
| `avg_mdcr_pymt_amt` | REAL | Average Medicare payment ($) |

---

## Methods

### SQL Pipeline (`queries/`)

| File | What It Does |
|---|---|
| `01_schema.sql` | Create `cms_claims` table with CMS PUF column names and indexes on NPI, country, and dates |
| `02_overlap_detection.sql` | Self-join on same NPI   one US claim, one foreign claim   with overlapping `clm_from_dt / clm_thru_dt` windows |
| `03_risk_scoring.sql` | Score every flagged NPI: +3 per pair · +1 per overlap day (cap 15) · +2 if charge ratio > 5× · +2 if payments > $10k · +3 if 3+ countries |
| `04_country_pair_summary.sql` | Aggregate fraud signals by foreign country   flagged providers, overlap instances, charge inflation, $ at risk |
| `05_specialty_benchmark.sql` | Compare foreign payments to the US average for the same HCPCS + specialty; flag anything ≥ 2× as INFLATED |
| `06_peer_outliers.sql` | Rule-free screen: z-score of each provider's average charge ratio against peers in the same specialty |

**Core fraud detection logic** (`02_overlap_detection.sql`):

```sql
SELECT a.rndrng_npi, a.rndrng_prvdr_last_org_name AS provider_name,
       b.rndrng_prvdr_cntry AS foreign_country,
       (MIN(a.clm_thru_dt, b.clm_thru_dt) -
        MAX(a.clm_from_dt, b.clm_from_dt)) AS overlap_days,
       ROUND(b.avg_sbmtd_chrg / NULLIF(b.avg_mdcr_alowd_amt, 0), 2) AS foreign_charge_ratio
FROM cms_claims AS a
JOIN cms_claims AS b
    ON  a.rndrng_npi         = b.rndrng_npi   -- same provider
    AND a.clm_id             < b.clm_id        -- avoid duplicate pairs
    AND a.rndrng_prvdr_cntry = 'US'            -- one side US
    AND b.rndrng_prvdr_cntry != 'US'           -- other side foreign
    AND a.clm_from_dt        <= b.clm_thru_dt  -- date overlap
    AND b.clm_from_dt        <= a.clm_thru_dt
ORDER BY overlap_days DESC, foreign_charge_ratio DESC;
```

**Risk score formula** (`03_risk_scoring.sql`):

```
Score = (pairs × 3)
      + MIN(total_overlap_days, 15)
      + 2  if max_charge_ratio > 5.0
      + 2  if total_suspicious_payment > $10,000
      + 3  if distinct_countries ≥ 3

HIGH   ≥ 12  →  OIG referral recommended
MEDIUM  6–11  →  Enhanced monitoring
LOW    < 6   →  Flag for review
```

### Streamlit Dashboard (`app.py`)

| Tab | Content |
|---|---|
| 🌍 **Foreign Country Risk** | Side-by-side bar charts   flagged providers and avg charge inflation ratio by country |
| 👤 **Flagged Providers** | Filterable NPI-level risk table   risk level, score, $ at risk, overlap days, foreign countries |
| 📋 **Claim Pairs** | Drill into overlapping US ↔ foreign claim pairs; Plotly timeline per NPI |
| 📊 **Charge Benchmarks** | INFLATED claims table   foreign payment vs US specialty average for same HCPCS |
| 📈 **Risk Distribution** | Pie chart by risk level · score histogram · suspicious $ at risk by specialty |

Sidebar filters: **Risk Level** · **Specialty** · **Min Overlap Days**

---

## Key Results

### Detection Summary (Synthetic Data)

| Metric | Result |
|---|---|
| Providers analysed | 2,000 NPIs |
| **Flagged as suspicious** | **200 NPIs (10%)**, every one a planted fraud provider |
| HIGH risk (OIG referral level) | 136 NPIs (MEDIUM 42, LOW 22) |
| **Total Medicare $ at risk** | **$854,792** across flagged providers |
| Highest charge inflation | 5–6× the Medicare allowed amount |
| Most inflated foreign countries | India · Nigeria · Ghana |

### Risk Score Breakdown

| Risk Level | Threshold | Action |
|---|---|---|
| **HIGH** | Score ≥ 12 | OIG referral recommended |
| **MEDIUM** | Score 6–11 | Enhanced monitoring |
| **LOW** | Score < 6 | Flag for review |

### Charge Benchmarking

Foreign claims billed at **≥ 2× the US specialty average** for the same HCPCS code are flagged as INFLATED. Top charge ratios by country (query 04):

| Country | Avg Charge Ratio (Submitted ÷ Allowed) |
|---|---|
| India | 5.55× |
| Nigeria | 5.54× |
| Ghana | 5.44× |

---

## Business Insights

| Finding | Implication |
|---|---|
| Date overlap is physically impossible | A single self-join produces high-precision fraud signals with no false positives by definition |
| Charge ratio amplifies signal | Foreign claims inflated > 5× alongside date overlap is a near-certain phantom billing indicator |
| Country-level aggregation enables triage | Investigators can prioritise by country, not NPI-by-NPI |
| Risk score enables ranked investigation | Sort HIGH → MEDIUM → LOW; allocate OIG resources accordingly |
| Schema mirrors real CMS PUF | Replace the synthetic CSV   zero query or dashboard changes needed |

---

## How to Reproduce

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Load data into SQLite
```bash
sqlite3 data/claims.db
.mode csv
.import data/claims.csv cms_claims
.quit
```

Or rebuild the database from the CSV in one step (keeps `claims.db` and `claims.csv` in sync):
```bash
python data/build_db.py
```

### 3. Run a query
```bash
sqlite3 data/claims.db < queries/02_overlap_detection.sql
```

### 3b. Run the checks
```bash
python tests/check.py
```

### 4. Launch the dashboard
```bash
streamlit run app.py
```

### 5. Use real CMS data (optional)
1. Download the PUF CSV from [data.cms.gov](https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider-and-service)
2. Replace `data/claims.csv` with the real file
3. Re-run the SQLite import   all 5 queries and the dashboard work unchanged

---

## Evaluation and corrections

The data generator also writes `data/labels.csv` (the planted fraud NPIs), so detection can be scored.
`tests/check.py` prints these numbers and asserts the invariants behind them.

| Detector | Flagged | Precision | Recall |
|---|---|---|---|
| Overlap rule (queries 02/03) | 200 | 1.00 | 1.00 |
| Peer-outlier screen, z ≥ 1.0 | 201 | 0.83 | 0.83 |
| Peer-outlier screen, z ≥ 2.0 | 107 | 0.99 | 0.53 |
| Peer-outlier screen, z ≥ 3.0 | 49 | 1.00 | 0.24 |

**Read this with care.** The overlap rule scores perfectly because the generator plants exactly that pattern, so
it is a test of the plumbing, not of real-world accuracy. The peer-outlier screen never looks at country or dates,
so its 0.83 / 0.83 at z ≥ 1 is the more honest signal that the charge-ratio feature carries information.

Corrections made when this was re-run:
- `overlap_days` was always 0. SQLite subtracted two ISO date strings as numbers, which compares only the year. It now uses `julianday()`, so the "+1 per overlap day" score term works.
- `claims.db` was older than `claims.csv` (9,976 claims against 9,936) and the dashboard reads the database. It is rebuilt with `data/build_db.py`.
- The headline numbers above (previously 18 flagged, 7 HIGH, $46,000+) came from that stale database and the broken overlap term, and are replaced.

## How the field approaches this

- **Outlier-first screening.** Program-integrity units describe a first pass that finds providers who are statistical outliers among their peers, then investigators gather evidence ([Texas HHSC OIG](https://oig.hhs.texas.gov/about-us/news/data-analytics-strengthens-oig-process)). Query 06 is a small version of that.
- **Impossible days.** Services adding up to more than 24 hours on one date of service are a standard red flag; this data has no units or times, so it is not testable here.
- **Supervised models need labels.** Published Part B work labels providers from the OIG exclusion list (LEIE) and handles extreme class imbalance by undersampling; Random Forest reached an AUC of 0.873 at a 90:10 class mix ([Part B study on PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851)). Excluded providers tend to be prosecuted for overt fraud, so those labels can miss subtler schemes.
- **Predictive analytics at CMS.** The Fraud Prevention System's savings were disputed: CMS reported a 5:1 return, while OIG's adjusted figure was $1.34 per dollar ([OIG, 2017](https://www.oversight.gov/sites/default/files/oig-reports/11500509.pdf)). Whatever the model, track outcomes.

## What I'd Do Next
- Add **temporal date parsing** to the synthetic generator to enable multi-year rolling-window overlap detection on real CMS annual releases
- Layer a **logistic regression or gradient boosting classifier** on top of the SQL-derived risk features (pairs, overlap days, charge ratio, peer z-score) and judge it by precision at the top 20 referrals; real labels would come from LEIE
- Validate flagged NPIs against the published **OIG exclusion list** and CMS preclusion list
- Add a **geospatial choropleth** mapping suspicious $ at risk by US state and foreign country
- Build a **PDF investigation report** export directly from the dashboard per flagged NPI

---

*Fraud pattern documented in CMS Office of Inspector General enforcement actions. Data: CMS Medicare Physician & Other Practitioners by Provider and Service (PUF).*
