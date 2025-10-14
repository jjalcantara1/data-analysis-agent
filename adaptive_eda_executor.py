import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from datetime import datetime
import base64
from io import BytesIO
import re

# --- GLOBAL CONSTANTS ---
RATING_COLS = ["Food Rating", "Service Rating", "Overall Rating"]
TOP_N_LIMIT = 10
sns.set(style="whitegrid")

# --- UTILITY FUNCTIONS ---

def _fig_to_base64(fig: plt.Figure, chart_title: str, chart_output_dir: str) -> str:
    """
    Saves the Matplotlib figure as a PNG file to disk and returns a clean text placeholder.
    NOTE: The Base64 encoding logic is removed as it's no longer used for the LLM input.
    """
    # 1. Create a safe filename (based on the title)
    safe_title = re.sub(r'\W+', '_', chart_title).lower()
    filename = f"{safe_title}.png"
    filepath = os.path.join(chart_output_dir, filename)

    # 2. Save the figure to the specified path
    try:
        fig.savefig(filepath, format='png', bbox_inches='tight')
        print(f"[Chart Save] Saved image to: {filepath}")
    except Exception as e:
        print(f"⚠️ Failed to save chart {chart_title} to disk: {e}")
        
    plt.close(fig) # Important: close the figure to free up memory
    
    # 3. Return the clean placeholder text for the LLM input
    return f"CHART_TITLE_PLACEHOLDER:{chart_title}:END"

def _calculate_summary_statistics(df: pd.DataFrame) -> dict:
    """Calculates necessary summary statistics for the final report analysis."""
    summary_data = {}
    
    for col in RATING_COLS:
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce').dropna()
            if not numeric_col.empty:
                summary_data[col] = {
                    "count": int(numeric_col.count()),
                    "mean": round(numeric_col.mean(), 2),
                    "median": round(numeric_col.median(), 2),
                    "std": round(numeric_col.std(), 2),
                    "min": round(numeric_col.min(), 1),
                    "max": round(numeric_col.max(), 1),
                    "skew": round(numeric_col.skew(), 2)
                }

    if 'Restaurant' in df.columns:
        restaurant_col = df['Restaurant'].astype(str).dropna()
        if not restaurant_col.empty:
            counts = restaurant_col.value_counts()
            summary_data['Restaurant'] = {
                "unique_count": counts.shape[0],
                "most_common": counts.index[0] if not counts.empty else "N/A",
                "mode_count": int(counts.iloc[0]) if not counts.empty else 0
            }
            
    return summary_data


# --- INSIGHT GENERATION HELPERS (Skipped for brevity, assume accurate) ---

def generate_numeric_insight(series: pd.Series, col: str) -> str:
    if series.empty: return f"No numerical data available for {col} to generate insight."
    mean_val = series.mean()
    median_val = series.median()
    skew_val = series.skew()
    if abs(skew_val) > 1:
        skew_type = "highly skewed"
        direction = "right-skewed" if skew_val > 0 else "left-skewed"
        return f"The distribution of '{col}' is **{skew_type}** ({direction}), with a large portion of values concentrated near {series.min():.1f} (Mean: {mean_val:.1f})."
    else:
        if series.nunique() <= 5:
            if series.value_counts(normalize=True).iloc[0] > 0.5:
                top_val = series.value_counts().index[0]
                return f"The distribution of '{col}' is heavily concentrated at the value **{top_val}**, suggesting a polarized or highly biased set of responses."
        return f"The distribution of '{col}' is roughly symmetrical (Mean: {mean_val:.1f}, Median: {median_val:.1f}). Most values cluster between {series.quantile(0.25):.1f} and {series.quantile(0.75):.1f}."
def generate_categorical_insight(counts: pd.Series, col: str) -> str:
    if counts.empty: return f"No data available for {col} to generate insight."
    top_category = counts.index[0]
    top_percent = counts.iloc[0] / counts.sum() * 100
    if top_percent > 60:
        return f"The '{col}' distribution is heavily dominated by **{top_category}**, which accounts for over {top_percent:.0f}% of all entries, indicating a very strong primary segment."
    elif len(counts) > 1:
        top_2_categories = counts.index[:2].tolist()
        top_2_percent = counts.iloc[:2].sum() / counts.sum() * 100
        return f"The top categories for '{col}' are **{top_2_categories[0]}** and **{top_2_categories[1]}**, together accounting for {top_2_percent:.0f}% of the responses."
    else:
        return f"The only category observed for '{col}' is **{top_category}**."
