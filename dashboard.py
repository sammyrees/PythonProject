import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

from cleaner import clean_partner_ids, clean_timestamps


# Streamlit page configuration

st.set_page_config(page_title="CTR Dashboard", layout="wide")
st.sidebar.image("logo.png", width=288)


# 1) Load + clean raw CSV (apply industry-standard null rules)

@st.cache_data(show_spinner="Loading data…")
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df.replace({"": np.nan, "N/A": np.nan, "NA": np.nan, "null": np.nan, "NULL": np.nan}, inplace=True)
    df["partner_id"] = clean_partner_ids(df["partner_id"])
    df["clicks"] = pd.to_numeric(df["clicks"], errors="coerce")
    df["impressions"] = pd.to_numeric(df["impressions"], errors="coerce")
    df["date"] = clean_timestamps(df["timestamp"])
    served = df["impressions"].notna() & (df["impressions"] > 0)
    df.loc[served & df["clicks"].isna(), "clicks"] = 0
    df = df[served].dropna(subset=["date"])
    return df

# ---- load on startup ----
df = load_data("data/sample_campaign_logs.csv")
st.title("Daily CTR & Alerts (30‑day window)")
partner_opts = sorted(df["partner_id"].unique())
selected = st.sidebar.multiselect("Filter partners", partner_opts, default=partner_opts)
df = df[df["partner_id"].isin(selected)]


# 2) Aggregate daily metrics & classify drops (10 / 20 / 30 %)

daily = (
    df.groupby(["partner_id", "date"], as_index=False)
      .agg(clicks=("clicks", "sum"), imps=("impressions", "sum"))
)
daily["ctr"] = daily["clicks"] / daily["imps"]
daily = daily.sort_values(["partner_id", "date"])
# compute previous day CTR
daily["prev_ctr"] = daily.groupby("partner_id")["ctr"].shift(1)
daily["pct_change"] = (daily["ctr"] - daily["prev_ctr"]) / daily["prev_ctr"]
# classify severity
conds = [daily["pct_change"] <= -0.3, daily["pct_change"] <= -0.2, daily["pct_change"] <= -0.1]
choices = ["30%", "20%", "10%"]
daily["drop_level"] = np.select(conds, choices, default="")
drop_rows = daily[daily["drop_level"] != ""]


# 3) Plotly line chart with multi‑severity markers

fig = px.line(daily, x="date", y="ctr", color="partner_id", markers=True,
              labels={"ctr": "CTR", "date": "Date", "partner_id": "Partner"},
              title="Daily Click‑Through Rate & Drop Alerts")
symbols = {"10%": "triangle-down", "20%": "diamond-x", "30%": "x"}
for lvl, sym in symbols.items():
    sub = drop_rows[drop_rows["drop_level"] == lvl]
    if not sub.empty:
        fig.add_scatter(x=sub["date"], y=sub["ctr"], mode="markers", marker_symbol=sym,
                        marker_size=10, name=f"> {lvl} drop")
st.plotly_chart(fig, use_container_width=True)


# 4) Notification if no mid/high-level drops
# Check for any 20% or 30% drops
has_20 = drop_rows[drop_rows["drop_level"] == "20%"].any().any()
has_30 = drop_rows[drop_rows["drop_level"] == "30%"].any().any()
if not has_20 and not has_30:
    st.info(" No day‑over‑day CTR declines of 20 % or 30 % were detected.")


# 5) Drop‑details table (with before/after CTR)

with st.expander("Drop details (≥10 %) "):
    details = (
        drop_rows[["partner_id", "date", "prev_ctr", "ctr", "pct_change", "drop_level"]]
        .rename(columns={"prev_ctr": "ctr_before", "ctr": "ctr_after", "drop_level": "severity"})
        .assign(
            ctr_before=lambda d: d["ctr_before"].round(4),
            ctr_after=lambda d: d["ctr_after"].round(4),
            pct_change=lambda d: (d["pct_change"] * 100).round(1).astype(str) + "%"
        )
        .sort_values(["partner_id", "date"]).reset_index(drop=True)
    )
    st.dataframe(details, hide_index=True)

st.markdown("\u200b")
st.caption("CTR = clicks / impressions. Previous-day CTR shown alongside today's CTR for flagged drops.")
