import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def detect_column_types(df: pd.DataFrame) -> dict:
    return {
        "numerical": df.select_dtypes(include=["number"]).columns.tolist(),
        "categorical": df.select_dtypes(include=["object", "category"]).columns.tolist(),
        "datetime": df.select_dtypes(include=["datetime64[ns]"]).columns.tolist(),
        "boolean": df.select_dtypes(include=["bool"]).columns.tolist(),
    }


def summary_statistics(df: pd.DataFrame, numeric_cols: list) -> pd.DataFrame:
    desc = df[numeric_cols].describe().T
    desc["missing"] = df[numeric_cols].isnull().sum()
    desc["outliers"] = df[numeric_cols].apply(
        lambda col: ((col < (col.quantile(0.25) - 1.5 * (col.quantile(0.75) - col.quantile(0.25)))) |
                     (col > (col.quantile(0.75) + 1.5 * (col.quantile(0.75) - col.quantile(0.25))))).sum()
    )
    return desc


def missingness_overview(df: pd.DataFrame) -> pd.DataFrame:
    miss = df.isnull().sum()
    percent = 100 * miss / len(df)
    return (
        pd.DataFrame({"missing": miss, "percent": percent})
        .query("missing > 0")
        .sort_values("percent", ascending=False)
    )


def correlation_analysis(df: pd.DataFrame, numeric_cols: list) -> pd.DataFrame:
    return df[numeric_cols].corr() if len(numeric_cols) >= 2 else pd.DataFrame()


def cardinality_check(df: pd.DataFrame, categorical_cols: list) -> pd.DataFrame:
    data = {
        "unique_values": [df[col].nunique() for col in categorical_cols],
        "most_frequent": [
            df[col].value_counts().idxmax() if df[col].nunique() else None
            for col in categorical_cols
        ],
    }
    return pd.DataFrame(data, index=categorical_cols)


def suggest_feature_engineering(types: dict) -> list:
    s = []
    if types["datetime"]:
        s.append("Extract year, month, or weekday from datetime columns.")
    if types["categorical"]:
        s.append("Encode categorical variables using one-hot or label encoding.")
    if types["numerical"]:
        s.append("Normalize or standardize numeric features.")
    return s or ["No feature engineering suggestions identified."]


def plot_distributions(df: pd.DataFrame, numeric_cols: list, max_plots: int = 5):
    cols = numeric_cols[:max_plots]
    df[cols].hist(bins=20, figsize=(14, 6))
    plt.suptitle("Numeric Column Distributions")
    plt.show()


def plot_correlations(df: pd.DataFrame, numeric_cols: list):
    if len(numeric_cols) < 2:
        print("Not enough numeric columns for correlation heatmap.")
        return
    corr = df[numeric_cols].corr()
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Correlation Heatmap")
    plt.show()


def perform_eda(df: pd.DataFrame) -> dict:
    types = detect_column_types(df)
    num_cols, cat_cols = types["numerical"], types["categorical"]

    summary = summary_statistics(df, num_cols) if num_cols else pd.DataFrame()
    missing = missingness_overview(df)
    corr = correlation_analysis(df, num_cols)
    card = cardinality_check(df, cat_cols)
    suggestions = suggest_feature_engineering(types)

    if num_cols:
        plot_distributions(df, num_cols)
        plot_correlations(df, num_cols)

    return {
        "column_types": types,
        "summary_statistics": summary.to_dict() if not summary.empty else {},
        "missingness": missing.to_dict() if not missing.empty else {},
        "correlations": corr.to_dict() if not corr.empty else {},
        "cardinality": card.to_dict() if not card.empty else {},
        "feature_engineering_suggestions": suggestions,
    }


# if __name__ == "__main__":
#     df_test = pd.DataFrame({
#         "price": np.random.normal(100, 15, 200),
#         "sales": np.random.normal(500, 80, 200),
#         "region": np.random.choice(["north", "south", "east", "west"], 200),
#         "date": pd.date_range("2024-01-01", periods=200)
#     })
#     report = perform_eda(df_test)
#     print("EDA summary keys:", report.keys())
