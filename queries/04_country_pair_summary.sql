-- ============================================================
-- Query 4: Which foreign countries appear most in fraud pairs?
--          Useful for OIG investigator prioritisation.
-- ============================================================

WITH overlapping_pairs AS (
    SELECT
        b.rndrng_prvdr_cntry                                       AS foreign_country,
        a.rndrng_prvdr_state_abrvtn                                AS us_state,
        a.rndrng_npi,
        a.avg_mdcr_pymt_amt + b.avg_mdcr_pymt_amt                 AS pair_payment,
        ROUND(b.avg_sbmtd_chrg / NULLIF(b.avg_mdcr_alowd_amt,0),2) AS charge_ratio,
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
)

SELECT
    foreign_country,
    COUNT(DISTINCT rndrng_npi)          AS flagged_providers,
    COUNT(*)                            AS overlap_instances,
    ROUND(SUM(pair_payment), 2)         AS total_at_risk_usd,
    ROUND(AVG(overlap_days), 1)         AS avg_overlap_days,
    ROUND(AVG(charge_ratio), 2)         AS avg_charge_ratio
FROM overlapping_pairs
GROUP BY foreign_country
ORDER BY flagged_providers DESC;
