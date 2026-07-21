# Evaluation runner lifecycle observability v1

Generic infrastructure fix for unobservable evaluation-runner process death.

## Diagnosis (machine-readable)

See `diagnosis.json`.

| Field | Value |
|---|---|
| ROOT_CAUSE_STATUS | NOT_IDENTIFIED (historical concrete cause) |
| GENERIC_OBSERVABILITY_GAP_CONFIRMED | true |
| FIRST_DIVERGENCE_BOUNDARY | after stdout member progress, before durable lifecycle persist / exit harvest |
| SYNTHETIC_REPRODUCTION | true |
| GENERIC_FIX_CLASS | evaluation_runner_lifecycle_observability_v1 |
| RERUN_EXECUTED | false |
| HOLDOUT_DATA_ACCESSED | false |
| EVALUATION_RUN_COUNT_UNCHANGED | true |

## Distinction

- Historical process-death cause for the midband 2/46 incident remains `UNKNOWN`.
- Generic observability gap (stdout-only progress, no exit/signal harvest, no atomic member checkpoint) is confirmed and covered by synthetic failure-mode tests.
