import pandas as pd
import numpy as np
import re

def auto_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    converted_cols = []
    for col in df.columns:
        if df[col].dtype == "object":
            cleaned = df[col].astype(str).str.replace(r"[^\d\.\-]", "", regex=True)
            numeric_series = pd.to_numeric(cleaned, errors="coerce")
            if numeric_series.notna().mean() > 0.5:
                df[col] = numeric_series
                converted_cols.append(col)
    df = df.drop_duplicates().applymap(lambda x: x.strip() if isinstance(x, str) else x)
    print(f"🧹 Columns converted to numeric: {converted_cols}")
    return df
