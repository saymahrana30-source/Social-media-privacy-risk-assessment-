# Privacy by Design in this project

| Principle | How the application applies it |
|---|---|
| Data minimisation | Questions ask "is it visible?", never for the value. Server stores only scores, finding types, severity, timestamps. |
| Purpose limitation | Data is used only to compute and display the assessment; no analytics profiling, no third parties. |
| Least privilege | No accounts; unguessable assessment ids; delete needs a one-time token; no admin endpoints. |
| Privacy by default | Nothing stored beyond scores; answers stay in the browser tab (sessionStorage) for the simulator and vanish on close. |
| Transparency | On-screen notice before the questionnaire; disclaimers on results and report; this documentation. |
| User control | `DELETE /api/assessment/{id}` + "Delete my stored result" button; NOT SURE option instead of forcing answers. |
| Retention limitation | Assessments older than `RETENTION_DAYS` (30) are purged automatically. |
| Secure processing | Strict validation, rate limiting, CSP and security headers, escaped output, hashed delete token, no secrets in code (`.env`). |
