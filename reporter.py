import json
import pandas as pd
from eda import perform_eda
from preprocess import detect_target_column, preprocess_data
from auto_model import train_models
from explain import explain_eda, explain_model


def generate_report(df: pd.DataFrame, dataset_name: str = "dataset") -> dict:
    """Run full hybrid pipeline: EDA → Modeling → Explanations → Structured report."""
    
    print("🔍 Running EDA...")
    eda_summary = perform_eda(df)
    eda_explanation = explain_eda(eda_summary, dataset_name)

    print("🤖 Training models...")
    target_info = detect_target_column(df)
    prep = preprocess_data(df, target_info["target"])
    model_results = train_models(
        prep["X_train"], prep["X_test"], prep["y_train"], prep["y_test"], prep["task_type"]
    )

    model_explanation = explain_model(model_results)

    report = {
        "dataset_name": dataset_name,
        "target_column": target_info["target"],
        "task_type": prep["task_type"],
        "eda_summary": eda_summary,
        "eda_explanation": eda_explanation,
        "model_results": model_results,
        "model_explanation": model_explanation,
    }

    return report


def print_report_summary(report: dict):
    """Print key findings in a readable format."""
    print("\n🧾 ===== FINAL REPORT SUMMARY =====")
    print(f"📊 Dataset: {report['dataset_name']}")
    print(f"🎯 Target: {report['target_column']}")
    print(f"🧠 Task Type: {report['task_type']}")
    
    print("\n🔹 EDA Summary:")
    print(report['eda_explanation'].get("summary", "N/A"))

    print("\n🔹 Key Findings:")
    for f in report['eda_explanation'].get("key_findings", []):
        print(f" - {f}")

    print("\n🔹 Model Insights:")
    print(report['model_explanation'].get("analysis", report['model_explanation'].get("explanation", "N/A")))

    print("\n🔹 Recommendations:")
    for r in report['model_explanation'].get("recommendations", []):
        print(f" - {r}")

    print("\nConfidence Scores:")
    print(f"EDA: {report['eda_explanation'].get('confidence', 'N/A')}")
    print(f"Model: {report['model_explanation'].get('confidence', 'N/A')}")


# if __name__ == "__main__":
#     import numpy as np

#     df_test = pd.DataFrame({
#         "price": np.random.normal(100, 15, 200),
#         "sales": np.random.normal(500, 80, 200),
#         "discount": np.random.uniform(0, 0.3, 200),
#         "region": np.random.choice(["north", "south", "east", "west"], 200)
#     })

#     final_report = generate_report(df_test, "Sales Data")
#     print_report_summary(final_report)

#     with open("final_report.json", "w", encoding="utf-8") as f:
#         json.dump(final_report, f, indent=2)
#     print("\n Report saved as final_report.json")
