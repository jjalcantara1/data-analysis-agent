import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from datetime import datetime
import base64
from io import BytesIO
import re

sns.set(style="whitegrid")

TOP_N_LIMIT = 10

def _fig_to_base64(fig: plt.Figure, chart_title: str, chart_output_dir: str) -> str:
    """Save Matplotlib figure and return clean placeholder text for Markdown."""
    safe_title = re.sub(r'\W+', '_', chart_title).lower()
    filename = f"{safe_title}.png"
    filepath = os.path.join(chart_output_dir, filename)
    try:
        fig.savefig(filepath, format='png', bbox_inches='tight')
        print(f"[Chart Save] Saved image to: {filepath}")
    except Exception as e:
        print(f"⚠️ Failed to save chart {chart_title}: {e}")
    plt.close(fig)
    return f"CHART_TITLE_PLACEHOLDER:{chart_title}:END"

def _calculate_summary_statistics(df: pd.DataFrame) -> dict:
    """Generate summary stats dynamically for all numeric columns."""
    summary_data = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        series = df[col].dropna()
        if not series.empty:
            summary_data[col] = {
                "count": int(series.count()),
                "mean": round(series.mean(), 2),
                "median": round(series.median(), 2),
                "std": round(series.std(), 2),
                "min": round(series.min(), 2),
                "max": round(series.max(), 2),
                "skew": round(series.skew(), 2),
            }
    return summary_data


def generate_numeric_insight(series: pd.Series, col: str) -> str:
    if series.empty:
        return f"No numeric data available for {col}."
    mean, median, skew = series.mean(), series.median(), series.skew()
    if abs(skew) > 1:
        skew_type = "right" if skew > 0 else "left"
        return f"'{col}' is highly {skew_type}-skewed, with most values near {series.min():.2f}."
    return f"'{col}' has a roughly symmetric distribution (mean={mean:.2f}, median={median:.2f})."

def generate_categorical_insight(counts: pd.Series, col: str) -> str:
    if counts.empty:
        return f"No data for {col}."
    top, top_pct = counts.index[0], counts.iloc[0] / counts.sum() * 100
    if top_pct > 60:
        return f"'{col}' is dominated by '{top}' ({top_pct:.1f}% of all entries)."
    elif len(counts) > 1:
        return f"Top '{col}' values: {', '.join(counts.index[:2])} ({top_pct:.1f}% for the top category)."
    return f"Only one unique category '{top}' found in '{col}'."

def generate_grouped_insight(plot_data: pd.DataFrame, cat_col: str, num_col: str) -> str:
    med = plot_data.groupby(cat_col)[num_col].median().sort_values(ascending=False)
    if len(med) < 2:
        return f"Only one category found for {cat_col}."
    return f"Median '{num_col}' is highest for '{med.index[0]}' ({med.iloc[0]:.2f}) and lowest for '{med.index[-1]}' ({med.iloc[-1]:.2f})."

def generate_correlation_insight(corr_matrix: pd.DataFrame) -> str:
    if corr_matrix.empty:
        return "No numeric features available for correlation."
    corr_series = corr_matrix.unstack().sort_values(ascending=False)
    corr_series = corr_series[corr_series.index.get_level_values(0) != corr_series.index.get_level_values(1)]
    if corr_series.empty:
        return "Not enough numeric columns to compute correlation."
    idx_max = corr_series.abs().idxmax()
    val = corr_series.loc[idx_max]
    return f"Strongest correlation is between '{idx_max[0]}' and '{idx_max[1]}' (r={val:.2f})."

def _build_final_markdown_report(report_sections: list, df_info: dict, chart_output_dir: str = "charts") -> str:
    markdown = f"""# Comprehensive EDA Report

## Dataset Summary
* Records: {df_info.get('rows')}
* Columns: {df_info.get('cols')}

---

## Key Insights and Visualizations
"""
    for section in report_sections:
        task_type = section['task_type']
        col = ", ".join(section['columns'])
        title = section['base64_uri'].split(':')[1]
        safe_title = re.sub(r'\W+', '_', title).lower()
        image_path = os.path.join(chart_output_dir, f"{safe_title}.png")
        markdown += f"""
### {task_type.title()} for {col}
**Insight:** {section['insight']}

![{title}]({image_path})
"""
    markdown += "\n---\n## Conclusion\nEDA complete."
    return markdown


