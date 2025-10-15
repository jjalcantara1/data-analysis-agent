import os
from adaptive_eda_executor.adaptive_eda_executor import adaptive_eda_executor

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
