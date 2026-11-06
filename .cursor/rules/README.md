# Cursor Rules

Lokaler Index der im Repo hinterlegten Cursor-Regeln.

## Regeln

### `capital-safety-evidence-integrity-v1.mdc`
Zweck:
- OWNER_MANDATORY: PROVEN ist beweispflichtig; NOT_PROVEN vor unbelegtem PASS
- Self-falsification und RETRACTION-Disziplin
- Pflichtblock `EVIDENCE_INTEGRITY_V1` bei Audits, Reviews, Freigaben

Verwendung:
- `alwaysApply: true` — jede Cursor-Session in diesem Repo

### `peak-trade-permanent-causal-work-standard-v1.mdc`
Zweck:
- CURRENT first, GHV-Fixpoint (Forward/Reverse/Transitive), kein stilles Scope-Weglassen
- Activation gate: LIGHTWEIGHT vs CAUSAL_MODE
- Pflichtblock `CAUSAL_COMPLETION_CONTRACT` in CAUSAL_MODE

Verwendung:
- `alwaysApply: true` — GHV/Causal-Traversal nur wenn Gate CAUSAL_MODE aktiv

### `peak_trade_founder_operator_paper_stability_guard.mdc`
Zweck:
- materialisiert das Founder/Operator-Master-Runbook als operative Cursor-Regel
- erzwingt `paper_stability_guard`
- verankert das Muster „ein Thema = ein PR“ und „read-only Inventur vor Mutation“

Kernpunkte:
- keine Mutation von Paper-, Shadow- oder Evidence-Beständen
- keine Live-Freischaltung
- keine Secrets/Keys im Klartext
- Scope klein halten
- docs/operator/observability/governance vor Runtime

Verwendung:
- als Standardregel für Cursor Multi-Agent Orchestrator im Founder/Operator-Arbeitsmodus
