import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from datetime import datetime
import base64
from io import BytesIO
import re
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pandas")
warnings.filterwarnings("ignore", message="Could not infer format")
warnings.filterwarnings("ignore", category=FutureWarning, module="seaborn")
sns.set(style="whitegrid")

from .utils import _fig_to_base64, _calculate_summary_statistics, generate_numeric_insight, generate_categorical_insight, generate_grouped_insight, generate_correlation_insight, _build_final_markdown_report, top_n_frequency

def adaptive_eda_executor(df: pd.DataFrame, eda_plan: list, output_dir="eda_outputs", top_n=10, chart_output_dir=None):
    if chart_output_dir is None:
        chart_output_dir = os.path.join(output_dir, "charts")
    os.makedirs(chart_output_dir, exist_ok=True)

    report_sections = []

    for item in eda_plan:
        task_type = item.get('type', '')
        columns = item.get('columns', [])
        reason = item.get('reason', '')

        if task_type == "Univariate Analysis":
            col = columns[0] if columns else None
            if col and col in df.columns:
                if df[col].dtype in ['object', 'category']:
                    counts = top_n_frequency(df, col, n=top_n)
                    if not counts.empty:
                        plot_title = f"Distribution of {col}"
                        fig, ax = plt.subplots(figsize=(8, 6))
                        if len(counts) <= 5:
                            ax.pie(counts.values, labels=counts.index, autopct='%1.1f%%', startangle=90)
                            plt.axis('equal')
                        else:
                            sns.barplot(x=counts.values, y=counts.index, orient="h", hue=counts.index, palette="magma", legend=False)
                        ax.set_title(plot_title)
                        plt.tight_layout()
                        base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir)
                        insight = generate_categorical_insight(counts, col)
                        report_sections.append({
                            "task_type": task_type,
                            "columns": columns,
                            "base64_uri": base64_uri,
                            "insight": insight
                        })
                elif df[col].dtype in ['int64', 'float64']:
                    numeric = df[col].dropna()
                    if not numeric.empty:
                        plot_title = f"Distribution of {col}"
                        fig, ax = plt.subplots(figsize=(8, 5))
                        sns.histplot(numeric, kde=True, bins=min(50, numeric.nunique()))
                        ax.set_title(plot_title)
                        plt.tight_layout()
                        base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir)
                        insight = generate_numeric_insight(numeric, col)
                        report_sections.append({
                            "task_type": task_type,
                            "columns": columns,
                            "base64_uri": base64_uri,
                            "insight": insight
                        })

        elif task_type == "Temporal Trend Analysis":
            col = columns[0] if columns else None
            if col and col in df.columns:
                try:
                    temp_parsed = pd.to_datetime(df[col], errors='coerce')
                    if temp_parsed.notnull().sum() > 0:
                        df_temp = df.copy()
                        df_temp[col] = temp_parsed
                        df_temp["Year"] = df_temp[col].dt.year
                        if df_temp[col].dt.month.notnull().sum() > 0:
                            df_temp["Month"] = df_temp[col].dt.to_period("M")
                            time_col = "Month"
                        else:
                            time_col = "Year"
                        time_counts = df_temp[time_col].value_counts().sort_index()
                        if not time_counts.empty:
                            fig, ax = plt.subplots(figsize=(10, 5))
                            sns.lineplot(x=time_counts.index.astype(str), y=time_counts.values, marker="o")
                            ax.set_title(f"Temporal Trend - {col}")
                            plt.xticks(rotation=45)
                            plt.tight_layout()
                            base64_uri = _fig_to_base64(fig, f"Temporal Trend - {col}", chart_output_dir)
                            insight = f"Shows how entries in '{col}' vary over time by {time_col.lower()}."
                            report_sections.append({
                                "task_type": task_type,
                                "columns": columns,
                                "base64_uri": base64_uri,
                                "insight": insight
                            })
                except Exception as e:
                    print(f"⚠️ Skipped temporal trend for {col}: {e}")

        elif task_type == "Geographical Distribution Analysis":
            col = columns[0] if columns else None
            if col and col in df.columns:
                counts = top_n_frequency(df, col, n=top_n)
                if not counts.empty:
                    plot_title = f"Top {top_n} {col}"
                    fig, ax = plt.subplots(figsize=(8, max(4, len(counts)/2)))
                    sns.barplot(x=counts.values, y=counts.index, orient="h", hue=counts.index, palette="magma", legend=False)
                    ax.set_title(plot_title)
                    plt.tight_layout()
                    base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir)
                    insight = generate_categorical_insight(counts, col)
                    report_sections.append({
                        "task_type": task_type,
                        "columns": columns,
                        "base64_uri": base64_uri,
                        "insight": insight
                    })

        elif task_type == "Categorical Distribution Analysis":
            for col in columns:
                if col in df.columns:
                    counts = top_n_frequency(df, col, n=top_n)
                    if not counts.empty:
                        plot_title = f"Top {top_n} {col}"
                        fig, ax = plt.subplots(figsize=(8, max(4, len(counts)/2)))
                        sns.barplot(x=counts.values, y=counts.index, orient="h", hue=counts.index, palette="magma", legend=False)
                        ax.set_title(plot_title)
                        plt.tight_layout()
                        base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir)
                        insight = generate_categorical_insight(counts, col)
                        report_sections.append({
                            "task_type": task_type,
                            "columns": [col],
                            "base64_uri": base64_uri,
                            "insight": insight
                        })

        elif task_type == "Comparative Duration Analysis":
            num_col = 'duration'
            cat_col = 'type'
            if num_col in df.columns and cat_col in df.columns:
                plot_data = df[[num_col, cat_col]].dropna()
                if not plot_data.empty:
                    fig, ax = plt.subplots(figsize=(8, 5))
                    sns.boxplot(x=cat_col, y=num_col, data=plot_data)
                    ax.set_title(f"Duration by {cat_col}")
                    plt.tight_layout()
                    base64_uri = _fig_to_base64(fig, f"Duration by {cat_col}", chart_output_dir)
                    insight = generate_grouped_insight(plot_data, cat_col, num_col)
                    report_sections.append({
                        "task_type": task_type,
                        "columns": columns,
                        "base64_uri": base64_uri,
                        "insight": insight
                    })

        elif task_type == "Distribution Analysis":
            col = columns[0] if columns else None
            if col and col in df.columns:
                if df[col].dtype in ['object', 'category']:
                    counts = top_n_frequency(df, col, n=top_n)
                    if not counts.empty:
                        plot_title = f"Distribution of {col}"
                        fig, ax = plt.subplots(figsize=(8, 6))
                        if len(counts) <= 5:
                            ax.pie(counts.values, labels=counts.index, autopct='%1.1f%%', startangle=90)
                            plt.axis('equal')
                        else:
                            sns.barplot(x=counts.values, y=counts.index, orient="h", hue=counts.index, palette="magma", legend=False)
                        ax.set_title(plot_title)
                        plt.tight_layout()
                        base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir)
                        insight = generate_categorical_insight(counts, col)
                        report_sections.append({
                            "task_type": task_type,
                            "columns": columns,
                            "base64_uri": base64_uri,
                            "insight": insight
                        })
                elif df[col].dtype in ['int64', 'float64']:
                    numeric = df[col].dropna()
                    if not numeric.empty:
                        plot_title = f"Histogram of {col}"
                        fig, ax = plt.subplots(figsize=(8, 5))
                        sns.histplot(numeric, kde=True, bins=min(50, numeric.nunique()))
                        ax.set_title(plot_title)
                        plt.tight_layout()
                        base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir)
                        insight = generate_numeric_insight(numeric, col)
                        report_sections.append({
                            "task_type": task_type,
                            "columns": columns,
                            "base64_uri": base64_uri,
                            "insight": insight
                        })

        elif task_type == "Product Category Impact Analysis":
            for col in columns:
                if col in df.columns:
                    counts = top_n_frequency(df, col, n=top_n)
                    if not counts.empty:
                        plot_title = f"Distribution of {col}"
                        fig, ax = plt.subplots(figsize=(8, max(4, len(counts)/2)))
                        sns.barplot(x=counts.values, y=counts.index, orient="h", hue=counts.index, palette="magma", legend=False)
                        ax.set_title(plot_title)
                        plt.tight_layout()
                        base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir)
                        insight = generate_categorical_insight(counts, col)
                        report_sections.append({
                            "task_type": task_type,
                            "columns": [col],
                            "base64_uri": base64_uri,
                            "insight": insight
                        })

        elif task_type == "Demographic Distribution Analysis":
            for col in columns:
                if col in df.columns:
                    if df[col].dtype in ['object', 'category']:
                        counts = top_n_frequency(df, col, n=top_n)
                        if not counts.empty:
                            plot_title = f"Distribution of {col}"
                            fig, ax = plt.subplots(figsize=(8, max(4, len(counts)/2)))
                            sns.barplot(x=counts.values, y=counts.index, orient="h", hue=counts.index, palette="magma", legend=False)
                            ax.set_title(plot_title)
                            plt.tight_layout()
                            base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir)
                            insight = generate_categorical_insight(counts, col)
                            report_sections.append({
                                "task_type": task_type,
                                "columns": [col],
                                "base64_uri": base64_uri,
                                "insight": insight
                            })
                    elif df[col].dtype in ['int64', 'float64']:
                        numeric = df[col].dropna()
                        if not numeric.empty:
                            plot_title = f"Distribution of {col}"
                            fig, ax = plt.subplots(figsize=(8, 5))
                            sns.histplot(numeric, kde=True, bins=min(50, numeric.nunique()))
                            ax.set_title(plot_title)
                            plt.tight_layout()
                            base64_uri = _fig_to_base64(fig, plot_title, chart_output_dir)
                            insight = generate_numeric_insight(numeric, col)
                            report_sections.append({
                                "task_type": task_type,
                                "columns": [col],
                                "base64_uri": base64_uri,
                                "insight": insight
                            })

    df_info = {"rows": len(df), "cols": len(df.columns)}
    summary_data = _calculate_summary_statistics(df)
    final_markdown = _build_final_markdown_report(report_sections, df_info, chart_output_dir)

    print(f"[Adaptive EDA] Completed. Outputs in: {output_dir}/")
    return {
        "markdown_with_base64": final_markdown,
        "summary_statistics": summary_data
    }
