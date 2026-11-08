
import unittest
import json
from ML.api.interface import recommend_question


class TestMLInterface(unittest.TestCase):

    def setUp(self):

        self.attempts = [
            {
                "topic": "Genesis",
                "correct": True,
                "response_time_ms": 12000,
            },
            {
                "topic": "Genesis",
                "correct": False,
                "response_time_ms": 18000,
            },
            {
                "topic": "Exodus",
                "correct": True,
                "response_time_ms": 10000,
            },
            {
                "topic": "Gospels",
                "correct": False,
                "response_time_ms": 22000,
            },
        ]

        self.questions = [
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
                "question_id": "GOS_001",
                "question_text": "Where was Jesus born?",
                "topic": "Gospels",
                "difficulty": 2,
            },
            {
                "question_id": "REV_001",
                "question_text": "What does the Book of Revelation describe?",
                "topic": "Revelation",
                "difficulty": 3,
            },
        ]

    def test_returns_recommendation(self):

        result = recommend_question(
            self.attempts,
            self.questions,
        )

        self.assertTrue(result["success"])

        self.assertIn(
            result["selected_question"]["question_id"],
            [q["question_id"] for q in self.questions],
        )

    def test_returns_valid_probability(self):

        result = recommend_question(
            self.attempts,
            self.questions,
        )

        probability = result["selected_question"][
            "predicted_probability"
        ]

        self.assertIsInstance(probability, float)
        self.assertGreaterEqual(probability, 0)
        self.assertLessEqual(probability, 1)

    def test_returns_diagnostics(self):

        result = recommend_question(
            self.attempts,
            self.questions,
        )

        self.assertIn("diagnostics", result)
        self.assertIn(
            "topic_guardrails",
            result["diagnostics"],
        )

    def test_empty_candidates_raise_error(self):

        with self.assertRaises(ValueError):
            recommend_question(
                self.attempts,
                [],
            )
    def test_response_is_json_serializable(self):

        result = recommend_question(
            self.attempts,
            self.questions,
        )

        # Convert the response into JSON
        json_response = json.dumps(result)

        # Convert it back into a Python dictionary
        restored_response = json.loads(json_response)

        self.assertEqual(
            restored_response["success"],
            True,
        )

        self.assertEqual(
            restored_response["selected_question"]["question_id"],
            result["selected_question"]["question_id"],
        )    

if __name__ == "__main__":
    unittest.main()

