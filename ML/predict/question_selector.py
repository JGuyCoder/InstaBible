
from collections import Counter
from numbers import Real
import math

if __package__:
    from .predict import predict_success_batch
    from .feature_builder import build_player_features
else:
    from predict import predict_success_batch
    from feature_builder import build_player_features


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

TARGET_PROBABILITY = 0.75

MIN_SUCCESS_PROBABILITY = 0.45
MAX_SUCCESS_PROBABILITY = 0.90

WEIGHTS = {
    "success_fit": 0.55,
    "topic_weakness": 0.30,
    "variety": 0.15,
}

RECENT_QUESTION_WINDOW = 5


# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

def validate_questions(candidate_questions):
    """Validate candidate question data."""

    if not isinstance(candidate_questions, list):
        raise ValueError("Candidate questions must be a list.")

    if not candidate_questions:
        raise ValueError("Candidate questions cannot be empty.")

    required_fields = {
        "question_id",
        "question_text",
        "topic",
        "difficulty",
    }

    seen_ids = set()

    for question in candidate_questions:

        if not isinstance(question, dict):
            raise ValueError("Each question must be a dictionary.")

        if not required_fields.issubset(question):
            raise ValueError("Question is missing required fields.")

        question_id = question["question_id"]

        if (
            isinstance(question_id, bool)
            or not isinstance(question_id, (str, int))
            or question_id == ""
        ):
            raise ValueError(
                "Question ID must be a nonempty string or integer."
            )

        if question_id in seen_ids:
            raise ValueError("Question IDs must be unique.")

        seen_ids.add(question_id)

        if (
            not isinstance(question["question_text"], str)
            or not question["question_text"].strip()
        ):
            raise ValueError("Question text cannot be empty.")

        if (
            not isinstance(question["topic"], str)
            or not question["topic"].strip()
        ):
            raise ValueError("Question topic cannot be empty.")

        difficulty = question["difficulty"]

        if (
            isinstance(difficulty, bool)
            or not isinstance(difficulty, int)
            or not 1 <= difficulty <= 5
        ):
            raise ValueError(
                "Difficulty must be an integer between 1 and 5."
            )


def validate_attempts(attempts):
    """Validate historical player attempts."""

    if not isinstance(attempts, list):
        raise ValueError("Attempts must be a list.")

    required_fields = {
        "topic",
        "correct",
        "response_time_ms",
    }

    for attempt in attempts:

        if not isinstance(attempt, dict):
            raise ValueError("Each attempt must be a dictionary.")

        if not required_fields.issubset(attempt):
            raise ValueError("Attempt is missing required fields.")

        if (
            not isinstance(attempt["topic"], str)
            or not attempt["topic"].strip()
        ):
            raise ValueError("Attempt topic cannot be empty.")

        if not isinstance(attempt["correct"], bool):
            raise ValueError("Correct must be a boolean.")

        response_time = attempt["response_time_ms"]

        if (
            isinstance(response_time, bool)
            or not isinstance(response_time, Real)
        ):
            raise ValueError("Response time must be numeric.")

        if not math.isfinite(response_time) or response_time < 0:
            raise ValueError(
                "Response time must be finite and nonnegative."
            )

        if "question_id" in attempt:

            question_id = attempt["question_id"]

            if (
                isinstance(question_id, bool)
                or not isinstance(question_id, (str, int))
                or question_id == ""
            ):
                raise ValueError(
                    "Attempt question ID must be a nonempty string or integer."
                )


def validate_predictions(predictions, expected_count):
    """Validate model prediction output."""

    if not isinstance(predictions, list):
        raise ValueError("Predictions must be a list.")

    if len(predictions) != expected_count:
        raise ValueError(
            "Prediction count does not match question count."
        )

    for prediction in predictions:

        if not isinstance(prediction, dict):
            raise ValueError("Each prediction must be a dictionary.")

        if "probability" not in prediction:
            raise ValueError(
                "Prediction must contain probability."
            )

        probability = prediction["probability"]

        if (
            isinstance(probability, bool)
            or not isinstance(probability, Real)
        ):
            raise ValueError("Probability must be numeric.")

        if not math.isfinite(probability):
            raise ValueError("Probability must be finite.")

        if not 0 <= probability <= 1:
            raise ValueError(
                "Probability must be between 0 and 1."
            )


def validate_topic_guardrails(
    min_topic_attempts,
    max_topic_share,
    planned_attempts,
):
    """Validate optional topic exposure settings."""

    if (
        isinstance(min_topic_attempts, bool)
        or not isinstance(min_topic_attempts, int)
        or min_topic_attempts < 0
    ):
        raise ValueError(
            "Minimum topic attempts must be a nonnegative integer."
        )

    if max_topic_share is not None:

        if (
            isinstance(max_topic_share, bool)
            or not isinstance(max_topic_share, Real)
            or not math.isfinite(max_topic_share)
            or not 0 < max_topic_share <= 1
        ):
            raise ValueError(
                "Maximum topic share must be greater than 0 and at most 1."
            )

        if (
            isinstance(planned_attempts, bool)
            or not isinstance(planned_attempts, int)
            or planned_attempts <= 0
        ):
            raise ValueError(
                "Planned attempts must be a positive integer "
                "when maximum topic share is enabled."
            )


