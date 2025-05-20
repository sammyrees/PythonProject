import pandas as pd

# 1. Load raw CSV as text (no auto-NaN conversion)
df_raw = pd.read_csv(
    "data/sample_campaign_logs.csv",
    dtype=str,
    keep_default_na=False
).applymap(lambda x: x.strip() if isinstance(x, str) else x)

# 2. Define the “missing” tokens we don’t want to include
missing_tokens = ["", "NULL", "null", "N/A", "NA", "na", "--"]

# 3. For each field, collect and sort all non-missing unique values
cols = ["partner_id", "campaign_id", "timestamp", "ad_slot"]
unique_values = {
    col: sorted(df_raw[col][~df_raw[col].isin(missing_tokens)].unique())
    for col in cols
}

# 4. Display them
for col, vals in unique_values.items():
    print(f"\n=== {col} ({len(vals)} unique) ===")
    for v in vals:
        print(" ", v)
# 5. Count missing entries in clicks & impressions
for num_col in ["clicks", "impressions"]:
    missing_count = df_raw[num_col].isin(missing_tokens).sum()
    total_count   = len(df_raw)
    print(f"\n*** {num_col} missing count: {missing_count} of {total_count} rows ({missing_count/total_count:.1%}) ***")