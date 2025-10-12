import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer


def detect_target_column(df: pd.DataFrame) -> dict:
    scores = {}
    n_rows = len(df)
    for col in df.columns:
        score = 0
        col_lower = col.lower()
        if any(k in col_lower for k in ["target", "label", "sales", "price", "amount", "score", "output", "y"]):
            score += 0.4
        if pd.api.types.is_numeric_dtype(df[col]):
            score += 0.2
        unique_vals = df[col].nunique()
        if 1 < unique_vals <= 20:
            score += 0.15
        if df[col].isnull().mean() < 0.2:
            score += 0.1
        num_cols = df.select_dtypes(include="number").columns
        if col in num_cols and len(num_cols) > 1:
            corr = df[num_cols].corr()[col].drop(col).abs().mean()
            if corr > 0.2:
                score += 0.15
        scores[col] = round(score, 2)

    target_col = max(scores, key=scores.get)
    return {"target": target_col, "score": scores[target_col], "all_scores": scores}


def determine_task_type(df: pd.DataFrame, target: str) -> str:
    y = df[target]
    if pd.api.types.is_numeric_dtype(y):
        return "classification" if y.nunique() <= 20 else "regression"
    return "classification"


def preprocess_data(df: pd.DataFrame, target: str, test_size: float = 0.2, random_state: int = 42):
    y = df[target]
    X = df.drop(columns=[target])

    numeric_features = X.select_dtypes(include=["int64", "float64"]).columns
    categorical_features = X.select_dtypes(include=["object", "category"]).columns

    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="mean")),
        ("scaler", StandardScaler())
    ])

    categorical_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features)
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    model_pipeline = Pipeline([("preprocessor", preprocessor)])
    X_train_processed = model_pipeline.fit_transform(X_train)
    X_test_processed = model_pipeline.transform(X_test)

    return {
        "target": target,
        "task_type": determine_task_type(df, target),
        "X_train": X_train_processed,
        "X_test": X_test_processed,
        "y_train": y_train.values,
        "y_test": y_test.values,
        "X_train_shape": X_train_processed.shape,
        "X_test_shape": X_test_processed.shape
    }


# if __name__ == "__main__":
#     np.random.seed(42)
#     df_test = pd.DataFrame({
#         "price": np.random.normal(100, 15, 200),
#         "sales": np.random.normal(500, 80, 200),
#         "discount": np.random.uniform(0, 0.3, 200),
#         "region": np.random.choice(["north", "south", "east", "west"], 200),
#         "date": pd.date_range("2024-01-01", periods=200)
#     })

#     target_info = detect_target_column(df_test)
#     print("Detected target:", target_info)

#     prep = preprocess_data(df_test, target_info["target"])
#     print(f"\nTask type: {prep['task_type']}")
#     print(f"X_train shape: {prep['X_train_shape']}, X_test shape: {prep['X_test_shape']}")