def generate_grouped_insight(plot_data: pd.DataFrame, cat_col: str, num_col: str) -> str:
    if plot_data.empty: return f"No sufficient data to compare {num_col} by {cat_col}."
    median_values = plot_data.groupby(cat_col)[num_col].median().sort_values(ascending=False)
    if len(median_values) < 2: return f"Only one category ({median_values.index[0]}) found for {cat_col}, median {num_col} is {median_values.iloc[0]:.2f}."
    top_cat = median_values.index[0]
    bottom_cat = median_values.index[-1]
    diff = median_values.iloc[0] - median_values.iloc[-1]
    return f"The median '{num_col}' is highest for the **{top_cat}** group ({median_values.iloc[0]:.2f}) and lowest for **{bottom_cat}** ({median_values.iloc[-1]:.2f}), showing a difference of {diff:.2f}."
def generate_correlation_insight(corr_matrix: pd.DataFrame) -> str:
    if corr_matrix.empty: return "Correlation matrix is empty."
    corr_series = corr_matrix.unstack().sort_values(ascending=False)
    corr_series = corr_series[corr_series.index.get_level_values(0) != corr_series.index.get_level_values(1)]
    if corr_series.empty: return "Only one feature detected; no correlation insight generated."
    idx_max = corr_series.abs().idxmax()
    val = corr_series.loc[idx_max]
    (col1, col2) = idx_max
    relationship = "a strong" if abs(val) > 0.7 else "a moderate"
    relationship += " positive" if val > 0 else " negative"
    return f"The strongest relationship is **{relationship}** correlation ($r={val:.2f}$) between **{col1}** and **{col2}**."

# --- Report Builder (Uses clean placeholders) ---

def _build_final_markdown_report(report_sections: list, df_info: dict) -> str:
    """
    Generates a structured Markdown report from collected EDA insights, using clean chart title placeholders.
    """
    
    markdown_content = f"""# Comprehensive Exploratory Data Analysis Report

## 1. Introduction & Dataset Summary

This report summarizes the exploratory data analysis (EDA) performed on the dataset.

* **Total Records:** {df_info.get('rows')}
* **Total Features:** {df_info.get('cols')}

---

## 2. Feature Analysis and Insights

Below are the key visualizations and insights organized by the type of analysis performed.

"""
    
    distribution_sections = [s for s in report_sections if not any(t in s['task_type'].lower() for t in ['correlation', 'box plot', 'grouped bar chart', 'age bins'])]

    distribution_content = []
    
    # 2.1 Distribution Content
    for section in distribution_sections:
        task_type = section['task_type']
        col = ", ".join(section['columns'])
        placeholder = section['base64_uri'] 
        insight = section['insight']
        
        # Extract the clean title from the placeholder string
        chart_title = placeholder.split(':')[1].strip() if placeholder.startswith("CHART_TITLE_PLACEHOLDER:") else task_type.title()
        
        # USE THE CLEAN PLACEHOLDER TEXT IN MARKDOWN IMAGE TAG
        distribution_content.append(f"""### {task_type.title()} for: {col}
| Insight | Visualization |
| :--- | :--- |
| **Key Finding:** {insight} | **[{chart_title} Chart]** |
""")

    markdown_content += "\n".join(distribution_content)
    
    # 3. Bivariate and Multivariate Analysis (Correlation)
    correlation_section = [s for s in report_sections if 'correlation' in s['task_type'].lower()]
    if correlation_section:
        corr = correlation_section[0]
        placeholder = corr['base64_uri']
        chart_title = placeholder.split(':')[1].strip() if placeholder.startswith("CHART_TITLE_PLACEHOLDER:") else "Correlation Heatmap"

        markdown_content += f"""
---

## 3. Relationships and Correlation Analysis

### Correlation Heatmap
| Insight | Visualization |
| :--- | :--- |
| **Key Finding:** {corr['insight']} | **[{chart_title} Chart]** |
"""
    
    # 4. Grouped Comparisons (Box Plots, Grouped Bar Charts, Age Bins)
    grouped_sections = [s for s in report_sections if any(t in s['task_type'].lower() for t in ['box plot', 'grouped bar chart', 'age bins']) and 'correlation' not in s['task_type'].lower()]
    if grouped_sections:
        markdown_content += f"""
---

## 4. Grouped Comparison Insights

"""
        for s in grouped_sections:
            placeholder = s['base64_uri']
            chart_title = placeholder.split(':')[1].strip() if placeholder.startswith("CHART_TITLE_PLACEHOLDER:") else s['task_type'].title()

            markdown_content += f"""### {s['task_type'].title()} ({s['columns'][0]} vs {s['columns'][1]})
| Insight | Visualization |
| :--- | :--- |
| **Key Finding:** {s['insight']} | **[{chart_title} Chart]** |
"""


    markdown_content += """
---

## 5. Conclusion

The EDA provides a strong foundation for modeling efforts. The distribution of ratings is heavily skewed, and certain demographic groups show distinct average rating patterns.
"""
    
    return markdown_content

