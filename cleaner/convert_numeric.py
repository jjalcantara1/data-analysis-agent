import pandas as pd

def execute_convert_numeric(df: pd.DataFrame, col: str):
    """
    Convert a column to numeric, aggressively cleaning non-numeric characters.
    """
    if col in df.columns and df[col].dtype == "object":
        print(f"[Auto-clean] Converting numeric column: {col}")

        if df[col].astype(str).str.contains(r"\d+\s*\+", regex=True).any():
            print(f"  [Auto-clean] Handling numeric plus sign (+) by removing it in column: {col}")
            df[col] = df[col].astype(str).str.replace("+", "", regex=False)

        cleaned = df[col].astype(str).str.replace(r"[^\d\.\-]", "", regex=True)
        numeric_series = pd.to_numeric(cleaned, errors="coerce")
        df[col] = numeric_series
    return df
