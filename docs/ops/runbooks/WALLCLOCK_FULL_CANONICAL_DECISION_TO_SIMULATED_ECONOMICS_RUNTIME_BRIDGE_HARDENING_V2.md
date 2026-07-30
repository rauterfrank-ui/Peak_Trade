# WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_HARDENING_V2

```text
status: ACTIVE
capability: WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_HARDENING_V2
owner: ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2
hardens: WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1
authority_effect: NONE
order_effect: NONE
```

Hardens the merged V1 analytical wallclock decision→economics bridge against the
Desktop forensic 1h runbook gaps: fill-ledger contract, provenance IDs,
idempotency, forced wiring isolation, canonical strategy probe, regime
fail-closed, price-basis explicitness, real safety evaluation, evidence streams,
extended verifier, stub scan, and machine-derived acceptance gates.

Does **not** authorize Orders, Paper, Testnet, Live, credentials, Promotion,
Economic Validity PASS, Preregistration, or a 1h wallclock session.

## CLI

```bash
python scripts/ops/run_wallclock_bridge_hardening_v2.py preflight
python scripts/ops/run_wallclock_bridge_hardening_v2.py canonical-strategy-probe
python scripts/ops/run_wallclock_bridge_hardening_v2.py forced-wiring-fixture
python scripts/ops/run_wallclock_bridge_hardening_v2.py stub-fallback-scan
```

## Hard invariants

```text
SESSION_RESTART_POLICY=NO_IMPLICIT_RESUME
DEFAULT_REGIME_FALLBACK_ACTIVE=false
FORCED_FIXTURE_WALLCLOCK_REACHABLE=false
ORDERS_AUTHORIZED=false
LIVE_AUTHORIZED=false
GO_FOR_PREREGISTRATION=false
GO_FOR_AUTHORIZATION=false
GO_FOR_1H_RUN=false
HARD_STOP=true
```
