import pandas as pd
from .gemini import _generate_gemini_response

def gemini_generate_eda_plan(df: pd.DataFrame) -> tuple[dict, float]:
    """Generates the structured JSON EDA plan with confidence."""
    sample = df.head(5).to_dict(orient="records")
    columns = list(df.columns)
    prompt = f"You are an expert data analyst. Generate a focused, high-quality EDA plan for the **cleaned** dataset, prioritizing the most important insights over quantity. Focus on key analyses that provide the deepest understanding. Columns: {columns}. Sample rows: {sample}..."
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
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "required": ["recommended_eda", "confidence"]
    }
    print("[Gemini] Generating EDA Plan...")
    response = _generate_gemini_response(prompt, json_schema=schema)
    return response["recommended_eda"], response["confidence"]
