
import csv
import json
import math
import random
import sys
import os

from collections import defaultdict
from pathlib import Path


# ============================================================
# 1. PROJECT PATHS AND IMPORTS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

PREDICT_DIR = BASE_DIR / "predict"

sys.path.insert(0, str(PREDICT_DIR))

from question_selector import select_question


OUTPUT_DIR = BASE_DIR / "evaluation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_FILE = OUTPUT_DIR / "simulation_v2_results.csv"


# ============================================================
# 2. EXPERIMENT CONFIGURATION
# ============================================================

TOPICS = [
    "Genesis",
    "Exodus",
    "Kings",
    "Gospels",
    "Early Church",
    "Revelation"
]

DIFFICULTIES = [1, 2, 3, 4, 5]

QUESTION_VARIANTS = 5

ATTEMPTS_PER_PLAYER = 120

REPETITIONS = 30

FIXED_DIFFICULTY = 3

RECENT_QUESTION_WINDOW = 5

BASE_SEED = 42

FORGETTING_RATE = 0.00003

# Topic exposure safeguards.
MIN_TOPIC_ATTEMPTS = 6

MAX_TOPIC_SHARE = 0.40


# ============================================================
# 3. SIMULATED PLAYER PROFILES
# ============================================================

PLAYER_PROFILES = {

    "Beginner": {
        "Genesis": 0.35,
        "Exodus": 0.35,
        "Kings": 0.35,
        "Gospels": 0.35,
        "Early Church": 0.35,
        "Revelation": 0.35
    },

    "Intermediate": {
        "Genesis": 0.55,
        "Exodus": 0.55,
        "Kings": 0.55,
        "Gospels": 0.55,
        "Early Church": 0.55,
        "Revelation": 0.55
    },

    "Advanced": {
        "Genesis": 0.78,
        "Exodus": 0.78,
        "Kings": 0.78,
        "Gospels": 0.78,
        "Early Church": 0.78,
        "Revelation": 0.78
    },

    "Uneven": {
        "Genesis": 0.78,
        "Exodus": 0.35,
        "Kings": 0.62,
        "Gospels": 0.45,
        "Early Church": 0.30,
        "Revelation": 0.70
    }
}


STRATEGIES = [
    "Random",
    "Fixed",
    "Adaptive",
    "Adaptive+Topics"
]


# ============================================================
# 4. RESULT FILE CONFIGURATION
# ============================================================

RESULT_FIELDS = [
    "profile",
    "strategy",
    "repetition",
    "attempts",
    "accuracy",
    "initial_mastery",
    "final_mastery",
    "mastery_gain",
    "average_difficulty",
    "early_difficulty",
    "late_difficulty",
    "difficulty_change",
    "repeated_question_rate",
    "repeated_topic_rate",
    "topic_coverage",
    "topic_distribution",
    "topic_mastery_gain"
]


def initialize_checkpoint():

    # A new experiment always starts with a fresh file.

    with open(
        CHECKPOINT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=RESULT_FIELDS
        )

        writer.writeheader()

        file.flush()
        os.fsync(file.fileno())


def append_checkpoint(result):

    # Convert dictionaries into CSV-compatible strings.

    row = result.copy()

    row["topic_distribution"] = json.dumps(
        row["topic_distribution"]
    )

    row["topic_mastery_gain"] = json.dumps(
        row["topic_mastery_gain"]
    )

    # Append one completed simulation.

    with open(
        CHECKPOINT_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=RESULT_FIELDS
        )

        writer.writerow(row)

        # Flush data to disk immediately.

        file.flush()
        os.fsync(file.fileno())


# ============================================================
# 5. GENERATE A SHARED QUESTION BANK
# ============================================================

def generate_question_pool():

    questions = []

    question_id = 1000

    for topic in TOPICS:

        for difficulty in DIFFICULTIES:

            for variant in range(QUESTION_VARIANTS):

                questions.append({

                    "question_id": question_id,

                    "question_text": (
                        f"Simulated {topic} question "
                        f"{variant + 1}, "
                        f"difficulty {difficulty}"
                    ),

                    "topic": topic,

                    "difficulty": difficulty

                })

                question_id += 1

    return questions


