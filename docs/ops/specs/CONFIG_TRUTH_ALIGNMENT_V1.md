# CONFIG_TRUTH_ALIGNMENT_V1

---
docs_token: DOCS_TOKEN_CONFIG_TRUTH_ALIGNMENT_V1
STATUS: CAPABILITY_AVAILABLE
scope: Phase-1 productive config truth alignment; fail-closed missing/invalid safety keys
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
ENFORCEMENT_ENABLED: false
CORE_LOGIC_CHANGE: false
ACTIVATION_STATE: BOUND_NOT_ACTIVATED
HARD_STOP: true
---

```text
CAPABILITY_ID=CONFIG_TRUTH_ALIGNMENT_V1
TITLE=Config Truth Alignment (Capability 0.3)
OWNER_REQUIREMENT=Prove and enforce Phase-1 effective config truth for productive entrypoints without runtime activation
CURRENT_STATE=Productive analytical bridge/IPSO/offline replay already hard-false on live/order flags; default config/config.toml max_open_positions=1; legacy permissive gaps existed (missing→None skip; root config.toml=10; test/historical 5)
TARGET_STATE=CONFIG_TRUTH_ALIGNED_PHASE1_EFFECTIVE_VALUES_PROVEN_NO_RUNTIME_ACTIVATION
OUT_OF_SCOPE=Master V2/Double Play/Bull-Bear/Dynamic Scope/Composition/Confirmation/Entry-Exit/Risk/Safety/Selection/Ranking/Reconciliation/Futures Accounting/Volatility calculation mutation; runtime/live/testnet/paper/network activation; authorization issuance/consumption; confirm-token semantic change; multi-future activation; max-age enforcement
AUTHORITY_OWNER=ops.config_truth_alignment_contract_v1
PRODUCTIVE_ENTRYPOINT=src/ops/config_truth_alignment_contract_v1.py (validator/owner) consumed by Phase-1 productive entrypoint proofs
CALL_GRAPH=
  Phase-1 Entrypoint
  → resolve_phase1_effective_config
  → env/CLI guard
  → PeakConfig productive path (config/config.toml)
  → bridge hard constants
  → max-age ENFORCEMENT_ENABLED=false
  → Phase1EffectiveConfigV1 + digest
CONFIG_KEYS=max_open_positions,enable_live_trading,live_authorized,orders_authorized,paper_execution_authorized,testnet_authorized,runtime_bridge_live_activated,MULTI_FUTURE_RUNTIME_AUTHORIZED,enforcement_enabled,volatility_numeric_max_age_enforcement,require_confirm_token
CONFIG_PRECEDENCE=phase1_hard_safety_constants > validated_cli_overrides > peak_config_productive_toml > missing_safety_defaults_false > missing_max_open_positions_fail_closed
MISSING_VALUE_SEMANTICS=safety flags default false; max_open_positions missing fail-closed (no fallback to 5/None/unlimited)
INVALID_VALUE_SEMANTICS=max_open_positions <1 or >1 rejected; safety true rejected; malformed bool rejected
FAILURE_SEMANTICS=ConfigTruthAlignmentError fail-closed; no silent permissive overwrite
SAFETY_INVARIANTS=BOUND_NOT_ACTIVATED; LIVE fail-closed; MULTI_FUTURE_RUNTIME_AUTHORIZED=false; VOL max-age non-enforcing (WATCHDOG_ONLY/RESEARCH_ONLY/DIAGNOSTIC_ONLY)
CORE_LOGIC_CHANGE=false
TEST_PLAN=tests/governance/test_config_truth_alignment_v1.py (positive/negative/entrypoint/legacy/digest/reload)
EVIDENCE_PLAN=ConfigTruthAlignmentReportV1 + Truth Map §3.4 update + consumer traces
ACTIVATION_STATE=BOUND_NOT_ACTIVATED
ROLLBACK_PLAN=Revert contract module + tests + Truth Map/capability doc; no runtime state to unwind
DOCS_UPDATE=docs/governance/PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md; this capability file
```

## Phase-1 effective truth

```text
max_open_positions=1
enable_live_trading=false
orders_authorized=false
paper_execution_authorized=false
testnet_authorized=false
runtime_bridge_live_activated=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
volatility_numeric_max_age_enforcement=false
```

## Consumer classification (summary)

| Entrypoint / surface | Class |
|---|---|
| Wallclock simulated-economics bridge | `PRODUCTIVE_CANONICAL` |
| IPSO wallclock observation | `PRODUCTIVE_CANONICAL` |
| IPSO productive issuance helper | `PRODUCTIVE_CANONICAL` |
| Offline Master V2 replay | `PRODUCTIVE_CANONICAL` |
| Vol max-age research accumulation | `RESEARCH_ONLY` |
| `LiveRiskLimits.from_config` | `PRODUCTIVE_LEGACY` (Phase-1 adapter required) |
| Root `config.toml` max_open_positions=10 | `HISTORICAL` (blocked as Phase-1 authority) |
| `config/config.test.toml` =5 | `TEST_ONLY` (blocked) |
| Universe/ranking trading authority | `DEAD_OR_UNREACHABLE` |
| Productive reconciliation host | `PRODUCTIVE_CANONICAL` (Capability 1.1 bound; live/orders fail-closed) |

## Owner module

`src&#47;ops&#47;config_truth_alignment_contract_v1.py`
