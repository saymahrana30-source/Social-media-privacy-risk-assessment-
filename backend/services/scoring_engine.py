"""scoring_engine.py - category scores (0-100) and the overall privacy risk score.

HIGHER SCORE = HIGHER ASSESSED EXPOSURE / RISK.   0 = lowest assessed risk, 100 = highest.

EDUCATIONAL ASSUMPTION: the weights and the level thresholds below are educational
assumptions. They must be validated/calibrated before being used for any real
professional risk decision. A score is not a guarantee that an account will or will
not be compromised.
"""
from backend.questionnaire import CATEGORY_KEYS

# Default weights (percent, must total 100) - configurable via calculate_privacy_risk(weights=...)
DEFAULT_WEIGHTS = {
    "profile": 10, "personal_info": 15, "location": 15, "content": 10, "connections": 10,
    "tagging": 5, "account_security": 15, "third_party_apps": 5, "social_engineering": 10,
    "digital_footprint": 5,
}

# (upper bound inclusive, level)
RISK_LEVELS = [(20, "LOW"), (40, "MODERATE"), (70, "HIGH"), (100, "CRITICAL")]


def round_half_up(x):
    return int(x + 0.5)


def classify_risk(score):
    """0-20 LOW, 21-40 MODERATE, 41-70 HIGH, 71-100 CRITICAL.

    The score is first rounded to a whole number (half up) so that what the user
    sees on screen always matches the level shown next to it."""
    s = round_half_up(max(0, min(100, score)))
    for upper, level in RISK_LEVELS:
        if s <= upper:
            return level
    return "CRITICAL"


def calculate_category_scores(features):
    """Weighted average of question risks inside each category, scaled to 0-100."""
    scores = {}
    for key in CATEGORY_KEYS:
        cat = features["categories"][key]
        scores[key] = round(100.0 * cat["weighted_risk"] / cat["max_weight"], 1) if cat["max_weight"] else 0.0
    return scores


def normalise_weights(weights=None):
    """Validate custom weights and scale them so they total 100."""
    weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
    missing = [k for k in CATEGORY_KEYS if k not in weights]
    extra = [k for k in weights if k not in CATEGORY_KEYS]
    if missing or extra:
        raise ValueError(f"weights must contain exactly the categories {CATEGORY_KEYS} (missing={missing}, unknown={extra})")
    if any((not isinstance(v, (int, float))) or v < 0 for v in weights.values()):
        raise ValueError("weights must be non-negative numbers")
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("weights must not all be zero")
    return {k: 100.0 * v / total for k, v in weights.items()}


def calculate_privacy_risk(category_scores, weights=None):
    """Overall 0-100 score from category scores using configurable weights."""
    w = normalise_weights(weights)
    raw = sum(category_scores[k] * w[k] / 100.0 for k in CATEGORY_KEYS)
    score = round_half_up(raw)
    return {"score": score, "level": classify_risk(score), "weights": {k: round(v, 1) for k, v in w.items()}}
