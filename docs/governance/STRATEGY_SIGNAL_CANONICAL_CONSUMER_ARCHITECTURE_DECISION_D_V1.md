# Strategy Signal Canonical Consumer Architecture Decision D v1

```text
DOCUMENT_TYPE=ARCHITECTURE_DECISION
DOCUMENT_VERSION=1
STATUS=RATIFIED_POSITIVE
GO_TOKEN=GO_DECISION_D_STRATEGY_SIGNAL_CANONICAL_CONSUMER_BINDING_V1

ARCHITECTURE_DECISION_D_NAME=
FAMILY_SCOPED_STRATEGY_AGREEMENT_INTO_EXISTING_SUITABILITY_V1

PREVIOUS_NEGATIVE_AUTHORIZATION=C
PREVIOUS_NEGATIVE_DOC=
docs/governance/STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1.md
DECISION_C_PRESERVED_AS_HISTORICAL_IST=true
DECISION_C_NOT_OVERWRITTEN=true

SELECTED_EXISTING_CANONICAL_STAGE=evaluate_suitability_binding_v1
SELECTED_EXISTING_STAGE_OWNER_FILE=
src/trading/master_v2/suitability_binding_v1.py
SELECTED_EXISTING_INPUT_CONTRACT=SuitabilityBindingInputV1
SELECTED_ORCHESTRATOR_CARRIER_CONTRACT=IntegratedOfflineReplayInputV1

CANONICAL_TOTAL_DECISION_OWNER=
run_integrated_offline_trading_logic_replay_v1
CANONICAL_REPLAY_INPUT_BUILDER=
build_integrated_offline_replay_input_v1

STRATEGY_SIGNAL_HAS_REAL_CANONICAL_CONSUMER=true
STRATEGY_SIGNAL_IS_PROVENANCE_ONLY=false
STRATEGY_SIGNAL_CAN_AFFECT_CANONICAL_DECISION=true
RAW_STRATEGY_SIGNAL_DIRECT_POSITION_AUTHORITY=false
RAW_STRATEGY_SIGNAL_DIRECT_EXIT_AUTHORITY=false
RAW_STRATEGY_SIGNAL_DIRECT_REVERSAL_AUTHORITY=false
RAW_STRATEGY_SIGNAL_DIRECT_SIZING_AUTHORITY=false
RAW_STRATEGY_SIGNAL_DIRECT_ORDER_AUTHORITY=false
NEW_PARALLEL_DECISION_STAGE_REQUIRED=false
NEW_TOTAL_DECISION_OWNER=false

SLICE_2_IMPLEMENTATION_AUTHORIZED=true
SLICE_2_IMPLEMENTATION_BLOCKED=false
NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=
FAMILY_SCOPED_STRATEGY_AGREEMENT_INTO_EXISTING_SUITABILITY_V1

CORE_SEMANTICS_CHANGED=true
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE
```

## Purpose

This document ratifies **Decision D** as the new positive architecture decision
under operator GO:

```text
GO_DECISION_D_STRATEGY_SIGNAL_CANONICAL_CONSUMER_BINDING_V1
```

It authorizes the bounded Slice-2 consumer path that Decision C documented as
missing, without inventing a parallel decision stage or granting raw ±1 signal
authority.

**Decision C remains the historical negative Ist-Befund** and is not overwritten:
[`STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1.md`](STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1.md).

## Binding architecture

```text
ARCHITECTURE_CLASS=
REUSE_FIRST_EXTENSION_OF_EXISTING_CANONICAL_STAGE
+
FAMILY_SCOPED_ONTOLOGY_REDESIGN_AT_ADAPTER_BOUNDARY

SIGNAL_VALUE_SEMANTICS=
FAMILY_SCOPED_CYCLE_AGREEMENT_MATERIAL_V1

ENCODING_CLASS_REQUIRED=true
UNIVERSAL_RAW_PM1_POSITION_ONTOLOGY=false
CROSS_FAMILY_COERCION=FAIL_CLOSED
```

### Exact consumer path

```text
StrategySignalBindingResultV1
→ normalize_strategy_signal_to_suitability_agreement_material_v1
   (src/backtest/strategy_signal_suitability_agreement_adapter_v1.py)
→ build_integrated_offline_replay_input_v1(
     ..., strategy_suitability_agreement_material=...)
→ run_integrated_offline_trading_logic_replay_v1
→ _suitability_input_for_assessment
→ evaluate_suitability_binding_v1
   → apply_strategy_suitability_agreement_material_v1
→ existing composition / entry_exit / evidence chain unchanged as authority owners
```

### Encoding classes

| Encoding class | cycle_signal_value | Consumer effect |
|---|---|---|
| `POSITIONAL_LS_STATE_V1` | `+1` long / `-1` short / `0` flat | side agreement vs DA side |
| `POSITIONAL_LONG01_STATE_V1` | `+1` long / `0` flat; `-1` fail-closed | long-only agreement |
| `ENTRY_EXIT_EVENT_V1` | `+1` entry / `-1` exit / `0` none | EXIT demotes eligibility only; never exit authority. Optional explicit `entry_side` ∈ {LONG, SHORT, NONE} (default NONE) is the only DA side carrier; `+1` alone is never LONG. Producer-side ratification status is frozen in [`OBL_B05_ENTRY_EXIT_PRODUCER_SIDE_AUTHORITY_DECISION_V1.md`](OBL_B05_ENTRY_EXIT_PRODUCER_SIDE_AUTHORITY_DECISION_V1.md) (`BOLLINGER_ENTRY_SIDE_DECISION=BLOCKED_AMBIGUITY`). Bollinger governance-doc alignment (still non-authorizing, `entry_side=NONE`) is recorded in [`OBL_B05_BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_THEN_LONG_DECISION_V1.md`](OBL_B05_BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_THEN_LONG_DECISION_V1.md). |
| `FILTER_MASK01_V1` | `1` allow / `0` block | eligibility gate |
| `UNKNOWN_OR_STUB_V1` | n/a | fail-closed |

### Authority boundaries

```text
RAW_STRATEGY_SIGNAL_DIRECT_POSITION_AUTHORITY=false
RAW_STRATEGY_SIGNAL_DIRECT_EXIT_AUTHORITY=false
RAW_STRATEGY_SIGNAL_DIRECT_REVERSAL_AUTHORITY=false
RAW_STRATEGY_SIGNAL_DIRECT_SIZING_AUTHORITY=false
RAW_STRATEGY_SIGNAL_DIRECT_ORDER_AUTHORITY=false
```

Strategy-signal values are input only for
`StrategySuitabilityAgreementMaterialV1`. Position/exit/reversal remain
Composition + EntryExitPolicy. Risk/sizing and orders/runtime remain untouched.

## Parent runbook

[`Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md`](Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md)
