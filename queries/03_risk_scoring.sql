-- ============================================================
-- Query 3: Risk-score every flagged provider NPI
--
-- Score components (additive):
--   +3  per overlapping country pair
--   +1  per overlap day (capped at 15)
--   +2  if foreign charge ratio > 5x (extreme charge inflation)
--   +2  if total suspicious Medicare payments > $10,000
--   +3  if provider appears in 3+ distinct countries
-- ============================================================

WITH overlapping_pairs AS (
    SELECT
        a.rndrng_npi,
        a.rndrng_prvdr_last_org_name                               AS provider_name,
        a.rndrng_prvdr_type                                        AS specialty,
        a.rndrng_prvdr_crdntls                                     AS credentials,
        a.rndrng_prvdr_state_abrvtn                                AS us_state,
        b.rndrng_prvdr_cntry                                       AS foreign_country,
        a.avg_mdcr_pymt_amt + b.avg_mdcr_pymt_amt                 AS pair_payment,
        ROUND(b.avg_sbmtd_chrg / NULLIF(b.avg_mdcr_alowd_amt,0), 2) AS charge_ratio,
        (MIN(a.clm_thru_dt, b.clm_thru_dt) -
         MAX(a.clm_from_dt, b.clm_from_dt))                       AS overlap_days
    FROM cms_claims a
    JOIN cms_claims b
        ON  a.rndrng_npi         = b.rndrng_npi
        AND a.clm_id             < b.clm_id
        AND a.rndrng_prvdr_cntry = 'US'
        AND b.rndrng_prvdr_cntry != 'US'
        AND a.clm_from_dt        <= b.clm_thru_dt
        AND b.clm_from_dt        <= a.clm_thru_dt
),

country_counts AS (
    SELECT rndrng_npi,
           COUNT(DISTINCT rndrng_prvdr_cntry) AS distinct_countries
    FROM cms_claims
    GROUP BY rndrng_npi
),

scored AS (
    SELECT
        p.rndrng_npi,
        p.provider_name,
        p.specialty,
        p.credentials,
        p.us_state,
        COUNT(*)                                        AS flagged_pairs,
        COUNT(DISTINCT p.foreign_country)               AS foreign_countries,
        ROUND(SUM(p.pair_payment), 2)                   AS total_suspicious_payment,
        ROUND(MAX(p.charge_ratio), 2)                   AS max_charge_ratio,
        SUM(MIN(p.overlap_days, 15))                    AS total_overlap_days,
        -- Score calculation
        COUNT(*) * 3
        + SUM(MIN(p.overlap_days, 15))
        + CASE WHEN MAX(p.charge_ratio) > 5.0   THEN 2 ELSE 0 END
        + CASE WHEN SUM(p.pair_payment) > 10000 THEN 2 ELSE 0 END
        + CASE WHEN cc.distinct_countries >= 3   THEN 3 ELSE 0 END  AS risk_score
    FROM overlapping_pairs p
    JOIN country_counts cc ON p.rndrng_npi = cc.rndrng_npi
    GROUP BY p.rndrng_npi, p.provider_name, p.specialty, p.credentials, p.us_state
)

SELECT
    rndrng_npi,
    provider_name,
    specialty,
    credentials,
    us_state,
    flagged_pairs,
    foreign_countries,
    total_suspicious_payment,
    max_charge_ratio,
    total_overlap_days,
    risk_score,
    CASE
        WHEN risk_score >= 12 THEN 'HIGH'
        WHEN risk_score >= 6  THEN 'MEDIUM'
        ELSE                       'LOW'
    END AS risk_level
FROM scored
ORDER BY risk_score DESC;
