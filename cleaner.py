import pandas as pd
import numpy as np
import re

def detect_explodable_columns(df: pd.DataFrame, sample_size=5):
    """Detect columns with multi-value entries (comma-separated or list-like)."""
    explodable = []
    for col in df.select_dtypes(include="object"):
        sample_vals = df[col].dropna().head(sample_size).astype(str)
        if any("," in val for val in sample_vals):
            explodable.append(col)
        elif any(val.startswith("[") and val.endswith("]") for val in sample_vals):
            explodable.append(col)
    return explodable

def auto_explode(df: pd.DataFrame, columns):
    """Explode detected multi-value columns."""
    df = df.copy()
    for col in columns:
        print(f"[Auto-clean] Exploding column: {col}")
        df[col] = df[col].apply(lambda x: [v.strip() for v in str(x).split(",")] if pd.notna(x) else [])
        df = df.explode(col).reset_index(drop=True)
    return df

def auto_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Strip whitespace
    for col in df.select_dtypes(include="object"):
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # Drop duplicates
    df = df.drop_duplicates()

    # Explode multi-value columns
    explodable = detect_explodable_columns(df)
    if explodable:
        df = auto_explode(df, explodable)
        print("[Auto-clean] Exploded columns:", explodable)
    else:
        print("[Auto-clean] No columns were exploded.")

    # Parse numeric-like columns
    for col in df.columns:
        if df[col].dtype == "object":
            cleaned = df[col].astype(str).str.replace(r"[^\d\.\-]", "", regex=True)
            numeric_series = pd.to_numeric(cleaned, errors="coerce")
            if numeric_series.notna().mean() > 0.5:
                df[col] = numeric_series

    # Parse dates
    if "date_added" in df.columns:
        df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")

    # Parse durations
    if "duration" in df.columns:
        def parse_duration(val):
            if pd.isna(val):
                return np.nan
            val = str(val).lower()
            num = re.findall(r"\d+", val)
            return float(num[0]) if num else np.nan
        df["duration"] = df["duration"].apply(parse_duration)

    return df
