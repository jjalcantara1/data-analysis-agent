import pandas as pd
import numpy as np
import re

def auto_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    for col in df.columns:
        if df[col].dtype == "object":
            cleaned = df[col].astype(str).str.replace(r"[^\d\.\-]", "", regex=True)
            numeric_series = pd.to_numeric(cleaned, errors="coerce")
            if numeric_series.notna().mean() > 0.5:
                df[col] = numeric_series

    df = df.drop_duplicates()

    for col in df.select_dtypes(include="object"):
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    for col in df.select_dtypes(include="object").columns:
        if df[col].str.contains(r'\|').any():
            print(f"[Auto-clean] Exploding column: {col}")
            df = df.assign(**{col: df[col].str.split('|')})  # convert to list
            df = df.explode(col).reset_index(drop=True)      # safely explode

    return df
