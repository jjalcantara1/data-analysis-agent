import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
from collections import Counter

sns.set(style="whitegrid")

def adaptive_eda_executor(df: pd.DataFrame, eda_plan: dict, output_dir="eda_outputs"):
    """
    Dynamically executes EDA tasks from Gemini recommendations.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for task in eda_plan.get("recommended_eda", []):
        task_type = task["type"].lower()
        reason = task.get("reason", "")
        print(f"[Adaptive EDA] Executing: {task['type']} ({reason})")
        
        try:
            if "missing" in task_type:
                df.isna().sum().to_csv(os.path.join(output_dir, "missing_values.csv"))

            elif "duplicate" in task_type:
                df.duplicated().to_csv(os.path.join(output_dir, "duplicate_rows.csv"))

            elif "descriptive" in task_type or "summary stats" in task_type:
                numeric_cols = df.select_dtypes(include="number").columns
                df[numeric_cols].describe().to_csv(os.path.join(output_dir, "descriptive_stats.csv"))

            elif "frequency" in task_type:
                # extract column name if specified in task text
                col_candidates = re.findall(r"'(.*?)'", task["type"])
                for col in col_candidates:
                    if col in df.columns:
                        freq = df[col].value_counts()
                        freq.to_csv(os.path.join(output_dir, f"{col}_frequency.csv"))
                        plt.figure(figsize=(8, 5))
                        sns.barplot(x=freq.index, y=freq.values)
                        plt.xticks(rotation=45)
                        plt.title(f"Frequency Distribution: {col}")
                        plt.tight_layout()
                        plt.savefig(os.path.join(output_dir, f"{col}_frequency.png"))
                        plt.close()

            elif "distribution" in task_type or "histogram" in task_type or "box plot" in task_type:
                numeric_cols = df.select_dtypes(include="number").columns
                for col in numeric_cols:
                    plt.figure(figsize=(8, 5))
                    sns.histplot(df[col].dropna(), kde=True, bins=30)
                    plt.title(f"Distribution of {col}")
                    plt.tight_layout()
                    plt.savefig(os.path.join(output_dir, f"{col}_distribution.png"))
                    plt.close()

            elif "relationship" in task_type or "scatter" in task_type:
                numeric_cols = df.select_dtypes(include="number").columns
                # try to parse column names from task description
                cols = re.findall(r"'(.*?)'", task["type"])
                for i, x_col in enumerate(cols):
                    if x_col in df.columns and i+1 < len(cols) and cols[i+1] in df.columns:
                        y_col = cols[i+1]
                        plt.figure(figsize=(8, 5))
                        sns.scatterplot(x=x_col, y=y_col, data=df)
                        plt.title(f"{y_col} vs {x_col}")
                        plt.tight_layout()
                        plt.savefig(os.path.join(output_dir, f"{y_col}_vs_{x_col}.png"))
                        plt.close()

            elif "category-wise" in task_type or "box plot" in task_type:
                # extract numeric and categorical columns dynamically
                cat_cols = df.select_dtypes(include="object").columns
                num_cols = df.select_dtypes(include="number").columns
                for cat_col in cat_cols:
                    for num_col in num_cols:
                        plt.figure(figsize=(10, 5))
                        sns.boxplot(x=cat_col, y=num_col, data=df)
                        plt.xticks(rotation=45)
                        plt.title(f"{num_col} by {cat_col}")
                        plt.tight_layout()
                        plt.savefig(os.path.join(output_dir, f"{num_col}_by_{cat_col}.png"))
                        plt.close()

            elif "text analysis" in task_type:
                text_cols = df.select_dtypes(include="object").columns
                for col in text_cols:
                    all_text = " ".join(df[col].dropna().astype(str).tolist())
                    words = re.findall(r"\w+", all_text.lower())
                    counter = Counter(words)
                    most_common = counter.most_common(50)
                    pd.DataFrame(most_common, columns=["word", "count"]).to_csv(
                        os.path.join(output_dir, f"{col}_top_words.csv"), index=False
                    )
        except Exception as e:
            print(f"⚠️ Could not execute task '{task['type']}': {e}")

    print(f"[Adaptive EDA] All tasks completed. Outputs saved in: {output_dir}/")
