import os
import json
import pandas as pd
from google import genai
from dotenv import load_dotenv
import numpy as np 
import re 
import base64 

# --- Gemini Client Initialization ---
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

# Helper function for NumPy JSON serialization
def numpy_encoder(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    # Handle pandas types not covered by np types
    if isinstance(obj, pd.Series) or isinstance(obj, pd.Index):
        return obj.tolist()
    return json.JSONEncoder.default(obj)

# Utility function to extract, save, and replace Base64 images
def _process_markdown_and_save_charts(markdown_text: str, output_dir: str) -> str:
    """
    Finds placeholder text (**[Chart Title Chart]**) created by the LLM 
    and replaces it with a Markdown link to the file saved on disk 
    (e.g., ![Chart Title](charts/chart_title.png)).
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # ----------------------------------------------------
    # PHASE 1: Replace clean placeholders with functional links
    # ----------------------------------------------------
    
    # Pattern to find the clean, bolded placeholder text: **[Chart Title Chart]**
    placeholder_pattern = r'\*\*\[(.+?) Chart\]\*\*'
    
    def replace_placeholder_with_link(match):
        chart_title = match.group(1).strip()
        
        # Create a safe filename that matches what the executor created
        safe_filename = re.sub(r'\W+', '_', chart_title).lower() + ".png"
        
        # Relative path from FINAL_EDA_REPORT.md (in the parent folder) to the chart file
        relative_path = os.path.join(os.path.basename(output_dir), safe_filename)
        
        # The final output: ![Chart Title](charts/chart_title.png)
        return f'![{chart_title}]({relative_path})'

    # Apply the replacement across the entire narrative
    cleaned_markdown = re.sub(placeholder_pattern, replace_placeholder_with_link, markdown_text)
    
    # ----------------------------------------------------
    # PHASE 2: Defensive Cleanup for Corrupted Base64 Tags
    # ----------------------------------------------------
    
    # This pattern catches the old corruption (which may exist in the LLM's response)
    # and replaces it with a clear error message.
    corrupted_base64_pattern = r'!\[.*?\]\(data:image/png;base64,.*?\)'
    
    def replace_corrupted_tag(match):
        return "**[Visualization File Missing - Corrupted Link]**"
        
    # Use re.S (DOTALL) flag to match across newlines in corrupted Base64 strings
    cleaned_markdown = re.sub(corrupted_base64_pattern, replace_corrupted_tag, cleaned_markdown, flags=re.S)

    # ----------------------------------------------------
    # PHASE 3: Final Output Note
    # ----------------------------------------------------
    
    note = "\n\n---\n\n**NOTE:** All charts are generated and saved as separate PNG files in the `./charts/` directory. The report refers to them by their title (e.g., ![Gender Distribution](charts/gender_distribution.png))."
    
    return cleaned_markdown + note


def _generate_gemini_response(prompt: str, json_schema: dict = None) -> dict or str:
    # ... (Keep original code, mock uses clean placeholder format) ...
    if not client:
        # --- MOCK RESPONSES (FOR OFFLINE USE) ---
        if json_schema:
             # ... (Keep json schema mocks) ...
             pass
        
        # MOCK NARRATIVE RESPONSE: Should use the clean placeholder format: **[Chart Title Chart]**
        return f"""
# Comprehensive Exploratory Data Analysis Report

## Executive Summary
The analysis reveals that the average Overall Rating is 4.12.

## Univariate Analysis: Rating Distribution
The chart below visually confirms the distribution. **[Rating Count Plot (Numeric as Categorical) Chart]**

## Conclusion & Recommendations
The structured data analysis allowed us to derive specific, actionable recommendations.
"""
    
    # --- LIVE API CALL ---
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
    Calls Gemini to generate a narrative report and then processes the chart links.
    """
    prep_plan_str = json.dumps(data_prep_plan, indent=2, default=numpy_encoder)
    eda_plan_str = json.dumps(eda_plan, indent=2, default=numpy_encoder)
    stats_str = json.dumps(summary_statistics, indent=2, default=numpy_encoder)

    prompt = f"""
You are a senior data science advisor. Your task is to write a comprehensive, professional, and narrative-style Exploratory Data Analysis (EDA) report.

**Crucial Instruction:** You must analyze the data provided in the SUMMARY STATISTICS section to form your conclusions. The charts are represented by bolded brackets, e.g., **[Gender Distribution Chart]**. Integrate these references seamlessly into your narrative by discussing them immediately before or after the bracketed title. DO NOT change the bracketed text, e.g., **[Gender Distribution Chart]**.

---
### INPUT DATA PREPARATION PLAN
{prep_plan_str}

### INPUT EDA PLAN
{eda_plan_str}

### INPUT SUMMARY STATISTICS (Analyze THIS DATA)
{stats_str}

### INPUT EDA EXECUTION RESULTS (Contains clean chart placeholders - DO NOT EDIT ANY MARKDOWN LINK SYNTAX)
{eda_results_markdown}
---

**OUTPUT INSTRUCTIONS:**
1.  **Analyze & Synthesize:** Use the actual numbers from the SUMMARY STATISTICS to drive your narrative.
2.  **Integrate Charts:** Preserve all chart placeholder text (e.g., **[Chart Title Chart]**) exactly as it appears.
3.  **Structure:** Use clear Markdown structure.
"""
    print("[Gemini] Generating FINAL Narrative Report...")
    
    # 1. Generate the raw Markdown report (which contains clean placeholders)
    raw_markdown = _generate_gemini_response(prompt)
    
    # 2. Process the raw markdown: replaces placeholder text with a functional Markdown link.
    return _process_markdown_and_save_charts(raw_markdown, output_dir)