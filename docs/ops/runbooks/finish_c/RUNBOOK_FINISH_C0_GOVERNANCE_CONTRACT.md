# Peak_Trade — Finish C0 — Governance Contract & Threat Model (NO‑LIVE default)

**Datum:** 2026-01-18  
**Status:** DRAFT (docs-only)  
**Modus:** governance‑safe, deterministisch, evidence‑first, **NO‑LIVE default**

> **Stop Rules (C0)**  
> - **Default NO‑LIVE**: keine realen Broker‑Calls, keine Orders.  
> - **Keine Secrets** in Logs/Docs/Beispielen.  
> - **Snapshot‑only**: keine Watch‑Loops.  
> - **Scope‑Drift ⇒ STOP** und ORCHESTRATOR re‑scoped.

---

## 0) Zweck

Dieses Runbook friert den Governance‑Contract für Finish Level C ein: **was darf gebaut werden**, **unter welchen Locks**, und **wie wird verhindert**, dass Live‑Execution versehentlich aktiviert wird.

---

## 1) Entry Point

### Voraussetzungen
- Repo vorhanden, Branch aktiv
- Änderungsmodus: **additive only** (Docs), keine Code‑Änderungen in C0

### Input
- Ziel: „Optional live‑near track“, aber **NO‑LIVE default**
- Rollen: ORCHESTRATOR + (SCOPE_KEEPER, ARCHITECT, RISK_OFFICER, CI_GUARDIAN, DOCS_SCRIBE, optional EVIDENCE_SCRIBE)

---

## 2) Exit Point (DoD)

Am Ende von C0 existiert ein **frozen contract**, der in späteren PRs als „Definition of Done“ und Scope‑Guard gilt:

- **NO‑LIVE default** klar und wiederholt
- **Enable‑Flag + Allowlist** als notwendige Bedingungen (beide erforderlich; default disabled)
- **No secrets**: Beispiele sind redacted/placeholder
- **No network** in Tests (mock/fake only)
- **Snapshot‑only**: keine Watch‑Loops in Runbooks als Standard
- **Artefakt‑Liste**: welche Docs/Templates/Snapshots erzeugt werden

---

## 3) Governance Contract (Text zum Einfrieren)

### 3.1 Hard Constraints (non‑negotiable)
- Live‑Broker‑Ops sind **opt‑in** und bleiben **standardmäßig deaktiviert**.
- Code/Docs dürfen **keine** Anleitungen enthalten, die Live‑Trading direkt ermöglichen.
- Keine realen Broker‑Endpoints/Accounts/Keys.
- Keine unbounded loops/polling als Default.

### 3.2 Gating Model (Mechanik, ohne Enablement)
**Live‑near** darf nur dann überhaupt „denkbar“ sein, wenn **alle** Bedingungen erfüllt sind:
- `enable_live_broker == false` als Default (muss aktiv auf `true` gesetzt werden)  
- `broker_allowlist` explizit gesetzt und **nicht leer**  
- „watch‑only“ Pfad bleibt verfügbar und Default in Operator UX

> In C0 werden nur die Regeln definiert, **nicht** implementiert.

### 3.3 Threat Model (minimal)
- **Unbeabsichtigtes Enablement** (Bug, falscher Default, config drift)
- **Secret leakage** (Logs, stack traces, CI artifacts)
- **Replay/Duplicate Orders** (idempotency fehlt)
- **Partial fills / race conditions** (reconciler fehlt)
- **Retry storms / rate limits** (backoff fehlt)

Kontrollen (target):
- Default‑off gating + explicit allowlist
- idempotency keys + dedupe
- reconciliation + invariants
- rate limiting + bounded retries
- audit log (append‑only events, redacted)

---

## 4) Snapshot Checklist (C0)

> Alles snapshot‑only (einmalig), keine Watches.

- [ ] `git status -sb` Snapshot (sauberer Arbeitsbaum vor/nach)
- [ ] `git diff --stat` Snapshot (nur neue Docs)
- [ ] Docs gates snapshot (changed scope)
- [ ] Artefakte‑Liste aktualisiert (siehe unten)

---

## 5) Artefakte (C0)

**Pflicht:**
- ``docs&#47;ops&#47;runbooks&#47;finish_c&#47;RUNBOOK_FINISH_C_MASTER.md``
- ``docs&#47;ops&#47;runbooks&#47;finish_c&#47;RUNBOOK_FINISH_C0_GOVERNANCE_CONTRACT.md``
- ``docs&#47;ops&#47;runbooks&#47;finish_c&#47;TEMPLATES_FINISH_C_EVIDENCE.md``
- ``docs&#47;ops&#47;runbooks&#47;finish_c&#47;TEMPLATES_FINISH_C_INCIDENT_PACK.md``

**Optional (operator-created später):**
- Evidence Entry unter ``docs&#47;ops&#47;evidence&#47;EV-YYYYMMDD-FINISH_C0-CONTRACT.md``

---

## 6) Operator Commands (Snapshot‑only)

```bash
cd /Users/frnkhrz/Peak_Trade || cd "$HOME/Peak_Trade"
git status -sb
git diff --stat

# Docs gates snapshot (changed scope)
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
```

---

## 7) Next PR Slice

**PR‑C1:** Broker Adapter Skeleton + Unit Tests + Fake/Mock Broker (NO‑LIVE, no network).  
Siehe `RUNBOOK_FINISH_C1_BROKER_ADAPTER_SKELETON.md`.