# --------------------------------------------------
# QUESTION SELECTION
# --------------------------------------------------

def select_question(
    candidate_questions,
    attempts,
    *,
    min_topic_attempts=0,
    max_topic_share=None,
    planned_attempts=None,
):
    """
    Select the most appropriate question for a player.

    Selection considers:
    1. Predicted probability of success.
    2. Historical weakness in the question's topic.
    3. Long-term question and topic variety.
    4. Optional minimum topic exposure.
    5. Optional maximum topic exposure.

    Topic safeguards are disabled by default.

    If no questions satisfy the probability guardrails,
    those guardrails are relaxed.

    If topic safeguards cannot be satisfied by the candidate
    pool, the relevant safeguard is relaxed and reported.
    """

    # Validate inputs.
    validate_questions(candidate_questions)
    validate_attempts(attempts)

    validate_topic_guardrails(
        min_topic_attempts,
        max_topic_share,
        planned_attempts,
    )

    # Build player statistics.
    candidate_topics = [
        question["topic"]
        for question in candidate_questions
    ]

    player_features = build_player_features(
        attempts,
        candidate_topics=candidate_topics,
    )

    topic_stats = player_features["topic_stats"]

    # Track recent questions.
    recent_question_ids = {
        attempt["question_id"]
        for attempt in attempts[-RECENT_QUESTION_WINDOW:]
        if "question_id" in attempt
    }

    # Track long-term question and topic frequency.
    question_counts = Counter(
        attempt["question_id"]
        for attempt in attempts
        if "question_id" in attempt
    )

    topic_counts = Counter(
        attempt["topic"]
        for attempt in attempts
    )

    # --------------------------------------------------
    # TOPIC EXPOSURE GUARDRAILS
    # --------------------------------------------------

    candidate_topic_set = set(candidate_topics)

    under_quota_topics = {
        topic
        for topic in candidate_topic_set
        if topic_counts[topic] < min_topic_attempts
    }

    max_topic_attempts = None

    if max_topic_share is not None:
        max_topic_attempts = math.floor(
            planned_attempts * max_topic_share
        )

    maxed_out_topics = set()

    if max_topic_attempts is not None:
        maxed_out_topics = {
            topic
            for topic in candidate_topic_set
            if topic_counts[topic] >= max_topic_attempts
        }

    # Prefer topics below their minimum exposure quota.
    minimum_priority_applied = (
        min_topic_attempts > 0
        and bool(under_quota_topics)
    )

    # If no under-quota topic has candidates, relax that priority.
    minimum_priority_relaxed = (
        min_topic_attempts > 0
        and not under_quota_topics
    )

    # Remove topics that have reached their maximum exposure.
    available_questions = [
        question
        for question in candidate_questions
        if question["topic"] not in maxed_out_topics
    ]

    max_share_applied = max_topic_attempts is not None
    max_share_relaxed = False

    # If the maximum cap removes every candidate, relax it.
    if not available_questions:
        available_questions = candidate_questions.copy()
        max_share_relaxed = True

    # Apply minimum topic priority to the remaining candidates.
    if minimum_priority_applied:

        priority_questions = [
            question
            for question in available_questions
            if question["topic"] in under_quota_topics
        ]

        if priority_questions:
            available_questions = priority_questions
        else:
            minimum_priority_relaxed = True
            minimum_priority_applied = False

    # --------------------------------------------------
    # MODEL PREDICTIONS
    # --------------------------------------------------

    # Predict every candidate in one batch.
    predictions = predict_success_batch(
        candidate_questions,
        player_features,
    )

    validate_predictions(
        predictions,
        len(candidate_questions),
    )

    ranked_questions = []

    # --------------------------------------------------
    # SCORE EVERY CANDIDATE
    # --------------------------------------------------

    for question, prediction in zip(
        candidate_questions,
        predictions,
    ):

        question_id = question["question_id"]
        topic = question["topic"]

        probability = prediction["probability"]

        # ----------------------------------------------
        # SUCCESS FIT
        # ----------------------------------------------

        success_fit = 1 - abs(
            probability - TARGET_PROBABILITY
        )

        # ----------------------------------------------
        # TOPIC WEAKNESS
        # ----------------------------------------------

        stats = topic_stats.get(
            topic,
            {
                "topic_accuracy": 0.5,
                "topic_attempt_count": 0,
            },
        )

        topic_accuracy = stats["topic_accuracy"]
        topic_attempt_count = stats["topic_attempt_count"]

        topic_weakness = 1 - topic_accuracy

        # ----------------------------------------------
        # LONG-TERM VARIETY
        # ----------------------------------------------

        question_frequency = question_counts[question_id]
        topic_frequency = topic_counts[topic]

        if question_id in recent_question_ids:
            question_variety = 0
        else:
            question_variety = 1 / (
                1 + question_frequency
            )

        topic_variety = 1 / (
            1 + topic_frequency
        )

        variety = (
            0.5 * question_variety
            + 0.5 * topic_variety
        )

        # ----------------------------------------------
        # COMBINED SELECTION SCORE
        # ----------------------------------------------

        selection_score = (
            WEIGHTS["success_fit"] * success_fit
            + WEIGHTS["topic_weakness"] * topic_weakness
            + WEIGHTS["variety"] * variety
        )

        eligible = (
            MIN_SUCCESS_PROBABILITY
            <= probability
            <= MAX_SUCCESS_PROBABILITY
            and question["difficulty"] <= 3
        )

        ranked_questions.append({
            **question,

            "probability": probability,
            "prediction": prediction.get("prediction"),

            "success_fit": success_fit,

            "topic_accuracy": topic_accuracy,
            "topic_attempt_count": topic_attempt_count,
            "topic_weakness": topic_weakness,

            "question_frequency": question_frequency,
            "topic_frequency": topic_frequency,

            "question_variety_score": question_variety,
            "topic_variety_score": topic_variety,
            "variety_score": variety,

            "selection_score": selection_score,
            "eligible": eligible,

            "topic_under_minimum": (
                topic_counts[topic] < min_topic_attempts
            ),

            "topic_at_maximum": (
                topic in maxed_out_topics
            ),

            "topic_priority": (
                topic in under_quota_topics
                if minimum_priority_applied
                else True
            ),
        })

    # --------------------------------------------------
    # RANKING AND PROBABILITY GUARDRAILS
    # --------------------------------------------------

    # Keep only candidates permitted by topic safeguards.
    allowed_ids = {
        question["question_id"]
        for question in available_questions
    }

    selection_pool = [
        question
        for question in ranked_questions
        if question["question_id"] in allowed_ids
    ]

    eligible_questions = [
        question
        for question in selection_pool
        if question["eligible"]
    ]

    guardrail_relaxed = not bool(eligible_questions)

    if guardrail_relaxed:
        eligible_questions = selection_pool.copy()

    # Rank the active selection pool.
    selection_pool.sort(
        key=lambda question: (
            question["eligible"],
            question["selection_score"],
        ),
        reverse=True,
    )

    # Sort the complete candidate list for inspection.
    ranked_questions.sort(
        key=lambda question: (
            question["topic_priority"],
            question["eligible"],
            question["selection_score"],
        ),
        reverse=True,
    )

    # Select the highest-ranked permitted question.
    selected_question = selection_pool[0]

    # --------------------------------------------------
    # RESULTS
    # --------------------------------------------------

    topic_guardrails = {
        "minimum_topic_attempts": min_topic_attempts,
        "maximum_topic_share": max_topic_share,
        "planned_attempts": planned_attempts,
        "maximum_topic_attempts": max_topic_attempts,

        "under_quota_topics": sorted(under_quota_topics),
        "maxed_out_topics": sorted(maxed_out_topics),

        "minimum_priority_applied": minimum_priority_applied,
        "minimum_priority_relaxed": minimum_priority_relaxed,

        "maximum_share_applied": max_share_applied,
        "maximum_share_relaxed": max_share_relaxed,
    }

    return {
        "selected_question": selected_question,
        "ranked_questions": ranked_questions,
        "eligible_questions": eligible_questions,
        "player_features": player_features,

        "guardrail_relaxed": guardrail_relaxed,
        "topic_guardrails": topic_guardrails,
    }


