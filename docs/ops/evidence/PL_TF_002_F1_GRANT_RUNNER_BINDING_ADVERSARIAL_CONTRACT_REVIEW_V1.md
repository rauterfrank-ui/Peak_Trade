# PL-TF-002 F1 Grant Runner Binding — Adversarial Contract Review V1

```text
WORK_PACKAGE_ID=PL_TF_002_F1_GRANT_RUNNER_BINDING_V1
BASELINE_ORIGIN_MAIN_SHA=efca36b05961443b28438bc553936be164e4977e
TRADING_LOGIC_CHANGED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
POST_ALLOWED=false
LIVE_GET_AUTHORIZED=false
```

## Root cause closed

Ops runner did not pass grant store; capture mint used technical cap (16) instead of
explicit Owner cumulative budget (9) for bounded F1 sessions.

## Adversarial checks

| Check | Result |
| --- | --- |
| execute_network without grant store | PASS (fail-closed before wire) |
| Owner budget 9 mint + tenth blocked | PASS (regression) |
| Technical transport limit 16 unchanged | PASS |
| Canonical WP/Session OWNER_GO preserved | PASS |
| Wrong OWNER_GO on runner | PASS (exit 2) |
| Productive trading without grant store path | PASS (unchanged; network capture now requires grant) |
| Silent grant renewal | PASS (existing idempotent mint) |
| Persist failure triggers GET retry | PASS (capture/persist separate) |

## Verdict

`PL_TF_002_F1_GRANT_RUNNER_BINDING_SAFE_FOR_MERGE_REVIEW` — ops integration only.
