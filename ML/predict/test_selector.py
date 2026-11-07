
import unittest
from unittest.mock import patch

from question_selector import (
    validate_questions,
    validate_attempts,
    validate_predictions,
    select_question,
)


class TestQuestionValidation(unittest.TestCase):

    def setUp(self):
        self.valid_question = {
            "question_id": "q1",
            "question_text": "What did God create first?",
            "topic": "Genesis",
            "difficulty": 1,
        }

    def test_candidate_questions_must_be_a_list(self):
        with self.assertRaises(ValueError):
            validate_questions("not a list")

    def test_candidate_question_must_be_a_dictionary(self):
        with self.assertRaises(ValueError):
            validate_questions(["not a dictionary"])

    def test_question_requires_all_fields(self):
        question = {"question_id": "q1"}

        with self.assertRaises(ValueError):
            validate_questions([question])

    def test_question_id_cannot_be_invalid(self):
        for invalid_id in [None, True, 1.5, ""]:
            question = self.valid_question.copy()
            question["question_id"] = invalid_id

            with self.assertRaises(ValueError):
                validate_questions([question])

    def test_question_ids_must_be_unique(self):
        question_1 = self.valid_question.copy()
        question_2 = self.valid_question.copy()

        with self.assertRaises(ValueError):
            validate_questions([question_1, question_2])

    def test_question_text_cannot_be_empty(self):
        question = self.valid_question.copy()
        question["question_text"] = "   "

        with self.assertRaises(ValueError):
            validate_questions([question])

    def test_topic_cannot_be_empty(self):
        question = self.valid_question.copy()
        question["topic"] = ""

        with self.assertRaises(ValueError):
            validate_questions([question])

    def test_difficulty_must_be_an_integer_between_1_and_5(self):
        for difficulty in [0, 6, 1.5, True, "3"]:
            question = self.valid_question.copy()
            question["difficulty"] = difficulty

            with self.assertRaises(ValueError):
                validate_questions([question])


class TestAttemptValidation(unittest.TestCase):

    def setUp(self):
        self.valid_attempt = {
            "topic": "Genesis",
            "correct": True,
            "response_time_ms": 2500,
            "question_id": "q1",
        }

    def test_attempts_must_be_a_list(self):
        with self.assertRaises(ValueError):
            validate_attempts("not a list")

    def test_attempt_must_be_a_dictionary(self):
        with self.assertRaises(ValueError):
            validate_attempts(["not a dictionary"])

    def test_attempt_requires_all_fields(self):
        attempt = {"topic": "Genesis"}

        with self.assertRaises(ValueError):
            validate_attempts([attempt])

    def test_attempt_topic_cannot_be_empty(self):
        attempt = self.valid_attempt.copy()
        attempt["topic"] = " "

        with self.assertRaises(ValueError):
            validate_attempts([attempt])

    def test_correct_must_be_a_boolean(self):
        for value in [0, 1, "True", None]:
            attempt = self.valid_attempt.copy()
            attempt["correct"] = value

            with self.assertRaises(ValueError):
                validate_attempts([attempt])

    def test_response_time_must_be_numeric(self):
        attempt = self.valid_attempt.copy()
        attempt["response_time_ms"] = "fast"

        with self.assertRaises(ValueError):
            validate_attempts([attempt])

    def test_response_time_cannot_be_negative(self):
        attempt = self.valid_attempt.copy()
        attempt["response_time_ms"] = -100

        with self.assertRaises(ValueError):
            validate_attempts([attempt])

    def test_optional_question_id_cannot_be_invalid(self):
        for invalid_id in [None, True, 1.5, ""]:
            attempt = self.valid_attempt.copy()
            attempt["question_id"] = invalid_id

            with self.assertRaises(ValueError):
                validate_attempts([attempt])


class TestPredictionValidation(unittest.TestCase):

    def test_prediction_must_be_a_dictionary(self):
        with self.assertRaises(ValueError):
            validate_predictions(["not a dictionary"], 1)

    def test_prediction_must_contain_probability(self):
        with self.assertRaises(ValueError):
            validate_predictions([{"prediction": 1}], 1)

    def test_probability_must_be_numeric(self):
        with self.assertRaises(ValueError):
            validate_predictions([{"probability": "high"}], 1)

    def test_probability_cannot_be_boolean(self):
        with self.assertRaises(ValueError):
            validate_predictions([{"probability": True}], 1)

    def test_probability_must_be_finite(self):
        for probability in [
            float("nan"),
            float("inf"),
            float("-inf"),
        ]:
            with self.assertRaises(ValueError):
                validate_predictions(
                    [{"probability": probability}],
                    1,
                )

    def test_probability_cannot_be_negative(self):
        with self.assertRaises(ValueError):
            validate_predictions([{"probability": -0.1}], 1)

    def test_probability_cannot_exceed_one(self):
        with self.assertRaises(ValueError):
            validate_predictions([{"probability": 1.1}], 1)


