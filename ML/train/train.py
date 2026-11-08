import pandas as pd
import joblib

from pathlib import Path

from sklearn.model_selection import GroupShuffleSplit
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    brier_score_loss,
    classification_report
)


# ==========================================
# 1. PATHS AND DATA
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "training_data.csv"
MODEL_DIR = BASE_DIR / "models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)

print(f"Dataset loaded: {df.shape}")


# ==========================================
# 2. FEATURES AND TARGET
# ==========================================

FEATURES = [
    "topic",
    "difficulty",
    "recent_accuracy",
    "topic_accuracy",
    "topic_attempt_count",
    "avg_previous_response_time"
]

TARGET = "correct"

X = df[FEATURES]
y = df[TARGET]

groups = df["player_id"]


# ==========================================
# 3. TRAIN / TEST SPLIT
# ==========================================

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.2,
    random_state=42
)

train_idx, test_idx = next(
    splitter.split(X, y, groups=groups)
)

X_train = X.iloc[train_idx]
X_test = X.iloc[test_idx]

y_train = y.iloc[train_idx]
y_test = y.iloc[test_idx]

print(f"\nTraining rows: {len(X_train)}")
print(f"Testing rows: {len(X_test)}")


# ==========================================
# 4. PREPROCESSING
# ==========================================

categorical_features = ["topic"]

numeric_features = [
    "difficulty",
    "recent_accuracy",
    "topic_accuracy",
    "topic_attempt_count",
    "avg_previous_response_time"
]


def create_preprocessor():

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ])

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    return ColumnTransformer([
        ("categorical", categorical_pipeline, categorical_features),
        ("numeric", numeric_pipeline, numeric_features)
    ])


# ==========================================
# 5. MODELS
# ==========================================

models = {

    "Dummy Classifier": DummyClassifier(
        strategy="prior"
    ),

    "Logistic Regression": LogisticRegression(
        max_iter=1000,
        random_state=42
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )

}


# ==========================================
# 6. TRAIN AND EVALUATE
# ==========================================

results = []
trained_models = {}

for name, model in models.items():

    pipeline = Pipeline([
        ("preprocessor", create_preprocessor()),
        ("model", model)
    ])

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    probabilities = pipeline.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(
        y_test, predictions, zero_division=0
    )
    recall = recall_score(
        y_test, predictions, zero_division=0
    )
    f1 = f1_score(
        y_test, predictions, zero_division=0
    )
    brier = brier_score_loss(y_test, probabilities)

    auc = (
        roc_auc_score(y_test, probabilities)
        if y_test.nunique() == 2
        else float("nan")
    )

    results.append({
        "model": name,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": auc,
        "brier_score": brier
    })

    trained_models[name] = pipeline

    print("\n" + "=" * 45)
    print(name)
    print("=" * 45)

    print(f"Accuracy:    {accuracy:.4f}")
    print(f"Precision:   {precision:.4f}")
    print(f"Recall:      {recall:.4f}")
    print(f"F1:          {f1:.4f}")
    print(f"ROC-AUC:     {auc:.4f}")
    print(f"Brier Score: {brier:.4f}")

    print("\nClassification Report:")
    print(classification_report(
        y_test,
        predictions,
        zero_division=0
    ))


# ==========================================
# 7. COMPARE MODELS
# ==========================================

results_df = pd.DataFrame(results)

print("\n" + "=" * 45)
print("MODEL COMPARISON")
print("=" * 45)

print(
    results_df.sort_values("brier_score").to_string(
        index=False
    )
)


# ==========================================
# 8. SAVE MODELS
# ==========================================

for name, pipeline in trained_models.items():

    filename = name.lower().replace(" ", "_") + ".joblib"

    joblib.dump(
        pipeline,
        MODEL_DIR / filename
    )

    print(f"Saved: {filename}")


# Select the model with the lowest Brier Score,
# excluding the Dummy Classifier.

real_models = results_df[
    results_df["model"] != "Dummy Classifier"
]

best_row = real_models.loc[
    real_models["brier_score"].idxmin()
]

dummy_brier = results_df.loc[
    results_df["model"] == "Dummy Classifier",
    "brier_score"
].iloc[0]

if best_row["brier_score"] < dummy_brier:

    best_name = best_row["model"]

    joblib.dump(
        trained_models[best_name],
        MODEL_DIR / "question_success_model.joblib"
    )

    print(f"\nSelected model: {best_name}")
    print("Saved as question_success_model.joblib")

else:
    print("\nWARNING: Neither ML model beat the dummy")
    print("on Brier Score. No production model selected.")


# ==========================================
# 9. SAVE EVALUATION RESULTS
# ==========================================

results_df.to_csv(
    MODEL_DIR / "evaluation_metrics.csv",
    index=False
)

print("\nEvaluation results saved.")
print(f"Model directory: {MODEL_DIR}")