
import csv
import json
from collections import defaultdict

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

RESULT_FILE = BASE_DIR / "simulation_v2_results.csv"

TOPICS = [
    "Genesis",
    "Exodus",
    "Kings",
    "Gospels",
    "Early Church",
    "Revelation"
]


def load_results():

    with open(
        RESULT_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        return list(csv.DictReader(file))


def analyze_topic_balance(results):

    grouped = defaultdict(list)

    for result in results:

        key = (
            result["profile"],
            result["strategy"]
        )

        result["topic_distribution"] = json.loads(
            result["topic_distribution"]
        )

        grouped[key].append(result)

    print("\nTOPIC BALANCE ANALYSIS")
    print("=" * 105)

    for profile in sorted(set(r["profile"] for r in results)):

        print(f"\nPROFILE: {profile}")
        print("-" * 105)

        for strategy in [
            "Random",
            "Fixed",
            "Adaptive",
            "Adaptive+Topics"
        ]:

            runs = grouped[(profile, strategy)]

            if not runs:
                continue

            topic_totals = defaultdict(int)

            largest_shares = []
            effective_topics = []

            minimum_violations = 0
            maximum_violations = 0

            for run in runs:

                distribution = run["topic_distribution"]

                counts = {
                    topic: distribution.get(topic, 0)
                    for topic in TOPICS
                }

                total = sum(counts.values())

                for topic, count in counts.items():

                    topic_totals[topic] += count

                    if count < 6:
                        minimum_violations += 1

                    if count > 48:
                        maximum_violations += 1

                shares = [
                    count / total
                    for count in counts.values()
                ]

                largest_shares.append(max(shares))

                effective_topics.append(
                    1 / sum(share ** 2 for share in shares)
                )

            total_attempts = len(runs) * 120

            print(f"\n{strategy}")

            print(
                f"  Largest topic share: "
                f"{sum(largest_shares) / len(runs):.1%}"
            )

            print(
                f"  Effective topics: "
                f"{sum(effective_topics) / len(runs):.2f}/6"
            )

            print(
                f"  Runs with a topic below 6 attempts: "
                f"{minimum_violations / (len(runs) * 6):.1%} "
                f"of topic-run combinations"
            )

            print(
                f"  Runs with a topic above 48 attempts: "
                f"{maximum_violations / (len(runs) * 6):.1%} "
                f"of topic-run combinations"
            )

            print("  Average topic attempts:")

            for topic in TOPICS:

                average = topic_totals[topic] / len(runs)

                print(
                    f"    {topic:15}: {average:6.2f}"
                )


if __name__ == "__main__":

    results = load_results()

    print(f"Loaded {len(results)} simulations.")

    analyze_topic_balance(results)
