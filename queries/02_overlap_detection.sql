-- ============================================================
-- Query 2: Detect providers billing from 2+ countries
--          with overlapping claim date windows
--
-- Fraud pattern (documented CMS OIG scheme):
--   The same NPI appears billing from a US address AND a foreign
--   country address during the same date window — physically
--   impossible, indicating phantom/fabricated foreign billing.
--
-- Date overlap: A.clm_from_dt <= B.clm_thru_dt
--           AND B.clm_from_dt <= A.clm_thru_dt
-- ============================================================

SELECT
    a.rndrng_npi,
    a.rndrng_prvdr_last_org_name                         AS provider_name,
    a.rndrng_prvdr_type                                  AS specialty,
    a.rndrng_prvdr_crdntls                               AS credentials,

    -- US-side claim
    a.clm_id                                             AS us_claim_id,
    a.rndrng_prvdr_state_abrvtn                          AS us_state,
    a.hcpcs_cd                                           AS us_hcpcs,
    a.hcpcs_desc                                         AS us_procedure,
    a.clm_from_dt                                        AS us_clm_from,
    a.clm_thru_dt                                        AS us_clm_thru,
    a.avg_mdcr_pymt_amt                                  AS us_payment,

    -- Foreign-side claim
    b.clm_id                                             AS foreign_claim_id,
    b.rndrng_prvdr_cntry                                 AS foreign_country,
    b.hcpcs_cd                                           AS foreign_hcpcs,
    b.hcpcs_desc                                         AS foreign_procedure,
    b.clm_from_dt                                        AS foreign_clm_from,
    b.clm_thru_dt                                        AS foreign_clm_thru,
    b.avg_mdcr_pymt_amt                                  AS foreign_payment,
    b.avg_sbmtd_chrg                                     AS foreign_submitted_charge,

    -- Overlap window in days
    (
        MIN(a.clm_thru_dt, b.clm_thru_dt) -
        MAX(a.clm_from_dt, b.clm_from_dt)
    )                                                    AS overlap_days,

    -- Charge inflation: submitted vs allowed (red flag if >> 3x)
    ROUND(b.avg_sbmtd_chrg / NULLIF(b.avg_mdcr_alowd_amt, 0), 2) AS foreign_charge_ratio

FROM cms_claims AS a
JOIN cms_claims AS b
    ON  a.rndrng_npi        = b.rndrng_npi          -- same provider NPI
    AND a.clm_id            < b.clm_id              -- avoid duplicate pairs
    AND a.rndrng_prvdr_cntry = 'US'                 -- one side must be US
    AND b.rndrng_prvdr_cntry != 'US'                -- other side is foreign
    AND a.clm_from_dt       <= b.clm_thru_dt        -- date overlap
    AND b.clm_from_dt       <= a.clm_thru_dt        -- date overlap

ORDER BY overlap_days DESC, foreign_charge_ratio DESC;
