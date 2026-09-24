# F1/M9 REAL Prospective Campaign Execution Enablement (Normative V1)

## Scope

This workpackage closes the adjudicated gap between hermetic authorized-run orchestration
and a **REAL_AUTHORIZED_CAMPAIGN_EXECUTION** path for campaign
`cv_maxage_f1_m9_prospective_candidate_selection_v1_2bab88a8289fb032`.

## Non-goals (this slice)

- No live issuance of runtime authorization for production REAL runs
- No external public market-data reads
- No durable writes under the canonical campaign root in production process
- No authorization consumption in production process

Hermetic and fake-adapter tests prove wiring only.

## Execution modes

| Mode | Purpose |
|------|---------|
| `BUILD_BIND_ONLY` | Verify/bind authorization; no terminal REAL effects |
| `HERMETIC_TERMINAL_TEST` | Isolated tmp_path terminal path via hermetic evidence builder |
| `REAL_AUTHORIZED_CAMPAIGN_EXECUTION` | Issued authorization + canonical supplier adapter + REAL evidence pipeline |

`authorized_campaign_execution_terminal_path_proven` applies to hermetic terminal tests only.
`real_authorized_campaign_execution_path_proven` is the sole gate for production REAL runs.

## Issuance owner

Module: `runtime_authorization_issuance_v1.py` — binds campaign, base SHA, supplier, durable root,
work units, capabilities, and exactly-once consumption identity.

## REAL entry

Script: `scripts/run_f1_m9_prospective_real_authorized_campaign_execution_v1.py`
(requires valid issued authorization file; process enablement completed in activation slice).

## Next blocker after closure

`F1_M9_REAL_CAMPAIGN_ACTIVATION_AND_PRODUCTION_WIRING_V1` (successor); then fresh authorization + REAL CLI run.
