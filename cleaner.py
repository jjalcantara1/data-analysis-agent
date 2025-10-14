import pandas as pd
import numpy as np
import re

def execute_explode(df: pd.DataFrame, col: str, delimiter: str):
    """Explode a column based on the plan, only if the delimiter is not 'NONE'."""
    if delimiter.upper() == 'NONE':
        print(f"[Auto-clean] Skipping explosion for {col} (identified as single-entity, e.g., Address).")
        return df

    if col not in df.columns:
        return df

    print(f"[Auto-clean] Exploding column: {col} with delimiter '{delimiter}'")
    
    # Safely split, strip whitespace, and handle nan/empty strings
    df[col] = df[col].apply(
        lambda x: [v.strip() for v in str(x).split(delimiter) if v.strip() != ''] 
        if pd.notna(x) and isinstance(x, str) and delimiter in str(x) else [x]
    )
    
    # Flatten single-element lists that weren't split
    df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) and len(x) == 1 else x)
    
    df = df.explode(col).reset_index(drop=True)
    return df

def execute_parse_date(df: pd.DataFrame, col: str, date_format: str):
    """Parse a date column using a specified format."""
    if col in df.columns:
        print(f"[Auto-clean] Parsing date column: {col} with format '{date_format}'")
        df[col] = pd.to_datetime(df[col], format=date_format, errors="coerce")
    return df

def execute_convert_numeric(df: pd.DataFrame, col: str):
    """
    Convert a column to numeric, aggressively cleaning non-numeric characters.
    """
    if col in df.columns and df[col].dtype == "object":
        print(f"[Auto-clean] Converting numeric column: {col}")
        
        # Handle common numeric string formats like '4+' by removing the '+'
        if df[col].astype(str).str.contains(r"\d+\s*\+", regex=True).any():
            print(f"  [Auto-clean] Handling numeric plus sign (+) by removing it in column: {col}")
            df[col] = df[col].astype(str).str.replace("+", "", regex=False)
        
        # Aggressively remove common non-numeric characters (currency, commas)
        cleaned = df[col].astype(str).str.replace(r"[^\d\.\-]", "", regex=True)
        numeric_series = pd.to_numeric(cleaned, errors="coerce")
        df[col] = numeric_series
    return df


def parse_duration_safe(val):
    """
    Parses duration into a clean numeric value and unit.
    Returns a tuple (value, unit).
    """
    if pd.isna(val) or val is None:
        return np.nan, np.nan
    val = str(val).strip().lower()
    
    match = re.search(r"(\d+)\s*(min|season|seasons)", val)
    if match:
        num = float(match.group(1))
        unit = match.group(2).replace('seasons', 'Season').replace('season', 'Season').replace('min', 'Minute')
        return num, unit
    
    return np.nan, np.nan 


def auto_clean(df: pd.DataFrame, data_prep_plan: dict) -> pd.DataFrame:
    df = df.copy()
    
    # General cleaning: strip whitespace from object columns
    for col in df.select_dtypes(include="object"):
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # General cleaning: drop exact duplicates
    df = df.drop_duplicates()
    
    # Execute Gemini's Data Preparation Plan tasks
    for task in data_prep_plan.get("data_prep", []):
        col = task.get("column")
        task_type = task.get("task")

        if task_type == "explode":
            delimiter = task.get("delimiter", ",").replace("\\n", "\n")
            df = execute_explode(df, col, delimiter)
        elif task_type == "parse_date":
            date_format = task.get("format")
            if date_format:
                df = execute_parse_date(df, col, date_format)
        elif task_type == "convert_numeric":
            df = execute_convert_numeric(df, col)

    # Specific cleaning for 'duration' column (if present)
    if "duration" in df.columns:
        parsed_data = df["duration"].apply(parse_duration_safe)
        
        df["duration_value"] = parsed_data.apply(lambda x: x[0])
        df["duration_unit"] = parsed_data.apply(lambda x: x[1])

        df = df.drop(columns=['duration'], errors='ignore')
        df = df.rename(columns={'duration_value': 'duration'})
        
        print("[Auto-clean] Cleaned and split 'duration' into 'duration' (value) and 'duration_unit'.")
        
    return df