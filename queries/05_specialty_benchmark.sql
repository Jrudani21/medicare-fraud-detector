-- ============================================================
-- Query 5: Benchmark foreign-billed payments vs US peers
--          by provider specialty and HCPCS code.
--
-- Significant deviation from specialty average is a red flag.
-- ============================================================

WITH us_benchmarks AS (
    SELECT
        rndrng_prvdr_type       AS specialty,
        hcpcs_cd,
        hcpcs_desc,
        COUNT(*)                AS us_claim_count,
        ROUND(AVG(avg_mdcr_pymt_amt), 2)  AS us_avg_payment,
        ROUND(AVG(avg_sbmtd_chrg), 2)     AS us_avg_submitted
    FROM cms_claims
    WHERE rndrng_prvdr_cntry = 'US'
    GROUP BY rndrng_prvdr_type, hcpcs_cd, hcpcs_desc
),

foreign_claims AS (
    SELECT
        c.rndrng_npi,
        c.rndrng_prvdr_last_org_name        AS provider_name,
        c.rndrng_prvdr_type                 AS specialty,
        c.rndrng_prvdr_cntry                AS country,
        c.hcpcs_cd,
        c.hcpcs_desc,
        c.avg_mdcr_pymt_amt                 AS foreign_payment,
        c.avg_sbmtd_chrg                    AS foreign_submitted
    FROM cms_claims c
    WHERE c.rndrng_prvdr_cntry != 'US'
      -- Only look at NPIs that also have US claims (the overlap fraud pattern)
      AND EXISTS (
          SELECT 1 FROM cms_claims us
          WHERE us.rndrng_npi = c.rndrng_npi
            AND us.rndrng_prvdr_cntry = 'US'
      )
)

SELECT
    f.rndrng_npi,
    f.provider_name,
    f.specialty,
    f.country                              AS billing_country,
    f.hcpcs_cd,
    f.hcpcs_desc,
    f.foreign_payment,
    b.us_avg_payment,
    ROUND(f.foreign_payment - b.us_avg_payment, 2)          AS payment_deviation,
    ROUND(f.foreign_payment / NULLIF(b.us_avg_payment,0), 2) AS payment_ratio,
    CASE
        WHEN f.foreign_payment > b.us_avg_payment * 2 THEN 'INFLATED'
        WHEN f.foreign_payment < b.us_avg_payment * 0.5 THEN 'DEFLATED'
        ELSE 'NORMAL'
    END AS deviation_flag
FROM foreign_claims f
LEFT JOIN us_benchmarks b
    ON f.specialty = b.specialty AND f.hcpcs_cd = b.hcpcs_cd
WHERE b.us_avg_payment IS NOT NULL
ORDER BY ABS(f.foreign_payment - b.us_avg_payment) DESC;
