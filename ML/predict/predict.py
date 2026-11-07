
import joblib
import pandas as pd

from pathlib import Path


# ==========================================
# 1. PATHS AND MODEL LOADING
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    BASE_DIR / "models" / "question_success_model.joblib"
)

model = joblib.load(MODEL_PATH)


# ==========================================
# 2. BATCH PREDICTION FUNCTION
# ==========================================

def predict_success_batch(
    candidate_questions,
    player_features
):
    """
    Predict success probabilities for multiple questions
    using one model inference call.

    candidate_questions:
        List of question dictionaries containing:
        - topic
        - difficulty

    player_features:
        Output from build_player_features().
    """

    if not candidate_questions:
        return []

    rows = []

    for question in candidate_questions:

        topic = question["topic"]

        topic_data = player_features["topic_stats"][topic]

        rows.append({

            "topic": topic,

            "difficulty": question["difficulty"],

            "recent_accuracy": player_features[
                "recent_accuracy"
            ],

            "topic_accuracy": topic_data[
                "topic_accuracy"
            ],

            "topic_attempt_count": topic_data[
                "topic_attempt_count"
            ],

            "avg_previous_response_time": player_features[
                "avg_previous_response_time"
            ]

        })

    player_data = pd.DataFrame(rows)

    probabilities = model.predict_proba(
        player_data
    )[:, 1]

    results = []

    for probability in probabilities:

        probability = float(probability)

        results.append({

            "probability": probability,

            "prediction": int(probability >= 0.5)

        })

    return results


# ==========================================
# 3. SINGLE PREDICTION FUNCTION
# ==========================================

def predict_success(
    topic,
    difficulty,
    recent_accuracy,
    topic_accuracy,
    topic_attempt_count,
    avg_previous_response_time
):

    player_data = pd.DataFrame([{

        "topic": topic,

        "difficulty": difficulty,

        "recent_accuracy": recent_accuracy,

        "topic_accuracy": topic_accuracy,

        "topic_attempt_count": topic_attempt_count,

        "avg_previous_response_time": avg_previous_response_time

    }])

    probability = model.predict_proba(
        player_data
    )[0][1]

    probability = float(probability)

    prediction = int(probability >= 0.5)

    return {

        "probability": probability,

        "prediction": prediction

    }


# ==========================================
# 4. TEST
# ==========================================

if __name__ == "__main__":

    result = predict_success(
        topic="Revelation",
        difficulty=4,
        recent_accuracy=0.65,
        topic_accuracy=0.40,
        topic_attempt_count=12,
        avg_previous_response_time=9.5
    )

    print("\nINSTABIBLE — ML PREDICTION")
    print("=" * 40)

    print(
        f"Probability of correct answer: "
        f"{result['probability']:.2%}"
    )

    print(
        "Predicted outcome:",
        "Correct" if result["prediction"] == 1 else "Incorrect"
    )
