# CHEATSHEET — AI Autonomy 4B M3 — Control Center Operator Quick Reference
Stand: 2026-01-09  
Scope: View-only / Docs-only Ops

## 1. Daily Routine (5–10 Minuten)
Checklist:
- [ ] GitHub Checks: required gates "green" (snapshot)
- [ ] Control Center Dashboard: lädt stabil (kein wiederholter Timeout)
- [ ] Evidence: falls Abweichung → Operator Notes mit Timestamp

## 2. "Wenn X, dann Y" (Kurzentscheidungen)
- Wenn required gate rot → sofort Incident Triage starten (S2)
- Wenn Dashboard sporadisch timed out → timeout-sichere Methode + Evidence (S1)
- Wenn Verdacht auf Scope Drift → SCOPE_KEEPER aktivieren (S3)

## 3. Evidence Minimum (immer)
- Timestamp (Europe/Berlin)
- Check-Name (exakt)
- 1 Screenshot oder 1 CLI Snippet
- 3 bullets: Symptom, vermutete Ursache, nächster Schritt

## 4. Timeout-Safe Monitoring (Kurz)
- Kein Dauer-Streaming.
- Lieber: status snapshots + manuelles Refresh.
- Dokumentiere "Attempt #" bei wiederholten Timeouts.

## 5. Triage Shortcuts
**docs-reference-targets-gate:**
- Suche nach nicht existierenden Targets / path-ähnlichen Strings
- Neutralisieren oder korrigieren

**Link Debt Trend:**
- Markdown-Hygiene, keine "nackten" Targets

**Policy / Guardrails:**
- Stop → Eskalation → Evidence sichern

## 6. Cross-Links
- **Incident Triage Runbook:**  
  `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_INCIDENT_TRIAGE.md`
- **Operations Runbook:**  
  `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md`
- **Dashboard Runbook:**  
  `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_DASHBOARD.md`
