import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
from collections import Counter
import numpy as np


sns.set(style="whitegrid")

def top_n_frequency(df, col, n=10, multi_sep=None):
    """Return top-N most frequent values without aggregating 'Other'."""
    if col not in df.columns:
        return pd.Series(dtype=int)
    
    series = df[col].dropna().astype(str)
    if multi_sep:
        exploded = series.str.split(multi_sep).apply(lambda x: [v.strip() for v in x]).explode()
    else:
        exploded = series
    
    counts = exploded.value_counts()
    top_counts = counts.head(n)
    return top_counts 


def adaptive_eda_executor(df: pd.DataFrame, eda_plan: dict, output_dir="eda_outputs", top_n=10):
    os.makedirs(output_dir, exist_ok=True)
    
    for task in eda_plan.get("recommended_eda", []):
        task_type = task["type"].lower()
        print(f"[Adaptive EDA] Executing: {task['type']}")
        
        try:
            # Missing values
            if "missing" in task_type:
                df.isna().sum().to_csv(os.path.join(output_dir, "missing_values.csv"))

            # Frequency / Top-N categorical
            elif "top-n" in task_type or "frequency" in task_type or "category" in task_type:
                for col in task.get("columns", []):
                    if col not in df.columns: # ⚠️ FIX: Check column existence
                        print(f"⚠️ Column '{col}' not found. Skipping Top-N analysis.")
                        continue

                    multi_sep = "," if col in ["cast", "listed_in"] else None
                    top_freq = top_n_frequency(df, col, n=top_n, multi_sep=multi_sep)
                    top_freq.to_csv(os.path.join(output_dir, f"{col}_top_{top_n}.csv"))

                    plt.figure(figsize=(8, max(4, len(top_freq)/2)))
                    sns.barplot(x=top_freq.values, y=top_freq.index, orient="h")
                    plt.title(f"Top {top_n} {col}")
                    plt.tight_layout()
                    plt.savefig(os.path.join(output_dir, f"{col}_top_{top_n}.png"))
                    plt.close()

            # Numeric distributions
            elif "distribution" in task_type or "histogram" in task_type or "box plot" in task_type:
                for col in task.get("columns", []):
                    if col not in df.columns: # ⚠️ FIX: Check column existence
                        print(f"⚠️ Column '{col}' not found. Skipping distribution analysis.")
                        continue
                        
                    numeric = pd.to_numeric(df[col], errors="coerce")
                    plt.figure(figsize=(8,5))
                    sns.histplot(numeric.dropna(), kde=True, bins=30)
                    plt.title(f"Distribution of {col}")
                    plt.tight_layout()
                    plt.savefig(os.path.join(output_dir, f"{col}_distribution.png"))
                    plt.close()

            # Scatter / relationships
            elif "relationship" in task_type or "scatter" in task_type:
                cols = task.get("columns", [])
                if len(cols) >= 2:
                    col_x, col_y = cols[0], cols[1]
                    # ⚠️ FIX: Check both columns exist before plotting
                    if col_x not in df.columns or col_y not in df.columns:
                        print(f"⚠️ Relationship skipped: Column '{col_x}' or '{col_y}' not found in data.")
                        continue
                        
                    plt.figure(figsize=(8,5))
                    sns.scatterplot(x=col_x, y=col_y, data=df)
                    plt.title(f"{col_y} vs {col_x}")
                    plt.tight_layout()
                    plt.savefig(os.path.join(output_dir, f"{col_y}_vs_{col_x}.png"))
                    plt.close()

            # Temporal / date analysis
            elif "temporal" in task_type or any("date" in c for c in task.get("columns", [])):
                for col in task.get("columns", []):
                    if col in df.columns:
                        # ⚠️ FIX: Ensure the column is actually a datetime object from the cleaning step
                        if not pd.api.types.is_datetime64_any_dtype(df[col]):
                            print(f"⚠️ Column '{col}' is not a datetime type. Skipping temporal analysis.")
                            continue
                            
                        dates = df[col].dropna()
                        if not dates.empty:
                            # Yearly trend
                            yearly_counts = dates.dt.year.value_counts().sort_index()
                            plt.figure(figsize=(10,4))
                            yearly_counts.plot(kind="bar")
                            plt.title(f"Content additions per year ({col})")
                            plt.xlabel("Year")
                            plt.ylabel("Count")
                            plt.tight_layout()
                            plt.savefig(os.path.join(output_dir, f"{col}_yearly_trend.png"))
                            plt.close()

                            # Monthly trend (seasonal pattern)
                            month_counts = dates.dt.month.value_counts().sort_index()
                            plt.figure(figsize=(10,4))
                            month_counts.plot(kind="bar")
                            plt.title(f"Content additions per month ({col})")
                            plt.xlabel("Month")
                            plt.ylabel("Count")
                            
                            # ⚠️ FIX: Dynamic Month Labels
                            MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                            
                            # Map the actual month numbers (1-12) present in the data to their names
                            present_months = month_counts.index.tolist()
                            actual_labels = [MONTH_NAMES[m - 1] for m in present_months]
                            
                            # Set the ticks to the indices (0, 1, 2...) and the labels to the month names
                            plt.xticks(ticks=range(len(present_months)), 
                                       labels=actual_labels, 
                                       rotation=45)
                                       
                            plt.tight_layout()
                            plt.savefig(os.path.join(output_dir, f"{col}_monthly_trend.png"))
                            plt.close()


            # Text analysis
            elif "text analysis" in task_type:
                for col in task.get("columns", []):
                    if col in df.columns:
                        all_text = " ".join(df[col].dropna().astype(str))
                        words = re.findall(r"\w+", all_text.lower())
                        counter = Counter(words)
                        most_common = counter.most_common(50)
                        pd.DataFrame(most_common, columns=["word","count"]).to_csv(
                            os.path.join(output_dir, f"{col}_top_words.csv"), index=False
                        )

        except Exception as e:
            print(f"⚠️ Could not execute task '{task['type']}': {e}")

    print(f"[Adaptive EDA] All tasks completed. Outputs saved in: {output_dir}/")