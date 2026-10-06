"""findings_engine.py - turn risky answers into ranked, human-readable findings."""
from backend.questionnaire import (CATEGORY_INFO, FINDING_THRESHOLD, QUESTION_BY_ID, SEVERITY_RANK)


def generate_privacy_findings(features, category_scores, overall, top_n=5):
    """Return findings sorted by importance (risk x weight x severity).

    Output shape (compare with the example in the brief):
      {"overall_score": 68, "level": "HIGH", "top_risks": [...5 findings...],
       "findings": [...all findings...], "category_scores": {...},
       "high_risk_categories": [...]}
    """
    findings = []
    for qid, f in features["questions"].items():
        if f["risk"] < FINDING_THRESHOLD:
            continue
        q = QUESTION_BY_ID[qid]
        impact = f["risk"] * q.weight * SEVERITY_RANK[q.severity]
        findings.append({
            "finding_type": q.finding_type,
            "question_id": q.id,
            "category": q.category,
            "category_label": CATEGORY_INFO[q.category]["label"],
            "severity": q.severity,
            "description": q.finding + (" (You answered NOT SURE - treated as exposed until verified.)"
                                        if f["answer"] == "NOT_SURE" else ""),
            "fix": q.fix,
            "safe_answer": q.safe_answer,
            "impact": round(impact, 2),
        })
    findings.sort(key=lambda x: (-x["impact"], x["finding_type"]))
    high_cats = [k for k, v in sorted(category_scores.items(), key=lambda kv: -kv[1]) if v >= 41]
    return {
        "overall_score": overall["score"],
        "level": overall["level"],
        "top_risks": findings[:top_n],
        "findings": findings,
        "category_scores": category_scores,
        "high_risk_categories": high_cats,
    }
