import os
import json
import pandas as pd
from google import genai
from dotenv import load_dotenv
import numpy as np 
import re 
import base64 

load_dotenv()
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GENAI_API_KEY:
    print("⚠️ GEMINI_API_KEY not found. Using mocked API responses in explain.py.")
    client = None
else:
    try:
        client = genai.Client(api_key=GENAI_API_KEY)
    except Exception as e:
        print(f"⚠️ Gemini Client initialization failed: {e}. Using mocked response in explain.py.")
        client = None

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
    Finds placeholder text (**[Chart Title Chart]**) created by the LLM 
    and replaces it with a Markdown link to the file saved on disk 
    (e.g., ![Chart Title](charts/chart_title.png)).
    """
    os.makedirs(output_dir, exist_ok=True)
    
    placeholder_pattern = r'\*\*\[(.+?) Chart\]\*\*'
    
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


def _generate_gemini_response(prompt: str, json_schema: dict = None) -> dict or str:
    if not client:
        if json_schema:
             pass
        
        
        return f"""
# Comprehensive Exploratory Data Analysis Report

## Executive Summary
The analysis reveals that the average Overall Rating is 4.12.

## Univariate Analysis: Rating Distribution
The chart below visually confirms the distribution. **[Rating Count Plot (Numeric as Categorical) Chart]**

## Conclusion & Recommendations
The structured data analysis allowed us to derive specific, actionable recommendations.
"""
    
    try:
        config = {"temperature": 0}
        if json_schema:
            config["response_mime_type"] = "application/json"
            config["response_schema"] = json_schema

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=config
        )
        if json_schema:
            return json.loads(response.text)
        return response.text
    except Exception as e:
        print(f"⚠️ Gemini API call failed: {e}")
        return "ERROR: API call failed. Could not generate report."

def gemini_generate_data_prep_plan(df: pd.DataFrame) -> dict:
    """Generates the structured JSON data preparation plan."""
    sample = df.head(5).to_dict(orient="records")
    columns = list(df.columns)
    prompt = f"You are an expert data engineer. Analyze the raw dataset sample to identify critical cleaning steps. Columns: {columns}. Sample rows: {sample}..."
    schema = {
        "type": "object",
        "properties": {
            "data_prep": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "column": {"type": "string"},
                        "task": {"type": "string", "enum": ["explode", "parse_date", "convert_numeric"]},
                        "delimiter": {"type": "string", "description": "Required if task is 'explode'. Use 'NONE' for addresses."},
                        "format": {"type": "string", "description": "Required if task is 'parse_date'. E.g., '%m/%d/%y %H:%M'"},
                        "reason": {"type": "string"},
                    },
                    "required": ["column", "task", "reason"]
                }
            }
        },
        "required": ["data_prep"]
    }
    print("[Gemini] Generating Data Preparation Plan...")
    return _generate_gemini_response(prompt, json_schema=schema)


def gemini_generate_eda_plan(df: pd.DataFrame) -> dict:
    """Generates the structured JSON EDA plan."""
    sample = df.head(5).to_dict(orient="records")
    columns = list(df.columns)
    prompt = f"You are an expert data analyst. Generate a structured, actionable EDA plan for the **cleaned** dataset. Columns: {columns}. Sample rows: {sample}..."
    schema = {
        "type": "object",
        "properties": {
            "recommended_eda": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "reason": {"type": "string"},
                        "columns": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["type", "reason"]
                }
            }
        },
        "required": ["recommended_eda"]
    }
    print("[Gemini] Generating EDA Plan...")
    return _generate_gemini_response(prompt, json_schema=schema)


def gemini_generate_final_report(data_prep_plan: dict, eda_plan: dict, eda_results_markdown: str, summary_statistics: dict, output_dir: str) -> str:
    """
    Calls Gemini to generate a concise, quality-focused narrative report and then processes the chart links.
    """
    prep_plan_str = json.dumps(data_prep_plan, indent=2, default=numpy_encoder)
    eda_plan_str = json.dumps(eda_plan, indent=2, default=numpy_encoder)
    stats_str = json.dumps(summary_statistics, indent=2, default=numpy_encoder)

    prompt = f"""
You are a senior data science advisor. Your task is to write a concise, high-quality Exploratory Data Analysis (EDA) report focusing on the most important insights.

**Crucial Instruction:** Analyze the SUMMARY STATISTICS to identify key patterns, anomalies, and actionable insights. Integrate chart references (e.g., **[Chart Title Chart]**) seamlessly into the narrative. DO NOT alter bracketed text.

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
1. **Focus on Quality:** Highlight 3-5 most important insights from the data. Avoid verbosity.
2. **Integrate Charts:** Reference charts naturally where they support key points.
3. **Structure:** Use Markdown with Executive Summary, Key Insights, and Conclusion.
4. **Be Concise:** Prioritize depth over length.
"""
    print("[Gemini] Generating FINAL Narrative Report...")
    
    raw_markdown = _generate_gemini_response(prompt)
    
    return _process_markdown_and_save_charts(raw_markdown, output_dir)
