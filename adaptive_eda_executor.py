import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
from collections import Counter
import numpy as np
from datetime import datetime

# Set visualization style
sns.set(style="whitegrid")

def top_n_frequency(df, col, n=10, multi_sep=None):
    """Return top-N most frequent values, handling multi-value columns if specified."""
    if col not in df.columns:
        return pd.Series(dtype=int)
    
    series = df[col].dropna().astype(str)
    if multi_sep:
        # Explode multi-value column based on delimiter
        exploded = series.str.split(multi_sep).apply(lambda x: [v.strip() for v in x]).explode()
    else:
        exploded = series
    
    counts = exploded.value_counts()
    top_counts = counts.head(n)
    return top_counts 


def adaptive_eda_executor(df: pd.DataFrame, eda_plan: dict, output_dir="eda_outputs", top_n=10):
    """
    Executes the recommended EDA plan, adapting plots based on data cardinality.
    This function incorporates fixes to suppress the seaborn FutureWarnings 
    by explicitly setting the 'hue' parameter and 'legend=False'.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # --- GLOBAL PRE-PROCESSING FOR EDA ---
    
    # 1. Feature Engineering: Derive 'Age' from 'YOB'
    if 'YOB' in df.columns:
        try:
            df['YOB_numeric'] = pd.to_numeric(df['YOB'], errors='coerce')
            current_year = 2025 # Using a fixed year for reproducible age calculation
            df['Age'] = current_year - df['YOB_numeric']
            print(f"[Feature Engineering] Derived 'Age' from 'YOB'.")
        except Exception as e:
            print(f"⚠️ Could not derive 'Age' from 'YOB': {e}")
            
    # 2. Convert known rating columns to numeric
    rating_cols = ["Food Rating", "Service Rating", "Overall Rating"]
    for col in rating_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # -------------------------------------


    for task in eda_plan.get("recommended_eda", []):
        task_type = task["type"].lower()
        print(f"[Adaptive EDA] Executing: {task['type']}")
        
        try:
            # 3. Histogram and KDE Plot (Numeric Distribution) - FIX APPLIED HERE for countplot
            if "histogram" in task_type and "kde plot" in task_type:
                for col in task.get("columns", []):
                    # Use 'Age' if 'YOB' was requested and Age exists
                    plot_col = 'Age' if col == 'YOB' and 'Age' in df.columns else col
                    
                    if plot_col not in df.columns:
                        print(f"⚠️ Column '{plot_col}' not found. Skipping numeric distribution.")
                        continue
                        
                    numeric = pd.to_numeric(df[plot_col], errors="coerce").dropna()
                    
                    if numeric.empty:
                        print(f"⚠️ Column '{plot_col}' is empty or entirely non-numeric. Skipping histogram.")
                        continue
                        
                    # FIX: If numeric column has low unique values (<10), treat as categorical (e.g., ratings 0, 1, 2)
                    if numeric.nunique() < 10 and plot_col not in ["Age", "Budget"]: 
                        print(f"ℹ️ Column '{plot_col}' has low unique numeric values. Treating as categorical countplot.")
                        plt.figure(figsize=(8,5))
                        # --- WARNING FIX: Added hue and legend=False ---
                        numeric_str = numeric.astype(str)
                        sns.countplot(
                            x=numeric_str, 
                            order=numeric_str.value_counts().index, 
                            palette="viridis",
                            hue=numeric_str,      # FIX: Explicitly set hue to the x variable
                            legend=False          # FIX: Suppress legend
                        )
                        # -----------------------------------------------
                        plt.title(f"Frequency Distribution of {plot_col}")
                        plt.xlabel(plot_col)
                        plt.ylabel("Count")
                        plt.tight_layout()
                        plt.savefig(os.path.join(output_dir, f"{plot_col}_categorical_countplot.png"))
                        plt.close()
                        continue
                        
                    # Standard Histogram/KDE plot for high cardinality numeric data (YOB/Age, Budget)
                    plt.figure(figsize=(10,6))
                    sns.histplot(numeric, kde=True, bins=min(50, numeric.nunique() if numeric.dtype != object else 20)) 
                    plt.title(f"Distribution of {plot_col}")
                    plt.xlabel(plot_col)
                    plt.ylabel("Density / Frequency")
                    plt.tight_layout()
                    plt.savefig(os.path.join(output_dir, f"{plot_col}_distribution_hist.png"))
                    plt.close()
            
            # 4. Bar Chart (Low-Cardinality Categorical Distribution) - FIX APPLIED HERE
            elif "bar chart" in task_type and "top n" not in task_type:
                for col in task.get("columns", []):
                    if col not in df.columns:
                        print(f"⚠️ Column '{col}' not found. Skipping bar chart analysis.")
                        continue
                        
                    data_to_plot = df[col].astype(str).replace('', np.nan).dropna()
                    
                    if data_to_plot.empty:
                        print(f"⚠️ Column '{col}' is empty. Skipping bar chart.")
                        continue

                    plt.figure(figsize=(8,6))
                    # --- WARNING FIX: Added hue and legend=False ---
                    sns.countplot(
                        x=data_to_plot, 
                        order=data_to_plot.value_counts().index,
                        palette="viridis",
                        hue=data_to_plot,     # FIX: Explicitly set hue to the x variable
                        legend=False          # FIX: Suppress legend
                    )
                    # -----------------------------------------------
                    plt.title(f"Frequency Distribution of {col}")
                    plt.xlabel(col)
                    plt.ylabel("Count")
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    plt.savefig(os.path.join(output_dir, f"{col}_bar_chart.png"))
                    plt.close()

            # 5. Top N Bar Chart (High-Cardinality/Explodable Categorical) - FIX APPLIED HERE
            elif "top n bar chart" in task_type:
                for col in task.get("columns", []):
                    if col not in df.columns:
                        print(f"⚠️ Column '{col}' not found. Skipping Top-N analysis.")
                        continue
                        
                    # Cuisines is likely a multi-value column
                    multi_sep = "," if col == "Cuisines" else None 
                    
                    top_freq = top_n_frequency(df, col, n=top_n, multi_sep=multi_sep)
                    
                    if top_freq.empty:
                        print(f"⚠️ Top-N analysis skipped for '{col}': No data found.")
                        continue
                        
                    top_freq.to_csv(os.path.join(output_dir, f"{col}_top_{top_n}_frequency.csv"))

                    plt.figure(figsize=(8, max(4, len(top_freq)/2)))
                    # --- WARNING FIX: Added hue and legend=False (y-variable for horizontal) ---
                    sns.barplot(
                        x=top_freq.values, 
                        y=top_freq.index, 
                        orient="h", 
                        palette="magma",
                        hue=top_freq.index,    # FIX: Explicitly set hue to the y variable (index)
                        legend=False           # FIX: Suppress legend
                    )
                    # ---------------------------------------------------------------------------
                    plt.title(f"Top {top_n} Most Frequent {col}")
                    plt.xlabel("Count")
                    plt.ylabel(col)
                    plt.tight_layout()
                    plt.savefig(os.path.join(output_dir, f"{col}_top_{top_n}_frequency.png"))
                    plt.close()
            
            # 6. Correlation Heatmap (No warning to fix)
            elif "correlation heatmap" in task_type:
                cols = task.get("columns", [])
                
                # Check for 'Age' and replace 'YOB' in the list of columns to plot
                final_cols = list(cols)
                if 'Age' in df.columns and 'YOB' in final_cols:
                    final_cols.remove('YOB')
                    final_cols.append('Age')
                
                plot_df = df[final_cols].apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna()
                
                if plot_df.shape[0] < 2:
                    print("⚠️ Correlation skipped: Not enough numeric data points after cleaning.")
                    continue
                    
                corr_matrix = plot_df.corr()
                
                plt.figure(figsize=(10, 8))
                sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='coolwarm', linewidths=.5, linecolor='black')
                plt.title("Correlation Heatmap of Key Numerical Features")
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, "correlation_heatmap.png"))
                plt.close()
            
            # 7. Box Plot / Violin Plot (Categorical vs. Numerical) - FIX APPLIED HERE
            elif "box plot" in task_type or "violin plot" in task_type:
                cols = task.get("columns", [])
                
                rating_cols = ["Food Rating", "Service Rating", "Overall Rating"]
                categorical_cols = [c for c in cols if c not in rating_cols and c in df.columns]
                
                for cat_col in categorical_cols:
                    for num_col in rating_cols:
                        if num_col in df.columns:
                            plot_data = df.dropna(subset=[num_col, cat_col]).copy()
                            
                            if plot_data.empty:
                                continue

                            plt.figure(figsize=(8, 6))
                            # --- WARNING FIX: Added hue and legend=False ---
                            sns.boxplot(
                                x=cat_col, 
                                y=num_col, 
                                data=plot_data, 
                                palette="Pastel1",
                                hue=cat_col,         # FIX: Explicitly set hue to the x variable
                                legend=False         # FIX: Suppress legend
                            )
                            # -----------------------------------------------
                            plt.title(f"Distribution of {num_col} by {cat_col}")
                            plt.xlabel(cat_col)
                            plt.ylabel(num_col)
                            plt.xticks(rotation=45, ha='right')
                            plt.tight_layout()
                            plt.savefig(os.path.join(output_dir, f"{cat_col}_vs_{num_col}_boxplot.png"))
                            plt.close()
            
            # 8. Grouped Bar Chart (Mean/Median) - FIX APPLIED HERE
            elif "grouped bar chart" in task_type:
                cols = task.get("columns", [])
                
                if "Overall Rating" in cols:
                    target_col = "Overall Rating"
                    feature_cols = [c for c in cols if c != target_col and c in df.columns]
                    
                    for feat_col in feature_cols:
                        # Top N categories only for cleaner plot
                        top_categories = df[feat_col].value_counts().head(top_n).index.tolist()
                        plot_df = df[df[feat_col].isin(top_categories)].copy()
                        
                        mean_ratings = plot_df.groupby(feat_col)[target_col].mean().sort_values(ascending=False)
                        
                        if mean_ratings.empty:
                            print(f"⚠️ Grouped Bar Chart skipped for '{feat_col}': No valid data points.")
                            continue
                            
                        plt.figure(figsize=(10, max(6, len(mean_ratings)/2)))
                        # --- WARNING FIX: Added hue and legend=False (y-variable for horizontal) ---
                        sns.barplot(
                            x=mean_ratings.values, 
                            y=mean_ratings.index, 
                            orient="h", 
                            palette="coolwarm",
                            hue=mean_ratings.index,   # FIX: Explicitly set hue to the y variable (index)
                            legend=False              # FIX: Suppress legend
                        )
                        # ---------------------------------------------------------------------------
                        plt.title(f"Average {target_col} by Top {top_n} {feat_col}")
                        plt.xlabel(f"Average {target_col}")
                        plt.ylabel(feat_col)
                        plt.tight_layout()
                        plt.savefig(os.path.join(output_dir, f"{feat_col}_vs_{target_col}_avg_rating.png"))
                        plt.close()
            
            # 10. Scatter Plot / Grouped Box Plot (Age Bins) - FIX APPLIED HERE for boxplot
            elif "age bins" in task_type:
                if 'Age' in df.columns and "Budget" in df.columns and "Overall Rating" in df.columns:
                    # Create Age Bins
                    age_bins = pd.cut(df['Age'], bins=[10, 20, 30, 40, 50, 60, 100], 
                                     labels=['10-19', '20-29', '30-39', '40-49', '50-59', '60+'], right=False)
                    df['Age_Group'] = age_bins
                    
                    # Grouped Box Plot: Age_Group vs Overall Rating
                    plot_data_rating = df.dropna(subset=['Age_Group', 'Overall Rating'])
                    if not plot_data_rating.empty:
                        plt.figure(figsize=(10, 6))
                        # --- WARNING FIX: Added hue and legend=False ---
                        sns.boxplot(
                            x='Age_Group', 
                            y='Overall Rating', 
                            data=plot_data_rating, 
                            palette="Pastel2",
                            hue='Age_Group',       # FIX: Explicitly set hue to the x variable
                            legend=False           # FIX: Suppress legend
                        )
                        # -----------------------------------------------
                        plt.title("Overall Rating Distribution by Age Group")
                        plt.xlabel("Age Group")
                        plt.ylabel("Overall Rating")
                        plt.tight_layout()
                        plt.savefig(os.path.join(output_dir, "Age_Group_vs_Overall_Rating_boxplot.png"))
                        plt.close()
                        
                    # Grouped Bar Plot: Age_Group vs Budget (Assuming Budget is categorical)
                    budget_data = df.dropna(subset=['Age_Group', 'Budget'])
                    if budget_data['Budget'].dtype == object or budget_data['Budget'].nunique() < 10: 
                        plt.figure(figsize=(10, 6))
                        sns.countplot(x='Age_Group', hue='Budget', 
                                      data=budget_data, 
                                      order=df['Age_Group'].cat.categories,
                                      palette="tab10")
                        plt.title("Budget Distribution by Age Group")
                        plt.xlabel("Age Group")
                        plt.ylabel("Count")
                        plt.xticks(rotation=45, ha='right')
                        plt.tight_layout()
                        plt.savefig(os.path.join(output_dir, "Age_Group_vs_Budget_countplot.png"))
                        plt.close()
                    else:
                        # Fallback to scatter plot if Budget is numeric
                        plot_data_budget_numeric = df.dropna(subset=['Age', 'Budget'])
                        if not plot_data_budget_numeric.empty:
                            plt.figure(figsize=(10, 6))
                            sns.regplot(x='Age', y='Budget', data=plot_data_budget_numeric, scatter_kws={'alpha':0.3})
                            plt.title("Age vs Budget (Scatter with Regression Line)")
                            plt.xlabel("Age")
                            plt.ylabel("Budget")
                            plt.tight_layout()
                            plt.savefig(os.path.join(output_dir, "Age_vs_Budget_regplot.png"))
                            plt.close()
                else:
                    print("⚠️ Age Bins Analysis skipped: Required columns ('Age', 'Budget', 'Overall Rating') not available.")


            # Skip unneeded/non-applicable tasks explicitly
            elif "temporal" in task_type or "text analysis" in task_type or "multi-value" in task_type:
                 print(f"[Adaptive EDA] Skipping {task['type']} as columns are not applicable (as per plan).")
                 continue
                 

        except Exception as e:
            print(f"⚠️ Could not execute task '{task['type']}': {e}")

    print(f"[Adaptive EDA] All tasks completed. Outputs saved in: {output_dir}/")
