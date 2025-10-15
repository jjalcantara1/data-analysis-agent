import argparse
import pandas as pd
from datetime import datetime
import os

from cleaner import auto_clean
from explain import gemini_generate_eda_plan, gemini_generate_data_prep_plan, gemini_generate_final_report 
from adaptive_eda_executor import adaptive_eda_executor 
from reporter import generate_report, save_final_markdown_report 

def main(input_path, output_folder_name=None):
    """Runs the full data cleaning, EDA, and report generation pipeline."""
    
    parent_folder = "sample_outputs"
    
    if not output_folder_name:
        folder_name = "output_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        folder_name = output_folder_name
        
    output_folder = os.path.join(parent_folder, folder_name)
    output_dir_charts = os.path.join(output_folder, "charts") 
    
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(output_dir_charts, exist_ok=True) 
    print(f"--- Saving all outputs to: {output_folder} ---")

    eda_output_dir = os.path.join(output_folder, "eda_outputs") 
    
    print(f"--- 2. Loading dataset: {input_path} ---")
    try:
        original_df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}. Cannot proceed.")
        return
    
    data_prep_plan = gemini_generate_data_prep_plan(original_df.copy()) 
    cleaned_df = auto_clean(original_df.copy(), data_prep_plan)
    
    print("--- 4. Generating Gemini EDA plan from CLEANED data ---")
    eda_plan = gemini_generate_eda_plan(cleaned_df.copy())
    
    print("--- 5. Executing adaptive EDA tasks and generating initial Markdown/Statistics ---")
    
    eda_results = adaptive_eda_executor(
            cleaned_df.copy(), 
            eda_plan, 
            output_dir=eda_output_dir,
            chart_output_dir=output_dir_charts 
        )    
    if eda_results is None:
        print("\nFATAL ERROR: The adaptive_eda_executor failed to return the results dictionary.")
        return 

    eda_results_markdown = eda_results['markdown_with_base64']
    summary_statistics = eda_results['summary_statistics']

    print("--- 6. Generating FINAL NARRATIVE REPORT with Gemini ---")
    
    final_report_text = gemini_generate_final_report(
        data_prep_plan, 
        eda_plan, 
        eda_results_markdown, 
        summary_statistics, 
        output_dir_charts 
    )
    
    final_report_path = os.path.join(output_folder, "FINAL_EDA_REPORT.md")
    save_final_markdown_report(final_report_text, final_report_path)
    
    json_report_path = os.path.join(output_folder, "metadata_summary.json")
    generate_report(original_df, cleaned_df, data_prep_plan, eda_plan, json_report_path)
    
    print("\n✅ Pipeline completed successfully.")
    print(f"The final report includes file-referenced charts and is saved here: {final_report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Data Analysis Pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to the input CSV file.")
    parser.add_argument("--output", type=str, required=False, help="Optional output folder name (will be placed inside 'sample_outputs').")
    args = parser.parse_args()
    
    main(args.input, args.output)