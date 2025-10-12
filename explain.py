import os
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found. Please add it to your .env file.")
genai.configure(api_key=api_key)


def _generate_gemini_response(prompt: str, temperature: float = 0.3) -> dict:
    """Send structured prompt to Gemini and safely parse JSON responses, including markdown-wrapped JSON."""
    try:
        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Handle wrapped JSON inside ```json ... ```
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"explanation": text, "confidence": 0.8, "reasoning_steps": []}

    except Exception as e:
        return {"error": str(e), "confidence": 0.0, "reasoning_steps": []}


def explain_eda(eda_summary: dict, dataset_name: str = "dataset") -> dict:
    prompt = f"""
You are a data analysis assistant.
Given this EDA summary from {dataset_name}:
{json.dumps(eda_summary, indent=2)}

Explain the dataset in simple terms.
Provide 3–5 key findings and 3 actionable recommendations.
Respond in JSON format:
{{
  "summary": "...",
  "key_findings": ["...", "..."],
  "recommendations": ["...", "..."],
  "confidence": 0.0 to 1.0
}}
"""
    return _generate_gemini_response(prompt)


def explain_model(model_results: dict) -> dict:
    prompt = f"""
You are an AI model evaluation assistant.
Given these model results:
{json.dumps(model_results, indent=2)}

1. Identify the best performing model and justify why.
2. Summarize strengths and weaknesses of all models.
3. Provide 2–3 recommendations for improvement.

Return JSON formatted output:
{{
  "best_model": "...",
  "analysis": "...",
  "recommendations": ["...", "..."],
  "confidence": 0.0 to 1.0
}}
"""
    return _generate_gemini_response(prompt)


# if __name__ == "__main__":
#     mock_eda = {
#         "column_types": {"numerical": ["price", "sales"], "categorical": ["region"]},
#         "summary_statistics": {"price": {"mean": 100, "std": 10}},
#         "feature_engineering_suggestions": ["Normalize price"],
#     }

#     mock_model = {
#         "task_type": "regression",
#         "models": {"RandomForestRegressor": {"R2": 0.78}, "LinearRegression": {"R2": 0.65}},
#         "best_model": {"name": "RandomForestRegressor", "R2": 0.78},
#     }

#     print("🔹 EDA Explanation:")
#     print(explain_eda(mock_eda, "Sales Data"))
#     print("\n🔹 Model Explanation:")
#     print(explain_model(mock_model))
