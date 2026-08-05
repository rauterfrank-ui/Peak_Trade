# Productive Pure-Stack Numeric Policy Evidence Pack Scaffolding v1

```text
DOCUMENT_TYPE=STAGE2_EVIDENCE_PACK_SCAFFOLDING_GOVERNANCE
DOCUMENT_VERSION=1
STATUS=INFRASTRUCTURE_ONLY_NO_CALIBRATION_NO_NUMBERS
BASELINE_ORIGIN_MAIN_SHA=80977448775bd4819cbeef9122364e6330d7100f
SCHEMA=docs/ops/schemas/productive_pure_stack_numeric_policy_evidence_pack_v1.schema.json
REQUIREMENTS=docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_EVIDENCE_REQUIREMENTS_V1.md
CAMPAIGN_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_CAMPAIGN_MANIFEST_V1.json
VALIDATOR=scripts/ops/validate_productive_pure_stack_numeric_policy_evidence_pack_v1.py
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
DASHBOARD_ROLE=READ_ONLY_CONSUMER
PRODUCTIVE_NUMERIC_VALUES_SET=0
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
```

## 0. What this PR is

This deliverable creates **only** the fail-closed Stage-2 Evidence Pack
scaffolding for the 18 numeric Owner Values classified
`NUMERIC_CALIBRATION_REQUIRED` in Stage 1.

It is infrastructure so that later shadow/replay calibration campaigns can
emit versioned, auditable Evidence packs.

## 1. What this PR is not

```text
CALIBRATION_EXECUTED=false
NUMERIC_CANDIDATES_PROPOSED=false
NUMERIC_DEFAULTS_INSERTED=false
NUMERIC_RECOMMENDATIONS_INSERTED=false
NUMERIC_EXAMPLE_VALUES_INSERTED=false
OWNER_RATIFICATION_OF_ANY_TOKEN=false
GROUP_AUTO_RATIFICATION=false
INPUT_AUTHORITY_FLIP=false
RUNTIME_BINDING=false
DASHBOARD_MUTATION=false
ARCHIVE_MUTATION=false
CONFIG_MUTATION=false
STATE_MUTATION=false
ORDERS=false
LIVE=false
TESTNET=false
```

No productive number was proposed, selected, recommended, defaulted, or
ratified. Every token remains `productive_numeric_value=null`.

## 2. Separation of concerns (hard)

1. **Evidence-pack scaffolding / generation** (this PR family) creates and
   validates non-productive Evidence structure.
2. **Productive activation** requires a **separate** PR and explicit Owner GO
   after per-token ratification.

These must never be collapsed into one silent promotion.

## 3. Ratification rules

```text
NO_TOKEN_MAY_BE_GROUP_AUTO_RATIFIED=true
EACH_PRODUCTIVE_VALUE_REQUIRES_SEPARATE_OWNER_RATIFICATION=true
REINVEST_FRACTION_REMAINS_MECHANICAL_COUPLING_ONLY=true
```

Batch or family-wide automatic ratification of the 18 tokens is forbidden.

## 4. Metric hierarchy

```text
PRIMARY=SAFETY_METRICS
SECONDARY=ECONOMIC_METRICS
ECONOMICS_MAY_BREAK_TIES_ONLY_AFTER_SAFETY_PASS=true
ISOLATED_SHARPE_OR_PROFIT_OPTIMIZATION=FORBIDDEN
```

## 5. Authority boundaries

```text
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
DASHBOARD=READ_ONLY_CONSUMER
FORBIDDEN_NUMERIC_AUTHORITY_SOURCES=
  fixtures
  scenarios
  WebUI hardcoded limits
  CMC.volatility_estimate as realized_volatility
  SurvivalResultV1
  SuitabilityResultV1
  dashboard presentation
  archive mutation as authority
  parallel arithmetic/volatility/opportunity kernel
```

## 6. Campaign scaffold state

The empty campaign manifest is intentionally:

```text
campaign_status=NOT_STARTED
evidence_complete=false
owner_ratified=false
productive_numeric_values_set=0
input_authority=false
runtime_implemented=false
```

## 7. Validator role

`scripts&#47;ops&#47;validate_productive_pure_stack_numeric_policy_evidence_pack_v1.py`
fail-closed rejects packs that set productive numbers, flip authority flags,
omit Stage-1/protocol digests, claim forbidden sources, treat
`REINVEST_FRACTION` as independent, use wallclock seconds for the capital-slot
time quantum, derive `INITIAL_SLOT_BASE` from account equity, or claim
completeness with incomplete stress/OOS/partition manifests.

## 8. References

- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md`
- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_OWNER_VALUES_TWO_STAGE_RATIFICATION_V1.md`
- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_OWNER_VALUES_STRUCTURAL_MANIFEST_V1.json`
- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_EVIDENCE_REQUIREMENTS_V1.md`
- `docs&#47;runbooks&#47;canonical&#47;PEAK_TRADE_MASTER_RUNBOOK.md`
