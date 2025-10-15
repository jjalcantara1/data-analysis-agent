import pandas as pd

def execute_explode(df: pd.DataFrame, col: str, delimiter: str):
    """Explode a column based on the plan, only if the delimiter is not 'NONE'."""
    if delimiter.upper() == 'NONE':
        print(f"[Auto-clean] Skipping explosion for {col} (identified as single-entity, e.g., Address).")
        return df

    if col not in df.columns:
        return df

    print(f"[Auto-clean] Exploding column: {col} with delimiter '{delimiter}'")

    df[col] = df[col].apply(
        lambda x: [v.strip() for v in str(x).split(delimiter) if v.strip() != '']
        if pd.notna(x) and isinstance(x, str) and delimiter in str(x) else [x]
    )

    df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) and len(x) == 1 else x)

    df = df.explode(col).reset_index(drop=True)
    return df
