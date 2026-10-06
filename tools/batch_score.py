"""batch_score.py - score a CSV of questionnaire answers (e.g. the synthetic dataset) in one go.

Usage:  python tools/batch_score.py data/social_media_privacy_assessments.csv reports/scored.csv
Only the questionnaire columns are read; every other column is ignored.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.questionnaire import QUESTIONS  # noqa: E402
from backend.services.assessment_engine import run_assessment  # noqa: E402


def main(src, dst):
    levels = Counter()
    with open(src, newline="", encoding="utf-8") as fin, open(dst, "w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin)
        writer = csv.writer(fout)
        writer.writerow(["row", "risk_score", "risk_level", "top_finding"])
        for i, row in enumerate(reader, 1):
            r = run_assessment({q.id: row[q.id] for q in QUESTIONS})
            top = r["findings"]["top_risks"][0]["finding_type"] if r["findings"]["top_risks"] else ""
            writer.writerow([i, r["overall"]["score"], r["overall"]["level"], top])
            levels[r["overall"]["level"]] += 1
    print("Scored rows by level:", dict(levels))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
