"""T01-T27: scoring, findings, recommendations and the improvement simulator."""
import pytest

from backend.questionnaire import QUESTION_BY_ID, QUESTIONS, CATEGORY_KEYS, demo_profile_answers, DEMO_FIX_IDS
from backend.services.assessment_engine import run_assessment
from backend.services.improvement_simulator import simulate_improvement
from backend.services.scoring_engine import (DEFAULT_WEIGHTS, calculate_privacy_risk, classify_risk,
                                             normalise_weights)


def risky(qid):
    q = QUESTION_BY_ID[qid]
    return max(q.risk_of(o) and o for o in q.options if q.risk_of(o) == 1.0)


def assess(answers):
    return run_assessment(answers)


def test_T01_fully_private_profile(safe, case):
    r = assess(safe)
    case("T01", "Fully private profile", "all safest answers", "score 0, LOW, no findings",
         f"score {r['overall']['score']}, {r['overall']['level']}, {len(r['findings']['findings'])} findings")
    assert r["overall"]["score"] == 0 and r["overall"]["level"] == "LOW" and not r["findings"]["findings"]


def test_T02_fully_public_profile(worst, case):
    r = assess(worst)
    case("T02", "Fully public synthetic profile", "all riskiest answers", "score 100, CRITICAL",
         f"score {r['overall']['score']}, {r['overall']['level']}")
    assert r["overall"]["score"] == 100 and r["overall"]["level"] == "CRITICAL"


SINGLE_RISK_CASES = [
    ("T03", "Public phone", "phone_public", "PHONE_PUBLIC", "personal_info"),
    ("T04", "Public e-mail", "email_public", "EMAIL_PUBLIC", "personal_info"),
    ("T05", "Public birthday", "birthday_public", "BIRTHDAY_PUBLIC", "personal_info"),
    ("T06", "Public location", "location_public", "LOCATION_PUBLIC", "location"),
    ("T07", "Real-time check-ins", "realtime_location", "REALTIME_LOCATION", "location"),
    ("T08", "Travel plans posted", "travel_posts", "TRAVEL_POSTS", "location"),
    ("T09", "Workplace exposure", "workplace_public", "WORKPLACE_PUBLIC", "personal_info"),
    ("T10", "Education exposure", "education_public", "EDUCATION_PUBLIC", "personal_info"),
    ("T11", "Public posts", "posts_public", "POSTS_PUBLIC", "content"),
    ("T12", "Unknown connections accepted", "unknown_connections", "UNKNOWN_CONNECTIONS", "connections"),
    ("T13", "Tag review disabled", "tag_review_enabled", "TAG_REVIEW_ENABLED", "tagging"),
    ("T14", "MFA disabled", "mfa_enabled", "MFA_ENABLED", "account_security"),
    ("T15", "Login alerts disabled", "login_alerts_enabled", "LOGIN_ALERTS_ENABLED", "account_security"),
    ("T16", "Password reuse reported", "password_reuse_reported", "PASSWORD_REUSE_REPORTED", "account_security"),
    ("T17", "Third-party apps not reviewed", "third_party_apps_reviewed", "THIRD_PARTY_APPS_REVIEWED", "third_party_apps"),
    ("T18", "Suspicious-link awareness low", "suspicious_link_awareness", "SUSPICIOUS_LINK_AWARENESS", "social_engineering"),
    ("T19", "Old posts not reviewed", "old_posts_reviewed", "OLD_POSTS_REVIEWED", "digital_footprint"),
    ("T20", "Privacy settings not reviewed", "privacy_settings_reviewed", "PRIVACY_SETTINGS_REVIEWED", "digital_footprint"),
]


@pytest.mark.parametrize("tid,scenario,qid,finding,category", SINGLE_RISK_CASES, ids=[c[0] for c in SINGLE_RISK_CASES])
def test_single_risk_is_detected(tid, scenario, qid, finding, category, safe, case):
    answers = dict(safe)
    q = QUESTION_BY_ID[qid]
    answers[qid] = max(q.options, key=q.risk_of)
    r = assess(answers)
    types = [f["finding_type"] for f in r["findings"]["findings"]]
    case(tid, scenario, f"{qid}={answers[qid]} (everything else safest)",
         f"finding {finding}; {category} score > 0; overall > 0",
         f"findings={types}; {category}={r['category_scores'][category]}; overall={r['overall']['score']}")
    assert types == [finding]
    assert r["category_scores"][category] > 0
    assert r["overall"]["score"] > 0
    assert all(r["category_scores"][c] == 0 for c in CATEGORY_KEYS if c != category)


