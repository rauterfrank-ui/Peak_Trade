# Productive Pure-Stack Numeric Policy Shadow Campaign v1

```text
DOCUMENT_TYPE=STAGE2_NUMERIC_POLICY_SHADOW_CAMPAIGN
DOCUMENT_VERSION=1
STATUS=SHADOW_EVIDENCE_COLLECTION_INFRASTRUCTURE_ONLY
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
DASHBOARD_ROLE=READ_ONLY_CONSUMER
DASHBOARD_AUTHORITY_EFFECT=NONE
PRODUCTIVE_ACTIVATION=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
OWNER_RATIFIED=false
ORDERS=false
TESTNET=false
LIVE=false
ARCHIVE_MUTATIONS=false
GROUP_AUTO_RATIFICATION=false
```

## 0. Purpose

This document binds the **Stage-2 Shadow Campaign Runner v1**: an isolated,
fail-closed Evidence collection runner for the 18
`NUMERIC_CALIBRATION_REQUIRED` Owner Values.

Shadow means **Evidence collection only**. It is **not** productive
calibration, not Owner ratification, not config write, and not runtime
activation.

## 1. Authority boundaries

```text
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
DASHBOARD=READ_ONLY_CONSUMER
TRADING_LOGIC_CHANGED=false
PRODUCTIVE_ACTIVATION=false
```

- Dashboard has **no** Evidence / numeric / input authority.
- Existing Pure-Stack evaluators remain unchanged.
- Stage-1 formula / metric producers introduced here are **shadow-only** and
  must keep `productive_activation=false`.
- `OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION` remains mechanical only:
  `1 - OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION`.

## 2. Output isolation

All campaign artifacts must be written only under:

```text
evidence/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/<campaign_id>/
```

Forbidden destinations (fail-closed):

- active dashboard archives
- workflow archives
- runtime archives
- path traversal / symlink escapes

Overwrite of an existing campaign directory is rejected.

## 3. Campaign state machine

Internal runner states:

```text
DECLARED → IN_PROGRESS → COMPLETE
                ↘ REJECTED
```

Pack schema mapping:

| Internal | Pack `campaign_status` |
|---|---|
| `DECLARED` / `IN_PROGRESS` | `IN_PROGRESS` |
| `COMPLETE` | `EVIDENCE_COMPLETE_PENDING_OWNER` |
| `REJECTED` | `REJECTED_FAIL_CLOSED` |

Rules:

- No transition to `COMPLETE` while schema, digest, or partition/stress/OOS
  manifests are incomplete.
- `evidence_complete=true` only with `COMPLETE`.
- `owner_ratified` remains `false` always in this capability.
- `COMPLETE` means **Evidence pack completeness only**, never productive
  release or Owner ratification.

## 4. Reproducibility / digest contract

Every run records:

```text
git_sha
config_digest
stage1_manifest_digest
calibration_protocol_digest
dataset_id
instrument_id
scenario_id
seed
event_time_epoch_s
wall_time_utc
sole_trading_authority
```

Digest mismatch against repository Stage-1 manifest or calibration protocol
fails closed.

## 5. Forbidden sources

```text
fixtures / scenario scalars as authority
WebUI hardcoded limits
dashboard presentation
CMC.volatility_estimate as realized_volatility
SurvivalResultV1 / SuitabilityResultV1 as Pure-Stack numeric authority
archive mutation as authority
parallel arithmetic / volatility / opportunity kernels
```

## 6. Data-collection groups (not ratification)

Optional shared observation grouping is **data collection only**.
Per-token Owner ratification remains a **separate later step**.
Group auto-ratification is forbidden.

## 7. Owners / references

- Runner package:
  `src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/`
- CLI:
  `scripts/ops/run_productive_pure_stack_numeric_policy_shadow_campaign_v1.py`
- Schema:
  `docs/ops/schemas/productive_pure_stack_numeric_policy_evidence_pack_v1.schema.json`
- Requirements:
  `docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_EVIDENCE_REQUIREMENTS_V1.md`
- Validator:
  `scripts/ops/validate_productive_pure_stack_numeric_policy_evidence_pack_v1.py`
- Calibration protocol:
  `docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md`
