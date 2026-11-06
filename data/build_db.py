"""Rebuild data/claims.db from data/claims.csv with the schema in queries/01_schema.sql.

Run from the repo root:  python data/build_db.py
Keeps the SQLite file in step with the CSV (the two had drifted apart).
"""
import csv, os, sqlite3

DB, CSV = "data/claims.db", "data/claims.csv"
if os.path.exists(DB):
    os.remove(DB)
db = sqlite3.connect(DB)
db.executescript(open("queries/01_schema.sql", encoding="utf-8").read())
rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
cols = list(rows[0])
db.executemany(f"INSERT INTO cms_claims({','.join(cols)}) VALUES({','.join('?' * len(cols))})",
               [[r[c] for c in cols] for r in rows])
db.commit()
print(f"Loaded {len(rows):,} claims into {DB}")
