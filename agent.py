# agent.py
import argparse
import pandas as pd
from cleaner import auto_clean
from explain import gemini_generate_eda_plan
import json
from datetime import datetime
import os

def main(input_path, output_path=None):
    print(f"Loading dataset: {input_path}")
    df = pd.read_csv(input_path)

    print("Cleaning dataset...")
    cleaned_df = auto_clean(df)

    print("Generating Gemini EDA plan...")
    eda_plan = gemini_generate_eda_plan(cleaned_df)

    # Automatic output folder if not provided
    if not output_path:
        output_path = "sample_outputs"
    os.makedirs(output_path, exist_ok=True)

    output_file = os.path.join(output_path, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    print(f"Generating report: {output_file}")
    with open(output_file, "w") as f:
        json.dump({
            "metadata": {
                "original_shape": list(df.shape),
                "cleaned_shape": list(cleaned_df.shape)
            },
            "eda_plan": eda_plan
        }, f, indent=2)

    print("EDA pipeline completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=False, help="Optional output folder")
    args = parser.parse_args()
    main(args.input, args.output)
