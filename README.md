# Social Media Privacy Risk Assessment Framework

> Privacy-focused cybersecurity framework for assessing social-media exposure, account-security practices, social-engineering risk, digital-footprint risk, and personalized privacy improvements using synthetic/self-reported data.

**This project is designed for defensive cybersecurity and privacy education. It uses synthetic or voluntarily provided assessment responses and does not scrape, track, or profile real social-media users.**

## Overview
A user answers a 56-question questionnaire about their *settings and habits* (never about actual phone numbers, addresses or passwords). The framework produces a **Privacy Risk Score (0-100)**, a risk level (LOW / MODERATE / HIGH / CRITICAL), ten category scores, ranked findings, prioritised recommendations, a "what if I improve my settings?" simulation, a printable report and a privacy checklist. A dashboard shows aggregate trends over 1,200 **synthetic** fictional profiles.

**Higher score = higher assessed exposure/risk.**

## Problem Statement
Hiring teams, schools and enterprises increasingly evaluate online footprints, and regulators emphasise data minimisation and consent. Students, job-seekers and small businesses rarely know which settings expose them to doxxing, impersonation and social engineering. A structured, repeatable, privacy-preserving self-assessment makes privacy hygiene practical.

## Objectives
1. Assess exposure across 10 categories using self-reported answers only.
2. Score risk with transparent, configurable weights.
3. Explain *why* each weakness matters and *what to do*, in priority order.
4. Show the effect of improvements (simulator).
5. Practise privacy by design: store only scores and finding types.

## Cybersecurity Relevance
Maps to: security awareness, privacy engineering, GRC (risk scoring, control checklists), identity protection, IAM hygiene (MFA, sessions, third-party access), application security (validation, rate limiting, CSP, XSS defence) and employee training. Roles: Cybersecurity Analyst, Privacy Analyst, GRC Analyst, SOC Analyst, Security Consultant, IAM Analyst, Security Awareness Specialist, Privacy Engineer.

## Privacy vs Security
*Privacy* controls how personal information is collected, shared, exposed and used. *Security* protects systems and accounts from unauthorised access. A strong password with MFA protects the account, yet a public phone number, birthday and travel plan still leak information. **Strong account security != strong privacy.** The synthetic dataset includes a "secure but open" archetype to demonstrate this. See `docs/CONCEPTS.md`.

## Features
- 56-question questionnaire (YES/NO/SOMETIMES/NOT SURE and PUBLIC/FRIENDS/PRIVATE style answers) in 10 categories
- Strict input validation (allow-list; unknown fields rejected)
- `extract_privacy_features()`, 10 category scores, configurable weighted overall score
- `generate_privacy_findings()` and `generate_recommendations()` (IMMEDIATE / IMPORTANT / GOOD PRACTICE)
- Improvement simulator (framework simulation, clearly labelled)
- Radar chart, dashboard with 6 charts, printable HTML report, printable checklist
- Privacy-first SQLite storage, retention limit, delete-token authorisation
- Optional local photo-metadata viewer/cleaner (`tools/metadata_viewer.py`)
- 52 automated tests (33 documented cases + 19 supporting tests)

## Architecture
```
User -> Privacy Questionnaire -> Input Validation -> Feature Extraction
     -> Category Analysis (10 categories) -> Risk Scoring Engine -> Overall Score + Level
     -> Findings Engine -> Recommendation Engine -> Dashboard -> Report
     (optional anonymised aggregates -> analytics)
```
Details and diagram: `docs/ARCHITECTURE.md`.

## Technology Stack
**Beginner stack (used):** HTML/CSS/vanilla JS, Python **Flask**, **SQLite**, **Chart.js** (vendored locally, no CDN), HTML report (print to PDF). Chosen because it has few moving parts, runs offline, and every line can be explained in a viva. *Limits:* in-memory rate limiter (single process), no accounts. *Modern alternative:* React + FastAPI + PostgreSQL gives typed schemas and scale but needs more setup. The scoring engine is framework-independent, so migrating is easy.