# ============================================================
# 6. HIDDEN PLAYER PERFORMANCE MODEL
# ============================================================

def sigmoid(value):

    value = max(-30, min(30, value))

    return 1 / (1 + math.exp(-value))


def actual_success_probability(
    ability,
    difficulty
):

    difficulty_threshold = (
        0.15 + (difficulty - 1) * 0.17
    )

    return sigmoid(
        8 * (ability - difficulty_threshold)
    )


def simulate_answer(
    ability,
    difficulty,
    rng
):

    probability = actual_success_probability(
        ability,
        difficulty
    )

    correct = rng.random() < probability

    return correct


# ============================================================
# 7. KNOWLEDGE GAIN AND FORGETTING
# ============================================================

def update_player_knowledge(
    abilities,
    topic,
    difficulty,
    correct
):

    # Apply forgetting to every topic.

    for current_topic in abilities:

        abilities[current_topic] = max(
            0.05,
            abilities[current_topic] - FORGETTING_RATE
        )

    # More difficult questions offer more learning
    # potential, but incorrect answers still provide
    # some learning through feedback.

    learning_potential = (
        0.0008 + difficulty * 0.00035
    )

    if correct:

        knowledge_gain = learning_potential

    else:

        knowledge_gain = learning_potential * 0.55

    abilities[topic] = min(
        0.98,
        abilities[topic] + knowledge_gain
    )


# ============================================================
# 8. QUESTION SELECTION STRATEGIES
# ============================================================

def choose_random_question(
    candidate_questions,
    rng
):

    return rng.choice(candidate_questions)


def choose_fixed_question(
    candidate_questions,
    rng
):

    fixed_candidates = [
        question
        for question in candidate_questions
        if question["difficulty"] == FIXED_DIFFICULTY
    ]

    if not fixed_candidates:

        raise RuntimeError(
            "No fixed-difficulty questions are available."
        )

    return rng.choice(fixed_candidates)


def choose_adaptive_question(
    candidate_questions,
    attempts
):

    result = select_question(
        candidate_questions,
        attempts
    )

    return result["selected_question"]


def choose_adaptive_topic_question(
    candidate_questions,
    attempts
):

    result = select_question(
        candidate_questions,
        attempts,
        min_topic_attempts=MIN_TOPIC_ATTEMPTS,
        max_topic_share=MAX_TOPIC_SHARE,
        planned_attempts=ATTEMPTS_PER_PLAYER
    )

    return result["selected_question"]


# ============================================================
# 9. SELECT QUESTION BASED ON STRATEGY
# ============================================================

def select_next_question(
    strategy,
    question_bank,
    attempts,
    rng
):

    # All strategies receive the same question bank.
    # All strategies avoid questions answered
    # within the recent-question cooldown.

    recent_ids = {
        attempt["question_id"]
        for attempt in attempts[-RECENT_QUESTION_WINDOW:]
    }

    available_questions = [
        question
        for question in question_bank
        if question["question_id"] not in recent_ids
    ]

    if not available_questions:

        available_questions = question_bank

    if strategy == "Random":

        return choose_random_question(
            available_questions,
            rng
        )

    elif strategy == "Fixed":

        return choose_fixed_question(
            available_questions,
            rng
        )

    elif strategy == "Adaptive":

        return choose_adaptive_question(
            available_questions,
            attempts
        )

    elif strategy == "Adaptive+Topics":

        return choose_adaptive_topic_question(
            available_questions,
            attempts
        )

    raise ValueError(
        f"Unknown strategy: {strategy}"
    )


# ============================================================
# 10. SIMULATE ONE PLAYER
# ============================================================

