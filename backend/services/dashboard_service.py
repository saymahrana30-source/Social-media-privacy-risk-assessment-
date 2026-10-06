"""dashboard_service.py - aggregate statistics for the dashboard.

Source: the SYNTHETIC dataset (data/social_media_privacy_assessments.csv). If the CSV is
missing it is generated in memory with a fixed seed. No real person is represented.
"""
import csv
import os
from collections import Counter
from functools import lru_cache

from backend.questionnaire import CATEGORY_INFO, CATEGORY_KEYS, CONTROL_QUESTIONS, QUESTION_BY_ID, QUESTIONS
from backend.services.assessment_engine import run_assessment
from backend.services.improvement_simulator import simulate_improvement

DIGITAL_FOOTPRINT_IDS = [q.id for q in QUESTIONS if q.category == "digital_footprint"]


def _read_rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return [{q.id: row[q.id] for q in QUESTIONS} for row in csv.DictReader(fh)]


def _generated_rows():
    from data.generate_dataset import generate_rows  # imported lazily (data/ is outside backend/)
    return [{k: v for k, v in r.items() if k in QUESTION_BY_ID} for r in generate_rows(1000, seed=42)]


@lru_cache(maxsize=4)
def _compute(path, mtime):
    rows = _read_rows(path) if path and os.path.exists(path) else _generated_rows()
    results = [run_assessment(a) for a in rows]
    n = len(results)

    avg_cat = {k: round(sum(r["category_scores"][k] for r in results) / n, 1) for k in CATEGORY_KEYS}
    avg_overall = round(sum(r["overall"]["score"] for r in results) / n, 1)
    dist = Counter(r["overall"]["level"] for r in results)
    weak = Counter(f["finding_type"] for r in results for f in r["findings"]["findings"])
    top_weak = [{"finding_type": t, "label": QUESTION_BY_ID[t.lower()].fix, "percent": round(100 * c / n, 1)}
                for t, c in weak.most_common(10)]
    controls = [{"control": q.control, "percent_enabled": round(100 * sum(1 for r in results if r["controls"][q.control]) / n, 1)}
                for q in CONTROL_QUESTIONS]
    footprint = [{"label": QUESTION_BY_ID[i].fix, "avg_risk": round(100 * sum(r["features"]["questions"][i]["risk"] for r in results) / n, 1)}
                 for i in DIGITAL_FOOTPRINT_IDS]
    sample = rows[:250]
    def avg_after(**kw):
        return round(sum(simulate_improvement(a, **kw)["after"]["score"] for a in sample) / len(sample), 1)
    improvement = {"current": round(sum(run_assessment(a)["overall"]["score"] for a in sample) / len(sample), 1),
                   "after_immediate": avg_after(apply=["IMMEDIATE"]),
                   "after_immediate_important": avg_after(apply=["IMMEDIATE", "IMPORTANT"]),
                   "after_all": avg_after(apply="all")}
    from backend.services.scoring_engine import classify_risk
    return {
        "population": n,
        "source": "synthetic fictional profiles (no real people)",
        "average_overall_score": avg_overall,
        "average_level": classify_risk(avg_overall),
        "category_averages": avg_cat,
        "category_labels": {k: CATEGORY_INFO[k]["label"] for k in CATEGORY_KEYS},
        "high_risk_categories": sum(1 for v in avg_cat.values() if v >= 41),
        "risk_distribution": {lvl: dist.get(lvl, 0) for lvl in ("LOW", "MODERATE", "HIGH", "CRITICAL")},
        "top_weaknesses": top_weak,
        "controls_enabled": controls,
        "average_controls_enabled": round(sum(sum(r["controls"].values()) for r in results) / n, 1),
        "total_controls": len(CONTROL_QUESTIONS),
        "average_findings": round(sum(len(r["findings"]["findings"]) for r in results) / n, 1),
        "digital_footprint": footprint,
        "improvement_comparison": improvement,
        "disclaimer": "Educational framework using synthetic data; weights and thresholds are assumptions.",
    }


def dashboard_stats(dataset_path):
    mtime = os.path.getmtime(dataset_path) if dataset_path and os.path.exists(dataset_path) else 0
    return _compute(dataset_path, mtime)