# --------------------------------------------------
# DEMONSTRATION
# --------------------------------------------------

if __name__ == "__main__":

    candidate_questions = [
        {
            "question_id": "GEN_001",
            "question_text": "Who built the ark?",
            "topic": "Genesis",
            "difficulty": 1,
        },
        {
            "question_id": "EXO_001",
            "question_text": "Who led the Israelites out of Egypt?",
            "topic": "Exodus",
            "difficulty": 2,
        },
        {
            "question_id": "KIN_001",
            "question_text": "Who was the first king of Israel?",
            "topic": "Kings",
            "difficulty": 3,
        },
    ]

    attempts = [
        {
            "question_id": "GEN_001",
            "topic": "Genesis",
            "correct": True,
            "response_time_ms": 2500,
        },
        {
            "question_id": "EXO_001",
            "topic": "Exodus",
            "correct": False,
            "response_time_ms": 5000,
        },
    ]

    result = select_question(
        candidate_questions,
        attempts,
        min_topic_attempts=6,
        max_topic_share=0.40,
        planned_attempts=120,
    )

    print("\nSELECTED QUESTION")
    print("-----------------")
    print(result["selected_question"]["question_text"])

    print("\nRANKED QUESTIONS")
    print("----------------")

    for question in result["ranked_questions"]:
        print(
            f"{question['question_id']} | "
            f"Probability: {question['probability']:.3f} | "
            f"Score: {question['selection_score']:.3f} | "
            f"Topic: {question['topic']} | "
            f"Under quota: {question['topic_under_minimum']}"
        )

    print("\nTOPIC GUARDRAILS")
    print("----------------")

    for name, value in result["topic_guardrails"].items():
        print(f"{name}: {value}")

    print(
        "\nProbability guardrails relaxed:",
        result["guardrail_relaxed"],
    )