def top_n_frequency(df, col, n=TOP_N_LIMIT, multi_sep=None):
    """Handles multi-value or normal categorical frequency extraction."""
    if col not in df.columns:
        return pd.Series(dtype=int)
    col_data = df[col].dropna().astype(str)
    if multi_sep and col_data.str.contains(multi_sep).any():
        exploded = col_data.str.split(multi_sep).explode().str.strip()
        counts = exploded.value_counts().head(n)
    else:
        counts = col_data.value_counts().head(n)
    return counts



def adaptive_eda_executor(df: pd.DataFrame, eda_plan: dict, output_dir="eda_outputs", top_n=TOP_N_LIMIT, chart_output_dir=None):
    if chart_output_dir is None:
        chart_output_dir = os.path.join(output_dir, "charts")
    os.makedirs(chart_output_dir, exist_ok=True)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

    datetime_cols = []
    for col in df.columns:
        try:
            if pd.to_datetime(df[col], errors='coerce').notnull().sum() > 0.5 * len(df):
                datetime_cols.append(col)
        except:
            continue

    print(f"[Detected] Numeric: {numeric_cols}")
    print(f"[Detected] Categorical: {categorical_cols}")
    print(f"[Detected] Date/Time: {datetime_cols}")

    report_sections = []

    for col in numeric_cols:
        numeric = df[col].dropna()
        if numeric.empty:
            continue
        plot_title = f"Distribution of {col}"
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.histplot(numeric, kde=True, bins=min(50, numeric.nunique()))
        ax.set_title(plot_title)
        plt.tight_layout()
        base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir)
        report_sections.append({
            "task_type": "Distribution Plot",
            "columns": [col],
            "base64_uri": base64_uri,
            "insight": generate_numeric_insight(numeric, col)
        })

    for col in categorical_cols:
        counts = top_n_frequency(df, col, n=top_n)
        if counts.empty or counts.sum() == 0:
            continue
        plot_title = f"Top {top_n} {col}"
        fig, ax = plt.subplots(figsize=(8, max(4, len(counts)/2)))
        sns.barplot(x=counts.values, y=counts.index, orient="h", palette="magma")
        ax.set_title(plot_title)
        plt.tight_layout()
        base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir)
        report_sections.append({
            "task_type": "Top N Bar Chart",
            "columns": [col],
            "base64_uri": base64_uri,
            "insight": generate_categorical_insight(counts, col)
        })

    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr(numeric_only=True)
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5)
        ax.set_title("Correlation Heatmap")
        plt.tight_layout()
        base64_uri = _fig_to_base64(fig, "Correlation Heatmap", chart_output_dir)
        report_sections.append({
            "task_type": "Correlation Heatmap",
            "columns": numeric_cols,
            "base64_uri": base64_uri,
            "insight": generate_correlation_insight(corr)
        })

    for col in datetime_cols:
        try:
            # Try parsing as full date
            temp_parsed = pd.to_datetime(df[col], errors='coerce')
            if temp_parsed.dt.year.nunique() > 1 or (temp_parsed.dt.year.nunique() == 1 and temp_parsed.dt.year.iloc[0] != 1970):
                df[col] = temp_parsed
            else:
                # Likely year strings, parse as %Y
                df[col] = pd.to_datetime(df[col], format='%Y', errors='coerce')
            df["Year"] = df[col].dt.year
            if df[col].dt.month.notnull().sum() > 0:
                df["Month"] = df[col].dt.to_period("M")
                time_col = "Month"
            else:
                time_col = "Year"

            time_counts = df[time_col].value_counts().sort_index()
            if time_counts.empty or time_counts.sum() == 0:
                print(f"[Skipped] No data for temporal trend on {col}")
                continue
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.lineplot(x=time_counts.index.astype(str), y=time_counts.values, marker="o")
            ax.set_title(f"Temporal Trend based on {col}")
            plt.xticks(rotation=45)
            plt.tight_layout()
            base64_uri = _fig_to_base64(fig, f"Temporal Trend - {col}", chart_output_dir)
            report_sections.append({
                "task_type": "Temporal Trend",
                "columns": [col],
                "base64_uri": base64_uri,
                "insight": f"Shows how entries in '{col}' vary over time by {time_col.lower()}."
            })
        except Exception as e:
            print(f"⚠️ Skipped temporal trend for {col}: {e}")

    df_info = {"rows": len(df), "cols": len(df.columns)}
    summary_data = _calculate_summary_statistics(df)
    final_markdown = _build_final_markdown_report(report_sections, df_info, chart_output_dir)

    print(f"[Adaptive EDA] Completed. Outputs in: {output_dir}/")
    return {
        "markdown_with_base64": final_markdown,
        "summary_statistics": summary_data
    }
