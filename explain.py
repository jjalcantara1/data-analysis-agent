import os
import json
import pandas as pd
from google import genai
from dotenv import load_dotenv

load_dotenv()
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GENAI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

try:
    client = genai.Client(api_key=GENAI_API_KEY)
except Exception as e:
    print(f"⚠️ Gemini Client initialization failed: {e}")
    client = None

def _generate_gemini_response(prompt: str, json_schema: dict) -> dict:
    if not client:
        print("⚠️ Cannot call API because the client is not initialized.")
        # Default empty structure for robust fallback
        if "data_prep" in json_schema.get("properties", {}):
            return {"data_prep": []}
        return {"recommended_eda": []}

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config={
                "temperature": 0,
                "response_mime_type": "application/json",
                "response_schema": json_schema
            }
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ Gemini API call failed: {e}")
        # Return default empty structure on failure
        if "data_prep" in json_schema.get("properties", {}):
            return {"data_prep": []}
        return {"recommended_eda": []}

def gemini_generate_data_prep_plan(df: pd.DataFrame) -> dict:
    sample = df.head(5).to_dict(orient="records")
    columns = list(df.columns)
    prompt = f"""
You are an expert data engineer. Analyze the raw dataset sample to identify critical cleaning steps.
Columns: {columns}
Sample rows: {sample}

Identify columns that require:
1. **Multi-value Explosion**: Columns containing lists, comma-separated values (e.g., cast, genres), or columns that might appear multi-value but are single entities (like addresses). **Crucially, specify the delimiter if it's not a comma.** For addresses, specify 'NONE' as the delimiter.
2. **Date Parsing**: Columns that contain date or timestamp information (e.g., 'Order Date'). **Crucially, provide a common format if you can infer one (e.g., '%m/%d/%y %H:%M')**.
3. **Numeric Conversion**: Columns that should be numeric but are stored as strings (e.g., 'Price Each' with commas or currency symbols).

Return a JSON with a top-level key `data_prep` listing these tasks.
"""
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
    # Existing EDA plan logic remains here, ensuring it runs on the cleaned data
    # ... (content remains the same as before, only internal function call changed) ...
    sample = df.head(5).to_dict(orient="records")
    columns = list(df.columns)
    prompt = f"""
You are an expert data analyst. Generate a structured, actionable EDA plan for the **cleaned** dataset.
Columns: {columns}
Sample rows: {sample}

Guidelines:
1. Include numerical, categorical, multi-value, text, and date/time analyses.
2. Suggest Top-N for high-cardinality categorical columns.
3. Suggest distributions, correlations, and scatter plots for numerical data.
4. Include temporal analysis if date/time columns exist.
5. Include text analysis for description or free-text fields.
6. Return JSON with top-level key `recommended_eda`. Each item must include:
    - type, reason, and optionally columns.
7. Suggest insights like top directors, popular genres, common release months, or other meaningful patterns.
"""
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