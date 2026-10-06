"""recommendation_engine.py - personalised, prioritised recommendations."""
from backend.questionnaire import (AWARENESS_TIPS, CATEGORY_INFO, PRIORITY_BY_SEVERITY,
                                   PRIORITY_ORDER, QUESTION_BY_ID)


def recommendation_for(finding_type):
    q = QUESTION_BY_ID[finding_type.lower()]
    return {"finding_type": q.finding_type, "category": q.category,
            "category_label": CATEGORY_INFO[q.category]["label"],
            "priority": PRIORITY_BY_SEVERITY[q.severity], "recommendation": q.recommendation}


def generate_recommendations(findings_result, category_scores=None):
    """One recommendation per finding, grouped IMMEDIATE / IMPORTANT / GOOD PRACTICE,
    plus short security-awareness guidance for categories scoring HIGH or worse."""
    items = []
    for f in findings_result["findings"]:
        rec = recommendation_for(f["finding_type"])
        rec["risk"] = f["description"]
        items.append(rec)
    order = {p: i for i, p in enumerate(PRIORITY_ORDER)}
    items.sort(key=lambda r: order[r["priority"]])  # stable: keeps impact order inside a priority
    grouped = {p: [r for r in items if r["priority"] == p] for p in PRIORITY_ORDER}
    awareness = []
    for key in findings_result["high_risk_categories"]:
        awareness.append({"category": key, "label": CATEGORY_INFO[key]["label"], "tip": AWARENESS_TIPS[key]})
    return {"items": items, "grouped": grouped, "awareness": awareness}
