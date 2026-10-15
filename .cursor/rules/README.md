# Cursor Rules

Lokaler Index der im Repo hinterlegten Cursor-Regeln.

## Regeln

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
