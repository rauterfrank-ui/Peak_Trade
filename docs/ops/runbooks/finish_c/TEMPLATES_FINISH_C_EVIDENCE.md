# Peak_Trade — Templates — Finish C Evidence (v1)

**Datum:** 2026-01-18  
**Status:** DRAFT  
**Modus:** evidence‑first, governance‑safe, **NO‑LIVE default**

> **Rules**  
> - Keine Secrets (auch keine „redacted echten“ Beispiele).  
> - Keine Live‑Enablement Anleitung.  
> - Evidence ist **verifizierbar** (Commands + Expected Output, snapshot‑only).

---

## 0) Zweck

Copy‑Paste Templates für Evidence Entries rund um Finish C (C0–C5).  
Baseline‑Conventions: `../../EVIDENCE_ENTRY_TEMPLATE.md`.

---

## 1) Evidence Entry Template (Finish C)

```markdown
## Evidence Entry: Finish C — [PHASE] — [SHORT_TITLE]

**Evidence ID:** EV-YYYYMMDD-FINISH_C[0-5]-[TAG]  
**Date:** YYYY-MM-DD  
**Category:** [CI/Workflow | Drill/Operator | Test/Refactor | Config Snapshot]  
**Owner:** ops / aiops  
**Status:** VERIFIED

### Scope
[1–2 Sätze: Welche Komponenten/Runbooks/Tests deckt diese Evidence ab?]

### Claims
- Claim 1: [z.B. "Mocked broker integration tests pass"]
- Claim 2: [z.B. "NO-LIVE default preserved (enable flag false)"]

### Evidence / Source Links (relative)
- Primary Source: [PR Merge Log](../../../docs/ops/merge_logs/PR_<N>_MERGE_LOG.md)  (falls vorhanden)
- Commit: <SHA>
- CI Run: <url or id> (optional)

### Verification Steps (snapshot-only)
1. Checkout commit `<SHA>`
2. Run: `<command>`
3. Expected: `<expected>`

### Safety / Governance Notes
- Default NO-LIVE: [confirmed]
- No network: [confirmed]
- No secrets: [confirmed]

### Risk Notes (optional)
- [Caveats/limits]

---
**Entry Created:** YYYY-MM-DD  
**Last Updated:** YYYY-MM-DD
```

---

## 2) „Latest Run“ (Beispiel-Fill, Platzhalter)

> **Wichtig:** Dieses Beispiel enthält **keine** Secrets und **keine** echten Broker-Details.  
> Bitte beim Ausfüllen: keine Keys/Tokens/Account IDs; keine echten Endpoints.

```markdown
## Evidence Entry: Finish C — C5 — Controlled Readiness (Latest Run)

**Evidence ID:** EV-YYYYMMDD-FINISH_C5-READINESS  
**Date:** YYYY-MM-DD  
**Category:** CI/Workflow  
**Owner:** ops / aiops  
**Status:** VERIFIED

### Scope
Finish C readiness documentation + mock-only dry-run track verification (no live enablement).

### Claims
- Claim 1: C1–C4 mock-only tests pass (adapter/orchestrator/reconcile/observability).
- Claim 2: Default NO-LIVE preserved; enabled flag semantics documented (default OFF).
- Claim 3: Docs gates snapshot pass (reference targets / policies as applicable).

### Evidence / Source Links (relative)
- Primary Source: [PR Merge Log](../../../docs/ops/merge_logs/PR_<N>_MERGE_LOG.md)
- Commit: <SHA>

### Verification Steps (snapshot-only)
1. Checkout commit `<SHA>`
2. Run: `pytest -q`
3. Run: `python -m ruff check .`
4. Run: `python -m ruff format --check .`
5. Run: `./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main`
6. Expected: all checks PASS; no network calls; no secrets in output.

### Safety / Governance Notes
- Default NO-LIVE: confirmed
- No network: confirmed (mock-only)
- No secrets: confirmed

### Risk Notes
- LOW (docs-only readiness; no live enablement)
```

---

## 3) TEMPLATE — Finish C Evidence Snapshot (Copy‑Paste)

> Snapshot‑only, NO‑LIVE default. Outputs bitte **verbatim** einfügen.  
> **Forbidden:** live trading, reale broker calls, secrets.

```markdown
# TEMPLATE — Finish C Evidence Snapshot
Date:
Owner:
Phase: C0/C1/C2/C3/C4/C5
PR:
Commit:

## Scope Statement
- Allowed: docs/tests/mock-only
- Forbidden: live trading, real broker calls, secrets

## Snapshot Outputs (paste verbatim)
### Repo Pre-Flight
- pwd:
- git rev-parse --show-toplevel:
- git status -sb:

### Tests
- pytest -q:

### Lint/Format
- ruff check:
- ruff format --check:

### Key Assertions
- enable-flag default OFF: PASS/FAIL
- allowlist validation present: PASS/FAIL
- idempotency tests: PASS/FAIL
- bounded retries: PASS/FAIL

## Artifacts Produced
- Files added/changed:
- Docs links:
```

---

## 4) Phase‑Tags (Empfehlung)

- `FINISH_C0-CONTRACT`
- `FINISH_C1-ADAPTER`
- `FINISH_C2-ORCH-DRYRUN`
- `FINISH_C3-RECONCILE`
- `FINISH_C4-OBS-DRYRUN`
- `FINISH_C5-READINESS`
