# Peak_Trade — Finish Runbook Pack (Cursor Multi‑Agent)

**Datum:** 2026-01-18  
**Modus:** governance‑safe, deterministisch, evidence‑first, **NO‑LIVE standard**  
**Kontext:** Cursor Multi‑Agent Chat (ORCHESTRATOR + 3–7 Agents parallel)

> **Stop Rules (global)**  
> - Kein Live‑Trading, keine Broker‑Orders, keine Secrets in Logs.  
> - Keine Watch‑Loops als Default (nur Snapshot‑Checks), außer explizit im Runbook erlaubt.  
> - Scope‑Drift → ORCHESTRATOR stoppt und fordert Re‑Scoping.  
> - Jede Phase endet mit einem **Snapshot** (Status/Gates/Artefakte).  

---

## Rollen (Standard‑Team, 3–7 Agents)

**ORCHESTRATOR (Lead):** Struktur, Phasen, Entscheidungen, Stop bei Drift  
**SCOPE_KEEPER:** Pfad-/Änderungsgrenzen, additive-only falls gefordert  
**ARCHITECT:** Contracts/Schemas, DoD, Abgrenzung  
**IMPLEMENTER:** Code/Config Changes (kleinste sinnvolle PR‑Slices)  
**TEST_ENGINEER:** Tests, determinism checks, fixtures  
**CI_GUARDIAN:** gh checks Snapshot, required checks hygiene  
**DOCS_SCRIBE:** Runbooks, Frontdoor Links, operator quickstarts  
**EVIDENCE_SCRIBE:** Evidence‑Snapshots, Merge‑Logs, EV‑IDs  
**RISK_OFFICER:** NO‑LIVE, safety rails, rollback/incident packs

> In Cursor Multi‑Agent Chat: ORCHESTRATOR startet alle Agents parallel (3–7) und sammelt Outputs pro Phase.

---

## Terminal‑Pre‑Flight (Pflichtblock für alle Runbooks)

```bash
# If you see > / dquote> / heredoc>, press Ctrl-C.

cd /Users/frnkhrz/Peak_Trade || cd "$HOME/Peak_Trade"
pwd
git rev-parse --show-toplevel
git status -sb
```

# RUNBOOK D1 — Workstream: Run Artifacts & Repro (Contract v1 → v1.1)

## Ziel
Run‑Artefakte sind **standardisiert**, versioniert und reproduzierbar.

## Einstiegspunkt
Runner/Backtests existieren; Outputs sind inkonsistent oder unversioniert.

## Endpunkt (DoD)
`run_manifest.json` + `config_snapshot.json` + `metrics.json` + `equity.csv` + `trades.csv`, determinism tests PASS, docs gates PASS.

## Phasen
- D1‑0 Contract Freeze (ARCHITECT) → Schema v1 frozen
- D1‑1 Implementation Slice (IMPLEMENTER) → one run produces full folder
- D1‑2 Determinism Tests (TEST_ENGINEER) → determinism PASS
- D1‑3 Docs Quickstart (DOCS_SCRIBE) → docs gates PASS

## Cursor Promptblock
```md
ORCHESTRATOR: RUNBOOK D1 start. Agents: ARCHITECT, IMPLEMENTER, TEST_ENGINEER, DOCS_SCRIBE, CI_GUARDIAN.
Phase D1-0: deliver artifacts schema v1 + file layout. Then D1-1.
```
