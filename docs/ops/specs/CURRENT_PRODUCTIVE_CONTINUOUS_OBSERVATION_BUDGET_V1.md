---
docs_token: DOCS_TOKEN_CURRENT_PRODUCTIVE_CONTINUOUS_OBSERVATION_BUDGET_V1
status: active
scope: Bounded productive continuous observation budget (cycles + duration only); no trading semantics
capability: CURRENT_PRODUCTIVE_CONTINUOUS_OBSERVATION_BUDGET_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-10-02
---

# Current Productive Continuous Observation Budget V1

Derived spec. Non-SSOT. Changes only how long the GET-only Product may
observe natural Distinct-C1 epochs. Trading thresholds, admission, and
POST pins are unchanged.

Authority module:
`src/ops/full_core_live_path_composition_root_v1/current_productive_continuous_observation_budget_v1.py`

Product launcher flags (default invocation unchanged):

```text
--max-cycles (default 4)
--max-run-duration-seconds (default 180.0)
```

Absolute finite ceiling (fail-closed above):

```text
ABSOLUTE_MAX_CYCLES_PER_RUN=12
ABSOLUTE_MAX_RUN_DURATION_SECONDS=900
```

No unbounded mode. No environment-variable override. Invalid input fails closed.
