import pandas as pd
import numpy as np
import re

from .explode import execute_explode
from .parse_date import execute_parse_date
from .convert_numeric import execute_convert_numeric

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


def auto_clean(df: pd.DataFrame, data_prep_plan: list) -> pd.DataFrame:
    df = df.copy()

    for col in df.select_dtypes(include="object"):
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    df = df.drop_duplicates()

    for task in data_prep_plan:
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

    if "duration" in df.columns:
        parsed_data = df["duration"].apply(parse_duration_safe)

        df["duration_value"] = parsed_data.apply(lambda x: x[0])
        df["duration_unit"] = parsed_data.apply(lambda x: x[1])

        df = df.drop(columns=['duration'], errors='ignore')
        df = df.rename(columns={'duration_value': 'duration'})

        print("[Auto-clean] Cleaned and split 'duration' into 'duration' (value) and 'duration_unit'.")

    return df
