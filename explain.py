# explain.py
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
        return {
            "recommended_eda": [
                {"type": "summary_stats", "reason": "Fallback basic summary"},
                {"type": "correlation", "reason": "Fallback correlation"},
                {"type": "category_counts", "columns": [], "reason": "Fallback top categories"}
            ]
        }

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            # 🐛 FIX IS HERE: Replace 'input_text=prompt' with 'contents=[prompt]'
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
                                    "reason": {"type": "string"}
                                },
                                "required": ["type", "reason"]
                            }
                        }
                    },
                    "required": ["recommended_eda"]
                }
            }
        )

        text_output = response.text
        return json.loads(text_output)
    except Exception as e:
        print(f"⚠️ Gemini API call failed: {e}")
        return {
            "recommended_eda": [
                {"type": "summary_stats", "reason": "Fallback basic summary"},
                {"type": "correlation", "reason": "Fallback correlation"},
                {"type": "category_counts", "columns": [], "reason": "Fallback top categories"}
            ]
        }

def gemini_generate_eda_plan(df: pd.DataFrame) -> dict:
    sample = df.head(3).to_dict(orient="records")
    columns = list(df.columns)

    prompt = f"""
You are an expert data analyst.
Columns: {columns}
Sample rows: {sample}
Generate a structured EDA plan in JSON format. The top-level key must be 'recommended_eda'.
Each item in the 'recommended_eda' array must be an object with keys 'type' and 'reason'.
"""
    return _generate_gemini_response(prompt)
