# Copyright (c) 2026 Janak Rudani. All rights reserved.
# Provenance: Jrudani21/medicare-fraud-detector/tests/check.py 2ae43708b8bc36a0
"""Runnable checks for the SQL pipeline. Run from the repo root:  python tests/check.py

Prints the detection numbers the README quotes and asserts the invariants behind them.
Needs data/claims.csv, data/claims.db and data/labels.csv (see data/generate.py, data/build_db.py).
"""
import csv, sqlite3

db = sqlite3.connect("data/claims.db")
sql = lambda n: open(f"queries/{n}.sql", encoding="utf-8").read()
labels = {r["rndrng_npi"]: int(r["planted_fraud"]) for r in csv.DictReader(open("data/labels.csv"))}
planted = {n for n, v in labels.items() if v}

# 1. database and CSV agree (they had drifted apart once)
n_csv = sum(1 for _ in open("data/claims.csv", encoding="utf-8")) - 1
n_db = db.execute("SELECT COUNT(*) FROM cms_claims").fetchone()[0]
assert n_db == n_csv, f"claims.db has {n_db} rows, claims.csv has {n_csv}: run python data/build_db.py"

# 2. overlap days are real day counts (ISO date strings were being subtracted as numbers)
pairs = db.execute(sql("02_overlap_detection")).fetchall()
cols = [d[0] for d in db.execute(sql("02_overlap_detection")).description]
od = [r[cols.index("overlap_days")] for r in pairs]
assert max(od) > 1 and min(od) >= 0, "overlap_days looks like a year difference again"

# 3. risk scoring
risk = db.execute(sql("03_risk_scoring")).fetchall()  # npi, ..., payment(7), ..., score(10), level(11)
flagged = {r[0] for r in risk}
assert flagged == planted, "the overlap rule should flag exactly the planted providers on synthetic data"
level = lambda x: sum(1 for r in risk if r[11] == x)
dollars = sum(r[7] for r in risk)

# 4. peer-outlier screen, evaluated against the planted labels
z = db.execute(sql("06_peer_outliers")).fetchall()  # npi, specialty, claims, mean_ratio, z
print(f"claims {n_db:,} | providers {len(labels):,} | planted fraud {len(planted)}")
print(f"overlap rule: {len(flagged)} flagged, HIGH {level('HIGH')}, MEDIUM {level('MEDIUM')}, LOW {level('LOW')}, ${dollars:,.0f} suspicious payments")
print("peer-outlier screen (charge-ratio z-score within specialty, no country or date rule):")
for cut in (1.0, 1.5, 2.0, 3.0):
    hit = {r[0] for r in z if r[4] >= cut}
    tp = len(hit & planted)
    print(f"  z >= {cut}: {len(hit):3d} flagged, precision {tp / max(len(hit), 1):.2f}, recall {tp / len(planted):.2f}")
hit = {r[0] for r in z if r[4] >= 2.0}
assert len(hit & planted) / len(hit) >= 0.9, "peer screen precision at z>=2 dropped below 0.9"
print("ok")
