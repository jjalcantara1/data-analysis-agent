import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def execute_eda_plan(df: pd.DataFrame, eda_plan: dict) -> dict:
    results = {}
    artifacts = {}

    for task in eda_plan.get("recommended_eda", []):
        if task["type"] == "summary_stats":
            results["summary"] = df.describe(include="all").to_dict()
        elif task["type"] == "correlation":
            numeric_df = df.select_dtypes(include=[np.number])
            corr = numeric_df.corr()
            results["correlation"] = corr.to_dict()
            plt.figure(figsize=(8,6))
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm")
            heatmap_path = os.path.join("artifacts", "correlation_heatmap.png")
            plt.savefig(heatmap_path)
            plt.close()
            artifacts["correlation_heatmap"] = heatmap_path
        elif task["type"] == "category_counts":
            cols = task.get("columns", df.select_dtypes(exclude=[np.number]).columns.tolist())
            results["top_categories"] = {c: df[c].value_counts().head(5).to_dict() for c in cols}
    results["artifacts"] = artifacts
    return results