def simulate_player(
    profile_name,
    initial_abilities,
    strategy,
    repetition,
    question_bank
):

    abilities = initial_abilities.copy()

    initial_abilities_copy = initial_abilities.copy()

    attempts = []

    selection_rng = random.Random(
        BASE_SEED
        + repetition * 10000
        + list(PLAYER_PROFILES).index(profile_name) * 100
        + STRATEGIES.index(strategy) * 10
    )

    outcome_rng = random.Random(
        BASE_SEED
        + repetition * 10000
        + list(PLAYER_PROFILES).index(profile_name) * 100
        + 50000
    )

    correct_count = 0

    total_difficulty = 0

    repeated_question_count = 0

    repeated_topic_count = 0

    topic_counts = defaultdict(int)

    early_difficulties = []

    late_difficulties = []

    for attempt_number in range(ATTEMPTS_PER_PLAYER):

        # ----------------------------------------------------
        # A. SELECT QUESTION
        # ----------------------------------------------------

        question = select_next_question(
            strategy,
            question_bank,
            attempts,
            selection_rng
        )

        topic = question["topic"]

        difficulty = question["difficulty"]

        question_id = question["question_id"]

        # ----------------------------------------------------
        # B. TRACK REPETITION
        # ----------------------------------------------------

        previous_question_ids = {
            attempt["question_id"]
            for attempt in attempts
        }

        if question_id in previous_question_ids:

            repeated_question_count += 1

        recent_topics = {
            attempt["topic"]
            for attempt in attempts[-RECENT_QUESTION_WINDOW:]
        }

        if topic in recent_topics:

            repeated_topic_count += 1

        # ----------------------------------------------------
        # C. SIMULATE THE ANSWER
        # ----------------------------------------------------

        correct = simulate_answer(
            abilities[topic],
            difficulty,
            outcome_rng
        )

        if correct:

            correct_count += 1

        # ----------------------------------------------------
        # D. SIMULATE RESPONSE TIME
        # ----------------------------------------------------

        response_time_ms = (
            4000
            + difficulty * 1800
            + (0 if correct else 3000)
            + outcome_rng.randint(-1000, 1000)
        )

        response_time_ms = max(
            500,
            response_time_ms
        )

        # ----------------------------------------------------
        # E. RECORD ATTEMPT
        # ----------------------------------------------------

        attempts.append({

            "question_id": question_id,

            "topic": topic,

            "correct": correct,

            "response_time_ms": response_time_ms

        })

        topic_counts[topic] += 1

        total_difficulty += difficulty

        # ----------------------------------------------------
        # F. UPDATE KNOWLEDGE
        # ----------------------------------------------------

        update_player_knowledge(
            abilities,
            topic,
            difficulty,
            correct
        )

        # ----------------------------------------------------
        # G. TRACK DIFFICULTY PROGRESSION
        # ----------------------------------------------------

        if attempt_number < 20:

            early_difficulties.append(difficulty)

        elif attempt_number >= ATTEMPTS_PER_PLAYER - 20:

            late_difficulties.append(difficulty)

    # ========================================================
    # 11. CALCULATE PLAYER RESULTS
    # ========================================================

    initial_average_ability = sum(
        initial_abilities_copy.values()
    ) / len(initial_abilities_copy)

    final_average_ability = sum(
        abilities.values()
    ) / len(abilities)

    topic_mastery_gain = {

        topic: abilities[topic] - initial_abilities_copy[topic]

        for topic in TOPICS

    }

    topic_coverage = sum(
        1
        for topic in TOPICS
        if topic_counts[topic] > 0
    )

    early_average_difficulty = (
        sum(early_difficulties) / len(early_difficulties)
    )

    late_average_difficulty = (
        sum(late_difficulties) / len(late_difficulties)
    )

    return {

        "profile": profile_name,

        "strategy": strategy,

        "repetition": repetition,

        "attempts": ATTEMPTS_PER_PLAYER,

        "accuracy": correct_count / ATTEMPTS_PER_PLAYER,

        "initial_mastery": initial_average_ability,

        "final_mastery": final_average_ability,

        "mastery_gain": (
            final_average_ability - initial_average_ability
        ),

        "average_difficulty": (
            total_difficulty / ATTEMPTS_PER_PLAYER
        ),

        "early_difficulty": early_average_difficulty,

        "late_difficulty": late_average_difficulty,

        "difficulty_change": (
            late_average_difficulty - early_average_difficulty
        ),

        "repeated_question_rate": (
            repeated_question_count / ATTEMPTS_PER_PLAYER
        ),

        "repeated_topic_rate": (
            repeated_topic_count / ATTEMPTS_PER_PLAYER
        ),

        "topic_coverage": topic_coverage,

        "topic_distribution": dict(topic_counts),

        "topic_mastery_gain": topic_mastery_gain

    }


