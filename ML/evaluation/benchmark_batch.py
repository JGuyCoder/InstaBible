
import sys
import time
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "predict"))

from predict import predict_success, predict_success_batch
from feature_builder import build_player_features


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

REPETITIONS = 20
TOPICS = [
    "Genesis",
    "Exodus",
    "Kings",
    "Gospels",
    "Early Church",
    "Revelation"
]


# ------------------------------------------------------------
# CREATE TEST DATA
# ------------------------------------------------------------

candidate_questions = []

question_id = 1

for topic in TOPICS:
    for difficulty in range(1, 6):
        for variant in range(5):
            candidate_questions.append({
                "question_id": question_id,
                "question_text": f"Question {question_id}",
                "topic": topic,
                "difficulty": difficulty
            })

            question_id += 1


attempts = [
    {
        "topic": "Genesis",
        "correct": True,
        "response_time_ms": 8000
    },
    {
        "topic": "Exodus",
        "correct": False,
        "response_time_ms": 12000
    },
    {
        "topic": "Kings",
        "correct": True,
        "response_time_ms": 9000
    },
    {
        "topic": "Gospels",
        "correct": True,
        "response_time_ms": 7000
    },
    {
        "topic": "Revelation",
        "correct": False,
        "response_time_ms": 15000
    }
]

player_features = build_player_features(
    attempts,
    [question["topic"] for question in candidate_questions]
)


# ------------------------------------------------------------
# VERIFY PREDICTION EQUIVALENCE
# ------------------------------------------------------------

batch_results = predict_success_batch(
    candidate_questions,
    player_features
)

individual_results = []

for question in candidate_questions:
    topic_data = player_features["topic_stats"][question["topic"]]

    result = predict_success(
        question["topic"],
        question["difficulty"],
        player_features["recent_accuracy"],
        topic_data["topic_accuracy"],
        topic_data["topic_attempt_count"],
        player_features["avg_previous_response_time"]
    )

    individual_results.append(result)


for batch, individual in zip(batch_results, individual_results):
    assert math.isclose(
        batch["probability"],
        individual["probability"],
        rel_tol=1e-7,
        abs_tol=1e-9
    ), "Batch and individual predictions do not match!"

print("Prediction equivalence: PASSED")


# ------------------------------------------------------------
# BENCHMARK
# ------------------------------------------------------------

start = time.perf_counter()

for _ in range(REPETITIONS):
    predict_success_batch(
        candidate_questions,
        player_features
    )

batch_time = time.perf_counter() - start


start = time.perf_counter()

for _ in range(REPETITIONS):
    for question in candidate_questions:
        topic_data = player_features["topic_stats"][question["topic"]]

        predict_success(
            question["topic"],
            question["difficulty"],
            player_features["recent_accuracy"],
            topic_data["topic_accuracy"],
            topic_data["topic_attempt_count"],
            player_features["avg_previous_response_time"]
        )

individual_time = time.perf_counter() - start


# ------------------------------------------------------------
# RESULTS
# ------------------------------------------------------------

speedup = individual_time / batch_time

print("\nINSTABIBLE — BATCH INFERENCE BENCHMARK")
print("=" * 50)

print(f"Candidate questions: {len(candidate_questions)}")
print(f"Repetitions: {REPETITIONS}")
print(f"Total predictions: {len(candidate_questions) * REPETITIONS}")

print(f"\nIndividual prediction time: {individual_time:.4f} seconds")
print(f"Batch prediction time:      {batch_time:.4f} seconds")

print(f"\nSpeed improvement: {speedup:.2f}x")
print(f"Time reduction: {((1 - batch_time / individual_time) * 100):.2f}%")
