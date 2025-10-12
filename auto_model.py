import numpy as np
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, f1_score, roc_auc_score
import xgboost as xgb
import joblib


def train_regression_models(X_train, X_test, y_train, y_test):
    models = {
        "LinearRegression": LinearRegression(),
        "RandomForestRegressor": RandomForestRegressor(n_estimators=100, random_state=42),
        "GradientBoostingRegressor": GradientBoostingRegressor(random_state=42),
        "XGBRegressor": xgb.XGBRegressor(
            n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42, n_jobs=-1
        )
    }

    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        results[name] = {
            "MAE": float(mean_absolute_error(y_test, preds)),
            "RMSE": float(np.sqrt(mean_squared_error(y_test, preds))),
            "R2": float(r2_score(y_test, preds)),
            "CV_R2": float(cross_val_score(model, X_train, y_train, cv=3, scoring="r2").mean()),
            "Feature_Importances": getattr(model, "feature_importances_", None).tolist()
            if hasattr(model, "feature_importances_") else None
        }
    return results


def train_classification_models(X_train, X_test, y_train, y_test):
    models = {
        "LogisticRegression": LogisticRegression(max_iter=200),
        "RandomForestClassifier": RandomForestClassifier(n_estimators=100, random_state=42),
        "XGBClassifier": xgb.XGBClassifier(
            n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42, n_jobs=-1
        )
    }

    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else preds
        results[name] = {
            "Accuracy": float(accuracy_score(y_test, preds)),
            "F1": float(f1_score(y_test, preds, average="weighted")),
            "ROC_AUC": float(roc_auc_score(y_test, proba, multi_class="ovr")),
            "CV_Accuracy": float(cross_val_score(model, X_train, y_train, cv=3, scoring="accuracy").mean()),
            "Feature_Importances": getattr(model, "feature_importances_", None).tolist()
            if hasattr(model, "feature_importances_") else None
        }
    return results


def select_best_model(results: dict, task_type: str) -> dict:
    key_metric = "R2" if task_type == "regression" else "Accuracy"
    best_name = max(results, key=lambda k: results[k].get(key_metric, -np.inf))
    best_model = results[best_name]
    best_model["name"] = best_name
    return best_model


def train_models(X_train, X_test, y_train, y_test, task_type: str):
    if task_type == "regression":
        results = train_regression_models(X_train, X_test, y_train, y_test)
    else:
        results = train_classification_models(X_train, X_test, y_train, y_test)

    best = select_best_model(results, task_type)
    return {"task_type": task_type, "models": results, "best_model": best}


if __name__ == "__main__":
    from preprocess import preprocess_data, detect_target_column
    import pandas as pd

    np.random.seed(42)
    df = pd.DataFrame({
        "price": np.random.normal(100, 15, 200),
        "sales": np.random.normal(500, 80, 200),
        "discount": np.random.uniform(0, 0.3, 200),
        "region": np.random.choice(["north", "south", "east", "west"], 200)
    })

    target_info = detect_target_column(df)
    prep = preprocess_data(df, target_info["target"])
    results = train_models(
        prep["X_train"], prep["X_test"], prep["y_train"], prep["y_test"], prep["task_type"]
    )

    print("\nBest model:", results["best_model"]["name"])
    print("Metrics:", results["best_model"])
