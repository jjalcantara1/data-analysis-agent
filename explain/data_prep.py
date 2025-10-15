import pandas as pd
from .gemini import _generate_gemini_response

def gemini_generate_data_prep_plan(df: pd.DataFrame) -> tuple[dict, float]:
    """Generates the structured JSON data preparation plan with confidence."""
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
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "required": ["data_prep", "confidence"]
    }
    print("[Gemini] Generating Data Preparation Plan...")
    response = _generate_gemini_response(prompt, json_schema=schema)
    return response["data_prep"], response["confidence"]
