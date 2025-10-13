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

def _generate_gemini_response(prompt: str) -> dict:
    if not client:
        print("⚠️ Cannot call API because the client is not initialized.")
        return {"recommended_eda": []}

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config={
                "temperature": 0,
                "response_mime_type": "application/json",
                "response_schema": {
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
            }
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ Gemini API call failed: {e}")
        return {"recommended_eda": []}

def gemini_generate_eda_plan(df: pd.DataFrame) -> dict:
    sample = df.head(5).to_dict(orient="records")
    columns = list(df.columns)
    prompt = f"""
You are an expert data analyst. Generate a structured, actionable EDA plan for the dataset.
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
    return _generate_gemini_response(prompt)
