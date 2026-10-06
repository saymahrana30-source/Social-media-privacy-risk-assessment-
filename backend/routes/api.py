"""REST API. See docs/API.md for request/response examples.

Authentication : none (no accounts, no personal data). Assessments are protected by an
                 unguessable 128-bit id; deletion additionally needs the one-time delete token.
Authorization  : only the holder of the delete token can delete.
Privacy        : answers are processed in memory and NOT stored - only scores and finding types.
"""
from flask import Blueprint, current_app, jsonify, render_template, request, Response

from backend.models import db as dbm
from backend.questionnaire import (CATEGORY_INFO, CHECKLIST, CONTROL_QUESTIONS, DEMO_FIX_IDS, QUESTION_BY_ID,
                                   demo_profile_answers, public_questionnaire)
from backend.services.assessment_engine import run_assessment
from backend.services.dashboard_service import dashboard_stats
from backend.services.improvement_simulator import simulate_improvement
from backend.services.recommendation_engine import generate_recommendations
from backend.utils.validation import ValidationError

api = Blueprint("api", __name__, url_prefix="/api")

DISCLAIMER = ("This is an educational risk framework. A score does not guarantee that an account will or will "
              "not be compromised. Weights and thresholds are educational assumptions that should be validated "
              "before any professional risk decision.")


def _json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    return data


def _public_result(result):
    f = result["findings"]
    return {
        "overall_score": result["overall"]["score"],
        "risk_level": result["overall"]["level"],
        "weights_used": result["overall"]["weights"],
        "category_scores": result["category_scores"],
        "category_labels": {k: CATEGORY_INFO[k]["label"] for k in result["category_scores"]},
        "high_risk_categories": f["high_risk_categories"],
        "top_risks": f["top_risks"],
        "findings": f["findings"],
        "recommendations": result["recommendations"],
        "controls_enabled": result["controls"],
        "disclaimer": DISCLAIMER,
    }


@api.get("/questionnaire")
def questionnaire():
    return jsonify({"categories": public_questionnaire(), "total_questions": len(QUESTION_BY_ID)})


@api.get("/demo-profile")
def demo_profile():
    return jsonify({"note": "Entirely fictional demonstration answers.", "answers": demo_profile_answers(),
                    "fix_ids": DEMO_FIX_IDS})


@api.post("/assessment")
def create_assessment():
    body = _json_body()
    unknown = set(body) - {"answers"}
    if unknown:  # reject unexpected top-level fields (e.g. someone sending "phone_number")
        raise ValidationError(f"Unexpected field(s): {sorted(str(k)[:30] for k in unknown)}")
    result = run_assessment(body.get("answers"))
    db = dbm.get_db()
    dbm.purge_expired(db, current_app.config["RETENTION_DAYS"])
    assessment_id, delete_token, created_at = dbm.save_assessment(db, result)
    payload = _public_result(result)
    payload.update({"assessment_id": assessment_id, "created_at": created_at, "delete_token": delete_token})
    return jsonify(payload), 201


def _get_or_404(assessment_id):
    data = dbm.load_assessment(dbm.get_db(), assessment_id)
    if data is None:
        return None
    return data


@api.get("/assessment/<assessment_id>")
def get_assessment(assessment_id):
    data = _get_or_404(assessment_id)
    if data is None:
        return jsonify({"error": "Assessment not found"}), 404
    data["category_labels"] = {k: CATEGORY_INFO[k]["label"] for k in data["category_scores"]}
    finding_types = {f["finding_type"] for f in data["findings"]}
    data["controls_enabled"] = {q.control: q.finding_type not in finding_types for q in CONTROL_QUESTIONS}
    data["disclaimer"] = DISCLAIMER
    return jsonify(data)


@api.get("/assessment/<assessment_id>/recommendations")
def get_recommendations(assessment_id):
    data = _get_or_404(assessment_id)
    if data is None:
        return jsonify({"error": "Assessment not found"}), 404
    findings = {"findings": [{"finding_type": f["finding_type"], "description": f["description"]} for f in data["findings"]],
                "high_risk_categories": [k for k, v in data["category_scores"].items() if v >= 41]}
    return jsonify(generate_recommendations(findings, data["category_scores"]))


@api.get("/assessment/<assessment_id>/report")
def get_report(assessment_id):
    data = _get_or_404(assessment_id)
    if data is None:
        return jsonify({"error": "Assessment not found"}), 404
    order = {"IMMEDIATE": 0, "IMPORTANT": 1, "GOOD PRACTICE": 2}
    recs = sorted(data["findings"], key=lambda f: order.get(f["priority"], 9))
    html = render_template("report.html", a=data, labels={k: CATEGORY_INFO[k]["label"] for k in CATEGORY_INFO},
                           recs=recs, checklist=CHECKLIST, disclaimer=DISCLAIMER)
    resp = Response(html, mimetype="text/html")
    if request.args.get("download") == "1":
        resp.headers["Content-Disposition"] = f'attachment; filename="privacy-report-{data["assessment_id"][:8]}.html"'
    return resp


@api.delete("/assessment/<assessment_id>")
def delete_assessment(assessment_id):
    token = request.headers.get("X-Delete-Token", "")
    outcome = dbm.delete_assessment(dbm.get_db(), assessment_id, token)
    if outcome is None:
        return jsonify({"error": "Assessment not found"}), 404
    if outcome is False:
        return jsonify({"error": "Invalid delete token"}), 403
    return jsonify({"deleted": True})


@api.post("/assessment/simulate-improvement")
def simulate():
    body = _json_body()
    unknown = set(body) - {"answers", "changes", "fix_ids", "apply"}
    if unknown:
        raise ValidationError(f"Unexpected field(s): {sorted(str(k)[:30] for k in unknown)}")
    fix_ids = body.get("fix_ids")
    if fix_ids is not None and (not isinstance(fix_ids, list) or len(fix_ids) > 100):
        raise ValidationError("'fix_ids' must be a list of question ids")
    apply_ = body.get("apply")
    if apply_ is not None and apply_ != "all" and not (isinstance(apply_, list) and all(isinstance(p, str) for p in apply_)):
        raise ValidationError("'apply' must be 'all' or a list of priorities")
    changes = body.get("changes")
    if changes is not None and not isinstance(changes, dict):
        raise ValidationError("'changes' must be an object")
    return jsonify(simulate_improvement(body.get("answers"), changes=changes, fix_ids=fix_ids, apply=apply_))


@api.get("/dashboard/stats")
def stats():
    data = dict(dashboard_stats(current_app.config["DATASET_PATH"]))
    data["stored_assessments"] = dbm.stored_assessment_count(dbm.get_db())
    return jsonify(data)


@api.get("/privacy-checklist")
def privacy_checklist():
    if request.args.get("format") == "txt":
        text = "SOCIAL MEDIA PRIVACY CHECKLIST\n\n" + "\n".join(f"[ ] {item}" for item in CHECKLIST) + "\n"
        return Response(text, mimetype="text/plain",
                        headers={"Content-Disposition": 'attachment; filename="privacy-checklist.txt"'})
    return jsonify({"title": "Social Media Privacy Checklist", "items": CHECKLIST})