# ============================================================
# 12. RUN THE EXPERIMENT
# ============================================================

def run_experiment():

    question_bank = generate_question_pool()

    results = []

    # Start a fresh checkpoint file.

    initialize_checkpoint()

    total_runs = (
        len(PLAYER_PROFILES)
        * len(STRATEGIES)
        * REPETITIONS
    )

    current_run = 0

    print("\nINSTABIBLE — SIMULATION V2")

    print("=" * 70)

    print(
        f"Question bank: {len(question_bank)} questions"
    )

    print(
        f"Player profiles: {len(PLAYER_PROFILES)}"
    )

    print(
        f"Strategies: {len(STRATEGIES)}"
    )

    print(
        f"Repetitions: {REPETITIONS}"
    )

    print(
        f"Attempts per player: {ATTEMPTS_PER_PLAYER}"
    )

    print(
        f"Topic minimum: {MIN_TOPIC_ATTEMPTS}"
    )

    print(
        f"Topic maximum share: {MAX_TOPIC_SHARE:.0%}"
    )

    print(
        f"Total simulated attempts: "
        f"{total_runs * ATTEMPTS_PER_PLAYER:,}"
    )

    print(
        f"Checkpoint file: {CHECKPOINT_FILE}"
    )

    print("=" * 70)

    for profile_name, initial_abilities in PLAYER_PROFILES.items():

        for strategy in STRATEGIES:

            for repetition in range(REPETITIONS):

                current_run += 1

                result = simulate_player(
                    profile_name,
                    initial_abilities,
                    strategy,
                    repetition,
                    question_bank
                )

                results.append(result)

                # Save immediately after each completed simulation.

                append_checkpoint(result)

                print(
                    f"[{current_run:03}/{total_runs}] "
                    f"{profile_name:14} | "
                    f"{strategy:16} | "
                    f"Accuracy: {result['accuracy']:.2%} | "
                    f"Mastery gain: {result['mastery_gain']:.4f}"
                )

    return results


# ============================================================
# 13. SAVE RESULTS
# ============================================================

def save_results(results):

    # Results have already been saved incrementally.
    # This function confirms the final checkpoint location.

    print(
        f"\nAll {len(results)} completed simulations saved to:\n"
        f"{CHECKPOINT_FILE}"
    )


# ============================================================
# 14. AGGREGATE RESULTS
# ============================================================

def calculate_averages(group):

    metrics = [

        "accuracy",
        "mastery_gain",
        "average_difficulty",
        "early_difficulty",
        "late_difficulty",
        "difficulty_change",
        "repeated_question_rate",
        "repeated_topic_rate",
        "topic_coverage"

    ]

    return {

        metric: sum(
            result[metric]
            for result in group
        ) / len(group)

        for metric in metrics

    }


# ============================================================
# 15. DISPLAY SUMMARY
# ============================================================

def display_summary(results):

    grouped = defaultdict(list)

    for result in results:

        key = (
            result["profile"],
            result["strategy"]
        )

        grouped[key].append(result)

    print("\n\nSIMULATION V2 — AGGREGATED RESULTS")

    print("=" * 115)

    print(
        f"{'Profile':14} "
        f"{'Strategy':16} "
        f"{'Accuracy':10} "
        f"{'Mastery Gain':13} "
        f"{'Difficulty':11} "
        f"{'Difficulty Δ':13} "
        f"{'Q Repeat':10} "
        f"{'Topic Cov.':10}"
    )

    print("-" * 115)

    for profile in PLAYER_PROFILES:

        for strategy in STRATEGIES:

            group = grouped[(profile, strategy)]

            averages = calculate_averages(group)

            print(
                f"{profile:14} "
                f"{strategy:16} "
                f"{averages['accuracy']:9.2%} "
                f"{averages['mastery_gain']:12.4f} "
                f"{averages['average_difficulty']:10.2f} "
                f"{averages['difficulty_change']:12.2f} "
                f"{averages['repeated_question_rate']:9.2%} "
                f"{averages['topic_coverage']:8.2f}/6"
            )

    print("=" * 115)


# ============================================================
# 16. MAIN
# ============================================================

if __name__ == "__main__":

    simulation_results = run_experiment()

    save_results(simulation_results)

    display_summary(simulation_results)
