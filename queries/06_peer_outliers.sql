-- Copyright (c) 2026 Janak Rudani. All rights reserved.
-- Provenance: Jrudani21/medicare-fraud-detector/queries/06_peer_outliers.sql d1743926497cdf3b
-- ============================================================
-- Query 6: Peer-outlier screen (no country or date rule needed)
--
-- Statistical outlier-first screening: compare each provider's
-- average charge ratio (submitted / allowed) with the other
-- providers of the same specialty, as a z-score. Investigators
-- then review the outliers, which is how state and federal
-- program-integrity units describe their first pass.
--
-- SQLite has no STDDEV, so variance = E[x^2] - E[x]^2.
-- ============================================================

WITH provider AS (
    SELECT
        rndrng_npi,
        rndrng_prvdr_type                                             AS specialty,
        COUNT(*)                                                      AS claims,
        AVG(avg_sbmtd_chrg / NULLIF(avg_mdcr_alowd_amt, 0))           AS mean_charge_ratio
    FROM cms_claims
    GROUP BY rndrng_npi, rndrng_prvdr_type
    HAVING COUNT(*) >= 2
),
peers AS (
    SELECT
        specialty,
        AVG(mean_charge_ratio)                                        AS mu,
        AVG(mean_charge_ratio * mean_charge_ratio)
          - AVG(mean_charge_ratio) * AVG(mean_charge_ratio)           AS var
    FROM provider
    GROUP BY specialty
)
SELECT
    p.rndrng_npi,
    p.specialty,
    p.claims,
    ROUND(p.mean_charge_ratio, 2)                                     AS mean_charge_ratio,
    ROUND((p.mean_charge_ratio - q.mu) / SQRT(q.var), 2)              AS z_score
FROM provider p
JOIN peers q USING (specialty)
ORDER BY z_score DESC;
