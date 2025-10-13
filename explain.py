import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GENAI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=GENAI_API_KEY)

def _generate_gemini_response(prompt: str) -> dict:
    """
    Calls Gemini API to generate an adaptive EDA plan.
    Returns JSON containing 'recommended_eda'.
    """
    try:
        response = genai.ChatCompletion.create(
            model="gemini-1.5",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        # Extract text from Gemini response
        text_output = response.choices[0].message.content

        return json.loads(text_output)
    except json.JSONDecodeError:
        print("⚠️ Gemini response could not be parsed, using fallback plan.")
        return {
            "recommended_eda": [
                {"type": "summary_stats", "reason": "Fallback basic summary"},
                {"type": "correlation", "reason": "Fallback correlation"},
                {"type": "category_counts", "columns": [], "reason": "Fallback top categories"}
            ]
        }
    except AttributeError as e:
        print(f"⚠️ Gemini API call failed: {e}")
        return {
            "recommended_eda": [
                {"type": "summary_stats", "reason": "Fallback basic summary"},
                {"type": "correlation", "reason": "Fallback correlation"},
                {"type": "category_counts", "columns": [], "reason": "Fallback top categories"}
            ]
        }

def gemini_generate_eda_plan(df) -> dict:
    sample = df.head(3).to_dict(orient="records")
    columns = list(df.columns)
    prompt = f"""
You are an expert data analyst.
Columns: {columns}
Sample rows: {sample}
Generate a structured EDA plan in JSON with keys 'recommended_eda'.
Each task should include 'type' and 'reason'.
"""
    return _generate_gemini_response(prompt)
