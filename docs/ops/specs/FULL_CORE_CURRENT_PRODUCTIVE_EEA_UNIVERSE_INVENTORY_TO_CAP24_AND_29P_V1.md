---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_TO_CAP24_AND_29P_V1
status: active
scope: Full-Core CURRENT_PRODUCTIVE EEA READ-ONLY universe inventory acquisition; Cap-2.1 no-network producer; Cap-2.2 structural ranking; Cap-2.3 reselection; Cap-2.4 BoundInstrument; LAB plus Fresh Pretrade GET; U01; P01 DOES_NOT_APPLY; USDC availEq; CU; STEP-29P; no POST; no Live enable
capability: FULL_CORE_CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_TO_CAP24_AND_29P_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-15
---

# Full Core Current Productive EEA Universe Inventory To Cap24 And 29P V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.CZ.
Consumes Owner-GO
`CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_TO_CAP24_AND_29P_TO_FIRST_REAL_BLOCKER_V1`.
Atlas remains `NAVIGATION_ONLY` / `AUTHORITY=NONE`.

This persist adds a separate CURRENT_PRODUCTIVE READ-ONLY acquisition
layer for `eea.okx.com` `&#47;api&#47;v5&#47;public&#47;instruments` and
`&#47;api&#47;v5&#47;public&#47;mark-price` (FUTURES+SWAP, no instId, no credentials, no
POST). Cap-2.1 remains the no-network domain producer. Cap-2.2 remains
structural ranking with `ECONOMIC_RANK_ACTIVATED=false`. This Owner-GO
authorizes execution of the existing Cap-2.3
`CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1` with
`RESELECTION_PERMITTED=true` and `MANUAL_INSTRUMENT_SELECTION_PERMITTED=false`.
Cap-2.4 mints CURRENT `BoundInstrumentV1` from that selection. Fresh
Pretrade GET, LIVE_ACCOUNT_BOUND, U01, standing P01 DOES_NOT_APPLY,
`details[ccy=USDC].availEq`, CU, and STEP-29P are reevaluated on the same
decision epoch.

Injected doubles may close adapter wiring. They are not CURRENT_PRODUCTIVE
29P. Productive READ-ONLY GETs on `eea.okx.com` mint CURRENT Cap-2.1–2.4
and reevaluate STEP-29P. `STEP_29P_RISK_ADMISSIBLE=true` does not admit
Live. Canary `DEFAULT_INSTRUMENT_ID` is not instrument authority. No POST.
No Live enable/arm. No wire-send.

```text
OWNER_GO=CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_TO_CAP24_AND_29P_TO_FIRST_REAL_BLOCKER_V1
OWNER_GO_STATUS=CONSUMED
PIN_OWNER_GO=OWNER_GO_REQUIRED_TO_SUPPLY_CURRENT_CAP24_BOUND_INSTRUMENT_INSTANCE_FOR_29P_WITHOUT_CANARY_IMPORT_OR_RESELECTION_V1
PIN_OWNER_GO_STATUS=CONSUMED_AND_SUPERSEDED_FOR_RESELECTION_BY_THIS_GO
EEA_UNIVERSE_HOST=eea.okx.com
CAP21_NETWORK_OWNER_CHANGED=false
ECONOMIC_RANK_ACTIVATED=false
RESELECTION_AUTHORIZED_BY_THIS_GO=true
MANUAL_INSTRUMENT_SELECTION_PERFORMED=false
P01_POLICY_DECISION=DOES_NOT_APPLY
CANARY_INSTRUMENT_AUTHORITY_IMPORTED=false
POST_COUNT=0
MAX_POSITIONS_EFFECTIVE=1
STEP_29P_RISK_ADMISSIBLE=true
FIRST_DEFINITIVE_BLOCK=LIVE_ENABLED_STANDING_GATE_REMAINS_FALSE
BLOCKER_CLASS=E
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
ATLAS_AUTHORITY=NONE
```
