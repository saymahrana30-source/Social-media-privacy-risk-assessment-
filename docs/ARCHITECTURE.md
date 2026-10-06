# Architecture & folder guide

```
User
 | Privacy Questionnaire (frontend/assessment.html)
 v
Input Validation (utils/validation.py)  -- unknown ids / values / fields rejected
 v
Feature Extraction (services/assessment_engine.py)
 v
+-------------------------------------------------------------+
| Category analysers (10): profile, personal info, location,  |
| content, connections, tagging, account security, third-party|
| apps, social engineering, digital footprint                 |
+-------------------------------------------------------------+
 v
Category Scores -> Risk Scoring Engine (scoring_engine.py) -> Overall Risk + Level
 v
Findings Engine (findings_engine.py) -> Recommendation Engine (recommendation_engine.py)
 v
Privacy Dashboard / Results page / Privacy Report (templates/report.html)
 v (optional, anonymised aggregates only)
Analytics: services/dashboard_service.py over the synthetic dataset
```
The ten categories are implemented *data-driven*: `backend/questionnaire.py` defines each question's category, weight, severity, finding text and recommendation, so one scoring function analyses all ten and adding a question is a one-block change.

## Folders
| Path | Purpose |
|---|---|
| `backend/app.py` | Flask app factory: security headers, rate limiter, error handlers, static frontend |
| `backend/config.py` | Environment-driven settings (`.env`) |
| `backend/questionnaire.py` | The 56 questions, scales, weights, findings, recommendations, demo profile, checklist |
| `backend/routes/api.py` | REST endpoints |
| `backend/models/db.py` | SQLite schema + privacy-first persistence (scores only), retention, delete |
| `backend/services/` | `assessment_engine`, `scoring_engine`, `findings_engine`, `recommendation_engine`, `improvement_simulator`, `dashboard_service` |
| `backend/utils/` | Validation (allow-list) and rate limiter |
| `backend/templates/report.html` | Printable report (auto-escaped) |
| `frontend/` | `index`, `learn`, `assessment`, `results`, `dashboard`, `checklist` pages; `css/`, `js/` (Chart.js vendored under `js/vendor/`) |
| `data/` | `generate_dataset.py` and the synthetic CSV (1,200 rows) |
| `tools/` | Local metadata viewer/cleaner, batch scorer |
| `tests/` | 52 pytest tests + `generate_test_report.py` |
| `reports/` | Generated reports/junit output (git-ignored) |
| `screenshots/` | Proof-of-work screenshots |
| `docs/` | Documentation (this folder) |
| `instance/` | SQLite database at runtime (git-ignored) |

## Database (spec section 25)
```
ASSESSMENTS(assessment_id PK, overall_score, risk_level, created_at, delete_token_hash)
CATEGORY_SCORES(category_score_id PK, assessment_id FK, category, score)
FINDINGS(finding_id PK, assessment_id FK, category, finding_type, severity, description)
RECOMMENDATIONS(recommendation_id PK, finding_type UNIQUE, recommendation, priority)   -- static catalogue
```
No phone/e-mail/address/birth-date/password/location/message columns exist. `delete_token_hash` is a SHA-256 hash of a random token, not personal data.
