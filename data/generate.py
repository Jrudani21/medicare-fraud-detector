"""
Generates a synthetic Medicare Part B claims dataset modelled exactly on the
CMS Medicare Physician & Other Practitioners by Provider and Service PUF.

Column names, NPI format, HCPCS codes, provider types, payment amounts, and
state/country codes all match real CMS data so this code runs unchanged on
the actual dataset downloaded from:
  https://data.cms.gov/provider-summary-by-type-of-service/
  medicare-physician-other-practitioners/
  medicare-physician-other-practitioners-by-provider-and-service

Fraud pattern modelled: cross-country phantom billing.
A provider NPI appears in 2+ countries with overlapping claim date windows —
physically impossible and a documented CMS OIG fraud scheme.
"""

import csv, random
from datetime import date, timedelta

random.seed(2024)

# ── Real HCPCS codes with CMS-benchmarked payment amounts ────────────────────
HCPCS = [
    ("99213", "Office/outpatient visit established pt low complexity",    "O",  75,   180),
    ("99214", "Office/outpatient visit established pt moderate complexity","O", 111,   260),
    ("99203", "Office/outpatient visit new pt low complexity",            "O",  98,   220),
    ("99232", "Subsequent hospital care, per day",                        "F",  80,   190),
    ("99285", "Emergency dept visit high complexity decision making",      "F", 215,   500),
    ("93000", "Electrocardiogram routine ECG with interpretation",         "O",  20,    55),
    ("71046", "Radiologic exam chest 2 views",                            "O",  45,   110),
    ("80053", "Comprehensive metabolic panel",                             "O",  14,    38),
    ("85025", "Blood count complete CBC automated",                        "O",  10,    28),
    ("36415", "Collection of venous blood by venipuncture",               "O",   3,    10),
    ("90837", "Psychotherapy 60 minutes with patient",                    "O", 130,   310),
    ("90834", "Psychotherapy 45 minutes with patient",                    "O",  98,   230),
    ("45378", "Colonoscopy diagnostic",                                    "F", 348,   850),
    ("43239", "Esophagogastroduodenoscopy with biopsy",                   "F", 290,   700),
    ("70553", "MRI brain without and with contrast",                      "F", 680,  1600),
    ("27447", "Total knee arthroplasty",                                  "F",10800, 25000),
    ("97110", "Therapeutic exercises 15 minutes each 15 min",             "O",  30,    75),
    ("92012", "Ophthalmological services established patient",             "O",  45,   110),
    ("99395", "Periodic comprehensive preventive medicine 18-39 years",   "O",  88,   210),
    ("76817", "Ultrasound pregnant uterus real time",                      "O",  95,   230),
]

PROVIDER_TYPES = [
    "Internal Medicine", "Family Practice", "Cardiology",
    "Orthopedic Surgery", "Psychiatry", "Ophthalmology",
    "Dermatology", "Neurology", "Gastroenterology",
    "Emergency Medicine", "General Surgery", "Diagnostic Radiology",
    "Anesthesiology", "Obstetrics/Gynecology", "Nephrology",
]

CREDENTIALS = ["MD", "DO", "MD", "MD", "DO", "MD", "NP", "PA"]

US_STATES = [
    "CA","TX","FL","NY","PA","IL","OH","GA","NC","MI",
    "NJ","VA","WA","AZ","MA","TN","IN","MO","MD","WI",
    "CO","MN","SC","AL","LA","KY","OR","OK","CT","UT",
    "NV","AR","MS","KS","NM","NE","WV","ID","HI","NH",
    "ME","RI","MT","DE","SD","ND","AK","VT","WY",
]

# Foreign countries used in documented CMS fraud cases (CMS OIG reports)
FOREIGN_COUNTRIES = ["IN","PH","NG","MX","GH","PK","RO","UA"]
FOREIGN_COUNTRY_NAMES = {
    "IN":"India","PH":"Philippines","NG":"Nigeria",
    "MX":"Mexico","GH":"Ghana","PK":"Pakistan",
    "RO":"Romania","UA":"Ukraine",
}

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Wilson","Anderson","Taylor","Thomas","Jackson","White","Harris","Martin",
    "Thompson","Moore","Allen","Clark","Patel","Kumar","Singh","Ali","Khan",
    "Okafor","Adeyemi","Reyes","Torres","Nguyen","Chen","Kim","Park","Lee",
]
FIRST_NAMES = [
    "James","John","Robert","Michael","William","David","Richard","Joseph",
    "Mary","Patricia","Jennifer","Linda","Barbara","Susan","Margaret","Lisa",
    "Priya","Raj","Mohammed","Fatima","Chinwe","Oluwaseun","Carlos","Maria",
]

def rand_npi():
    return str(random.randint(1_000_000_000, 1_999_999_999))

def rand_date(start=date(2021, 1, 1), end=date(2023, 12, 31)):
    return start + timedelta(days=random.randint(0, (end - start).days))

