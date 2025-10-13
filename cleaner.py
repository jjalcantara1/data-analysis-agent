import pandas as pd
import numpy as np
import re

def detect_explodable_columns(df: pd.DataFrame, sample_size=5):
    """
    Detect columns that contain multi-value entries (pipe-separated or list-like)
    """
    explodable = []
    for col in df.select_dtypes(include="object"):
        sample_vals = df[col].dropna().head(sample_size).astype(str)
        if any("|" in val for val in sample_vals):
            explodable.append(col)
        elif any(val.startswith("[") and val.endswith("]") for val in sample_vals):
            explodable.append(col)
    return explodable

def auto_explode(df: pd.DataFrame, columns):
    """
    Explode detected multi-value columns
    """
    df = df.copy()
    for col in columns:
        print(f"[Auto-clean] Exploding column: {col}")
        df[col] = df[col].apply(lambda x: str(x).split("|") if pd.notna(x) else [])
        df = df.explode(col).reset_index(drop=True)
    return df

def auto_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    exploded_columns = []

    for col in df.columns:
        # convert numeric-like strings to numbers
        if df[col].dtype == "object":
            cleaned = df[col].astype(str).str.replace(r"[^\d\.\-]", "", regex=True)
            numeric_series = pd.to_numeric(cleaned, errors="coerce")
            if numeric_series.notna().mean() > 0.5:
                df[col] = numeric_series

    df = df.drop_duplicates()

    for col in df.select_dtypes(include="object"):
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # detect and explode multi-value columns safely
    explodable = detect_explodable_columns(df)
    if explodable:
        df = auto_explode(df, explodable)
        print("[Auto-clean] Exploded columns:", explodable)
    else:
        print("[Auto-clean] No columns were exploded.")

    return df
