-- ============================================================
-- CMS Medicare Part B Claims  Cross-Country Fraud Detection
--
-- Schema mirrors the CMS Medicare Physician & Other Practitioners
-- by Provider and Service PUF available at:
--   https://data.cms.gov/provider-summary-by-type-of-service/
--   medicare-physician-other-practitioners/
--   medicare-physician-other-practitioners-by-provider-and-service
--
-- To load the real CMS dataset:
--   1. Download the CSV from the link above
--   2. Run:  sqlite3 data/claims.db
--            .mode csv
--            .import data/Medicare_Physician_Other_Practitioners_by_Provider_2022.csv cms_claims
--   3. Adjust column aliases in queries if needed (CMS uses same names)
-- ============================================================

CREATE TABLE IF NOT EXISTS cms_claims (
    clm_id                      TEXT PRIMARY KEY,
    rndrng_npi                  TEXT    NOT NULL,   -- 10-digit National Provider Identifier
    rndrng_prvdr_last_org_name  TEXT,
    rndrng_prvdr_first_name     TEXT,
    rndrng_prvdr_crdntls        TEXT,               -- MD, DO, NP, PA ...
    rndrng_prvdr_type           TEXT,               -- Internal Medicine, Cardiology ...
    rndrng_prvdr_state_abrvtn   TEXT,               -- US state (blank if foreign)
    rndrng_prvdr_cntry          TEXT    NOT NULL,   -- US or ISO country code
    hcpcs_cd                    TEXT    NOT NULL,   -- procedure code
    hcpcs_desc                  TEXT,
    place_of_srvc               TEXT,               -- O=office, F=facility
    clm_from_dt                 DATE    NOT NULL,
    clm_thru_dt                 DATE    NOT NULL,
    avg_sbmtd_chrg              REAL,               -- avg submitted charge
    avg_mdcr_alowd_amt          REAL,               -- avg Medicare allowed amount
    avg_mdcr_pymt_amt           REAL                -- avg Medicare payment amount
);

CREATE INDEX IF NOT EXISTS idx_npi    ON cms_claims (rndrng_npi);
CREATE INDEX IF NOT EXISTS idx_cntry  ON cms_claims (rndrng_prvdr_cntry);
CREATE INDEX IF NOT EXISTS idx_dates  ON cms_claims (clm_from_dt, clm_thru_dt);
