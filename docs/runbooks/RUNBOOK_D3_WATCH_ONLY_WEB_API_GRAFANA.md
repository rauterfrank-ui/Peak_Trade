# Peak_Trade — RUNBOOK D3: Watch-Only Web/API + Grafana (Observability UX)

**Datum:** 2026-01-18  
**Modus:** governance-safe, deterministisch, evidence-first, **NO-LIVE standard**  
**Kontext:** Cursor Multi-Agent Chat (ORCHESTRATOR + 3–7 Agents parallel)

> **Stop Rules (global)**
> - Kein Live-Trading, keine Broker-Orders, keine Secrets in Logs.
> - Keine Watch-Loops als Default (nur Snapshot-Checks), außer explizit im Runbook erlaubt.
> - Scope-Drift → ORCHESTRATOR stoppt und fordert Re-Scoping.
> - Jede Phase endet mit einem **Snapshot** (Status/Gates/Artefakte).

---

## Rollen (Standard-Team, 3–7 Agents)

**ORCHESTRATOR (Lead):** Struktur, Phasen, Entscheidungen, Stop bei Drift  
**SCOPE_KEEPER:** Pfad-/Änderungsgrenzen, additive-only falls gefordert  
**ARCHITECT:** Contracts/Schemas, DoD, Abgrenzung  
**IMPLEMENTER:** Code/Config Changes (kleinste sinnvolle PR-Slices)  
**TEST_ENGINEER:** Tests, determinism checks, fixtures  
**CI_GUARDIAN:** gh checks Snapshot, required checks hygiene  
**DOCS_SCRIBE:** Runbooks, Frontdoor Links, operator quickstarts  
**EVIDENCE_SCRIBE:** Evidence-Snapshots, Merge-Logs, EV-IDs  
**RISK_OFFICER:** NO-LIVE, safety rails, rollback/incident packs

> In Cursor Multi-Agent Chat: ORCHESTRATOR startet alle Agents parallel (3–7) und sammelt Outputs pro Phase.

---

## Terminal-Pre-Flight (Pflichtblock für alle Runbooks)

```bash
# If you see > / dquote> / heredoc>, press Ctrl-C.

# Repo root (best-effort)
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
cd "${REPO_ROOT:-"$HOME/Peak_Trade"}"

pwd
git rev-parse --show-toplevel
git status -sb
```

---

## Ziel

Read-only API/UI: Runs list/detail + health; Grafana panels.

## Einstiegspunkt

API/Grafana teilweise da; Run Listing/Detail fehlt oder ist instabil.

## Endpunkt (DoD)

API v0 vollständig, UI pages, Grafana verify snapshot PASS, security tests PASS.

## Phasen

- D3-0 API Contract v0 (ARCHITECT) → contract frozen
- D3-1 Implementation (IMPLEMENTER) → endpoints + pages
- D3-2 Tests + Gates (TEST_ENGINEER + CI_GUARDIAN) → CI green
- D3-3 Grafana Panels (IMPLEMENTER + DOCS_SCRIBE) → verify PASS

## Cursor Promptblock

```md
ORCHESTRATOR: RUNBOOK D3 start. Agents: ARCHITECT, IMPLEMENTER, TEST_ENGINEER, CI_GUARDIAN, DOCS_SCRIBE.
Phase D3-0: finalize contract + schemas, then D3-1.
```
