---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_V1
status: active
scope: Full-Core CURRENT_PRODUCTIVE Live Account Bound and STEP-29P instrument-scope adapter; Cap-2.4 BoundInstrument consumer; no canary DEFAULT_INSTRUMENT_ID authority import; same-epoch U01 plus details[ccy=USDC].availEq GET; CU mint without U04 double-count; 29P reevaluation; first real blocker current Cap-2.4 BoundInstrument instance missing; no POST; no Live enable
capability: FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-15
---

# Full Core Current Productive Live Account Bound And Instrument Scope For 29P V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.CY.
Consumes Owner-GO
`CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_TO_FIRST_REAL_BLOCKER_V1`.
Atlas remains `NAVIGATION_ONLY` / `AUTHORITY=NONE`.

This persist binds STEP-29P to an explicit Cap-2.4 `BoundInstrumentV1`
(exactly one selected future, `MAX_POSITIONS=1`) and evaluates
`LIVE_ACCOUNT_BOUND` through the existing typed seam over Fresh Pretrade
GET identity extracts. It does not import canary
`DEFAULT_INSTRUMENT_ID` as Full-Core instrument authority. It does not
re-select. Missing, stale, mismatch, or multiple instruments fail
closed. Historical Cap-2.3 selection evidence is not reconstructed as
the current productive instrument.

P01 remains explicit `DOES_NOT_APPLY` by architectural redundancy.
Same-epoch READ-ONLY `/api/v5/account/config` (U01) and
`/api/v5/account/balance` (`details[ccy=USDC].availEq`) are authorized.
U04 is not subtracted again. CU mint proceeds when observation, explicit
P01 DNA fact, and U01 eligibility are bound.

Injected transport may close the LAB/instrument adapter wiring. It is
not CURRENT_PRODUCTIVE 29P. CURRENT_PRODUCTIVE 29P remains false until
a current Cap-2.4 BoundInstrument instance and productive trusted GET
are both present. The first real blocker of this persist is the missing
current Cap-2.4 BoundInstrument instance. No POST. No Live enable/arm.
No wire-send.

```text
OWNER_GO=CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_TO_FIRST_REAL_BLOCKER_V1
OWNER_GO_STATUS=CONSUMED
PIN_OWNER_GO=OWNER_GO_REQUIRED_TO_BIND_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_V1
PIN_OWNER_GO_STATUS=CONSUMED
P01_POLICY_DECISION=DOES_NOT_APPLY
P01_DECISION_BASIS=ARCHITECTURAL_REDUNDANCY_NOT_HISTORICAL_ABSENCE
P01_LEGACY_RECONSTRUCTION_PERFORMED=false
P01_RUNTIME_INSTANCE_PRESENT=false
CANARY_INSTRUMENT_AUTHORITY_IMPORTED=false
GET_ENDPOINT_U01=/api/v5/account/config
GET_ENDPOINT_BALANCE=/api/v5/account/balance
AUTHORIZED_GET_COUNT=2
POST_COUNT=0
U04_SUBTRACTED=false
MAX_POSITIONS_EFFECTIVE=1
STEP_29P_RISK_ADMISSIBLE=false
FIRST_DEFINITIVE_BLOCK=CURRENT_PRODUCTIVE_CAP24_BOUND_INSTRUMENT_INSTANCE_MISSING
BLOCKER_CLASS=B
ATLAS_AUTHORITY=NONE
```
