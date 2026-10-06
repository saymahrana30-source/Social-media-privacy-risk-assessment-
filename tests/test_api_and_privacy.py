"""T28-T30 plus input validation, API behaviour and the privacy/security tests (S01-S12)."""
import sqlite3

from backend.questionnaire import demo_profile_answers

# ------------------------------------------------------------------ T28-T30
def test_T28_database_save(client, app, case):
    r = client.post("/api/assessment", json={"answers": demo_profile_answers()})
    body = r.get_json()
    got = client.get(f"/api/assessment/{body['assessment_id']}").get_json()
    case("T28", "Database save", "POST demo answers, then GET by id", "201; stored score/level equal response; findings stored",
         f"{r.status_code}; {got['overall_score']}/{got['risk_level']} vs {body['overall_score']}/{body['risk_level']}; {len(got['findings'])} findings")
    assert r.status_code == 201 and got["overall_score"] == body["overall_score"] and got["findings"]


def test_T29_sensitive_data_not_stored(client, app, case):
    answers = demo_profile_answers()
    r = client.post("/api/assessment", json={"answers": answers, "phone_number": "9999999999", "email": "x@example.com"})
    r2 = client.post("/api/assessment", json={"answers": answers})
    conn = sqlite3.connect(app.config["DATABASE_PATH"])
    columns = {t: [c[1] for c in conn.execute(f"PRAGMA table_info({t})")] for t in
               ("assessments", "category_scores", "findings", "recommendations")}
    all_text = " ".join(str(v) for t in columns for row in conn.execute(f"SELECT * FROM {t}") for v in row)
    banned = ("phone", "email", "address", "birth", "password", "location_exact", "message")
    bad_cols = [c for cols in columns.values() for c in cols if any(b in c.lower() for b in banned)]
    case("T29", "Sensitive data not stored", "POST with extra phone/email fields; inspect DB schema and content",
         "extra fields rejected (400); no sensitive columns; raw answers/values absent from DB",
         f"extra-field status {r.status_code}; sensitive columns {bad_cols}; '9999999999' in DB: {'9999999999' in all_text}")
    assert r.status_code == 400 and r2.status_code == 201
    assert bad_cols == [] and "9999999999" not in all_text and "x@example.com" not in all_text
    assert "answers" not in all_text.lower()


def test_T30_report_generation(client, case):
    created = client.post("/api/assessment", json={"answers": demo_profile_answers()}).get_json()
    rep = client.get(f"/api/assessment/{created['assessment_id']}/report")
    html = rep.get_data(as_text=True)
    case("T30", "Report generation", "GET /report for a saved assessment", "200 HTML with ID, score, level, checklist, disclaimer",
         f"{rep.status_code}; ID={created['assessment_id'] in html}; disclaimer={'educational risk framework' in html}; checklist={'Enable MFA' in html}")
    assert rep.status_code == 200 and created["assessment_id"] in html
    assert "educational risk framework" in html and "Enable MFA" in html and str(created["overall_score"]) in html


# ------------------------------------------------------------------ validation
def test_missing_answers_rejected(client):
    r = client.post("/api/assessment", json={"answers": {"phone_public": "YES"}})
    assert r.status_code == 400 and "Missing" in " ".join(r.get_json()["details"])


def test_invalid_value_and_unknown_question_rejected(client, safe):
    bad = dict(safe); bad["phone_public"] = "MAYBE"; bad["not_a_question"] = "YES"
    r = client.post("/api/assessment", json={"answers": bad})
    assert r.status_code == 400 and len(r.get_json()["details"]) == 2


def test_non_json_and_wrong_types_rejected(client):
    assert client.post("/api/assessment", data="nope", content_type="text/plain").status_code == 400
    assert client.post("/api/assessment", json={"answers": ["YES"]}).status_code == 400


def test_answer_normalisation(client, safe):
    a = dict(safe); a["phone_public"] = "not sure"
    assert client.post("/api/assessment", json={"answers": a}).status_code == 201


# ------------------------------------------------------------------ API behaviour
def test_recommendations_and_questionnaire_endpoints(client):
    q = client.get("/api/questionnaire").get_json()
    assert q["total_questions"] >= 40 and len(q["categories"]) == 10
    created = client.post("/api/assessment", json={"answers": demo_profile_answers()}).get_json()
    recs = client.get(f"/api/assessment/{created['assessment_id']}/recommendations").get_json()
    assert recs["grouped"]["IMMEDIATE"]


def test_simulate_endpoint_is_stateless(client, app):
    r = client.post("/api/assessment/simulate-improvement", json={"answers": demo_profile_answers(), "apply": "all"})
    assert r.status_code == 200 and r.get_json()["after"]["score"] == 0
    conn = sqlite3.connect(app.config["DATABASE_PATH"])
    assert conn.execute("SELECT COUNT(*) FROM assessments").fetchone()[0] == 0


def test_dashboard_and_checklist(client):
    s = client.get("/api/dashboard/stats").get_json()
    assert s["population"] >= 1000 and sum(s["risk_distribution"].values()) == s["population"]
    assert 0 <= s["average_overall_score"] <= 100
    assert len(client.get("/api/privacy-checklist").get_json()["items"]) == 18
    assert "[ ] Enable MFA" in client.get("/api/privacy-checklist?format=txt").get_data(as_text=True)


def test_unknown_assessment_404(client):
    assert client.get("/api/assessment/doesnotexist").status_code == 404


