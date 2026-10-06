# REST API

All responses are JSON (except the HTML report and the text checklist). Base URL `http://127.0.0.1:5000`.

**Authentication:** none - the app has no accounts and holds no personal data. **Authorization:** an assessment id is an unguessable 128-bit value; deletion additionally needs the one-time `X-Delete-Token` returned at creation. **Rate limiting:** 120 req/min per IP overall and 20 writes/min (configurable). **Errors:** `400` validation `{error, details[]}`, `403` bad token, `404` unknown id, `413` body > 32 KB, `429` rate limit, `500` generic message (no stack traces).

## POST /api/assessment
Request: `{"answers": {"<question_id>": "<ANSWER>", ...}}` - all 56 questions required; answers case-insensitive (`not sure` -> `NOT_SURE`). Extra top-level fields (e.g. `phone_number`) are rejected.
Response `201`: `assessment_id, created_at, delete_token, overall_score, risk_level, weights_used, category_scores, category_labels, high_risk_categories, top_risks, findings, recommendations{items,grouped,awareness}, controls_enabled, disclaimer`.
Privacy: answers are scored in memory; only scores, finding types and severity are written to the database.

## GET /api/assessment/{id}
Stored result: `overall_score, risk_level, created_at, category_scores, findings[{category, finding_type, severity, description, recommendation, priority}], controls_enabled`.

## GET /api/assessment/{id}/recommendations
`{items, grouped:{IMMEDIATE, IMPORTANT, "GOOD PRACTICE"}, awareness}`.

## GET /api/assessment/{id}/report[?download=1]
Printable HTML report.

## POST /api/assessment/simulate-improvement
Request: `{"answers": {...56...}, "fix_ids": ["mfa_enabled", ...]}` or `"apply": "all"` or `"apply": ["IMMEDIATE"]` or `"changes": {"phone_public": "NO"}`.
Response: `before{score,level,category_scores}, after{...}, risk_reduction, changes[], disclaimer`. Stateless - nothing is stored.

## GET /api/dashboard/stats
Aggregates over the synthetic dataset plus the count of stored assessments.

## GET /api/privacy-checklist[?format=txt]
18-item checklist as JSON or downloadable text.

## DELETE /api/assessment/{id}
Header `X-Delete-Token: <token>` -> `200 {"deleted": true}`; findings and category scores are removed by cascade.

## GET /api/questionnaire, GET /api/demo-profile
Questionnaire definition (ids, text, options only - no scoring internals) and the fictional demo answers.

### Example
```bash
curl -s localhost:5000/api/demo-profile > demo.json
python - <<'PY'
import json, urllib.request
answers = json.load(open("demo.json"))["answers"]
req = urllib.request.Request("http://127.0.0.1:5000/api/assessment", json.dumps({"answers": answers}).encode(),
                             {"Content-Type": "application/json"})
r = json.load(urllib.request.urlopen(req)); print(r["overall_score"], r["risk_level"])
PY
```
