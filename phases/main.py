import argparse
import pandas as pd
from datetime import datetime
import os
import json

from cleaner.auto_clean import auto_clean
from explain.eda_plan import gemini_generate_eda_plan
from reporter.save_report import save_final_markdown_report
from reporter.generate_report import generate_report

from .plan import plan_phase
from .retrieve import retrieve_phase
from .analyze import analyze_phase
from .respond import respond_phase

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