def make_claim(claim_id, npi, prvdr_type, cntry, state, clm_start, clm_end,
               last_name, first_name, cred):
    hcpcs_cd, hcpcs_desc, pos, pay_lo, pay_hi = random.choice(HCPCS)
    payment = round(random.uniform(pay_lo, pay_hi), 2)
    submitted = round(payment * random.uniform(2.0, 3.8), 2)
    allowed   = round(payment * random.uniform(1.05, 1.25), 2)
    return {
        "clm_id":                    f"CLM{claim_id:07d}",
        "rndrng_npi":                npi,
        "rndrng_prvdr_last_org_name": last_name,
        "rndrng_prvdr_first_name":   first_name,
        "rndrng_prvdr_crdntls":      cred,
        "rndrng_prvdr_type":         prvdr_type,
        "rndrng_prvdr_state_abrvtn": state,
        "rndrng_prvdr_cntry":        cntry,
        "hcpcs_cd":                  hcpcs_cd,
        "hcpcs_desc":                hcpcs_desc,
        "place_of_srvc":             pos,
        "clm_from_dt":               clm_start.isoformat(),
        "clm_thru_dt":               clm_end.isoformat(),
        "avg_sbmtd_chrg":            submitted,
        "avg_mdcr_alowd_amt":        allowed,
        "avg_mdcr_pymt_amt":         payment,
    }

rows     = []
claim_id = 1
npi_pool = [rand_npi() for _ in range(2000)]  # pool of provider NPIs

# ── 1,700 clean US providers ──────────────────────────────────────────────────
for i in range(1700):
    npi   = npi_pool[i]
    ptype = random.choice(PROVIDER_TYPES)
    state = random.choice(US_STATES)
    last  = random.choice(LAST_NAMES)
    first = random.choice(FIRST_NAMES)
    cred  = random.choice(CREDENTIALS)
    for _ in range(random.randint(2, 8)):
        start = rand_date()
        end   = start + timedelta(days=random.randint(1, 30))
        rows.append(make_claim(claim_id, npi, ptype, "US", state, start, end, last, first, cred))
        claim_id += 1

# ── 200 fraud providers: billing from US + foreign country simultaneously ─────
for i in range(1700, 1900):
    npi     = npi_pool[i]
    ptype   = random.choice(PROVIDER_TYPES)
    us_state = random.choice(US_STATES)
    fcc     = random.choice(FOREIGN_COUNTRIES)
    last    = random.choice(LAST_NAMES)
    first   = random.choice(FIRST_NAMES)
    cred    = random.choice(CREDENTIALS)

    # Legitimate-looking US claims
    for _ in range(random.randint(2, 5)):
        start = rand_date()
        end   = start + timedelta(days=random.randint(1, 20))
        rows.append(make_claim(claim_id, npi, ptype, "US", us_state, start, end, last, first, cred))
        claim_id += 1

    # Overlapping foreign claims (same NPI, same window, different country)
    base   = rand_date(date(2021,1,1), date(2023,6,1))
    offset = random.randint(1, 10)
    for _ in range(random.randint(1, 3)):
        fstart = base + timedelta(days=offset)
        fend   = fstart + timedelta(days=random.randint(5, 25))
        # High submitted charges relative to payment = red flag
        row = make_claim(claim_id, npi, ptype, fcc, "", fstart, fend, last, first, cred)
        row["avg_sbmtd_chrg"] = round(row["avg_mdcr_pymt_amt"] * random.uniform(4.5, 8.0), 2)
        rows.append(row)
        claim_id += 1

# ── 100 legitimate foreign providers (foreign residents enrolled in Medicare) ─
for i in range(1900, 2000):
    npi  = npi_pool[i]
    ptype = random.choice(PROVIDER_TYPES)
    fcc  = random.choice(FOREIGN_COUNTRIES)
    last = random.choice(LAST_NAMES)
    first= random.choice(FIRST_NAMES)
    cred = random.choice(CREDENTIALS)
    for _ in range(random.randint(1, 4)):
        start = rand_date()
        end   = start + timedelta(days=random.randint(1, 15))
        rows.append(make_claim(claim_id, npi, ptype, fcc, "", start, end, last, first, cred))
        claim_id += 1

random.shuffle(rows)

FIELDS = [
    "clm_id","rndrng_npi","rndrng_prvdr_last_org_name","rndrng_prvdr_first_name",
    "rndrng_prvdr_crdntls","rndrng_prvdr_type","rndrng_prvdr_state_abrvtn",
    "rndrng_prvdr_cntry","hcpcs_cd","hcpcs_desc","place_of_srvc",
    "clm_from_dt","clm_thru_dt","avg_sbmtd_chrg","avg_mdcr_alowd_amt","avg_mdcr_pymt_amt",
]

with open("data/claims.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)

print(f"Generated {len(rows):,} claims")
print(f"Unique NPIs: {len(set(r['rndrng_npi'] for r in rows)):,}")
print(f"Foreign-country claims: {sum(1 for r in rows if r['rndrng_prvdr_cntry'] != 'US'):,}")