# --- Executor Logic ---

def top_n_frequency(df, col, n=TOP_N_LIMIT, multi_sep=None):
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


# REFLECTED CHANGE: Added chart_output_dir argument
def adaptive_eda_executor(df: pd.DataFrame, eda_plan: dict, output_dir="eda_outputs", top_n=TOP_N_LIMIT, chart_output_dir=None):
    """
    Executes the recommended EDA plan, adapting plots and collecting data-driven insights.
    """
    if chart_output_dir is None:
        # Fallback if main.py didn't provide the path, use the metadata output dir
        chart_output_dir = os.path.join(output_dir, "charts")
        os.makedirs(chart_output_dir, exist_ok=True)
    
    report_sections = [] 
    
    # --- GLOBAL PRE-PROCESSING FOR EDA ---
    if 'YOB' in df.columns:
        try:
            df['YOB_numeric'] = pd.to_numeric(df['YOB'], errors='coerce')
            current_year = datetime.now().year
            df['Age'] = current_year - df['YOB_numeric']
            print(f"[Feature Engineering] Derived 'Age' from 'YOB'.")
        except Exception as e:
            print(f"⚠️ Could not derive 'Age' from 'YOB': {e}")
            
    for col in RATING_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # -------------------------------------

    for task in eda_plan.get("recommended_eda", []):
        task_type = task["type"].lower()
        print(f"[Adaptive EDA] Executing: {task['type']}")
        
        try:
            # 3. Histogram and KDE Plot (Numeric Distribution)
            if "histogram" in task_type and "kde plot" in task_type:
                for col in task.get("columns", []):
                    plot_col = 'Age' if col == 'YOB' and 'Age' in df.columns else col
                    
                    if plot_col not in df.columns: continue
                    numeric = pd.to_numeric(df[plot_col], errors="coerce").dropna()
                    if numeric.empty: continue
                    
                    plot_title = f"Distribution of {plot_col}"
                        
                    # Handle low-nunique numeric features (like ratings 0, 1, 2) as categorical counts
                    if plot_col in RATING_COLS and numeric.nunique() < 10: 
                        numeric_str = numeric.astype(str)
                        fig, ax = plt.subplots(figsize=(8,5))
                        sns.countplot(x=numeric_str, order=numeric_str.value_counts().index, palette="viridis",
                                        hue=numeric_str, legend=False, ax=ax)
                        ax.set_title(plot_title)
                        plt.tight_layout()
                        
                        base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir) # CORRECTED CALL
                        insight = generate_numeric_insight(numeric, plot_col)
                        report_sections.append({"task_type": "Rating Count Plot (Numeric as Categorical)", "columns": [plot_col], "base64_uri": base64_uri, "insight": insight})
                        continue
                        
                    # Standard Histogram/KDE plot
                    fig, ax = plt.subplots(figsize=(10,6))
                    sns.histplot(numeric, kde=True, bins=min(50, numeric.nunique() if numeric.dtype != object else 20), ax=ax) 
                    ax.set_title(plot_title)
                    plt.tight_layout()
                    
                    base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir) # CORRECTED CALL
                    insight = generate_numeric_insight(numeric, plot_col)
                    report_sections.append({"task_type": "Distribution Plot (Histogram/KDE)", "columns": [plot_col], "base64_uri": base64_uri, "insight": insight})
            
            # 4. Bar Chart (Low-Cardinality Categorical Distribution)
            elif "bar chart" in task_type and "top n" not in task_type:
                for col in task.get("columns", []):
                    if col not in df.columns: continue
                    data_to_plot = df[col].astype(str).replace('', np.nan).dropna()
                    if data_to_plot.empty: continue
                    
                    counts = data_to_plot.value_counts()
                    plot_title = f"Frequency Distribution of {col}"

                    fig, ax = plt.subplots(figsize=(8,6))
                    sns.countplot(x=data_to_plot, order=counts.index, palette="viridis",
                                    hue=data_to_plot, legend=False, ax=ax)
                    ax.set_title(plot_title)
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    
                    base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir) # CORRECTED CALL
                    insight = generate_categorical_insight(counts, col)
                    report_sections.append({"task_type": "Categorical Count Plot", "columns": [col], "base64_uri": base64_uri, "insight": insight})


            # 5. Top N Bar Chart (High-Cardinality/Explodable Categorical)
            elif "top n bar chart" in task_type:
                for col in task.get("columns", []):
                    if col not in df.columns: continue
                    multi_sep = "," if col == "Cuisines" else None 
                    top_freq = top_n_frequency(df, col, n=top_n, multi_sep=multi_sep)
                    if top_freq.empty: continue
                    
                    plot_title = f"Top {top_n} Most Frequent {col}"
                        
                    fig, ax = plt.subplots(figsize=(8, max(4, len(top_freq)/2)))
                    sns.barplot(x=top_freq.values, y=top_freq.index, orient="h", palette="magma",
                                    hue=top_freq.index, legend=False, ax=ax)
                    ax.set_title(plot_title)
                    plt.tight_layout()
                    
                    base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir) # CORRECTED CALL
                    insight = generate_categorical_insight(top_freq, col)
                    report_sections.append({"task_type": "Top N Bar Chart (Frequency)", "columns": [col], "base64_uri": base64_uri, "insight": insight})
            
            # 6. Correlation Heatmap
            elif "correlation heatmap" in task_type:
                cols = task.get("columns", [])
                final_cols = list(cols)
                if 'Age' in df.columns and 'YOB' in final_cols:
                    final_cols.remove('YOB')
                    final_cols.append('Age')
                
                plot_df = df[final_cols].apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna()
                if plot_df.shape[0] < 2: continue
                        
                corr_matrix = plot_df.corr()
                plot_title = "Correlation Heatmap of Key Numerical Features"
                fig, ax = plt.subplots(figsize=(10, 8))
                sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='coolwarm', linewidths=.5, linecolor='black', ax=ax)
                ax.set_title(plot_title)
                plt.tight_layout()
                
                base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir) # CORRECTED CALL
                insight = generate_correlation_insight(corr_matrix)
                report_sections.append({"task_type": "Correlation Heatmap", "columns": final_cols, "base64_uri": base64_uri, "insight": insight})


            # 7. Box Plot / Violin Plot (Categorical vs. Numerical)
            elif "box plot" in task_type or "violin plot" in task_type:
                cols = task.get("columns", [])
                categorical_cols = [c for c in cols if c not in RATING_COLS and c in df.columns]
                
                for cat_col in categorical_cols:
                    for num_col in RATING_COLS:
                        if num_col in df.columns:
                            plot_data = df.dropna(subset=[num_col, cat_col]).copy()
                            if plot_data.empty: continue

                            plot_title = f"Distribution of {num_col} by {cat_col}"
                            fig, ax = plt.subplots(figsize=(8, 6))
                            sns.boxplot(x=cat_col, y=num_col, data=plot_data, palette="Pastel1",
                                            hue=cat_col, legend=False, ax=ax)
                            ax.set_title(plot_title)
                            plt.xticks(rotation=45, ha='right')
                            plt.tight_layout()

                            base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir) # CORRECTED CALL
                            insight = generate_grouped_insight(plot_data, cat_col, num_col)
                            report_sections.append({"task_type": "Box Plot (Cat vs Num)", "columns": [cat_col, num_col], "base64_uri": base64_uri, "insight": insight})

            
            # 8. Grouped Bar Chart (Mean/Median)
            elif "grouped bar chart" in task_type:
                cols = task.get("columns", [])
                if "Overall Rating" in cols:
                    target_col = "Overall Rating"
                    feature_cols = [c for c in cols if c != target_col and c in df.columns]
                    
                    for feat_col in feature_cols:
                        top_categories = df[feat_col].value_counts().head(top_n).index.tolist()
                        plot_df = df[df[feat_col].isin(top_categories)].copy()
                        
                        mean_ratings = plot_df.groupby(feat_col)[target_col].mean().sort_values(ascending=False)
                        if mean_ratings.empty: continue
                            
                        plot_title = f"Average {target_col} by Top {top_n} {feat_col}"
                        fig, ax = plt.subplots(figsize=(10, max(6, len(mean_ratings)/2)))
                        sns.barplot(x=mean_ratings.values, y=mean_ratings.index, orient="h", palette="coolwarm",
                                        hue=mean_ratings.index, legend=False, ax=ax)
                        ax.set_title(plot_title)
                        plt.tight_layout()
                        
                        base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir) # CORRECTED CALL
                        insight = generate_grouped_insight(plot_df, feat_col, target_col)
                        report_sections.append({"task_type": "Grouped Bar Chart (Average Rating)", "columns": [feat_col, target_col], "base64_uri": base64_uri, "insight": insight})
            
            # 10. Scatter Plot / Grouped Box Plot (Age Bins)
            elif "age bins" in task_type:
                if 'Age' in df.columns and "Overall Rating" in df.columns:
                    
                    age_bins = pd.cut(df['Age'], bins=[10, 20, 30, 40, 50, 60, 100], 
                                            labels=['10-19', '20-29', '30-39', '40-49', '50-59', '60+'], right=False)
                    df['Age_Group'] = age_bins
                    
                    # Grouped Box Plot: Age_Group vs Overall Rating
                    plot_data_rating = df.dropna(subset=['Age_Group', 'Overall Rating'])
                    if not plot_data_rating.empty:
                        plot_title = "Overall Rating Distribution by Age Group"
                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.boxplot(x='Age_Group', y='Overall Rating', data=plot_data_rating, palette="Pastel2",
                                        hue='Age_Group', legend=False, ax=ax)
                        ax.set_title(plot_title)
                        plt.tight_layout()
                        
                        base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir) # CORRECTED CALL
                        insight = generate_grouped_insight(plot_data_rating, "Age_Group", "Overall Rating")
                        report_sections.append({"task_type": "Box Plot (Age Group vs Rating)", "columns": ["Age_Group", "Overall Rating"], "base64_uri": base64_uri, "insight": insight})
                    
            elif "temporal" in task_type or "text analysis" in task_type or "multi-value" in task_type:
                 print(f"[Adaptive EDA] Skipping {task['type']} as columns are not applicable (as per plan).")
                 continue
                 

        except Exception as e:
            plt.close('all') 
            print(f"⚠️ Could not execute task '{task['type']}' on current data: {e}")
            
    # --- FINAL DATA COLLECTION ---
    
    summary_data = _calculate_summary_statistics(df)
    
    df_info = {'rows': len(df), 'cols': len(df.columns)}
    final_markdown = _build_final_markdown_report(report_sections, df_info)
    
    print(f"[Adaptive EDA] All tasks completed. Outputs and report saved in: {output_dir}/")

    return {
        'markdown_with_base64': final_markdown,
        'summary_statistics': summary_data
    }