## Privacy Questionnaire
Categories A-J: Profile Visibility (4), Personal Information (7), Location Privacy (7), Posts & Content (4), Friends/Followers (4), Tagging & Mentions (5), Authentication & Account Security (7), Third-Party Apps (5), Messaging & Social Engineering (7), Digital Footprint (6) = **56 questions**. Source of truth: `backend/questionnaire.py`. For "is this visible?" questions you only answer YES / NO / NOT SURE - the data itself is never entered.

## Risk Categories
Profile Exposure, Personal Information, Location Exposure, Content Exposure, Connection Risk, Tagging Risk, Account Security, Third-Party App Risk, Social Engineering, Digital Footprint. Each is 0-100 (0 = lower assessed risk).

## Risk Scoring
Each answer has a risk value (0-1); e.g. YES on "phone public" = 1.0, NOT SURE = 0.6, NO = 0. A category score is the *question-weighted average x 100*. The overall score is the weighted average of category scores (default weights below, configurable and auto-normalised to 100%).

| Category | Weight | | Category | Weight |
|---|---|---|---|---|
| Profile | 10% | | Account Security | 15% |
| Personal Information | 15% | | Third-Party Apps | 5% |
| Location | 15% | | Social Engineering | 10% |
| Posts & Content | 10% | | Digital Footprint | 5% |
| Connections | 10% | | Tagging | 5% |

Levels: **0-20 LOW, 21-40 MODERATE, 41-70 HIGH, 71-100 CRITICAL** (score rounded half-up first, so the number on screen and its level always agree).
> **Important:** weights, risk values and thresholds are *educational assumptions* and must be validated/calibrated before any professional risk decision. A score is not a guarantee that an account will or will not be compromised.

## Privacy Findings
Any answer with risk >= 0.5 creates a finding, ranked by `risk x question weight x severity`. NOT SURE counts as "possibly exposed" and is flagged as such.

## Recommendation Engine
One personalised recommendation per finding, grouped **IMMEDIATE** (HIGH severity), **IMPORTANT** (MEDIUM), **GOOD PRACTICE** (LOW), plus awareness guidance for any category scoring HIGH or worse.

## Improvement Simulator
`POST /api/assessment/simulate-improvement` re-scores your answers with selected fixes applied (stateless - nothing is stored). Demo: **75 CRITICAL -> 52 HIGH (23-point reduction)** after 9 fixes. Always labelled a framework simulation, not a guarantee.

## Digital Footprint
Active footprint (what you deliberately share) vs passive footprint (data generated through activity). Only *self-reported* practices are assessed: old posts, unused accounts, public comments, profile history, privacy-settings reviews, self-search.

## Social Engineering Awareness
Explains conceptually how public context (employer, college, travel, family, interests) can make scams convincing, and how to defend: verify through another channel, never share verification codes, avoid unknown connections. No attack scripts or personalised messages are produced.

## Account Security
MFA, unique passwords, password manager, login alerts, recovery options, active sessions, trusted devices. "Security controls enabled" (x/11) is shown on the results page and dashboard.

## Privacy Dashboard
`/dashboard.html`: cards (average score, level, high-risk categories, findings, controls) and six charts - category risk, risk distribution, top weaknesses, account-security controls, digital-footprint risk, improvement comparison - built from synthetic data, with a **Start Privacy Assessment** button.

## Privacy Report
`GET /api/assessment/{id}/report` -> printable HTML (Print -> Save as PDF) with ID, date, score, level, category scores, top findings, recommendations, priority actions, checklist and disclaimer. Built only from stored scores/finding types (no sensitive data). Jinja2 auto-escaping prevents XSS.

## Privacy by Design
Data minimisation (no PII fields; answers not stored), purpose limitation (scores only), privacy by default (no accounts, no tracking), least privilege (unguessable ID + delete token), transparency (on-screen notices), user control (delete endpoint), retention limitation (auto-purge after 30 days), secure processing (validation, CSP, rate limits). See `docs/PRIVACY_BY_DESIGN.md`.

## Installation
```bash
# STEP 1 - get the project
git clone <repository-url> Social-Media-Privacy-Risk-Assessment
cd Social-Media-Privacy-Risk-Assessment
# STEP 2 - virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
# STEP 3 - dependencies
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
# STEP 4 - (re)generate the synthetic dataset (optional; a copy is included)
python data/generate_dataset.py
```

