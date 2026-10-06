# Project Report: Social Media Privacy Risk Assessment Framework

## Abstract
This project presents a Social Media Privacy Risk Assessment Framework: a defensive, educational tool that converts self-reported privacy settings and habits into a 0-100 risk score with ten category scores, ranked findings, prioritised recommendations and a what-if simulator. It uses synthetic data only, stores no personal information, and is validated by 52 automated tests. On a fictional demonstration profile the score falls from 75 (CRITICAL) to 52 (HIGH) after nine recommended changes.

## 1. Introduction
Online footprints are examined by employers, schools and attackers alike. People often do not know which settings expose them. This project offers a repeatable, privacy-preserving self-assessment that teaches as it scores.

## 2. Problem Statement
Users lack a simple way to measure social-media exposure across visibility, personal information, location, content, connections, tagging, account security, third-party access, social-engineering behaviour and historical footprint, and to turn the result into concrete actions - without handing over the very data they want to protect.

## 3. Objectives
(1) Assess ten exposure categories from self-reported answers; (2) score risk transparently with configurable weights; (3) generate prioritised recommendations and awareness guidance; (4) simulate improvements; (5) apply privacy by design; (6) verify with tests.

## 4. Social Media Privacy Background
Social-media privacy concerns who can see, collect and use information about a person. Public profiles, contact details, birth dates, workplace and location trails increase the information available for profiling, impersonation and scams. Regulators emphasise data minimisation and consent.

## 5. Digital Footprint
The active footprint comprises deliberate posts; the passive footprint comprises data generated through activity. The framework evaluates self-reported old posts, unused accounts, public comments, profile history and review habits.

## 6. Privacy vs Security
Privacy governs exposure and use of personal information; security protects systems and accounts. They overlap (MFA, sessions) but differ: a protected account can still publish too much. The synthetic dataset includes archetypes that are secure-but-open and private-but-unsafe.

## 7. Social Engineering
Attackers exploit trust and urgency; public context (employer, college, travel, family, interests, events) can make messages believable. The framework scores behaviours (unknown connections, suspicious links, shared verification codes, impersonation checks) and teaches defences. It contains no attack content.

## 8. Existing Approaches
Platform privacy check-ups review settings on a single platform; awareness training explains concepts generically; OSINT-style scanners examine real profiles, which raises ethical and legal problems. This framework is platform-neutral, questionnaire-based, and examines no real profile.

## 9. Proposed Framework
A questionnaire feeds validation, feature extraction, ten category analyses, a weighted scoring engine, classification, findings and recommendation engines, a simulator, a dashboard and a report.

## 10. Architecture
Flask API and static frontend; SQLite persistence limited to scores and finding types; Chart.js visualisations; Jinja2 report. See docs/ARCHITECTURE.md.

## 11. Questionnaire Design
56 questions in categories A-J using YES / NO / SOMETIMES / NOT SURE or PUBLIC / FRIENDS / PRIVATE (and EVERYONE / FRIENDS / NO_ONE for tagging). Questions ask whether information is visible; no personal values are requested. NOT SURE is scored as possibly exposed.

## 12. Synthetic Dataset
1,200 fictional records generated with a fixed seed from a Beta-distributed carelessness level, five archetypes, per-category shifts and a per-question prevalence offset; risk_score and risk_level come from the same engine used by the app.

## 13. Feature Engineering
`extract_privacy_features()` maps each answer to a risk value (0-1), weight, category and contribution type (for example, exposure, account-security or social-engineering contribution) and records control states.

## 14. Category Risk Analysis
Ten category scores, each 0-100, are the weighted mean of question risks scaled by 100; higher means more assessed exposure.

## 15. Risk Scoring
Overall score = sum(category score x category weight). Default weights: profile 10, personal information 15, location 15, content 10, connections 10, tagging 5, account security 15, third-party apps 5, social engineering 10, digital footprint 5. Levels: 0-20 LOW, 21-40 MODERATE, 41-70 HIGH, 71-100 CRITICAL. Weights and thresholds are educational assumptions requiring calibration.

## 16. Findings Engine
Answers with risk >= 0.5 become findings, ranked by risk x weight x severity, with the top five highlighted and high-risk categories listed.

## 17. Recommendation Engine
Each finding maps to a recommendation grouped IMMEDIATE, IMPORTANT or GOOD PRACTICE; categories scoring HIGH or worse add awareness guidance.

## 18. Improvement Simulator
Re-scores answers with selected fixes (or all fixes of a priority) and reports before/after scores, level change and risk reduction, always labelled as a framework simulation.

## 19. Account Security
MFA, unique passwords, password manager, login alerts, recovery options, session and device review contribute to the account-security score and to the 'controls enabled' indicator (x of 11).

## 20. Third-Party Applications
Connected, unused, old and broadly permissioned apps and social sign-ins are assessed under the principle of least privilege.

## 21. Location Privacy
Real-time sharing, geotagging, check-ins, home/work exposure, travel plans and routines are assessed from self-reports; no geolocation is performed. Posting after leaving a location reduces immediate exposure.

## 22. Digital Footprint Analysis
Self-reported historical content, unused accounts and review habits are scored; periodic review is recommended.

## 23. Privacy Dashboard
Cards and six charts summarise the synthetic population: category averages, risk distribution, top weaknesses, control adoption, digital-footprint risk and improvement comparison.

## 24. Privacy by Design
Data minimisation, purpose limitation, privacy by default, least privilege, transparency, user control, retention limitation and secure processing are implemented and tested (docs/PRIVACY_BY_DESIGN.md).

## 25. Testing
33 documented cases (T01-T30 plus S-series) and 19 supporting tests - 52 in total - cover private/public extremes, each risky setting, calculations, boundaries at 20/40/70, recommendations, simulation, persistence, data minimisation and report generation (docs/TEST_RESULTS.md).

## 26. Security Testing
Verified: no sensitive data stored, strict validation, XSS escaping, rate limiting, request-size limit, non-leaking errors, token-protected cascading deletion, hashed token, retention purge, security headers and CSP, and local-only metadata handling.

## 27. Results
Demonstration profile: 75 CRITICAL to 52 HIGH (-23). Synthetic population (n=1,200): mean 39.5 (MODERATE); LOW 303, MODERATE 348, HIGH 412, CRITICAL 137. Applying all IMMEDIATE fixes lowers the mean (250-profile sample) from 38.9 to 27.6; IMMEDIATE+IMPORTANT to 8.1; all fixes to 5.6. These describe the model on synthetic data, not real behaviour.

## 28. Limitations
Self-reported data, assumed weights, no empirical calibration, platform-neutral wording, single-process rate limiting, no accounts, synthetic evaluation only.

## 29. Future Scope
Platform-specific checklists, organisational policies, awareness quizzes, maturity scoring, teen/family modules, employee training, GRC reporting, anonymous trend analysis, calibration against expert judgement, localisation, accessibility, comparison over time, local-only client-side mode.

## 30. Conclusion
The framework shows that meaningful privacy assessment is possible without collecting personal data: it scores configuration and behaviour, explains risk, prioritises action and demonstrates privacy-by-design engineering in practice.
