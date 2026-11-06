---
docs_token: DOCS_TOKEN_PARAMETER_SENSITIVITY_SPLIT_OBSERVATION_TRANSPORT_V1
status: active
scope: Optional transport of existing computed offline sensitivity split metrics
capability: PARAMETER_SENSITIVITY_SPLIT_OBSERVATION_TRANSPORT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-11-04
---

# Parameter sensitivity split observation transport v1

Subordinate to Master Runbook; research evidence only, productive authority NONE.

[Existing owner](../../../src/backtest/parameter_sensitivity_v1.py) accepts optional
`split_result_observer` on `run_parameter_sensitivity_v1`. It is called after
actual metrics computation for each computed split and receives read-only point/
split/ref/period/count/cost/funding metadata plus read-only copied metrics. It
introduces no new metric definition, missing-value conversion, automatic sample
validity or canonical identity. Existing stored v1 records and digests are unchanged.

Final point status remains authoritative. Earlier split observations can exist for
a later FAILED point. A consumer must join exact refs, final EVALUATED status and
all required split observations before claiming a complete measured experiment.
An insufficient or failed split emits no fabricated observation. Observer failure
uses the existing failed-point/full-grid path. Partial evidence must not be silently
promoted to experiment success. Unbound observer means no callback.

Observation collection/persistence, complete identity/provenance, units, time scope,
frequency and nonfinite handling belong to explicit consumers. No persistence,
Phase10/Meta execution, candidate translation, policy mutation, promotion or
productive activation is implied. Bar count alone is not independent sample proof.
[Actual computation and unchanged-result evidence](../evidence/parameter_sensitivity_split_observation_v1_2026_11_04/README.md).
