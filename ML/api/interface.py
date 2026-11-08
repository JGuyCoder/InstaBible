
"""
Public interface for the InstaBible ML engine.

The backend calls recommend_question() and receives a
JSON-serializable recommendation.
"""

from ML.predict.question_selector import select_question


# --------------------------------------------------
# DEFAULT CONFIGURATION
# --------------------------------------------------

DEFAULT_MIN_TOPIC_ATTEMPTS = 6
DEFAULT_MAX_TOPIC_SHARE = 0.40
DEFAULT_PLANNED_ATTEMPTS = 120


# --------------------------------------------------
# PUBLIC INTERFACE
# --------------------------------------------------

def recommend_question(
    attempts,
    candidate_questions,
    *,
    min_topic_attempts=DEFAULT_MIN_TOPIC_ATTEMPTS,
    max_topic_share=DEFAULT_MAX_TOPIC_SHARE,
    planned_attempts=DEFAULT_PLANNED_ATTEMPTS,
):
    """
    Recommend the next question for a player.

    Parameters
    ----------
    attempts : list[dict]
        Player's historical attempts, oldest to newest.

    candidate_questions : list[dict]
        Questions available for selection.

    min_topic_attempts : int
        Minimum historical exposure priority per topic.

    max_topic_share : float or None
        Maximum allowed share of planned attempts for a topic.
        Set to None to disable the maximum-share safeguard.

    planned_attempts : int or None
        Expected total attempts in the current learning plan.
        Required when max_topic_share is enabled.

    Returns
    -------
    dict
        Selected question, predictions, ranking, and diagnostics.

    Raises
    ------
    ValueError
        If the supplied data is invalid or no candidates exist.
    """

    # --------------------------------------------------
    # RUN THE EXISTING QUESTION SELECTOR
    # --------------------------------------------------

    result = select_question(
        candidate_questions,
        attempts,
        min_topic_attempts=min_topic_attempts,
        max_topic_share=max_topic_share,
        planned_attempts=planned_attempts,
    )

    # --------------------------------------------------
    # EXTRACT THE SELECTED QUESTION
    # --------------------------------------------------

    selected = result["selected_question"]

    # --------------------------------------------------
    # BUILD A BACKEND-FRIENDLY RESPONSE
    # --------------------------------------------------

    return {
        "success": True,

        "selected_question": {
            "question_id": selected["question_id"],
            "question_text": selected["question_text"],
            "topic": selected["topic"],
            "difficulty": selected["difficulty"],
            "predicted_probability": selected["probability"],
            "prediction": selected["prediction"],
        },

        "ranked_questions": result["ranked_questions"],

        "eligible_questions": result["eligible_questions"],

        "diagnostics": {
            "guardrail_relaxed": result["guardrail_relaxed"],
            "topic_guardrails": result["topic_guardrails"],
        },
    }
