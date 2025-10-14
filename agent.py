import argparse
import pandas as pd
from datetime import datetime
import os

# Assuming these files exist in the same directory:
from cleaner import auto_clean
from explain import gemini_generate_eda_plan, gemini_generate_data_prep_plan, gemini_generate_final_report 
from adaptive_eda_executor import adaptive_eda_executor 
from reporter import generate_report, save_final_markdown_report 

def main(input_path, output_folder_name=None):
    """Runs the full data cleaning, EDA, and report generation pipeline."""
    
    # --- 1. Output Folder Setup ---
    parent_folder = "sample_outputs"
    
    if not output_folder_name:
        folder_name = "output_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        folder_name = output_folder_name
        
    output_folder = os.path.join(parent_folder, folder_name)
    output_dir_charts = os.path.join(output_folder, "charts") # Separate folder for extracted charts
    
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(output_dir_charts, exist_ok=True) # Ensure chart directory exists
    print(f"--- Saving all outputs to: {output_folder} ---")

    eda_output_dir = os.path.join(output_folder, "eda_outputs") # Log folder, charts are saved to output_dir_charts
    
    print(f"--- 2. Loading dataset: {input_path} ---")
    try:
        original_df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}. Cannot proceed.")
        return
    
    # 3. Generate and Execute Data Prep Plan (Cleaning)
    data_prep_plan = gemini_generate_data_prep_plan(original_df.copy()) 
    cleaned_df = auto_clean(original_df.copy(), data_prep_plan)
    
    # 4. Generate EDA Plan
    print("--- 4. Generating Gemini EDA plan from CLEANED data ---")
    eda_plan = gemini_generate_eda_plan(cleaned_df.copy())
    
    # 5. Execute Adaptive EDA and Get Data/Base64 Charts
    print("--- 5. Executing adaptive EDA tasks and generating initial Markdown/Statistics ---")
    
    # adaptive_eda_executor returns: {'markdown_with_base64', 'summary_statistics'}
    eda_results = adaptive_eda_executor(
            cleaned_df.copy(), 
            eda_plan, 
            output_dir=eda_output_dir,
            chart_output_dir=output_dir_charts # NEW ARGUMENT
        )    
    if eda_results is None:
        print("\nFATAL ERROR: The adaptive_eda_executor failed to return the results dictionary.")
        return 

    eda_results_markdown = eda_results['markdown_with_base64']
    summary_statistics = eda_results['summary_statistics']

    # 6. Generate Final Narrative Report using Gemini (Passes statistics for analysis)
    print("--- 6. Generating FINAL NARRATIVE REPORT with Gemini ---")
    
    # NOTE: The output_dir_charts is passed here, where the Base64 images will be saved as PNG files
    final_report_text = gemini_generate_final_report(
        data_prep_plan, 
        eda_plan, 
        eda_results_markdown, 
        summary_statistics, 
        output_dir_charts 
    )
    
    # 7. Save the final narrative report (now contains file path references)
    final_report_path = os.path.join(output_folder, "FINAL_EDA_REPORT.md")
    save_final_markdown_report(final_report_text, final_report_path)
    
    # 8. Generate structured JSON report (metadata summary)
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