class TestQuestionSelector(unittest.TestCase):

    def setUp(self):
        self.questions = [
            {
                "question_id": "q1",
                "question_text": "Question 1",
                "topic": "Genesis",
                "difficulty": 2,
            },
            {
                "question_id": "q2",
                "question_text": "Question 2",
                "topic": "Exodus",
                "difficulty": 3,
            },
            {
                "question_id": "q3",
                "question_text": "Question 3",
                "topic": "Kings",
                "difficulty": 4,
            },
        ]

        self.attempts = []

    def mock_predictions(self, probabilities):
        return [
            {
                "probability": probability,
                "prediction": int(probability >= 0.5),
            }
            for probability in probabilities
        ]

    @patch("question_selector.predict_success_batch")
    def test_empty_attempt_history(self, mock_predict):
        mock_predict.return_value = self.mock_predictions(
            [0.75, 0.75, 0.75]
        )

        result = select_question(self.questions, [])

        self.assertIsNotNone(result["selected_question"])
        self.assertEqual(len(result["ranked_questions"]), 3)

    @patch("question_selector.predict_success_batch")
    def test_empty_candidate_questions(self, mock_predict):
        with self.assertRaises(ValueError):
            select_question([], [])

        mock_predict.assert_not_called()

    @patch("question_selector.predict_success_batch")
    def test_eligible_questions_rank_above_ineligible(
        self,
        mock_predict,
    ):
        mock_predict.return_value = self.mock_predictions(
            [0.20, 0.75, 0.95]
        )

        result = select_question(self.questions, [])

        self.assertEqual(
            result["ranked_questions"][0]["question_id"],
            "q2",
        )

    @patch("question_selector.predict_success_batch")
    def test_guardrail_excludes_difficult_questions(
        self,
        mock_predict,
    ):
        mock_predict.return_value = self.mock_predictions(
            [0.75, 0.75, 0.75]
        )

        result = select_question(self.questions, [])

        self.assertNotIn(
            "q3",
            [
                question["question_id"]
                for question in result["eligible_questions"]
            ],
        )

    @patch("question_selector.predict_success_batch")
    def test_guardrail_relaxes_when_no_questions_are_eligible(
        self,
        mock_predict,
    ):
        mock_predict.return_value = self.mock_predictions(
            [0.20, 0.95, 0.95]
        )

        result = select_question(self.questions, [])

        self.assertTrue(result["guardrail_relaxed"])
        self.assertIsNotNone(result["selected_question"])

    @patch("question_selector.predict_success_batch")
    def test_fallback_uses_weighted_selection_score(
        self,
        mock_predict,
    ):
        mock_predict.return_value = self.mock_predictions(
            [0.20, 0.95, 0.95]
        )

        result = select_question(self.questions, [])

        self.assertEqual(
            result["selected_question"]["question_id"],
            result["ranked_questions"][0]["question_id"],
        )

    @patch("question_selector.predict_success_batch")
    def test_ranked_questions_are_in_descending_score_order(
        self,
        mock_predict,
    ):
        mock_predict.return_value = self.mock_predictions(
            [0.60, 0.80, 0.70]
        )

        result = select_question(self.questions, [])

        ranked = result["ranked_questions"]

        eligible = [
            question["selection_score"]
            for question in ranked
            if question["eligible"]
        ]

        ineligible = [
            question["selection_score"]
            for question in ranked
            if not question["eligible"]
        ]

        self.assertEqual(
            eligible,
            sorted(eligible, reverse=True),
        )

        self.assertEqual(
            ineligible,
            sorted(ineligible, reverse=True),
        )

        if eligible and ineligible:
            first_ineligible = next(
                i
                for i, question in enumerate(ranked)
                if not question["eligible"]
            )

            self.assertTrue(
                all(
                    question["eligible"]
                    for question in ranked[:first_ineligible]
                )
            )

    @patch("question_selector.predict_success_batch")
    def test_recently_answered_question_is_penalized(
        self,
        mock_predict,
    ):
        mock_predict.return_value = self.mock_predictions(
            [0.75, 0.75, 0.75]
        )

        attempts = [
            {
                "topic": "Genesis",
                "correct": True,
                "response_time_ms": 2000,
                "question_id": "q1",
            }
        ]

        result = select_question(self.questions, attempts)

        ranked = {
            question["question_id"]: question
            for question in result["ranked_questions"]
        }

        recently_answered = ranked["q1"]
        other_question = ranked["q2"]

        self.assertEqual(
            recently_answered["question_variety_score"],
            0,
        )

        self.assertGreater(
            recently_answered["topic_variety_score"],
            0,
        )

        self.assertGreater(
            other_question["question_variety_score"],
            recently_answered["question_variety_score"],
        )

    @patch("question_selector.predict_success_batch")
    def test_unseen_topic_uses_default_statistics(
        self,
        mock_predict,
    ):
        mock_predict.return_value = self.mock_predictions(
            [0.75, 0.75, 0.75]
        )

        result = select_question(self.questions, [])

        genesis = next(
            question
            for question in result["ranked_questions"]
            if question["topic"] == "Genesis"
        )

        self.assertEqual(genesis["topic_accuracy"], 0.5)
        self.assertEqual(genesis["topic_attempt_count"], 0)