## Usage
```bash
# STEP 5 + 6 - one command starts API and frontend (Flask serves both)
python backend/app.py
# STEP 7 - open http://127.0.0.1:5000  -> "Start Privacy Assessment"
# STEP 8 - complete the questionnaire (or click "Load fictional demo answers")
# STEP 9 - read your Privacy Risk Score
# STEP 10 - explore category analysis (radar chart, bars, findings, recommendations)
# STEP 11 - run the improvement simulation
# STEP 12 - open the printable report
```
Other tools: `python tools/metadata_viewer.py photo.jpg [--strip clean.jpg]`, `python tools/batch_score.py data/social_media_privacy_assessments.csv reports/scored.csv`.

## API Documentation
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/assessment` | Score answers, store scores only, return result + one-time delete token |
| GET | `/api/assessment/{id}` | Stored scores/findings |
| GET | `/api/assessment/{id}/recommendations` | Prioritised recommendations |
| GET | `/api/assessment/{id}/report` | Printable HTML report |
| POST | `/api/assessment/simulate-improvement` | Stateless what-if simulation |
| GET | `/api/dashboard/stats` | Aggregates over the synthetic dataset |
| GET | `/api/privacy-checklist` | Checklist (`?format=txt` to download) |
| DELETE | `/api/assessment/{id}` | Delete (needs `X-Delete-Token`) |
| GET | `/api/questionnaire`, `/api/demo-profile` | Questionnaire and fictional demo answers |

Full request/response/validation/error details: `docs/API.md`.

## Testing
```bash
python -m pytest -q                          # 52 tests
python tests/generate_test_report.py         # writes docs/TEST_RESULTS.md
```
33 documented cases (T01-T30 scoring/functional + S-series security) have Test ID, scenario, input, expected, actual and pass/fail in `docs/TEST_RESULTS.md`; 19 further tests cover validation and API behaviour.

## Security & Privacy Testing
Verified automatically: no sensitive columns or values in the database (extra fields such as phone/e-mail are rejected); allow-list validation; XSS escaping in the report; rate limiting (429); body-size limit (413); error responses do not leak internals; delete requires a token and cascades; token stored only as a SHA-256 hash; retention purge; security headers/CSP; no free-text questions; metadata tool strips EXIF from a copy and leaves the original untouched.

## Results
| Measurement | Value |
|---|---|
| Fictional demo profile | **75/100 CRITICAL** -> after 9 fixes **52/100 HIGH** (-23) |
| Synthetic population (1,200 profiles) | average **39.5 (MODERATE)**; LOW 303, MODERATE 348, HIGH 412, CRITICAL 137 |
| Avg score if all IMMEDIATE / +IMPORTANT / all fixes applied (250-profile sample) | 38.9 -> 27.6 -> 8.1 -> 5.6 |
| Tests | 52 passed, 0 failed |

These figures come from synthetic data and an educational model; they show the framework works, not how real people behave.

## Limitations
Self-reported answers can be wrong or biased; risk values/weights are assumptions, not calibrated statistics; no real platform integration (by design); the in-memory rate limiter works for one process only; no user accounts; the questionnaire is platform-neutral so some platform-specific settings differ.

## Future Improvements
Platform-specific checklists, configurable organisational policies, awareness quizzes, privacy maturity scoring, teen/family safety modules, employee training mode, GRC reporting, anonymous organisational trend analysis, better calibration, localisation, accessibility audit, report comparison over time, client-side-only mode. No invasive monitoring or scraping.

## Screenshots
See `screenshots/` and `docs/SCREENSHOT_CHECKLIST.md` for the 29 proof shots and filenames.

## Learning Outcomes
Risk scoring models; privacy vs security; data minimisation and privacy by design; secure REST API design; input validation, XSS/CSP/rate limiting; test design (boundaries, negative tests); synthetic-data generation; data visualisation; GitHub documentation.

## Ethical Disclaimer
Defensive education only. No scraping, no account enumeration, no bypassing privacy settings, no profiling of real individuals, no social-engineering scripts. Use synthetic or your *own* voluntarily entered answers. This is an educational risk framework, not a guarantee that an account will or will not be compromised.

## Author
<Your name> - <saymah rana>
