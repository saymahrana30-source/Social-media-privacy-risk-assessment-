"""assessment_engine.py - feature extraction + the end-to-end assessment pipeline.

Pipeline (matches the architecture diagram):
  validated answers -> extract_privacy_features -> category scores -> overall score
  -> findings -> recommendations
"""
from backend.questionnaire import CATEGORY_INFO, CATEGORY_KEYS, CONTROL_QUESTIONS, QUESTIONS
from backend.utils.validation import validate_answers


def extract_privacy_features(answers):
    """Convert questionnaire answers into numerical privacy-risk features.

    Returns a structured dictionary:
      {
        "questions":  {qid: {"answer", "risk" (0-1), "weight", "category", "contribution"}},
        "categories": {key: {"weighted_risk", "max_weight", "answered"}},
        "controls":   {control label: True/False},
        "exposure_flags": {qid: True/False}    # risk >= 0.5 -> flagged
      }
    Examples of contributions (spec section 6): a public phone number is a "High exposure
    contribution"; MFA disabled is an "Account-security risk contribution"; accepting unknown
    connections is a "Social-engineering risk contribution".
    """
    features = {"questions": {}, "categories": {}, "controls": {}, "exposure_flags": {}}
    for key in CATEGORY_KEYS:
        features["categories"][key] = {"weighted_risk": 0.0, "max_weight": 0, "answered": 0}

    for q in QUESTIONS:
        answer = answers[q.id]
        risk = q.risk_of(answer)
        contribution = CATEGORY_INFO[q.category]["contribution"]
        features["questions"][q.id] = {
            "answer": answer, "risk": risk, "weight": q.weight,
            "category": q.category, "contribution": contribution,
        }
        features["exposure_flags"][q.id] = risk >= 0.5
        cat = features["categories"][q.category]
        cat["weighted_risk"] += risk * q.weight
        cat["max_weight"] += q.weight
        cat["answered"] += 1

    for q in CONTROL_QUESTIONS:
        features["controls"][q.control] = features["questions"][q.id]["risk"] == 0.0
    return features


def run_assessment(raw_answers, weights=None):
    """Validate answers and run the complete pipeline. Returns one result dict.

    Imports are local to avoid circular imports between the engines.
    """
    from backend.services.findings_engine import generate_privacy_findings
    from backend.services.recommendation_engine import generate_recommendations
    from backend.services.scoring_engine import calculate_category_scores, calculate_privacy_risk

    answers = validate_answers(raw_answers)
    features = extract_privacy_features(answers)
    category_scores = calculate_category_scores(features)
    overall = calculate_privacy_risk(category_scores, weights)
    findings = generate_privacy_findings(features, category_scores, overall)
    recommendations = generate_recommendations(findings, category_scores)
    return {
        "answers": answers, "features": features, "category_scores": category_scores,
        "overall": overall, "findings": findings, "recommendations": recommendations,
        "controls": features["controls"],
    }
