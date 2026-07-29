# PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION_V1

```text
status: ACTIVE
capability: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION
implementation_status: AUTHORIZATION_AND_EXECUTION_IMPLEMENTATION_READINESS
session_contract: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1
owner: ops.pre_economic_zero_order_evidence_session_authorization_v1
authority_effect: NONE
activation_effect: NONE
economic_gate_effect: NONE
```

> **Authorization + production-path implementation readiness — not a live Operator-GO, not a 6h execution, not Economic PASS, not Shadow.**
>
> This capability implements the fail-closed authorization contract, Operator-GO
> binding mechanism, production runner path, OKX Futures/SWAP read-only
> telemetry surface, safety preflight, production evidence schema, and
> production verifier required *before* a later, separate Operator-GO may
> authorize one real 6h zero-order evidence session.
>
> This PR does **not** execute a production session and does **not** grant GO.

## Machine tokens

```text
PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION=true
AUTHORIZATION_AND_EXECUTION_IMPLEMENTATION_READINESS=true
PRODUCTION_SESSION_EXECUTED=false
SESSION_EVIDENCE_VALID=false
SESSION_EVIDENCE=ABSENT
OPERATOR_GO_REQUIRED_LATER=true
OPERATOR_GO_GRANTED=false
SESSION_EXECUTION_AUTHORIZED=false
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false
SHADOW_ACTIVATION_AUTHORIZED=false
PAPER_ACTIVATION_AUTHORIZED=false
TESTNET_ACTIVATION_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
RUNTIME_AUTHORITY=NONE
VENUE=OKX
MARKET_TYPE=SWAP_OR_FUTURES
BTC_EXCLUDED=true
SPOT_EXCLUDED=true
DASHBOARD_IS_CONSUMER_ONLY=true
```

## Owner surfaces

| Surface | Path |
|---|---|
| Authorization + GO contract | `src/ops/pre_economic_zero_order_evidence_session_authorization_v1.py` |
| Session state machine | `src/ops/pre_economic_zero_order_evidence_session_state_machine_v1.py` |
| OKX read-only telemetry | `src/ops/pre_economic_zero_order_evidence_session_okx_readonly_telemetry_v1.py` |
| Safety preflight | `src/ops/pre_economic_zero_order_evidence_session_safety_preflight_v1.py` |
| Production runner | `src/ops/pre_economic_zero_order_evidence_session_production_runner_v1.py` |
| Production verifier | `src/ops/pre_economic_zero_order_evidence_session_production_verifier_v1.py` |
| CLI | `scripts/ops/run_pre_economic_zero_order_evidence_session_authorization_and_execution_v1.py` |
| Config | `config/ops/pre_economic_zero_order_evidence_session_authorization_v1.toml` |
| Auth template (unarmed) | `config/ops/pre_economic_zero_order_evidence_session_authorization_contract_template_v1.json` |
| Tests | `tests/ops/test_pre_economic_zero_order_evidence_session_authorization_and_execution_v1.py` |

## Authorization contract

A production session requires an external, machine-readable authorization
contract binding at least:

- capability / session version
- `venue=OKX`
- `market_type=SWAP` or `FUTURES`
- instrument allowlist (BTC forbidden, Spot forbidden)
- `zero_order_only=true`, `orders_allowed=false`
- `session_duration_seconds=21600`
- `enabled`, `armed`, `session_execution_authorized`, `dry_run`
- `issued_at`, `not_before`, `expires_at`, `one_time_use`
- `authorization_id`, config digest, revision SHA
- Operator-GO token binding digest (never the raw token)
- revocation state / reference
- max clock skew; optional host/environment binding

The committed template is **unarmed** and not production-bound.

## Operator-GO

```text
Token prefix: GO_PEZ_SESSION_AUTH_EXEC_V1_
Supply at runtime only (--go-token or PEZ_OPERATOR_GO_TOKEN)
Never commit the token
Must bind authorization_id + config_digest + revision_sha
One-time use, time-bounded, revocable
Env flag alone is never authority
enabled/armed alone never starts a session
```

## Production path semantics

States: `CREATED → AUTHORIZED → STARTING → RUNNING → COMPLETED`
Abort / failure terminals: `ABORTED`, `INCOMPLETE`, `INVALID`, `REVOKED`, `EXPIRED`.

- `COMPLETED` means only that the technical duration finished.
- `SESSION_EVIDENCE_VALID` may be set **only** by the production verifier.
- No silent resume; process loss → `INCOMPLETE` / `INVALID`.
- No merging of partial runs into a 6h session.
- Synthetic / replay evidence cannot satisfy production VALID.
- Wallclock arming for a later separate 6h run is owned by
  `PRE_ECONOMIC_ZERO_ORDER_WALLCLOCK_EXECUTION_ARMING_V1`
  (`docs/ops/runbooks/PRE_ECONOMIC_ZERO_ORDER_WALLCLOCK_EXECUTION_ARMING_V1.md`).
  Two-stage authority (GO + short-lived arming) is required; this authorization
  readiness surface alone does not start a session.

## Telemetry / safety

- Venue: OKX only
- Market: Futures / Perpetual SWAP only
- BTC excluded; Spot excluded
- Public read-only market data client reuse (`OkxPublicMarketDataClientV1`)
- Order-capable methods, trading permissions, execution plugins → fail-closed
- Dashboard remains a pure consumer (not authority / SSOT)

## Explicit non-claims

```text
NOT_OPERATOR_GO=true
NOT_SIX_HOUR_SESSION_EXECUTED=true
NOT_SESSION_EVIDENCE_VALID=true
NOT_ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=true
NOT_SHADOW_ACTIVATION=true
NOT_PAPER=true
NOT_TESTNET=true
NOT_LIVE=true
NOT_ORDERS=true
NOT_IMPLICIT_AUTHORITY=true
```

## Operator commands

```bash
python scripts/ops/run_pre_economic_zero_order_evidence_session_authorization_and_execution_v1.py validate-config --json
python scripts/ops/run_pre_economic_zero_order_evidence_session_authorization_and_execution_v1.py validate-authorization --authorization path/to/contract.json --json
python scripts/ops/run_pre_economic_zero_order_evidence_session_authorization_and_execution_v1.py preflight --json
python scripts/ops/run_pre_economic_zero_order_evidence_session_authorization_and_execution_v1.py dry-run --json
python scripts/ops/run_pre_economic_zero_order_evidence_session_authorization_and_execution_v1.py production-start --json
python scripts/ops/run_pre_economic_zero_order_evidence_session_authorization_and_execution_v1.py verify-production --evidence-root PATH --json
```

`production-start` hard-blocks without valid external authorization + GO.
Real 6h wallclock start additionally requires the separate wallclock-arming
capability and operator confirm (see
`docs/ops/runbooks/PRE_ECONOMIC_ZERO_ORDER_WALLCLOCK_EXECUTION_ARMING_V1.md`).

## Later Operator action (not this PR)

A separate, explicit Operator-GO **and** short-lived wallclock arming lease must
be issued against a concrete authorization contract before any real 6h session
may start.
