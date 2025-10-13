import argparse
import pandas as pd
from cleaner import auto_clean
# 🆕 Import the new data prep function
from explain import gemini_generate_eda_plan, gemini_generate_data_prep_plan 
from adaptive_eda_executor import adaptive_eda_executor 
import json
from datetime import datetime
import os

def main(input_path, output_path=None):
    print(f"Loading dataset: {input_path}")
    df = pd.read_csv(input_path)

    # 🆕 STEP 1: Let Gemini determine the cleaning/prep steps from RAW data
    data_prep_plan = gemini_generate_data_prep_plan(df)

    print("Cleaning dataset using Gemini's Data Prep Plan...")
    # 🆕 STEP 2: Pass the plan to auto_clean
    cleaned_df = auto_clean(df, data_prep_plan)

    # 🆕 STEP 3: Let Gemini determine the EDA plan from CLEANED data
    print("Generating Gemini EDA plan...")
    eda_plan = gemini_generate_eda_plan(cleaned_df)

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
            # 🆕 Include the Data Prep Plan in the report
            "data_prep_plan": data_prep_plan, 
            "eda_plan": eda_plan
        }, f, indent=2)

    print("Executing adaptive EDA tasks...")
    adaptive_eda_executor(cleaned_df, eda_plan, output_dir=os.path.join(output_path, "eda_outputs"))

    print("EDA pipeline completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=False, help="Optional output folder")
    args = parser.parse_args()
    main(args.input, args.output)