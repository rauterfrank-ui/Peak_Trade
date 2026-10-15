# Owner-Scoped GET Budget Enforcement — Adversarial Contract Review V1

```text
WORK_PACKAGE_ID=PR_7112_SCOPED_GET_BUDGET_FINAL_ADVERSARIAL_REVIEW_V1
BASELINE_ORIGIN_MAIN_SHA=4b222dc532bb7229a3d13db8f3b159e97744cbf9
TRADING_LOGIC_CHANGED=false
PRODUCTION_TRADING_POLICY_CHANGED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
POST_ALLOWED=false
LIVE_GET_AUTHORIZED=false
```

## Root cause closed

Per-process `request_count` allowed cumulative Owner budget bypass across session
restarts. Durable grant ledger + atomic pre-send reservation closes this for
grant-bound PL-TF-002 sessions only.

## Adversarial checks

| Check | Result |
| --- | --- |
| Productive trading cycles without grant | PASS (enforcer default `None`) |
| Timeout/uncertain wire without enforcer | PASS (legacy TIMEOUT result preserved) |
| Timeout/uncertain wire with enforcer | PASS (fail-closed; reservation finalized uncertain) |
| Fifth GET after 1+2+1 across processes | PASS (blocked pre-wire; regression test) |
| Direct transport bypass without `get()` | OUT OF SCOPE (callers must use transport seam) |
| Grant identity collision / stale reuse | PASS (SHA256 binding + idempotent mint) |
| Partial ledger write / crash mid-reserve | PASS (in-flight counts against budget) |
| Concurrent reserve | PASS (fcntl flock + regression test) |
| Implicit grant renewal | PASS (no auto-mint without binding) |
| Credential persistence in ledger | PASS (no secret markers test) |
| F1 collector 11 items / 9 HTTP GETs | PASS (offline fake transport regression) |
| POST authority expansion | PASS (`prove_grant_does_not_authorize_post_v1`) |

## Verdict

`OWNER_SCOPED_GET_BUDGET_ENFORCEMENT_SAFE_FOR_MERGE_REVIEW` — scoped read-only
session boundary only; not a trading activation or Live GET authorization.
