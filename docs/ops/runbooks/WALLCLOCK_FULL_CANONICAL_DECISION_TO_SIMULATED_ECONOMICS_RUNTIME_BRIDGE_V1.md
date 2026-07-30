# WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1

```text
status: ACTIVE
capability: WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1
owner: ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1
authority_effect: NONE
activation_effect: NONE
runtime_effect: NONE
order_effect: NONE
economic_gate_effect: NONE
closes_alias: INTEGRATED_PAPER_SHADOW_STRATEGY_INTENT_AND_PORTFOLIO_ECONOMICS_EVIDENCE_V1
```

> **Capability implementation — analytical wallclock decision→economics bridge.**
> Binds productive public-MD wallclock observation into the sole Master-V2 /
> Double-Play decision authority and a session-persistent simulated portfolio.
> Does **not** authorize Orders, Paper-Execution, Testnet, Live, credentials,
> private APIs, Promotion, or Economic Validity PASS.
> Live runtime-bridge status remains `BOUND_NOT_ACTIVATED` for order authority.
> Merge does not start a session.

## Root cause closed

PR #5594 / productive 6h closeout:
`TECHNICAL_PASS_ECONOMIC_EVIDENCE_NOT_PRODUCED` — wallclock path hardcoded HOLD /
quantity=0 and wrote portfolio/economic stubs. Full-system decision and
economics were not executed.

## Canonical call graph (this capability)

```text
OKX Public Market Data
→ Feature Pipeline
→ Regime Pipeline
→ Master V2 / Double Play (run_integrated_offline_trading_logic_replay_v1)
→ Risk / Position Sizing
→ Safety Kernel
→ intended_side / intended_quantity
→ Analytical Simulated Execution
→ Simulated Fill / Fee / Slippage
→ Session-persistent Portfolio
→ Realized / Unrealized PnL / Equity / Drawdown
→ Evidence
→ Full Economic Reconstruction Verifier
```

## Hard invariants

```text
orders_authorized=false
testnet_authorized=false
live_authorized=false
paper_execution_authorized=false
credentials_authorized=false
auto_promotion_authorized=false
ECONOMIC_VALIDITY_PASS=false
PROMOTION_PASS=false
runtime_bridge_live_activated=false
execution_eligible=false
execution_class=ANALYTICAL_SIMULATION_NOT_PAPER_EXECUTION
second_decision_authority=forbidden
```

## Reuse-before-new

| Surface | Owner |
|---|---|
| Decision authority | `trading.master_v2.integrated_offline_trading_logic_replay_v1` |
| Portfolio / fee / slippage | `ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1` |
| Wallclock session / MD transport | `ops.integrated_paper_shadow_observation_wallclock_session_execution_v1` |
| Productive auth / real MD | `ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1` |

## Owners (this capability)

| Surface | Path |
|---|---|
| Package | `src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/` |
| Config | `config/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.toml` |
| CLI | `scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py` |
| Tests | `tests/ops/test_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py` |

## CLI

```bash
python scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py preflight
python scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py runtime-probe --out <path>
python scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py verify-evidence --evidence-root <path>
```

`preflight` / `runtime-probe` / `verify-evidence` are offline. Real wallclock MD
sessions still require separate productive authorization (unchanged).

## Explicit non-goals

- Private API / credentials
- Orders / Paper-Execution / Testnet / Live
- Promotion / Economic Validity PASS
- Second decision authority
- Activating live runtime-bridge order authority
- Automatic session grant on merge

## Acceptance

1. Wallclock cycles no longer default to HOLD stub when bridge enabled
2. Feature + regime produced from mid-price history
3. Sole decision authority is integrated offline trading logic replay
4. Risk/sizing/safety run inside that authority
5. Actionable intents can produce analytical fills with fee/slippage
6. Portfolio persists across cycles; PnL/equity/drawdown evidence written
7. Full Economic Reconstruction Verifier PASS on probe evidence
8. Authority flags remain false
