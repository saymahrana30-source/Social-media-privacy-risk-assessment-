"""improvement_simulator.py - "What happens if I improve my settings?"

This is a FRAMEWORK SIMULATION. It re-runs the scoring model with changed answers.
It is not a guarantee of real-world safety.
"""
from backend.questionnaire import PRIORITY_BY_SEVERITY, QUESTION_BY_ID
from backend.services.assessment_engine import run_assessment
from backend.utils.validation import ValidationError, validate_answers

DISCLAIMER = ("Framework simulation only: it shows how the educational scoring model would change "
              "if the listed settings changed. It is not a guarantee of real-world safety.")


def simulate_improvement(answers, changes=None, fix_ids=None, apply=None, weights=None):
    """Compute before/after scores.

    changes : {question_id: new_answer}              explicit changes
    fix_ids : [question_id, ...]                    set these to their safest answer
    apply   : "all" | list of priorities            fix every finding of that priority
    """
    before = run_assessment(answers, weights)
    new_answers = dict(before["answers"])
    changed = {}

    if changes:
        cleaned = validate_answers(changes, require_all=False)
        changed.update(cleaned)
    for qid in fix_ids or []:
        if qid not in QUESTION_BY_ID:
            raise ValidationError(f"Unknown question id in fix_ids: {str(qid)[:40]!r}")
        changed[qid] = QUESTION_BY_ID[qid].safe_answer
    if apply:
        wanted = None if apply == "all" else {str(p).upper() for p in (apply if isinstance(apply, list) else [apply])}
        for f in before["findings"]["findings"]:
            q = QUESTION_BY_ID[f["question_id"]]
            if wanted is None or PRIORITY_BY_SEVERITY[q.severity] in wanted:
                changed[q.id] = q.safe_answer

    changes_list = []
    for qid, new in changed.items():
        old = new_answers[qid]
        if old != new:
            changes_list.append({"question_id": qid, "from": old, "to": new, "fix": QUESTION_BY_ID[qid].fix})
            new_answers[qid] = new
    after = run_assessment(new_answers, weights)
    return {
        "before": {"score": before["overall"]["score"], "level": before["overall"]["level"],
                   "category_scores": before["category_scores"]},
        "after": {"score": after["overall"]["score"], "level": after["overall"]["level"],
                  "category_scores": after["category_scores"]},
        "risk_reduction": before["overall"]["score"] - after["overall"]["score"],
        "changes": changes_list,
        "disclaimer": DISCLAIMER,
    }
