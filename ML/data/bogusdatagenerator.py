
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)

TOPICS = [
    "Genesis",
    "Exodus",
    "Kings",
    "Gospels",
    "Early Church",
    "Revelation"
]

NUM_PLAYERS = 100
ATTEMPTS_PER_PLAYER = 80

records = []

for player_id in range(NUM_PLAYERS):

    player_skill = rng.normal(0, 1)

    topic_skills = {
        topic: rng.normal(0, 0.8)
        for topic in TOPICS
    }

    history = []
    topic_history = {topic: [] for topic in TOPICS}
    response_history = []

    for _ in range(ATTEMPTS_PER_PLAYER):

        topic = rng.choice(TOPICS)
        difficulty = int(rng.integers(1, 6))

        recent_accuracy = (
            np.mean(history[-10:]) if history else 0.5
        )

        topic_accuracy = (
            np.mean(topic_history[topic])
            if topic_history[topic] else 0.5
        )

        topic_attempt_count = len(topic_history[topic])

        avg_previous_response_time = (
            np.mean(response_history)
            if response_history else 10.0
        )

        ability = player_skill + topic_skills[topic]

        logit = (
            ability
            - 0.55 * (difficulty - 3)
            + 0.35 * (topic_accuracy - 0.5)
        )

        probability = 1 / (1 + np.exp(-logit))

        correct = int(rng.random() < probability)

        response_time = max(
            1.0,
            rng.normal(
                12 - 1.5 * difficulty + 4 * (1 - correct),
                2
            )
        )

        records.append({
            "player_id": player_id,
            "topic": topic,
            "difficulty": difficulty,
            "recent_accuracy": recent_accuracy,
            "topic_accuracy": topic_accuracy,
            "topic_attempt_count": topic_attempt_count,
            "avg_previous_response_time": avg_previous_response_time,
            "correct": correct
        })

        history.append(correct)
        topic_history[topic].append(correct)
        response_history.append(response_time)

df = pd.DataFrame(records)

output_path = Path(__file__).parent / "training_data.csv"
df.to_csv(output_path, index=False)

print(f"Generated {len(df)} attempts.")
print(f"Saved to {output_path}")

print("\nDataset preview:")
print(df.head())

print("\nOverall accuracy:")
print(df["correct"].mean())

print("\nAccuracy by topic:")
print(df.groupby("topic")["correct"].mean())
