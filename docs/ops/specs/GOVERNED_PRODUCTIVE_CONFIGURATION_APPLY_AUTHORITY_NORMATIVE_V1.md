---
docs_token: DOCS_TOKEN_GOVERNED_PRODUCTIVE_CONFIGURATION_APPLY_AUTHORITY_NORMATIVE_V1
status: active
scope: Governed productive configuration apply authority (M10 → apply record; no runtime apply)
workpackage_id: GOVERNED_RUNTIME_APPLY_MATERIALIZATION_AUTHORITY_RATIFICATION_V1
last_updated: 2026-09-26
---

# Governed Productive Configuration Apply Authority V1

```text
WORKPACKAGE_ID=GOVERNED_RUNTIME_APPLY_MATERIALIZATION_AUTHORITY_RATIFICATION_V1
APPLY_AUTHORITY_ID=GOVERNED_PRODUCTIVE_CONFIGURATION_APPLY_AUTHORITY_V1
M10_REMAINS_PROMOTION_SSOT=true
AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY=false
RUNTIME_APPLY_STARTED=false
REAL_RUNTIME_MATERIALIZATION_PERFORMED=false
```

Owner ratification:
`config/governance/governed_runtime_apply_materialization_authority_ratification_v1_owner_decision_v1.json`

Decision:
`config/governance/governed_productive_configuration_apply_authority_v1_decision_v1.json`

Owners:

- `src/governance/governed_productive_configuration_apply_authority_v1.py`
- `src/governance/governed_productive_configuration_apply_record_v1.py`

## Semantic law

```text
PROMOTION_AUTHORIZED != RUNTIME_APPLY_AUTHORIZED != RUNTIME_APPLIED != EXTERNAL_EFFECT_AUTHORIZED
```

M10 authorized promotion records make a candidate **eligible** for a separately governed apply
decision. They do not mutate productive configuration, start runtime apply, or authorize external
effects.

This authority stops at typed **apply-record** artifacts (`APPLY_ELIGIBLE`, `APPLY_DENIED`,
`APPLY_AUTHORIZED`). State `APPLIED` is reserved and not reachable in this work package.

## Bounded productive proof target

Positive ratification is limited to **F1/M9-S1** (`canonical_m9_volatility_numeric_max_age`).
F2, F3, F5, and universe membership do not imply apply authority.

## Non-goals

- Runtime configuration writers, daemons, schedulers, M11 automation
- Productive configuration mutation or parameter activation
- G2 primary-evidence → offline observation ingress
- Testnet/Live/external effects

## Verification

`tests/governance/test_governed_productive_configuration_apply_authority_v1.py`
