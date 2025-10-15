import argparse
import pandas as pd
from datetime import datetime
import os
import json

from cleaner import auto_clean
from explain import gemini_generate_eda_plan, gemini_generate_data_prep_plan, gemini_generate_final_report
from adaptive_eda_executor import adaptive_eda_executor
from reporter import generate_report, save_final_markdown_report

def plan_phase(df_sample):
    """Plan phase: Use Gemini to generate data prep plan and reasoning."""
    plan, confidence = gemini_generate_data_prep_plan(df_sample)
    reasoning = "Planned data preparation based on dataset sample, identifying cleaning steps."
    return plan, reasoning, confidence

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

def analyze_phase(cleaned_df, eda_plan, output_folder):
    """Analyze phase: Execute EDA and generate insights."""
    eda_results = adaptive_eda_executor(cleaned_df, eda_plan, output_dir=os.path.join(output_folder, "eda_outputs"), chart_output_dir=os.path.join(output_folder, "charts"))
    if eda_results is None:
        reasoning = "EDA execution failed."
        confidence = 0.0
        return None, reasoning, confidence

    reasoning = "Executed adaptive EDA, generating charts and summary statistics."
    confidence = 0.85
    return eda_results, reasoning, confidence

def respond_phase(data_prep_plan, eda_plan, eda_results, output_folder):
    """Respond phase: Generate final report."""
    final_report = gemini_generate_final_report(data_prep_plan, eda_plan, eda_results['markdown_with_base64'], eda_results['summary_statistics'], os.path.join(output_folder, "charts"))
    reasoning = "Generated final narrative report with insights and charts."
    confidence = 0.9
    return final_report, reasoning, confidence

def main(input_path, output_folder_name=None):
    """Runs the full data analysis pipeline with structured reasoning sequence."""

    parent_folder = "sample_outputs"

    if not output_folder_name:
        folder_name = "output_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        folder_name = output_folder_name

    output_folder = os.path.join(parent_folder, folder_name)
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(os.path.join(output_folder, "charts"), exist_ok=True)
    os.makedirs(os.path.join(output_folder, "eda_outputs"), exist_ok=True)

    reasoning_steps = []
    confidence_scores = {}

    # Retrieve Phase
    original_df, retrieve_reasoning, retrieve_conf = retrieve_phase(input_path, output_folder)
    reasoning_steps.append({"phase": "Retrieve", "reasoning": retrieve_reasoning})
    confidence_scores["Retrieve"] = retrieve_conf
    if original_df is None:
        return {"error": "Data retrieval failed."}

    # Plan Phase
    plan, plan_reasoning, plan_conf = plan_phase(original_df)
    reasoning_steps.append({"phase": "Plan", "reasoning": plan_reasoning})
    confidence_scores["Plan"] = plan_conf

    # Clean data using plan
    cleaned_df = auto_clean(original_df.copy(), plan)

    # Analyze Phase
    eda_plan, eda_conf = gemini_generate_eda_plan(cleaned_df)
    eda_results, analyze_reasoning, analyze_conf = analyze_phase(cleaned_df, eda_plan, output_folder)
    reasoning_steps.append({"phase": "Analyze", "reasoning": analyze_reasoning})
    confidence_scores["Analyze"] = analyze_conf
    if eda_results is None:
        return {"error": "Analysis failed."}

    # Respond Phase
    final_report, respond_reasoning, respond_conf = respond_phase(plan, eda_plan, eda_results, output_folder)
    reasoning_steps.append({"phase": "Respond", "reasoning": respond_reasoning})
    confidence_scores["Respond"] = respond_conf

    # Save outputs
    final_report_path = os.path.join(output_folder, "FINAL_EDA_REPORT.md")
    save_final_markdown_report(final_report, final_report_path)

    json_report_path = os.path.join(output_folder, "metadata_summary.json")
    generate_report(original_df, cleaned_df, plan, eda_plan, json_report_path)

    # Structured output
    structured_output = {
        "reasoning_steps": reasoning_steps,
        "confidence_scores": confidence_scores,
        "final_response": {
            "report_path": final_report_path,
            "summary": "Pipeline completed with structured reasoning."
        }
    }

    output_json_path = os.path.join(output_folder, "structured_output.json")
    with open(output_json_path, 'w') as f:
        json.dump(structured_output, f, indent=2)

    print(f"Structured output saved to: {output_json_path}")
    return structured_output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Data Analysis Pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to the input CSV file.")
    parser.add_argument("--output", type=str, required=False, help="Optional output folder name (will be placed inside 'sample_outputs').")
    args = parser.parse_args()

    result = main(args.input, args.output)
    print(json.dumps(result, indent=2))
