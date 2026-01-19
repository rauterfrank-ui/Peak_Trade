# Peak_Trade — Templates — Finish C Incident Pack (v1, NO‑LIVE default)

**Datum:** 2026-01-18  
**Status:** DRAFT  
**Modus:** governance‑safe, evidence‑first, **NO‑LIVE default**

> **Stop Rules (Incident Pack)**  
> - Keine realen Broker‑Calls/Orders im Rahmen dieses Templates.  
> - Keine Secrets in Artefakten.  
> - Snapshot‑only Sammlung (keine Watch‑Loops).  
> - Wenn Scope Richtung „Live enable“ driftet ⇒ STOP.

---

## 0) Zweck

Dieses Template standardisiert einen Incident‑Pack für den **Dry‑Run / Mock‑Broker** Track von Finish C:

- schnelle Einordnung
- Snapshot‑Artefakte (Logs/State/Audit)
- Hypothesen + Repro‑Steps
- Mitigation (nur safe, ohne Live‑Enablement)

---

## 1) Incident Header

```markdown
## Incident: Finish C — [TITLE]

**Incident ID:** INC-YYYYMMDD-HHMM-[TAG]  
**Date:** YYYY-MM-DD  
**Owner:** ops / aiops  
**Severity:** [S0|S1|S2|S3]  
**Status:** [OPEN|MITIGATED|RESOLVED]

### Summary
[1–3 Sätze: Was ist passiert? Welche Komponente?]

### Scope
- Component(s): [BrokerAdapter | Orchestrator | Reconciler | SafetyRails | Observability]
- Mode: DRY-RUN / MOCK-ONLY
- Live impact: NONE (NO-LIVE default)

### Timeline (UTC)
- T0: ...
- T1: ...

### Immediate Actions (snapshot-only)
- [ ] Stop / isolate dry-run process (if running)
- [ ] Capture snapshots (see section 2)
```

---

## 1.1) TEMPLATE — Finish C Incident Pack (No‑Secrets) (Copy‑Paste)

> **No‑Secrets**: keine Keys, keine Endpoints, keine Credentials, keine PII.  
> **Snapshot‑only**: keine Watch‑Loops, keine live actions.

```markdown
# TEMPLATE — Finish C Incident Pack (No-Secrets)
Incident ID:
Date/Time:
Owner:
Severity:
Phase (C0–C5):

## Summary
What happened (no secrets, no keys, no endpoints)?

## Impact
- User impact:
- Data impact:
- Operational impact:

## Timeline (UTC)
- T0:
- T1:
- T2:

## Detection
How was it detected? Which metric/log?

## Root Cause (hypothesis -> confirmed)
- Hypothesis:
- Evidence:
- Confirmed cause:

## Mitigation
What was done to stop/limit impact?

## Corrective Actions (CAPA)
- Immediate:
- Short-term:
- Long-term:

## Prevent Recurrence
- New tests:
- New guardrails:
- Docs/runbooks updates:

## Attachments (sanitized)
- Evidence snapshot links:
- Relevant commits/PRs:
```

---

## 2) Snapshot Collection (no watch)

> Ziel: reproduzierbare Fakten. Keine „tail -f“, kein polling.

```bash
cd /Users/frnkhrz/Peak_Trade || cd "$HOME/Peak_Trade"
git status -sb
git rev-parse HEAD

# Optional: run targeted tests relevant to failure (snapshot)
# pytest -q tests/live/orchestrator -q
# pytest -q tests/live/reconcile -q

# Docs gates (wenn docs betroffen)
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

Artefakte (lokal sammeln, keine Secrets):
- ``out&#47;finish_c&#47;incident&#47;<INC_ID>&#47;git_status.txt``
- ``out&#47;finish_c&#47;incident&#47;<INC_ID>&#47;diff_stat.txt``
- ``out&#47;finish_c&#47;incident&#47;<INC_ID>&#47;audit_events.json`` (redacted)
- ``out&#47;finish_c&#47;incident&#47;<INC_ID>&#47;state_snapshot.json``
- ``out&#47;finish_c&#47;incident&#47;<INC_ID>&#47;metrics_snapshot.txt``

---

## 3) Hypothesen / Root Cause (RCA Draft)

```markdown
### Observations
- ...

### Hypotheses
- H1: ...
- H2: ...

### Repro Steps (safe, mock-only)
1. ...
2. ...
Expected: ...
Actual: ...
```

---

## 4) Mitigation (Governance‑safe)

Erlaubt:
- bounded retries/backoff anpassen (wenn deterministisch testbar)
- safety rail thresholds nachziehen (mit Tests)
- mehr Logging **ohne** Secrets (redacted)
- zusätzliche failure-matrix tests

Nicht erlaubt:
- Live‑Enablement (enable flag/allowlist) als „Fix“
- Einfügen realer Broker‑Endpoints/Credentials

---

## 5) References (existing runbooks)

- ``..&#47;general.md`` (baseline incident response)
- ``..&#47;execution_error.md`` (execution error playbook)
- `RUNBOOK_FINISH_C_MASTER.md` (Finish C master)
