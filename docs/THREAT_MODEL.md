# Threat model and privacy risk matrix (defensive)

Fictional social-media user "Alex" (no real person). Likelihood and impact are qualitative and depend on context - treat them as educational assumptions.

## Threat model
| Asset | Threat | Exposure | Potential impact | Existing control | Recommended control |
|---|---|---|---|---|---|
| Account | Account takeover | Weak/reused password, no MFA, unchecked sessions | Loss of account, abuse of contacts | Password | MFA, unique passwords + manager, login alerts, review sessions/devices |
| Identity information | Impersonation | Public birthday, workplace, photos | Fake profiles, fraud attempts | Profile name | Hide birth year, limit workplace/education visibility, report fakes |
| Contact information | Phishing | Public phone/e-mail | Targeted scam messages, spam | None | Hide contact details; use alias e-mail; verify links |
| Location privacy | Physical-safety exposure / stalking | Live location, check-ins, travel posts | Safety risk, unattended home signal | Platform defaults | Delay posts, disable geotags, limit audience |
| Private content | Unwanted profiling / oversharing | Public posts and old content | Reputation harm, data aggregation | Post audience setting | Friends-only default, review historical posts |
| Social relationships | Social engineering | Unknown connections, public friend list | Trust abuse via fake friends | Friend requests | Verify requests, hide lists, audit connections |
| Third-party app access | Excess permissions / app compromise | Unused or broad integrations | Data leakage via app | App consent screen | Least privilege, revoke old apps |
| Tags & mentions | Exposure through others | Anyone can tag, no review | Location/identity leaks by friends | None | Tag review, limit who can tag |

## Privacy risk matrix
| Item | Likelihood | Impact |
|---|---|---|
| Public phone number | Medium | Medium |
| Real-time location exposure | Medium | High |
| MFA disabled | Medium | High |
| Password reuse | Medium | High |
| Unknown connection requests accepted | High | Medium |
| Public full birth date | Medium | Medium |
| Tag review disabled | Medium | Medium |
| Old posts never reviewed | High | Low |
| Unused third-party apps connected | Medium | Medium |
| Sharing verification codes | Low | High |

Actual risk depends on context (who you are, who might target you, what else is public).

## Threat model of the application itself
| Threat | Mitigation |
|---|---|
| Users submitting personal data | Allow-list validation, no free-text fields, extra fields rejected, nothing but scores stored |
| XSS | `textContent` rendering in JS, Jinja2 auto-escape, CSP `script-src 'self'` |
| Abuse / DoS | Per-IP rate limits, 32 KB body limit |
| Database disclosure | Contains only scores and finding types; random unguessable ids; token hash |
| Third-party script risk | Chart.js vendored locally; no CDN |
| Information leakage in errors | Generic 500 handler |
