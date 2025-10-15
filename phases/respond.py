import os
from explain.final_report import gemini_generate_final_report

def respond_phase(data_prep_plan, eda_plan, eda_results, output_folder):
    """Respond phase: Generate final report."""
    final_report = gemini_generate_final_report(data_prep_plan, eda_plan, eda_results['markdown_with_base64'], eda_results['summary_statistics'], os.path.join(output_folder, "charts"))
    reasoning = "Generated final narrative report with insights and charts."
    confidence = 0.9
    return final_report, reasoning, confidence
