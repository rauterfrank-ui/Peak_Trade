---
docs_token: DOCS_TOKEN_CURRENT_PRODUCTIVE_CONTINUOUS_OBSERVATION_BUDGET_V1
status: active
scope: Bounded productive continuous observation budget (cycles + duration only); no trading semantics
capability: CURRENT_PRODUCTIVE_CONTINUOUS_OBSERVATION_BUDGET_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-10-12
---

# Current Productive Continuous Observation Budget V1

Derived spec. Non-SSOT. Changes only how long the GET-only Product may
observe natural Distinct-C1 epochs. Trading thresholds, admission, and
POST pins are unchanged.

## Duration semantics (launcher vs S6 sequencer)

`--max-run-duration-seconds` (default `180.0`) constrains **only** the S6
observation sequencer inside
`run_current_productive_governed_continuous_cycle_run_v1` (monotonic clock
starts at sequencer entry). It is **not** a launcher-wide wall-clock timeout.

Productive runs may spend additional monotonic time in launcher preflight
(EEA/Cap24, selection handoff, transport/G17/obs wiring) and in post-S6
report finalization. Those phases are outside `max_run_duration_seconds`
enforcement.

When `PRE_EXTERNAL_CONVERGENCE_REPORT.json` is emitted, additive duration
fields (monotonic, schema `v1`) distinguish:

```text
TOTAL_WALLCLOCK_SECONDS        — full productive launcher span (monotonic)
PREFLIGHT_ELAPSED_SECONDS      — origin through pre-S6 wiring
SEQUENCER_ELAPSED_SECONDS      — S6 orchestrator elapsed (budget scope)
FINALIZATION_ELAPSED_SECONDS   — post-S6 return through report write
MAX_RUN_DURATION_SECONDS_SCOPE — constant S6_OBSERVATION_SEQUENCER_ONLY
```

Historical reports without these keys remain valid; consumers must not
fabricate missing measurements.

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
