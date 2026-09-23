# Risk Sizing Bypass Fate Vocabulary And Decision Authority Freeze V1

**Status:** BINDING fate-vocabulary + decision-authority freeze (docs + static contract only)  
**Date:** 2026-09-23  
**Obligation:** `OBL_B05_BYPASS_FATE_VOCABULARY_AND_DECISION_AUTHORITY_FREEZE_V1`  
**Machine contract:** [`config/governance/risk_sizing_bypass_fate_vocabulary_and_decision_authority_freeze_v1.json`](../../config/governance/risk_sizing_bypass_fate_vocabulary_and_decision_authority_freeze_v1.json)  
**Related (unchanged fates):** [`RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md`](RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md) · [`RISK_SIZING_AUTHORITY_DECISION_CONTRACT_FREEZE_V1.md`](RISK_SIZING_AUTHORITY_DECISION_CONTRACT_FREEZE_V1.md) · [`RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1.md`](RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1.md)

```
RISK_SIZING_BYPASS_FATE_VOCABULARY_AND_DECISION_AUTHORITY_FREEZE_V1=true
INVENTORY_ONLY=true
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
PER_BYPASS_FATE_ADJUDICATION_EXECUTED=false
PER_BYPASS_FATE_ASSIGNMENT_AUTHORIZED_BY_THIS_SLICE=false
UNKNOWN_FATE_COUNT=5
BYPASS_PATH_COUNT=5
BYPASS_SET_CHANGED=false
CONSOLIDATION_STATUS=NOT_STARTED
CONVERSION_READY=false
NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false
C2_INPUT_AUTHORITIES=UNRESOLVED
NO_RUNTIME_REWIRE=true
NO_SIZING_MATH_CHANGE=true
NO_CRS_SCOPE_EXPANSION=true
NO_REPO_WIDE_OWNER_PROMOTION=true
NO_FOREIGN_TOKEN_NORMALIZATION=true
DEPRECATE_LEGACY_PATH_IS_NOT_OPERATOR_FATE=true
DEPRECATED_QUARANTINED_IS_NOT_OPERATOR_FATE=true
SINGULAR_REPO_WIDE_OWNER_REQUIRED=false
MV2_INTENT_BOUND_QUANTITY_ALGEBRA_OWNER=src.governance.capital_risk_sizing_v1
MV2_INTENT_BOUND_QUANTITY_ALGEBRA_OWNER_SCOPE=mv2_governance_intent_bound
CANONICAL_RISK_SIZING_OWNER=UNRESOLVED
DECISION_AUTHORITY=SCOPED_OPERATOR_GO
DECISION_AUTHORITY_HOLDER=Peak_Trade_Operator
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED=false
```

## Purpose

Close the semantic precondition for later B05 bypass-fate adjudication:

1. canonical, minimal fate vocabulary for `operator_fate_adjudication`
2. explicit Decision Authority for who may assign a per-BYPASS fate
3. fail-closed evidence / assignment rules for a later adjudication slice

This slice does **not** adjudicate the five CURRENT BYPASS fates.

## Decision Authority

```text
DECISION_AUTHORITY=SCOPED_OPERATOR_GO
DECISION_AUTHORITY_HOLDER=Peak_Trade_Operator
DECISION_AUTHORITY_GATE=EXPLICIT_SCOPED_OPERATOR_GO_FOR_WP_B05_BYPASS_FATE_OPERATOR_ADJUDICATION_V1
```

Not Decision Authority for per-BYPASS fate assignment:

- `src.governance.capital_risk_sizing_v1` (MV2 quantity-algebra owner only)
- `CURRENT_SYSTEM_INTERACTION_AUTHORITY_MAP_V1` (`AUTHORITY=NONE`)
- code ownership / reachability / chat memory / filename heuristics

Evidence (CURRENT governance, not invented fachliche CRS authority):

- `docs/governance/drift_cleanup_plan_v1.md` Section B — structural items including B-05 require explicit Operator-GO
- inventory SSOT — OBL_B05 bypass fate remains open until separate Operator-GO
- `open_obligations.json` — OBL_B05 classified `REQUIRES_RUNTIME_GO`

This freeze **pins** that authority; it does **not** itself assign fates.

## Allowed operator fate tokens (exact set)

Sorted machine list is authoritative in the JSON contract.

| Token | Normative meaning (summary) | Later runtime GO for implementation? |
|---|---|---|
| `UNKNOWN` | Missing / insufficient / not-yet-adjudicated evidence; fail-closed default | n/a (default pin) |
| `CONFLICTING` | CURRENT authoritative surfaces disagree; no single non-UNKNOWN fate | yes (to resolve conflict productively) |
| `KEEP_PARALLEL_NON_CANONICAL` | Remain productive parallel non-CRS route; no consolidation claim | no for pin alone; rewire still separate if ever attempted |
| `GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE` | Must not be treated as system/economic size authority | yes if enforcement/quarantine wiring required |
| `INTEND_REBIND_TO_CRS` | Operator-intended future migration toward CRS for scoped surface | yes for any rebind/rewire |
| `RESEARCH_OR_OFFLINE_SCOPE_ONLY` | Research/offline/eval authority only; not productive system-evidence owner | yes if enforcement required |

Full required-evidence, forbidden-interpretation, CRS/MV2 relation, and runtime-effect=NONE fields live in the JSON contract.

## Foreign tokens (not operator fate)

Do **not** normalize into `operator_fate_adjudication`:

- `DEPRECATE_LEGACY_PATH` — CRS `export_bypass_scan_v1` legacy PositionSizer classification
- `DEPRECATED_QUARANTINED` — companion EFS quarantine subcontract status

Semantic identity with those tokens is **not** CURRENT-proven for operator fate.

## Fail-closed later adjudication rules

Later per-ID adjudication must FAIL if:

- token not in the allowed set
- foreign token used as operator fate
- assignment without scoped Operator-GO for that adjudication WP
- assignment without the token’s required evidence
- adjudication-only slice claims runtime effect / rewire / delete / disable
- bypass ID add/remove
- `CONVERSION_READY` flip, C2 resolve, or repo-wide owner promotion

Missing or conflicting evidence ⇒ remain `UNKNOWN` or assign `CONFLICTING` (not invent a preferred fate).

## CURRENT pins (unchanged by this freeze)

All five inventored bypasses remain:

```text
operator_fate_adjudication=UNKNOWN
```

IDs:

- `BYPASS_CLASSIC_BACKTEST_DEFAULT`
- `BYPASS_CORE_POSITION_SIZER`
- `BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS`
- `BYPASS_LIVE_SHADOW_POSITION_FRACTION`
- `BYPASS_OFFLINE_EVAL_SIZING_CONTRACT`

## Forensic basis for vocabulary distinctions (not adjudications)

The five open B05 questions distinguish operative end-states that this vocabulary must be able to name later:

1. keep productive parallel non-canonical route
2. governance-exclude from system/economic evidence authority
3. intend future rebind toward CRS (implementation separate)
4. research/offline scope only
5. insufficient evidence (`UNKNOWN`) or authoritative conflict (`CONFLICTING`)

These distinctions are already carried as open inventory governance questions and OBL_B05 / Section B Operator-GO gates. This freeze only names the outcome vocabulary; it does not answer the five questions.

## Explicit non-claims

- no per-BYPASS fate assignment
- no runtime rewire / delete / disable / rebind
- no C2 work
- no conversion-ready flip
- no sizing-math change
- no repo-wide CRS owner promotion
- no BYPASS-set change
- no consolidation implementation
- Map `AUTHORITY` remains `NONE`