# ------------------------------------------------------------------ privacy & security (S01-S12)
def test_S01_delete_requires_token(client, case):
    created = client.post("/api/assessment", json={"answers": demo_profile_answers()}).get_json()
    aid = created["assessment_id"]
    no_token = client.delete(f"/api/assessment/{aid}").status_code
    wrong = client.delete(f"/api/assessment/{aid}", headers={"X-Delete-Token": "wrong"}).status_code
    ok = client.delete(f"/api/assessment/{aid}", headers={"X-Delete-Token": created["delete_token"]}).status_code
    gone = client.get(f"/api/assessment/{aid}").status_code
    case("S01", "Data deletion & authorization", "DELETE without / with wrong / with correct token", "403, 403, 200, then 404",
         f"{no_token}, {wrong}, {ok}, {gone}")
    assert (no_token, wrong, ok, gone) == (403, 403, 200, 404)


def test_S02_delete_cascades(client, app):
    created = client.post("/api/assessment", json={"answers": demo_profile_answers()}).get_json()
    client.delete(f"/api/assessment/{created['assessment_id']}", headers={"X-Delete-Token": created["delete_token"]})
    conn = sqlite3.connect(app.config["DATABASE_PATH"])
    assert conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM category_scores").fetchone()[0] == 0


def test_S03_delete_token_stored_only_as_hash(client, app):
    created = client.post("/api/assessment", json={"answers": demo_profile_answers()}).get_json()
    conn = sqlite3.connect(app.config["DATABASE_PATH"])
    stored = conn.execute("SELECT delete_token_hash FROM assessments").fetchone()[0]
    assert created["delete_token"] not in stored and len(stored) == 64


def test_S04_security_headers(client, case):
    r = client.get("/api/privacy-checklist")
    csp = r.headers.get("Content-Security-Policy", "")
    case("S04", "Security headers", "GET any endpoint", "CSP default-src 'self', nosniff, frame deny",
         f"CSP ok={csp.startswith(chr(100)+'efault-src')}; nosniff={r.headers.get('X-Content-Type-Options')}; XFO={r.headers.get('X-Frame-Options')}")
    assert "default-src 'self'" in csp and "script-src 'self'" in csp
    assert r.headers["X-Content-Type-Options"] == "nosniff" and r.headers["X-Frame-Options"] == "DENY"


def test_S05_rate_limiting(tmp_path, case):
    from backend.app import create_app
    app = create_app({"DATABASE_PATH": str(tmp_path / "rl.db"), "RATE_LIMIT_PER_MINUTE": 5, "RATE_LIMIT_POST_PER_MINUTE": 3})
    c = app.test_client()
    codes = [c.get("/api/privacy-checklist").status_code for _ in range(7)]
    case("S05", "API rate limiting", "7 GET requests with a limit of 5/min", "first 5 -> 200, then 429", str(codes))
    assert codes[:5] == [200] * 5 and codes[5:] == [429, 429]


def test_S06_xss_is_escaped_in_report(client, app):
    created = client.post("/api/assessment", json={"answers": demo_profile_answers()}).get_json()
    conn = sqlite3.connect(app.config["DATABASE_PATH"])
    conn.execute("UPDATE findings SET description=? WHERE assessment_id=?", ("<script>alert(1)</script>", created["assessment_id"]))
    conn.commit()
    html = client.get(f"/api/assessment/{created['assessment_id']}/report").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html


def test_S07_unexpected_server_error_does_not_leak(client, monkeypatch):
    import backend.routes.api as api_module
    monkeypatch.setattr(api_module, "run_assessment", lambda *_: (_ for _ in ()).throw(RuntimeError("secret internals")))
    app_client = client
    app_client.application.config["PROPAGATE_EXCEPTIONS"] = False
    r = app_client.post("/api/assessment", json={"answers": {}})
    assert r.status_code == 500 and "secret internals" not in r.get_data(as_text=True)


def test_S08_oversized_body_rejected(client):
    r = client.post("/api/assessment", data="x" * 40000, content_type="application/json")
    assert r.status_code == 413


def test_S09_retention_purge(client, app):
    from backend.models import db as dbm
    created = client.post("/api/assessment", json={"answers": demo_profile_answers()}).get_json()
    conn = sqlite3.connect(app.config["DATABASE_PATH"])
    conn.execute("UPDATE assessments SET created_at='2000-01-01T00:00:00+00:00'"); conn.commit()
    client.post("/api/assessment", json={"answers": demo_profile_answers()})  # triggers purge
    assert client.get(f"/api/assessment/{created['assessment_id']}").status_code == 404


def test_S10_env_example_has_no_real_secret():
    from pathlib import Path
    text = (Path(__file__).resolve().parent.parent / ".env.example").read_text()
    assert "change-me" in text and "password" not in text.lower()


def test_S11_no_questions_ask_for_personal_values():
    from backend.questionnaire import QUESTIONS
    for q in QUESTIONS:
        assert q.options and all(o.isupper() for o in q.options), q.id  # only enumerated answers, never free text


def test_S12_metadata_viewer_strips_exif(tmp_path):
    from PIL import Image
    from tools.metadata_viewer import read_metadata, strip_metadata
    img = Image.new("RGB", (8, 8), "red")
    exif = Image.Exif(); exif[0x010F] = "FakeCam"; exif[0x0131] = "FakeSoftware"
    src = tmp_path / "in.jpg"; img.save(src, exif=exif)
    assert read_metadata(str(src))["Make"] == "FakeCam"
    out = tmp_path / "out.jpg"; strip_metadata(str(src), str(out))
    assert read_metadata(str(out)) == {} and src.exists()
