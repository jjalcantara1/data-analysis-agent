import pandas as pd

def execute_parse_date(df: pd.DataFrame, col: str, date_format: str):
    """Parse a date column using a specified format, with fallback to inference."""
    if col in df.columns:
        print(f"[Auto-clean] Parsing date column: {col} with format '{date_format}'")
        parsed_with_format = pd.to_datetime(df[col], format=date_format, errors="coerce")
        success_rate = parsed_with_format.notnull().sum() / len(df[col])
        if success_rate > 0.5:
            df[col] = parsed_with_format
            print(f"[Auto-clean] Successfully parsed {col} with format '{date_format}' (success rate: {success_rate:.2%})")
        else:
            print(f"[Auto-clean] Format '{date_format}' failed (success rate: {success_rate:.2%}), falling back to inference.")
            df[col] = pd.to_datetime(df[col], errors="coerce")
            fallback_success = df[col].notnull().sum() / len(df[col])
            print(f"[Auto-clean] Fallback parsing succeeded for {fallback_success:.2%} of values.")
    return df
