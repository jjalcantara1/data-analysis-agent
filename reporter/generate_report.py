import json
import os
from datetime import datetime
import pandas as pd
import numpy as np

from .utils import numpy_encoder

def generate_report(original_df, cleaned_df, data_prep_plan, eda_plan, output_path: str):
    """
    Generates a structured JSON report summarizing the data cleaning and EDA plan metadata.
    """
    report = {
        "metadata": {
            "original_shape": original_df.shape,
            "cleaned_shape": cleaned_df.shape,
            "retrieved_at": datetime.now().isoformat()
        },
        "cleaning_summary": {
            "duplicates_removed": original_df.shape[0] - cleaned_df.shape[0],
            "columns_converted": [c for c in cleaned_df.columns if c not in original_df.columns]
        },
        "data_prep_plan": data_prep_plan,
        "eda_plan": eda_plan,
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        # Use numpy_encoder for robust JSON serialization
        json.dump(report, f, indent=2, default=numpy_encoder)
