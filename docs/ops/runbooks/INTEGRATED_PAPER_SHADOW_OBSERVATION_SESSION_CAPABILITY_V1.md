# INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1

```text
status: ACTIVE
capability: INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1
owner: ops.integrated_paper_shadow_observation_session_v1
authority_effect: NONE
activation_effect: NONE
economic_gate_effect: NONE
runtime_effect: NONE
order_effect: NONE
```

> **Capability implementation — not authorization, not wallclock session, not Operator-GO.**
> Provides the canonical Integrated Paper-Shadow Observation path surfaces:
> entrypoint, simulated portfolio economics, readiness producer, lifecycle,
> OKX Futures market-data policy, durable evidence, and bundle verifier.
> `PAPER_SHADOW_OBSERVATION_AUTHORIZED` remains `false`.

## Pipeline position

```text
FULL_CANONICAL_SYSTEM_PARITY
→ INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_PASS
→ PAPER_SHADOW_OBSERVATION_READINESS_PASS
→ OPERATOR_PAPER_SHADOW_OBSERVATION_GO   # NOT implemented here
→ INTEGRATED_PAPER_SHADOW_OBSERVATION
→ INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE
→ INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED
→ ECONOMIC_VALIDITY_PASS
→ PROMOTION → TESTNET → LIVE
```

## Owners

| Surface | Path |
|---|---|
| Package | `src/ops/integrated_paper_shadow_observation_session_v1/` |
| Config | `config/ops/integrated_paper_shadow_observation_session_v1.toml` |
| Offline CLI | `scripts/ops/run_integrated_paper_shadow_observation_session_contract_v1.py` |
| Portfolio economics model | `.../portfolio_economics_model_v1.py` |
| Market-data policy | `.../market_data_policy_v1.py` |
| Session lifecycle | `.../session_lifecycle_v1.py` |
| Entrypoint | `.../entrypoint_v1.py` |
| Readiness producer | `.../readiness_producer_v1.py` |
| Evidence | `.../evidence_v1.py` |
| Bundle verifier | `.../bundle_verifier_v1.py` |
| Gate-split owner | `ops.integrated_paper_shadow_economic_validity_pipeline_v1` |

## Hard invariants

```text
PAPER_SHADOW_OBSERVATION_AUTHORIZED=false
ORDERS_ALLOWED=false
BROKER_WRITES_ALLOWED=false
NETWORK_ALLOWED=false
CREDENTIALS_ALLOWED=false
WALLCLOCK_SESSION_EXECUTION_ALLOWED=false
OPERATOR_GO_GRANTED=false
NO_AUTO_PROMOTION=true
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
ECONOMIC_VALIDITY_PASS=false
```

## Observation entrypoint

- Mode must be exactly `observation` (fail-closed).
- Venue: OKX Futures only; Spot forbidden; BTC forbidden per governance allowlist.
- Decision pipeline reuses the canonical offline Master-V2 / Double-Play / Safety cycle.
- Portfolio fills/fees/slippage/funding/PnL are **simulated only**.
- No order-capable client, no broker write, no credentials, no network.

## Readiness producer

`produce_paper_shadow_observation_readiness_v1` discovers repository truth and
evaluates `PAPER_SHADOW_OBSERVATION_READINESS_PASS` through the canonical gate-split
evaluator. Forced PASS is rejected. Missing Operator-GO contract keeps readiness
fail-closed. Authorization is never implied by readiness.

## Session lifecycle

Defines Start / Timeout / Stop / Lock / Killstate / No-Auto-Promotion.
Wallclock execution is refused (`WALLCLOCK_SESSION_EXECUTION_FORBIDDEN`).
Killstate triggers include stale data, gaps, clock drift, invariant violation,
unexpected write attempt, config drift, duplicate session, evidence sink failure.

## Evidence + verifier

Durable artifacts: session manifest, config snapshot, portfolio snapshot,
decision trace, risk telemetry, no-order attestation, economic metrics,
replay metadata, lifecycle plan, integrity + sha256 manifest.
Verifier rejects synthetic PASS and never sets system Economic Validity.

## Explicit non-goals

- Operator-GO grant / arming
- Wallclock observation session execution
- Scheduler / daemon start
- Runtime bridge activation
- Testnet / Live / Orders
- Equivalence to Pre-Economic Zero-Order connectivity evidence

## Offline operator command (contract only)

```bash
python scripts/ops/run_integrated_paper_shadow_observation_session_contract_v1.py --mode observation --json
```