def test_T21_category_score_calculation(safe, case):
    # Profile category has weights 3+2+2+2 = 9. Making only profile_visibility PUBLIC (w=3, risk 1.0) -> 3/9 = 33.3
    answers = dict(safe)
    answers["profile_visibility"] = "PUBLIC"
    r = assess(answers)
    case("T21", "Category score calculation", "profile_visibility=PUBLIC only", "profile = 33.3",
         f"profile = {r['category_scores']['profile']}")
    assert r["category_scores"]["profile"] == 33.3


def test_T22_overall_score_calculation(worst, safe, case):
    # Maximum risk only in 'location' (weight 15%) -> overall 15
    answers = dict(safe)
    for q in QUESTIONS:
        if q.category == "location":
            answers[q.id] = max(q.options, key=q.risk_of)
    r = assess(answers)
    # Custom weights: location only -> 100
    only_loc = calculate_privacy_risk(r["category_scores"], {k: (1 if k == "location" else 0) for k in CATEGORY_KEYS})
    case("T22", "Overall score calculation (default + custom weights)", "location category at 100, rest 0",
         "default weights -> 15; location-only weights -> 100", f"{r['overall']['score']}; {only_loc['score']}")
    assert r["overall"]["score"] == 15 and only_loc["score"] == 100
    assert sum(DEFAULT_WEIGHTS.values()) == 100
    with pytest.raises(ValueError):
        normalise_weights({"profile": 10})


@pytest.mark.parametrize("tid,score,level", [("T23", 20, "LOW"), ("T24", 40, "MODERATE"), ("T25", 70, "HIGH")])
def test_boundaries(tid, score, level, case):
    below, at, above = classify_risk(score), classify_risk(score), classify_risk(score + 1)
    expected_above = {"T23": "MODERATE", "T24": "HIGH", "T25": "CRITICAL"}[tid]
    case(tid, f"Score boundary {score}", f"scores {score} and {score + 1}", f"{score}->{level}; {score + 1}->{expected_above}",
         f"{score}->{at}; {score + 1}->{above}")
    assert at == level and above == expected_above


def test_T26_recommendation_generation(case):
    r = assess(demo_profile_answers())
    recs = r["recommendations"]
    priorities = [x["priority"] for x in recs["items"]]
    has_phone = any(x["finding_type"] == "PHONE_PUBLIC" and x["priority"] == "IMMEDIATE" for x in recs["items"])
    case("T26", "Recommendation generation", "demo profile", "personalised, ordered IMMEDIATE>IMPORTANT>GOOD PRACTICE; phone rec is IMMEDIATE",
         f"{len(recs['items'])} recs; first={priorities[0]}; phone IMMEDIATE={has_phone}")
    assert has_phone and priorities == sorted(priorities, key=["IMMEDIATE", "IMPORTANT", "GOOD PRACTICE"].index)
    assert recs["awareness"], "high-risk categories should produce awareness guidance"


def test_T27_improvement_simulation(case):
    sim = simulate_improvement(demo_profile_answers(), fix_ids=DEMO_FIX_IDS)
    case("T27", "Improvement simulation", "demo profile + 9 fixes", "score decreases; reduction = before - after; disclaimer present",
         f"{sim['before']['score']} -> {sim['after']['score']} (reduction {sim['risk_reduction']})")
    assert sim["after"]["score"] < sim["before"]["score"]
    assert sim["risk_reduction"] == sim["before"]["score"] - sim["after"]["score"]
    assert "not a guarantee" in sim["disclaimer"]


def test_questionnaire_has_at_least_40_questions_and_10_categories():
    assert len(QUESTIONS) >= 40 and len({q.category for q in QUESTIONS}) == 10


def test_not_sure_counts_as_exposed(safe):
    a = dict(safe); a["phone_public"] = "NOT_SURE"
    assert any(f["finding_type"] == "PHONE_PUBLIC" for f in assess(a)["findings"]["findings"])
