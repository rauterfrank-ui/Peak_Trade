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
- Activation gate: LIGHTWEIGHT vs CAUSAL_MODE (fail-closed; keine LIGHTWEIGHT-Pfade unter trading/execution/governance/risk)
- Pflichtblock `CAUSAL_COMPLETION_CONTRACT` in CAUSAL_MODE
- Ergänzt `peak-trade-ghv-forensic-source-provenance.mdc` bei GHV-Tooling (REFERENCE_ONLY)

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

### `PEAK_TRADE_TRADING_LOGIC_IMMUTABILITY_POLICY_V1.mdc`
Zweck:
- Owner-ratified: CURRENT trading logic is immutable; integration and validation adapt to it
- forbids reverse adaptation (gates/tests/Bugbot must not drive trading-semantics changes)
- mandates impact analysis and fail-closed stop when safety or trading semantics would change

### `peak-trade-owner-objective-first-v1.mdc`
Zweck:
- dauerhafte Arbeitsregel: jede Maßnahme muss auf das geltende fachliche Owner-Ziel ausgerichtet sein
- trennt Werkzeugausführung, technischen Vertragsstatus und Owner-Zielerreichung
- erteilt keine zusätzliche Autorität und schwächt bestehende Schutzregeln nicht

Verwendung:
- `alwaysApply: true` — jede Cursor-Session in diesem Repo
- verbindlicher Text nur in dieser Datei; keine Zweitkopie in anderen Universen
