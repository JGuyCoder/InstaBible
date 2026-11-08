
from collections import defaultdict


# ==========================================
# 1. FEATURE BUILDER
# ==========================================

def build_player_features(attempts, candidate_topics=None):
    """
    Convert a player's historical attempts into ML features.

    attempts:
        Chronologically ordered list of dictionaries containing:
        - topic
        - correct
        - response_time_ms

    candidate_topics:
        Topics represented in the current question pool.

    Returns:
        Dictionary compatible with question_selector.py.
    """

    # Ensure attempts are in chronological order.
    # The caller must supply them oldest to newest.

    if not isinstance(attempts, list):
        raise TypeError("Attempts must be provided as a list.")

    # ==========================================
    # 2. RECENT ACCURACY
    # ==========================================

    if attempts:
        recent_attempts = attempts[-10:]

        recent_accuracy = sum(
            bool(attempt["correct"])
            for attempt in recent_attempts
        ) / len(recent_attempts)

    else:
        recent_accuracy = 0.5

    # ==========================================
    # 3. AVERAGE RESPONSE TIME
    # ==========================================

    if attempts:
        avg_previous_response_time = sum(
            attempt["response_time_ms"]
            for attempt in attempts
        ) / len(attempts) / 1000

    else:
        avg_previous_response_time = 0.0

    # ==========================================
    # 4. TOPIC STATISTICS
    # ==========================================

    topic_attempts = defaultdict(list)

    for attempt in attempts:

        topic = attempt["topic"]

        topic_attempts[topic].append(
            bool(attempt["correct"])
        )

    topics = set(topic_attempts.keys())

    if candidate_topics is not None:
        topics.update(candidate_topics)

    topic_stats = {}

    for topic in topics:

        history = topic_attempts[topic]

        if history:

            topic_accuracy = sum(history) / len(history)
            topic_attempt_count = len(history)

        else:

            # Cold-start defaults for an unfamiliar topic.
            topic_accuracy = 0.5
            topic_attempt_count = 0

        topic_stats[topic] = {
            "topic_accuracy": topic_accuracy,
            "topic_attempt_count": topic_attempt_count
        }

    # ==========================================
    # 5. RETURN FEATURES
    # ==========================================

    return {
        "recent_accuracy": recent_accuracy,
        "avg_previous_response_time": avg_previous_response_time,
        "topic_stats": topic_stats
    }


# ==========================================
# 6. TEST
# ==========================================

if __name__ == "__main__":

    attempts = [
        {
            "topic": "Genesis",
            "correct": True,
            "response_time_ms": 8500
        },
        {
            "topic": "Revelation",
            "correct": False,
            "response_time_ms": 12000
        },
        {
            "topic": "Genesis",
            "correct": True,
            "response_time_ms": 7000
        },
        {
            "topic": "Kings",
            "correct": False,
            "response_time_ms": 15000
        },
        {
            "topic": "Revelation",
            "correct": True,
            "response_time_ms": 11000
        }
    ]

    candidate_topics = [
        "Genesis",
        "Exodus",
        "Kings",
        "Gospels",
        "Early Church",
        "Revelation"
    ]

    features = build_player_features(
        attempts,
        candidate_topics
    )

    print("\nINSTABIBLE — PLAYER FEATURE BUILDER")
    print("=" * 45)

    print(f"Recent accuracy: {features['recent_accuracy']:.2%}")

    print(
        "Average response time: "
        f"{features['avg_previous_response_time']:.2f} seconds"
    )

    print("\nTOPIC STATISTICS")
    print("-" * 45)

    for topic, stats in features["topic_stats"].items():

        print(
            f"{topic:15} | "
            f"Accuracy: {stats['topic_accuracy']:.2%} | "
            f"Attempts: {stats['topic_attempt_count']}"
        )
