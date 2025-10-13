import pandas as pd
from cleaner import auto_clean
from explain import gemini_generate_eda_plan
from eda import execute_eda_plan
from reporter import generate_report
import os
from datetime import datetime

def main(input_file: str, output_dir: str = "sample_outputs"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("artifacts", exist_ok=True)

    print(f"Loading dataset: {input_file}")
    df = pd.read_csv(input_file)

    print("Cleaning dataset...")
    cleaned_df = auto_clean(df)

    print("Generating Gemini EDA plan...")
    eda_plan = gemini_generate_eda_plan(cleaned_df)

    print("Executing adaptive EDA...")
    eda_results = execute_eda_plan(cleaned_df, eda_plan)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"report_{timestamp}.json")

    print(f"Generating report: {report_path}")
    generate_report(df, cleaned_df, eda_plan, eda_results, report_path)

    print("EDA pipeline completed successfully.")

# if __name__ == "__main__":
#     import argparse
#     parser = argparse.ArgumentParser(description="Intelligent EDA Agent")
#     parser.add_argument("--input", required=True, help="Path to CSV input file")
#     parser.add_argument("--output", default="sample_outputs", help="Directory to save reports")
#     args = parser.parse_args()
#     main(args.input, args.output)
