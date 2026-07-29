# PRE_ECONOMIC_ZERO_ORDER_WALLCLOCK_EXECUTION_ARMING_V1 — Operator Runbook

```text
status: ACTIVE
capability: PRE_ECONOMIC_ZERO_ORDER_WALLCLOCK_EXECUTION_ARMING_V1
truth_claim: PRE_ECONOMIC_ZERO_ORDER_WALLCLOCK_EXECUTION_ARMING_IMPLEMENTED
session_contract: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1
authority_effect: NONE
activation_effect: NONE
economic_gate_effect: NONE
```

> **Arming capability only.** This runbook explains how to separately arm and
> later start one 6h zero-order evidence session. It does **not** execute the
> session, does **not** set Economic PASS, and does **not** authorize Shadow /
> Paper / Testnet / Live / Orders.

## Truth claim (only)

```text
PRE_ECONOMIC_ZERO_ORDER_WALLCLOCK_EXECUTION_ARMING_IMPLEMENTED
```

Forbidden claims:

```text
ECONOMIC_VALIDITY_PASS
PROFITABILITY_PROVEN
LOSS_IMPOSSIBLE
SHADOW_READY
PROMOTION_AUTHORIZED
```

## Safety defaults (fail-closed)

```text
enabled=false
armed=false
dry_run=true
session_execution_authorized=false
orders=false
broker_write=false
live_authorized=false
paper_authorized=false
testnet_authorized=false
shadow_activation_authorized=false
wallclock_execution_authorized=false
```

## Two-stage authority (mandatory)

1. **Operator-GO contract** — time-bounded, one-time, digest-bound authorization
2. **Short-lived wallclock arming lease** — separate lease (TTL ≤ 900s) bound to
   the same authorization_id / config_digest / revision_sha / GO fingerprint

```text
Operator-GO alone MUST NOT start the session.
Arming alone MUST NOT start without a valid Operator-GO contract.
```

## Canonical State Switch (not Switch/Stay)

Evidence binds read-only to Bull/Bear **State Switch**:

- Owner: `trading.master_v2.double_play_state` (`transition_state`)
- Binding adapter: `trading.master_v2.bull_bear_state_switch_scenario_binding_adapter_v0`
- Freshness `STALE` follows landscape Availability semantics for aged switch
  evidence (fields retained; no invented Stay/Switch token)

Invalid placeholder terms such as `switch_stay_state` / Switch-Stay must not
appear in evidence.

## What a 6h session is (and is not)

A successful 6h wallclock run produces **first integrated economic observation
evidence** under real OKX Futures read-only market data with hypothetical
execution (fees/slippage/counterfactual PnL).

It is **not**:

- a final robustness proof
- Economic Validity Offline Gate PASS
- Shadow / 29T / 29R activation
- promotion authority

## Operator commands (separate from this PR merge)

```bash
# Stage 1 — validate GO + authorization contract
python scripts/ops/run_pre_economic_zero_order_wallclock_arming_v1.py \
  validate-authorization --authorization PATH/TO/contract.json \
  --go-token "$PEZ_OPERATOR_GO_TOKEN" --revision-sha "$(git rev-parse HEAD)" --json

# Stage 2 — issue short-lived arming lease (runtime only; do not commit)
python scripts/ops/run_pre_economic_zero_order_wallclock_arming_v1.py \
  issue-arming-lease --authorization PATH/TO/contract.json \
  --output /tmp/pez_arming_lease.json --arming-id pez_arm_$(date -u +%Y%m%dT%H%M%SZ) \
  --go-token "$PEZ_OPERATOR_GO_TOKEN" --ttl-seconds 900 --json

# Two-stage preflight
python scripts/ops/run_pre_economic_zero_order_wallclock_arming_v1.py \
  preflight --authorization PATH/TO/contract.json \
  --arming-lease /tmp/pez_arming_lease.json \
  --go-token "$PEZ_OPERATOR_GO_TOKEN" --revision-sha "$(git rev-parse HEAD)" --json

# Explicit confirm is required; this capability PR still refuses auto-execution
python scripts/ops/run_pre_economic_zero_order_wallclock_arming_v1.py \
  production-start --authorization PATH/TO/contract.json \
  --arming-lease /tmp/pez_arming_lease.json \
  --go-token "$PEZ_OPERATOR_GO_TOKEN" --revision-sha "$(git rev-parse HEAD)" \
  --confirm-wallclock-arming --json
```

After a later, separately authorized 6h run:

```bash
python scripts/ops/run_pre_economic_zero_order_wallclock_arming_v1.py \
  verify-production --evidence-root PATH/TO/evidence --json
```

## Owner surfaces

| Surface | Path |
|---|---|
| Wallclock arming lease | `src/ops/pre_economic_zero_order_wallclock_arming_v1.py` |
| Economic evidence | `src/ops/pre_economic_zero_order_economic_evidence_v1.py` |
| Decision observer | `src/ops/pre_economic_zero_order_decision_cycle_observer_v1.py` |
| Production runner | `src/ops/pre_economic_zero_order_evidence_session_production_runner_v1.py` |
| Production verifier | `src/ops/pre_economic_zero_order_evidence_session_production_verifier_v1.py` |
| CLI | `scripts/ops/run_pre_economic_zero_order_wallclock_arming_v1.py` |
| Config | `config/ops/pre_economic_zero_order_evidence_session_authorization_v1.toml` |
| Arming template | `config/ops/pre_economic_zero_order_wallclock_arming_lease_template_v1.json` |
| Tests | `tests/ops/test_pre_economic_zero_order_wallclock_arming_v1.py` |

## Next action

```text
NEXT_ACTION=separates Operator-Arming und anschließender 6h-Evidence-Run
SESSION_EXECUTED=false
ORDERS=false
DOWNSTREAM_AUTHORITY_GRANTED=false
HARD_STOP=true
```
