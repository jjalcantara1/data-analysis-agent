import json
import os
from datetime import datetime

def generate_report(original_df, cleaned_df, eda_plan, eda_results, output_path: str):
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
        "eda_plan": eda_plan,
        "eda_results": eda_results
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
