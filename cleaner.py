import pandas as pd
import numpy as np
import re

# Removed detect_explodable_columns and auto_explode as their logic is now in the Gemini plan

def execute_explode(df: pd.DataFrame, col: str, delimiter: str):
    """Explode a column based on the plan, only if the delimiter is not 'NONE'."""
    if delimiter.upper() == 'NONE':
        print(f"[Auto-clean] Skipping explosion for {col} (identified as single-entity, e.g., Address).")
        return df

    if col not in df.columns:
        return df

    print(f"[Auto-clean] Exploding column: {col} with delimiter '{delimiter}'")
    
    # Handle NaN values before applying string operations
    series = df[col].dropna().astype(str)
    
    # Split, strip whitespace, and create a list
    df[col] = df[col].apply(
        lambda x: [v.strip() for v in str(x).split(delimiter)] 
        if pd.notna(x) and delimiter in str(x) else [x]
    )
    
    # Explode the list column
    df = df.explode(col).reset_index(drop=True)
    return df

def execute_parse_date(df: pd.DataFrame, col: str, date_format: str):
    """Parse a date column using a specified format."""
    if col in df.columns:
        print(f"[Auto-clean] Parsing date column: {col} with format '{date_format}'")
        df[col] = pd.to_datetime(df[col], format=date_format, errors="coerce")
    return df

def execute_convert_numeric(df: pd.DataFrame, col: str):
    """Convert a column to numeric, aggressively cleaning non-numeric characters."""
    if col in df.columns and df[col].dtype == "object":
        print(f"[Auto-clean] Converting numeric column: {col}")
        
        # Aggressively remove common non-numeric characters (currency, commas)
        cleaned = df[col].astype(str).str.replace(r"[^\d\.\-]", "", regex=True)
        numeric_series = pd.to_numeric(cleaned, errors="coerce")
        df[col] = numeric_series
    return df

def auto_clean(df: pd.DataFrame, data_prep_plan: dict) -> pd.DataFrame:
    df = df.copy()
    
    # Strip whitespace (general cleaning remains)
    for col in df.select_dtypes(include="object"):
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # Drop duplicates (general cleaning remains)
    df = df.drop_duplicates()
    
    # 🆕 Execute Gemini's Data Preparation Plan
    for task in data_prep_plan.get("data_prep", []):
        col = task.get("column")
        task_type = task.get("task")

        if task_type == "explode":
            delimiter = task.get("delimiter", ",").replace("\\n", "\n") # Default to comma, handle newline
            df = execute_explode(df, col, delimiter)
        elif task_type == "parse_date":
            date_format = task.get("format")
            if date_format:
                df = execute_parse_date(df, col, date_format)
        elif task_type == "convert_numeric":
            df = execute_convert_numeric(df, col)

    # Parse durations (specific hardcoded logic for 'duration' remains as a safeguard)
    if "duration" in df.columns:
        def parse_duration(val):
            if pd.isna(val):
                return np.nan
            val = str(val).lower()
            num = re.findall(r"\d+", val)
            return float(num[0]) if num else np.nan
        df["duration"] = df["duration"].apply(parse_duration)

    return df