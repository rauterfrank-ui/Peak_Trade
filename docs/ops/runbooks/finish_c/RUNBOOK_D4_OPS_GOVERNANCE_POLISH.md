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

# RUNBOOK D4 — Workstream: Ops/Governance Polish (Docs Gates, Evidence, Merge Logs, Release Checklist)

## Ziel
Stabile Gates, konsistente Templates und Frontdoor‑Links, plus klarer Release‑/Closeout‑Pfad für Operatoren.

## Einstiegspunkt
Viele Runbooks/Docs existieren bereits; es gibt Gate‑Incidents durch inkonsistente Templates, fehlende Links oder uneinheitliche Merge‑Logs.

## Endpunkt (DoD)
- Docs‑/Ops‑Templates sind konsistent (Evidence/Merge‑Log/PR‑Body) und referenziert.  
- Docs‑Gates sind stabil (Snapshot‑Checks, keine Watch‑Loops).  
- Operator kann Gate‑Snapshots interpretieren und weiß, welche Artefakte bei Änderungen verpflichtend sind.

## Phasen
- D4‑0 Inventory & Debt Map (DOCS_SCRIBE + CI_GUARDIAN) → debt map + plan
- D4‑1 Templates (DOCS_SCRIBE) → templates committed
- D4‑2 Gate Hardening (CI_GUARDIAN + IMPLEMENTER) → gates green
- D4‑3 Release Checklist (RISK_OFFICER + DOCS_SCRIBE) → checklist doc referenced

## Cursor Promptblock

```md
ORCHESTRATOR: RUNBOOK D4 start. Agents: DOCS_SCRIBE, CI_GUARDIAN, IMPLEMENTER, RISK_OFFICER, EVIDENCE_SCRIBE.
Phase D4-0: debt map + plan, then D4-1.
```

---

## Snapshot‑Only Standardkommandos (D4)

> **Kein Watch.** Alle Commands sind einmalige Snapshots.

```bash
# Diff snapshots (docs-only scope)
git diff --stat
git diff

# Docs gates (snapshot-only, changed scope)
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main

# Narrow link target checks (optional, snapshot-only)
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
./scripts/ops/verify_docs_reference_targets_trend.sh --changed --base origin/main

# Merge log hygiene (snapshot-only)
python scripts/ops/check_merge_log_hygiene.py
```

---

## Output‑Artefakte (D4, Minimum)

- **Template Updates**: betroffene Template‑Dateien unter `docs/` / `templates/` (falls genutzt)
- **Merge‑Log**: `docs&#47;ops&#47;PR_<NNN>_MERGE_LOG.md` (oder äquivalentes Muster im Repo)
- **Evidence Snapshot**: EV‑ID Eintrag im Evidence‑Index (falls im Repo vorhanden)
- **Gate Snapshot**: ein „PASS/FAIL + kurze Notiz“ Block im Merge‑Log (keine Watch‑Outputs)
