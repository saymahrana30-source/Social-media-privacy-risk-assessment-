"""generate_dataset.py - builds the SYNTHETIC privacy-assessment dataset.

Every row is a fictional person. Nothing here is scraped or collected from real accounts.

Usage:   python data/generate_dataset.py [--rows 1200] [--seed 42]
Output:  data/social_media_privacy_assessments.csv

How the data is made (so you can explain it in a viva):
  1. Each fictional profile gets a hidden 'carelessness' level (Beta distribution).
  2. A random ARCHETYPE shifts some categories up/down - e.g. 'secure_but_open' has strong account
     security but shares a lot publicly. This demonstrates that Strong Security != Strong Privacy.
  3. A stable per-question 'commonness' offset makes some weaknesses more common than others.
  4. For each question, the answer whose risk value is closest to the profile's target risk is
     chosen with some randomness (a softmax over distance).
  5. The same scoring engine used by the app computes risk_score and risk_level.
"""
import argparse
import csv
import math
import random
import zlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.questionnaire import QUESTIONS, SCALES, CATEGORY_KEYS  # noqa: E402
from backend.services.assessment_engine import run_assessment  # noqa: E402

OUT_FILE = ROOT / "data" / "social_media_privacy_assessments.csv"

ARCHETYPES = {  # name: (probability weight, {category: shift in target risk})
    "careless": (0.20, {k: +0.20 for k in CATEGORY_KEYS}),
    "typical": (0.40, {}),
    "careful": (0.20, {k: -0.25 for k in CATEGORY_KEYS}),
    "secure_but_open": (0.10, {"account_security": -0.35, "third_party_apps": -0.2, "personal_info": +0.25, "location": +0.25, "profile": +0.2}),
    "private_but_unsafe": (0.10, {"profile": -0.3, "personal_info": -0.3, "location": -0.25, "account_security": +0.3, "social_engineering": +0.3}),
}


def _commonness(qid):
    """Stable per-question offset (-0.25 .. +0.25) so some weaknesses are more common than others,
    like in real life (e.g. 'never reviewed old posts' is far more common than 'shared a code')."""
    return ((zlib.crc32(qid.encode()) % 100) / 100 - 0.5) * 0.5


def _clip(x):
    return max(0.0, min(1.0, x))


def _pick_option(rng, scale, target):
    options = list(SCALES[scale].items())
    # NOT_SURE is rarer than a definite answer, and answers with the same risk share the probability
    # (otherwise duplicated 0.6-risk labels would be over-represented).
    prior = {"NOT_SURE": 0.3}
    shared = {risk: sum(1 for _, r in options if r == risk) for _, risk in options}
    weights = [math.exp(-((risk - target) ** 2) / (2 * 0.18 ** 2)) * prior.get(o, 1.0) / shared[risk] ** 0.5
               for o, risk in options]
    return rng.choices([o for o, _ in options], weights=weights, k=1)[0]


def generate_rows(n=1200, seed=42):
    rng = random.Random(seed)
    names = list(ARCHETYPES)
    probs = [ARCHETYPES[a][0] for a in names]
    rows = []
    for i in range(n):
        base = rng.betavariate(2.0, 2.8)
        shifts = ARCHETYPES[rng.choices(names, probs)[0]][1]
        answers = {}
        for q in QUESTIONS:
            target = _clip(base + shifts.get(q.category, 0.0) + _commonness(q.id) + rng.gauss(0, 0.15))
            answers[q.id] = _pick_option(rng, q.scale, target)
        result = run_assessment(answers)
        row = {"profile_id": f"SYN-{i + 1:05d}"}
        row.update(answers)
        row.update({f"score_{k}": v for k, v in result["category_scores"].items()})
        row["risk_score"] = result["overall"]["score"]
        row["risk_level"] = result["overall"]["level"]
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Generate the synthetic privacy-assessment dataset")
    parser.add_argument("--rows", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    rows = generate_rows(args.rows, args.seed)
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    levels = {}
    for r in rows:
        levels[r["risk_level"]] = levels.get(r["risk_level"], 0) + 1
    print(f"Wrote {len(rows)} synthetic records to {OUT_FILE}")
    print("Risk level distribution:", levels)


if __name__ == "__main__":
    main()
