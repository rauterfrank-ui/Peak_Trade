# Market Dashboard Projection Octet Runtime Verify V1

Generated: `2026-08-04T19:43:33.462472Z`
Repository HEAD / origin/main: `8c02f8793411939149eb7f33d6877a68a23a727f`
Dashboard: http://127.0.0.1:8000/market
Archive root: `&#47;Users&#47;frnkhrz&#47;Library&#47;Application Support&#47;Peak_Trade&#47;workflow_dashboard_v1_okx_fresh_20260724T214822Z`

## Batch

`BATCH_ID=B2_PROJECTION_OCTET_RUNTIME_VERIFY`

Read-only runtime/archive verification of eight presentation-bound projection families.
No trading, runtime, producer, materializer, or read-model mutation. No projection artifact creation.

## Consumer invariants

- `DASHBOARD_ROLE=PURE_CONSUMER`
- `AUTHORITY_EFFECT=NONE`
- `TRADING_LOGIC_CHANGED=false`
- `RUNTIME_CHANGED=false`
- `PRODUCER_CHANGED=false`
- `MATERIALIZER_EXECUTED=false`
- `CANONICAL_READMODEL_CHANGED=false`
- `KILL_SWITCH_LIVE_AUTOLOAD_USED=false`
- `LATEST_EVIDENCE_AUTO_SELECTED=false`

## Family verification results

| Family | Authorized path | Present | Schema | Loader | Runtime state | DOM |
|---|---|---|---|---|---|---|
| `dynamic_scope` | `readmodels&#47;dynamic_scope_presentation_projection.v1.json` | NO | `dynamic_scope_presentation_projection.v1` | ABSENT/DYNAMIC_SCOPE_PRESENTATION_PROJECTION_ABSENT | `RUNTIME_ARTIFACT_ABSENT` | `MISSING_SOURCE` |
| `regime_bull_bear_switch` | `readmodels&#47;bull_bear_regime_presentation_projection.v1.json` | NO | `bull_bear_regime_presentation_projection.v1` | ABSENT/BULL_BEAR_REGIME_PRESENTATION_PROJECTION_ABSENT | `RUNTIME_ARTIFACT_ABSENT` | `MISSING_SOURCE` |
| `canonical_decision` | `readmodels&#47;canonical_decision_presentation_projection.v1.json` | NO | `canonical_decision_presentation_projection.v1` | ABSENT/CANONICAL_DECISION_PRESENTATION_PROJECTION_ABSENT | `RUNTIME_ARTIFACT_ABSENT` | `MISSING_SOURCE` |
| `double_play` | `readmodels&#47;double_play_presentation_projection.v1.json` | NO | `double_play_presentation_projection.v1` | ABSENT/DOUBLE_PLAY_PRESENTATION_PROJECTION_ABSENT | `RUNTIME_ARTIFACT_ABSENT` | `MISSING_SOURCE` |
| `safety_authority` | `readmodels&#47;safety_authority.v1.json` | NO | `safety_authority_presentation_projection.v1` | ABSENT/SAFETY_AUTHORITY_PRESENTATION_PROJECTION_ABSENT | `RUNTIME_ARTIFACT_ABSENT` | `MISSING_SOURCE` |
| `risk_sizing_capital` | `readmodels&#47;risk_sizing_capital_presentation_projection.v1.json` | NO | `risk_sizing_capital_presentation_projection.v1` | ABSENT/RISK_SIZING_CAPITAL_PRESENTATION_PROJECTION_ABSENT | `RUNTIME_ARTIFACT_ABSENT` | `MISSING_SOURCE` |
| `execution_reconciliation` | `readmodels&#47;execution_reconciliation_presentation_projection.v1.json` | NO | `execution_reconciliation_presentation_projection.v1` | ABSENT/EXECUTION_RECONCILIATION_PRESENTATION_PROJECTION_ABSENT | `RUNTIME_ARTIFACT_ABSENT` | `MISSING_SOURCE` |
| `economic_summary` | `readmodels&#47;economic_summary_presentation_projection.v1.json` | NO | `economic_summary_presentation_projection.v1` | ABSENT/ECONOMIC_SUMMARY_PRESENTATION_PROJECTION_ABSENT | `RUNTIME_ARTIFACT_ABSENT` | `MISSING_SOURCE` |

## Summary

- Families verified: **8**
- Artifacts present: **0**
- Artifacts missing: **8**
- Schema invalid: **0** (absent, not invalid)
- Presenter available: **True**
- Serializer available: **True**
- Fallback/substitution used: **false**

## Live-DOM inventory reconcile

- OLD_MISSING_SOURCE_COUNT=**50**
- NEW_MISSING_SOURCE_COUNT=**50**
- OLD_NOT_BOUND_COUNT=**18**
- NEW_NOT_BOUND_COUNT=**17**

MISSING_SOURCE unchanged at 50 because all eight B2 projection families remain RUNTIME_ARTIFACT_ABSENT. NOT_BOUND decreased 18→17 in live DOM recount at HEAD 8c02f879 after universe-selection rail bind (#5710); intentional/blocked unbound surfaces remain; no B2 presentation compensation applied.

## Progress accounting

- B1 `B1_ALREADY_BOUND_CLOSEOUT`: CLOSED_UNCHANGED
- B2 `B2_PROJECTION_OCTET_RUNTIME_VERIFY`: COMPLETE_READ_ONLY_VERIFY
- B3 `decision_strip_blockers_unbound`: **NOT AUTHORIZED**
  - Reason: `ACTIVE_DOUBLE_PLAY_PROJECTION_ABSENT:readmodels&#47;double_play_presentation_projection.v1.json;DOUBLE_PLAY_LOADER_UNRESOLVED:DOUBLE_PLAY_PRESENTATION_PROJECTION_ABSENT;BLOCKER_FIELD_CONTRACT_NOT_PROVEN_WITHOUT_ACTIVE_ARTIFACT;TEMPLATE_BLOCKERS_STILL_HARDCODED_NOT_BOUND`
- B4 `B4_INTENTIONAL_AND_BLOCKED_FREEZE`: CLOSED_UNCHANGED

## Artifacts in this folder

- `VERIFY.json` — machine-readable family verify cycle
- `INVENTORY_RECONCILE.json` — old/new MISSING_SOURCE and NOT_BOUND counts
- `PROGRESS_ACCOUNTING.json` — B1/B2/B3/B4 accounting
- `live_market.html` — live DOM capture at HEAD
- `live_data_availability.json` — MISSING_SOURCE/NOT_BOUND element extract

