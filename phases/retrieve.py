import pandas as pd

def retrieve_phase(input_path, output_folder):
    """Retrieve phase: Load data and perform data parsing/analysis."""
    try:
        original_df = pd.read_csv(input_path)
        reasoning = f"Successfully loaded dataset from {input_path} with {len(original_df)} rows and {len(original_df.columns)} columns."
    except FileNotFoundError:
        reasoning = f"Failed to load dataset from {input_path}."
        return None, reasoning, 0.0

    # Retrieval action: Parse and summarize data structure
    try:
        data_summary = {
            "columns": list(original_df.columns),
            "dtypes": original_df.dtypes.astype(str).to_dict(),
            "missing_values": original_df.isnull().sum().to_dict()
        }
        reasoning += f" Parsed data structure: {len(data_summary['columns'])} columns, data types identified, missing values counted."
        confidence = 0.95
    except Exception as e:
        data_summary = None
        reasoning += f" Data parsing failed: {str(e)}."
        confidence = 0.7

    return original_df, reasoning, confidence
