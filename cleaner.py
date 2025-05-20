# cleaning.py
import pandas as pd
import numpy as np
import re
import streamlit as st  # only if you use st.warning/print inside functions

def clean_partner_ids(s: pd.Series) -> pd.Series:
    s = s.str.lower().str.strip()
    s = s.str.replace(r'[^a-z0-9]', '', regex=True)
    s = s.replace({
        "br1ghtblox": "brightblox",
        "funbles":    "funables",
        "k1dzsy":     "kidzsy",
        "m1n1mx":     "minimax",
        "plypyls":    "playpals",
        "plypls":     "playpals",
        "zppytoys":   "zappytoys",
    })
    unknown = set(s.unique()) - {
        "brightblox","funables","kidzsy",
        "minimax","playpals","toonjoy","zappytoys"
    }
    if unknown:
        st.warning(f"Unrecognized partner_id(s): {unknown}")
    return s

def clean_timestamps(s: pd.Series) -> pd.Series:
    dt1 = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    dt2 = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    ts = dt1.fillna(dt2)
    bad = s[ts.isna()].unique()
    if len(bad):
        st.warning(f"Could not parse timestamps: {bad}")
    return ts.dt.date