class TestTopicExposureGuardrails(unittest.TestCase):

    def setUp(self):
        self.questions = [
            {
                "question_id": "q1",
                "question_text": "Genesis question",
                "topic": "Genesis",
                "difficulty": 2,
            },
            {
                "question_id": "q2",
                "question_text": "Exodus question",
                "topic": "Exodus",
                "difficulty": 2,
            },
            {
                "question_id": "q3",
                "question_text": "Kings question",
                "topic": "Kings",
                "difficulty": 2,
            },
        ]

        self.predictions = [
            {"probability": 0.75, "prediction": 1},
            {"probability": 0.75, "prediction": 1},
            {"probability": 0.75, "prediction": 1},
        ]

    def make_attempts(self, topic_counts):
        attempts = []

        for topic, count in topic_counts.items():
            for index in range(count):
                attempts.append({
                    "question_id": f"{topic}_{index}",
                    "topic": topic,
                    "correct": True,
                    "response_time_ms": 2000,
                })

        return attempts

    @patch("question_selector.predict_success_batch")
    def test_minimum_exposure_prioritizes_underexposed_topics(
        self,
        mock_predict,
    ):
        mock_predict.return_value = self.predictions

        attempts = self.make_attempts({
            "Genesis": 6,
            "Exodus": 2,
            "Kings": 6,
        })

        result = select_question(
            self.questions,
            attempts,
            min_topic_attempts=6,
        )

        self.assertEqual(
            result["selected_question"]["topic"],
            "Exodus",
        )

        self.assertTrue(
            result["topic_guardrails"]["minimum_priority_applied"]
        )

    @patch("question_selector.predict_success_batch")
    def test_maximum_share_excludes_capped_topics(
        self,
        mock_predict,
    ):
        mock_predict.return_value = self.predictions

        attempts = self.make_attempts({
            "Genesis": 4,
            "Exodus": 1,
            "Kings": 0,
        })

        result = select_question(
            self.questions,
            attempts,
            max_topic_share=0.40,
            planned_attempts=10,
        )

        self.assertNotEqual(
            result["selected_question"]["topic"],
            "Genesis",
        )

        self.assertIn(
            "Genesis",
            result["topic_guardrails"]["maxed_out_topics"],
        )

        self.assertFalse(
            result["topic_guardrails"]["maximum_share_relaxed"]
        )

    @patch("question_selector.predict_success_batch")
    def test_maximum_share_relaxes_when_all_topics_are_capped(
        self,
        mock_predict,
    ):
        mock_predict.return_value = self.predictions

        attempts = self.make_attempts({
            "Genesis": 4,
            "Exodus": 4,
            "Kings": 4,
        })

        result = select_question(
            self.questions,
            attempts,
            max_topic_share=0.40,
            planned_attempts=10,
        )

        self.assertIsNotNone(result["selected_question"])

        self.assertTrue(
            result["topic_guardrails"]["maximum_share_relaxed"]
        )

    @patch("question_selector.predict_success_batch")
    def test_minimum_priority_relaxes_when_no_topics_are_under_quota(
        self,
        mock_predict,
    ):
        mock_predict.return_value = self.predictions

        attempts = self.make_attempts({
            "Genesis": 6,
            "Exodus": 6,
            "Kings": 6,
        })

        result = select_question(
            self.questions,
            attempts,
            min_topic_attempts=6,
        )

        self.assertIsNotNone(result["selected_question"])

        self.assertFalse(
            result["topic_guardrails"]["minimum_priority_applied"]
        )

        self.assertTrue(
            result["topic_guardrails"]["minimum_priority_relaxed"]
        )

    @patch("question_selector.predict_success_batch")
    def test_topic_safeguards_are_disabled_by_default(
        self,
        mock_predict,
    ):
        mock_predict.return_value = self.predictions

        result = select_question(
            self.questions,
            [],
        )

        guardrails = result["topic_guardrails"]

        self.assertEqual(
            guardrails["minimum_topic_attempts"],
            0,
        )

        self.assertIsNone(
            guardrails["maximum_topic_share"]
        )

        self.assertIsNone(
            guardrails["planned_attempts"]
        )

        self.assertFalse(
            guardrails["minimum_priority_applied"]
        )

        self.assertFalse(
            guardrails["maximum_share_applied"]
        )

    def test_invalid_topic_guardrail_parameters(self):
        invalid_settings = [
            {"min_topic_attempts": -1},
            {"min_topic_attempts": True},
            {"min_topic_attempts": 1.5},
            {"max_topic_share": 0},
            {"max_topic_share": 1.1},
            {"max_topic_share": True},
            {"max_topic_share": float("nan")},
            {
                "max_topic_share": 0.40,
                "planned_attempts": 0,
            },
            {
                "max_topic_share": 0.40,
                "planned_attempts": -10,
            },
            {
                "max_topic_share": 0.40,
                "planned_attempts": 10.5,
            },
        ]

        for settings in invalid_settings:
            with self.subTest(settings=settings):
                with self.assertRaises(ValueError):
                    select_question(
                        self.questions,
                        [],
                        **settings,
                    )


if __name__ == "__main__":
    unittest.main()
