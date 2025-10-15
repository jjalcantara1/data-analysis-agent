import json
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GENAI_API_KEY:
    print("GEMINI_API_KEY not found. Using mocked API responses in explain.py.")
    client = None
else:
    try:
        client = genai.Client(api_key=GENAI_API_KEY)
    except Exception as e:
        print(f"Gemini Client initialization failed: {e}. Using mocked response in explain.py.")
        client = None

def _generate_gemini_response(prompt: str, json_schema: dict = None) -> dict or str:
    if not client:
        if json_schema:
            if "data_prep" in json_schema.get("properties", {}):
                return {"data_prep": [], "confidence": 0.5}
            elif "recommended_eda" in json_schema.get("properties", {}):
                return {"recommended_eda": [], "confidence": 0.5}
            else:
                return {}

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
        print(f"Gemini API call failed: {e}")
        if json_schema:
            if "data_prep" in json_schema.get("properties", {}):
                return {"data_prep": [], "confidence": 0.5}
            elif "recommended_eda" in json_schema.get("properties", {}):
                return {"recommended_eda": [], "confidence": 0.5}
            else:
                return {}
        return "ERROR: API call failed. Could not generate report."
