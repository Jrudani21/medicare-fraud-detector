"""
CMS Medicare Cross-Country Provider Fraud Dashboard

Data source: CMS Medicare Physician & Other Practitioners by Provider and Service
https://data.cms.gov/provider-summary-by-type-of-service/
medicare-physician-other-practitioners/
medicare-physician-other-practitioners-by-provider-and-service

Fraud pattern: same NPI billing from US + foreign country in overlapping windows.
"""
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="CMS Fraud Detector",
    page_icon="🏥",
    layout="wide",
)

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 2rem; color: #d9615a; }
.risk-HIGH   { color:#e05555; font-weight:700; }
.risk-MEDIUM { color:#e0a855; font-weight:700; }
.risk-LOW    { color:#55a8e0; font-weight:700; }
</style>
""", unsafe_allow_html=True)

COUNTRY_NAMES = {
    "IN":"India","PH":"Philippines","NG":"Nigeria","MX":"Mexico",
    "GH":"Ghana","PK":"Pakistan","RO":"Romania","UA":"Ukraine","US":"United States",
}

@st.cache_resource
def get_conn():
    return sqlite3.connect("data/claims.db", check_same_thread=False)

@st.cache_data
def load_risk_scores():
    return pd.read_sql_query(open("queries/03_risk_scoring.sql").read(), get_conn())

@st.cache_data
def load_overlapping_pairs():
    return pd.read_sql_query(open("queries/02_overlap_detection.sql").read(), get_conn())

@st.cache_data
def load_country_summary():
    return pd.read_sql_query(open("queries/04_country_pair_summary.sql").read(), get_conn())

@st.cache_data
def load_benchmarks():
    return pd.read_sql_query(open("queries/05_specialty_benchmark.sql").read(), get_conn())

@st.cache_data
def load_claims():
    return pd.read_csv("data/claims.csv", parse_dates=["clm_from_dt","clm_thru_dt"])

risk_df    = load_risk_scores()
pairs_df   = load_overlapping_pairs()
country_df = load_country_summary()
bench_df   = load_benchmarks()
claims_df  = load_claims()

total_providers = claims_df["rndrng_npi"].nunique()
flagged         = risk_df["rndrng_npi"].nunique()
high_risk       = (risk_df["risk_level"] == "HIGH").sum()
total_at_risk   = risk_df["total_suspicious_payment"].sum()

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🏥 CMS Medicare Cross-Country Fraud Detector")
st.caption(
    "Identifies providers (NPIs) billing from a US address and a foreign country "
    "simultaneously — a documented CMS OIG phantom billing scheme. "
    "Data structure: Medicare Physician & Other Practitioners by Provider and Service."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Providers",   f"{total_providers:,}")
c2.metric("Flagged NPIs",      f"{flagged:,}",  delta=f"{flagged/total_providers*100:.1f}% of all")
c3.metric("HIGH Risk",         str(high_risk),  delta_color="inverse", delta="Needs OIG referral")
c4.metric("Medicare $ at Risk", f"${total_at_risk:,.0f}")

st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("Filters")
risk_filter = st.sidebar.multiselect("Risk Level", ["HIGH","MEDIUM","LOW"], default=["HIGH","MEDIUM"])
specialty_opts = sorted(risk_df["specialty"].dropna().unique())
spec_filter = st.sidebar.multiselect("Specialty", specialty_opts, default=specialty_opts)
min_overlap = st.sidebar.slider("Min Overlap Days", 0, 30, 0)

filtered_risk  = risk_df[risk_df["risk_level"].isin(risk_filter) & risk_df["specialty"].isin(spec_filter)]
filtered_pairs = pairs_df[
    pairs_df["rndrng_npi"].isin(filtered_risk["rndrng_npi"]) &
    (pairs_df["overlap_days"] >= min_overlap)
]

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌍 Foreign Country Risk",
    "👤 Flagged Providers",
    "📋 Claim Pairs",
    "📊 Charge Benchmarks",
    "📈 Risk Distribution",
])

# ─── Tab 1: Country risk bar ─────────────────────────────────────────────────
with tab1:
    st.subheader("Foreign Countries Appearing in Overlapping Billing Pairs")
    country_df["country_name"] = country_df["foreign_country"].map(COUNTRY_NAMES).fillna(country_df["foreign_country"])

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(
            country_df.sort_values("flagged_providers", ascending=True),
            x="flagged_providers", y="country_name", orientation="h",
            color="flagged_providers", color_continuous_scale="Reds",
            title="Flagged providers by foreign country",
            labels={"flagged_providers":"Providers","country_name":"Country"},
        )
        fig.update_layout(coloraxis_showscale=False, height=340, margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = px.bar(
            country_df.sort_values("avg_charge_ratio", ascending=True),
            x="avg_charge_ratio", y="country_name", orientation="h",
            color="avg_charge_ratio", color_continuous_scale="OrRd",
            title="Avg charge inflation ratio (submitted ÷ allowed)",
            labels={"avg_charge_ratio":"Charge Ratio","country_name":"Country"},
        )
        fig2.update_layout(coloraxis_showscale=False, height=340, margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(
        country_df.rename(columns={
            "foreign_country":"ISO","country_name":"Country",
            "flagged_providers":"Flagged Providers","overlap_instances":"Overlap Instances",
            "total_at_risk_usd":"Total $ at Risk","avg_overlap_days":"Avg Overlap Days",
            "avg_charge_ratio":"Avg Charge Ratio",
        }),
        use_container_width=True, hide_index=True,
    )

# ─── Tab 2: Provider risk table ───────────────────────────────────────────────
with tab2:
    st.subheader(f"Flagged Providers — {len(filtered_risk):,} NPIs")

    display = filtered_risk.copy()
    display["total_suspicious_payment"] = display["total_suspicious_payment"].apply(lambda x: f"${x:,.0f}")
    display["max_charge_ratio"] = display["max_charge_ratio"].apply(lambda x: f"{x:.1f}x")

    st.dataframe(
        display.rename(columns={
            "rndrng_npi":"NPI","provider_name":"Provider","specialty":"Specialty",
            "credentials":"Credentials","us_state":"US State",
            "flagged_pairs":"Pairs","foreign_countries":"Foreign Countries",
            "total_suspicious_payment":"$ at Risk","max_charge_ratio":"Max Charge Ratio",
            "total_overlap_days":"Overlap Days","risk_score":"Score","risk_level":"Risk",
        }),
        use_container_width=True, hide_index=True,
    )

# ─── Tab 3: Overlapping claim pairs drill-down ────────────────────────────────
with tab3:
    st.subheader("Overlapping US ↔ Foreign Claim Pairs")

    selected = st.selectbox(
        "Select NPI to inspect",
        ["All"] + sorted(filtered_risk["rndrng_npi"].tolist()),
    )

    view = filtered_pairs if selected == "All" else filtered_pairs[filtered_pairs["rndrng_npi"] == selected]

    display_pairs = view.copy()
    for col in ["us_payment","foreign_payment","foreign_submitted_charge"]:
        display_pairs[col] = display_pairs[col].apply(lambda x: f"${x:,.0f}")

    st.dataframe(display_pairs, use_container_width=True, hide_index=True)

    if selected != "All" and not view.empty:
        st.markdown(f"**Claim timeline for NPI {selected}**")
        npi_claims = claims_df[claims_df["rndrng_npi"] == selected].copy()
        npi_claims["label"] = npi_claims["rndrng_prvdr_cntry"].map(
            lambda c: COUNTRY_NAMES.get(c, c)
        )
        fig_tl = px.timeline(
            npi_claims, x_start="clm_from_dt", x_end="clm_thru_dt",
            y="label", color="rndrng_prvdr_cntry",
            hover_data=["hcpcs_cd","hcpcs_desc","avg_mdcr_pymt_amt"],
            title=f"NPI {selected} — billing windows by country",
        )
        fig_tl.update_layout(height=300, showlegend=False, margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig_tl, use_container_width=True)

# ─── Tab 4: Charge benchmarks ─────────────────────────────────────────────────
with tab4:
    st.subheader("Foreign Billing vs US Specialty Benchmark")
    st.caption("Compares what flagged foreign-billed providers charged vs the average for the same HCPCS code and specialty in the US.")

    inflated = bench_df[bench_df["deviation_flag"] == "INFLATED"].copy()
    inflated["payment_ratio"] = inflated["payment_ratio"].apply(lambda x: f"{x:.2f}x")
    inflated["payment_deviation"] = inflated["payment_deviation"].apply(lambda x: f"+${x:,.0f}")
    inflated["foreign_payment"] = inflated["foreign_payment"].apply(lambda x: f"${x:,.0f}")
    inflated["us_avg_payment"] = inflated["us_avg_payment"].apply(lambda x: f"${x:,.0f}")

    st.markdown(f"**{len(inflated)} INFLATED claims** (foreign payment > 2× US benchmark)")
    st.dataframe(
        inflated[["rndrng_npi","provider_name","specialty","billing_country",
                  "hcpcs_cd","hcpcs_desc","foreign_payment","us_avg_payment",
                  "payment_deviation","payment_ratio"]].rename(columns={
            "rndrng_npi":"NPI","provider_name":"Provider","specialty":"Specialty",
            "billing_country":"Country","hcpcs_cd":"HCPCS","hcpcs_desc":"Procedure",
            "foreign_payment":"Foreign $","us_avg_payment":"US Avg $",
            "payment_deviation":"Deviation","payment_ratio":"Ratio",
        }),
        use_container_width=True, hide_index=True,
    )

# ─── Tab 5: Risk distribution ─────────────────────────────────────────────────
with tab5:
    col_a, col_b = st.columns(2)

    with col_a:
        lc = risk_df["risk_level"].value_counts().reset_index()
        lc.columns = ["Risk Level","Count"]
        fig_pie = px.pie(lc, names="Risk Level", values="Count",
            color="Risk Level",
            color_discrete_map={"HIGH":"#e05555","MEDIUM":"#e0a855","LOW":"#55a8e0"},
            title="Flagged providers by risk level")
        fig_pie.update_layout(margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        fig_hist = px.histogram(risk_df, x="risk_score", color="risk_level", nbins=20,
            color_discrete_map={"HIGH":"#e05555","MEDIUM":"#e0a855","LOW":"#55a8e0"},
            title="Risk score distribution",
            labels={"risk_score":"Score","count":"Providers"})
        fig_hist.update_layout(margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig_hist, use_container_width=True)

    fig_spec = px.bar(
        risk_df.groupby("specialty")["total_suspicious_payment"].sum()
               .reset_index().sort_values("total_suspicious_payment", ascending=False),
        x="specialty", y="total_suspicious_payment",
        color="total_suspicious_payment", color_continuous_scale="Reds",
        title="Total suspicious Medicare $ at risk by specialty",
        labels={"specialty":"Specialty","total_suspicious_payment":"$ at Risk"},
    )
    fig_spec.update_layout(coloraxis_showscale=False, margin=dict(l=0,r=0,t=40,b=0),
                           xaxis_tickangle=-35)
    st.plotly_chart(fig_spec, use_container_width=True)
