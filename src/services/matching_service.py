
import json
from pathlib import Path

from src.utils.scoring import calculate_match


DATA_FILE = Path("data/internships.json")


def load_internships():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_matching_internships(profile):
    internships = load_internships()
    results = []

    for internship in internships:
        match = calculate_match(profile, internship)

        results.append({
            **internship,
            **match,
        })

    results.sort(
        key=lambda item: (
            item["eligible"],
            item["match_score"],
        ),
        reverse=True,
    )

    return results
