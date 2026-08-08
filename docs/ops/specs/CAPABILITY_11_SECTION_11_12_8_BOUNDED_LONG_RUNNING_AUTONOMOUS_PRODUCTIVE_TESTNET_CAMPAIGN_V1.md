---
docs_token: DOCS_TOKEN_CAPABILITY_11_SECTION_11_12_8_BOUNDED_LONG_RUNNING_AUTONOMOUS_PRODUCTIVE_TESTNET_CAMPAIGN_V1
status: active
scope: Phase 11 §11.12.8 bounded long-running productive Testnet campaign path — multi-cycle wallclock executor, OKX ACK/reject parse, SSOT duration bound; no productive campaign start in this PR; §11.13 unstarted
capability: CAPABILITY_11_SECTION_11_12_8_BOUNDED_LONG_RUNNING_AUTONOMOUS_PRODUCTIVE_TESTNET_CAMPAIGN_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-08
---

# Capability — §11.12.8 Bounded Long-Running Autonomous Productive Testnet Campaign V1

## Goal

Implement the coherent long-running productive path specified by
`docs/implementation/SECTION_11_12_8_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_FORENSIC_IMPLEMENTATION_SPEC.md`
so that after merge a **separate** Owner-GO can execute the bounded campaign.

```text
LONG_RUNNING_CAMPAIGN_PATH_PRESENT=true
ONE_SHOT_AUTOCOMPLETE_REMOVED=true
CANONICAL_DURATION_BOUND_DEFINED=true
SECTION_11_12_8_CAMPAIGN_DURATION_BOUND_SECONDS=3600
SECTION_11_12_8_CAMPAIGN_MAX_CYCLES=120
SECTION_11_12_8_CYCLE_CADENCE_SECONDS=60
WIRE_SENT_IS_NOT_EXCHANGE_ACK=true
PRODUCTIVE_TESTNET_CAMPAIGN_STARTED=false
SECTION_11_12_8_CLOSED=false
SECTION_11_13_STARTED=false
NEXT_CANONICAL_STEP_AFTER_MERGE=SEPARATE_OWNER_GO_EXECUTE_BOUNDED_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_NOW
NO_ADDITIONAL_IMPLEMENTATION_GO_REQUIRED_BEFORE_EXECUTE=true
```

## Out of scope for this PR

- Starting the productive Testnet campaign
- Network/order side effects during validation
- Claiming §11.12.8 closed
- Starting §11.13 / Live
- Trading-core mutation

## Owners

| Surface | Owner |
| --- | --- |
| Productive consumer/executor | `ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1` |
| Unlock / HTTP client | `ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1` |
| Forensic design | `docs/implementation/SECTION_11_12_8_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_FORENSIC_IMPLEMENTATION_SPEC.md` |
| SSOT bounds | Master Runbook §11.12.8.1 |
