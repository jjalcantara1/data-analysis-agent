import json
import pandas as pd
import numpy as np
import re
import os
from .gemini import _generate_gemini_response

def numpy_encoder(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, pd.Series) or isinstance(obj, pd.Index):
        return obj.tolist()
    return json.JSONEncoder.default(obj)

def _process_markdown_and_save_charts(markdown_text: str, output_dir: str) -> str:
    """
    Finds placeholder text (**[Chart Title]**) created by the LLM
    and replaces it with a Markdown link to the file saved on disk
    (e.g., ![Chart Title](charts/chart_title.png)).
    """
    os.makedirs(output_dir, exist_ok=True)

    placeholder_pattern = r'\*\*\[(.+?)\]\*\*'

    def replace_placeholder_with_link(match):
        chart_title = match.group(1).strip()

        safe_filename = re.sub(r'\W+', '_', chart_title).lower() + ".png"

        relative_path = os.path.join(os.path.basename(output_dir), safe_filename)

        return f'![{chart_title}]({relative_path})'

    cleaned_markdown = re.sub(placeholder_pattern, replace_placeholder_with_link, markdown_text)

    corrupted_base64_pattern = r'!\[.*?\]\(data:image/png;base64,.*?\)'

    def replace_corrupted_tag(match):
        return "**[Visualization File Missing - Corrupted Link]**"

    cleaned_markdown = re.sub(corrupted_base64_pattern, replace_corrupted_tag, cleaned_markdown, flags=re.S)

    note = "\n\n---\n\n**NOTE:** All charts are generated and saved as separate PNG files in the `./charts/` directory. The report refers to them by their title (e.g., ![Gender Distribution](charts/gender_distribution.png))."

    return cleaned_markdown + note

def gemini_generate_final_report(data_prep_plan: dict, eda_plan: dict, eda_results_markdown: str, summary_statistics: dict, output_dir: str) -> str:
    """
    Calls Gemini to generate a concise, quality-focused narrative report and then processes the chart links.
    """
    prep_plan_str = json.dumps(data_prep_plan, indent=2, default=numpy_encoder)
    eda_plan_str = json.dumps(eda_plan, indent=2, default=numpy_encoder)
    stats_str = json.dumps(summary_statistics, indent=2, default=numpy_encoder)

    # Extract available chart titles from eda_results_markdown
    chart_titles = re.findall(r'!\[([^\]]+)\]', eda_results_markdown)
    chart_titles_str = ', '.join(set(chart_titles))

    prompt = f"""
You are a senior data science advisor. Your task is to write a concise, high-quality Exploratory Data Analysis (EDA) report focusing on the most important insights.

**Crucial Instruction:** Analyze the SUMMARY STATISTICS to identify key patterns, anomalies, and actionable insights. For each insight, start with exactly ONE chart reference in the format **[Exact Chart Title]**, followed immediately by the explanatory paragraph. Use only the exact chart titles from the available list: {chart_titles_str}. Do not use multiple charts per insight. Structure: **[Exact Chart Title]** then paragraph. Do not alter bracketed text.

---
### INPUT DATA PREPARATION PLAN
{prep_plan_str}

### INPUT EDA PLAN
{eda_plan_str}

### INPUT SUMMARY STATISTICS (Analyze THIS DATA for key insights)
{stats_str}

### INPUT EDA EXECUTION RESULTS (Chart placeholders - DO NOT EDIT)
{eda_results_markdown}
---

**OUTPUT INSTRUCTIONS:**
1. **EDA-Only Report:** This report should contain solely the EDA. Do not include the Data Preparation Plan.
2. **EDA Plan Section:** List the EDA analyses that were actually executed, based on the key insights and charts generated. Ensure it matches exactly the executed EDA reflected in the visualizations.
3. **Focus on Quality:** Highlight most important insights from the data. Provide detailed, high-quality analysis with depth and comprehensiveness.
4. **Integrate Charts:** For each numbered insight, use exactly ONE **[Exact Chart Title]** at the start, followed by the paragraph. No multiple charts. Choose from: {chart_titles_str}.
5. **Structure:** Use Markdown with Executive Summary, EDA Plan, Key Insights (numbered), and Conclusion. Ensure clean separation: Chart, then paragraph.
6. **Be Comprehensive:** Provide thorough analysis for each insight.
7. **Strict Format:** Each insight must be: 1. **[Exact Chart Title]** Paragraph text here.
"""
    print("[Gemini] Generating FINAL Narrative Report...")

    raw_markdown = _generate_gemini_response(prompt)

    return _process_markdown_and_save_charts(raw_markdown, output_dir)
