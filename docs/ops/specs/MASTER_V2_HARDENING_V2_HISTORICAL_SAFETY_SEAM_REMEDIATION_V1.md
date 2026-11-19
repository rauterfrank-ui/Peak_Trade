# MASTER V2 — Hardening-v2 historical safety-seam remediation v1

status: ACTIVE
last_updated: 2026-11-19
owner: Peak_Trade
purpose: Bounded host/hardening consumption rewire so later Hardening-v2 guards conform to conserved Master V2 / Double Play safety semantics. Not a new Safety policy. Not Replay-owner mutation. Not live authority.
docs_token: DOCS_TOKEN_MASTER_V2_HARDENING_V2_HISTORICAL_SAFETY_SEAM_REMEDIATION_V1

```text
HISTORICAL_REFERENCE_AUTHORITY=NONE
RESTORATION_TARGET_ID=MASTER_V2_DOUBLE_PLAY_CONSERVED_REFERENCE_V1
RESTORATION_CLASS=HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_V1
SLICE_ID=HARDENING_V2_HOST_SAFETY_SEAM_REMEDIATION_BOUNDED_V1
CURRENT_SYSTEM_SEMANTIC_DELTA=true
NEW_SEMANTIC_POLICY=false
UNATTESTED_FORMULA_CHANGE=false
CANONICAL_COMPUTE_OWNER_CHANGED=false
CANONICAL_RISK_OWNER_CHANGED=false
CANONICAL_SAFETY_OWNER_CHANGED=false
CANONICAL_INTENT_OWNER_CHANGED=false
CANONICAL_SIDESTATE_OWNER_CHANGED=false
ENTRY_EXIT_OWNER_CHANGED=false
EXECUTION_AUTHORITY_CHANGED=false
LIVE_AUTHORITY_CHANGED=false
TRADING_AUTHORITY_CHANGED=false
BRIDGE_SAFETY_ROLE=INPUT_PRODUCER_ONLY
EVALUATE_BRIDGE_SAFETY_V2_PRODUCTIVE_OWNER=false
EVALUATE_BRIDGE_SAFETY_V2_PRODUCTIVE_HOST_REACHABLE=false
NO_TRADING=true
NO_LIVE_AUTHORITY=true
NO_EXECUTION_AUTHORITY=true
```

This document is bounded slice attestation for the Hardening-v2 / host
consumption seam. It is not Restoration SSOT. Admission class remains
`HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_V1`.

Forbidden Master-V2 / Double-Play owner files are not mutated by this slice.
Ops host/hardening paths are not a forbidden mutation surface; no replacement
of the committed Replay exact-file grant is required or performed.

## 1) Historical core (immutable under this slice)

```text
Double Play → EntryExit → STEP-29P → canonical Replay Safety → STEP-29Q PLAN_ONLY
```

Replay remains Compute Owner. Cap 6.5 `evaluate_bridge_safety_v2` remains the
SafetyMode / TradingGate **input producer**, not a second Replay Safety owner.

## 2) Remediation

1. Hardening-v2 consumes canonical Cap 6.5 producer bundle signals. Historical
   adverse / profit / time producers are not replaced by unbound
   `triggered=false` stubs. This describes the historical remediation, not an
   instruction to restore the separate adverse exit removed by the subsequent
   full-Scope correction below.
2. Post-mapper HOLD is demoted to a downstream new-exposure execution guard.
   Historical EXIT / REDUCE mapped BUY/SELL is not rewritten to HOLD.
3. Host mapper does not invent ENTER BUY/SELL from sizing when CanonicalOrderIntent
   is absent. EXIT / REDUCE reasons such as `safety_exit` are not treated as a
   generic HOLD veto.
4. Simulated fills remain on the existing Hardening-v2 analytical portfolio.
   Cap 7.2 `SimulatedExecutionPort` remains the activated no-order v1 owner.
   No new execution abstraction. No live/submit path.

## 3) Negative claims

- Independent pre-trade Safety kernel is not pulled into Replay.
- XP-03 is not activated.
- STEP-29M / EV is not bound.
- A06 / sibling adapters are not promoted.
- No new block table, permission protocol, KillSwitch, or eligibility policy.

## 4) Full-Scope test reconciliation, 2026-11-19

PR #7302 (`71e4ce6912476be757ada2b4d334892320c424c6`, 2026-11-17)
applied the owner-approved [full Dynamic Scope correction](FULL_CORE_CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_REPAIR_V1.md).
The current Layer-C distances project the full effective `D_t`; its
`adverse_exit_distance` field supplies protection geometry, not a separate early
exit. The host evaluates the producer bundle with the explicit reason
`full_dynamic_scope_no_separate_adverse_exit`. Independent safety, hard-risk,
profit-protection, time and invalidation rules retain their own inputs.

The former case D in the [Safety-seam tests](../../../tests/ops/test_hardening_v2_historical_safety_seam_contracts_v1.py)
still demanded a separate exit beyond an entry-relative distance of 80 price
units. That was a legacy configuration value, neither basis points nor a
percentage and neither the current Scope anchor nor its effective distance.
This stale expectation explains the failure recorded after PR #7341.

The replacement cases use both position sides, the original typed volatility
producer with 61 synthetic finalized PT1M Mark prices, and the original replay
consumer. They observe its actual input and effective Scope: crossing the
former entry-relative threshold does not emit an early adverse exit. With an
independent safety trigger, the same consumer produces an EXIT, maps the
correct close side and quantity, and closes the analytical position. A missing
typed estimate cannot satisfy these cases. The profit case now names its own
profit-protection distance instead of the unrelated legacy Up-distance field.

The existing LONG/SHORT full-Scope boundary cases separately verify no early
Scope event, Downscope at the full boundary and confirmation under the epoch
rule. These tests do not establish native L10 host continuity, real fills or
overall Safety acceptance. No runtime owner, threshold or authorization is
changed by this test reconciliation. The [source-bound follow-up evidence](../evidence/HARDENING_V2_FULL_SCOPE_SAFETY_CONTRACT_RECONCILIATION_2026-11-19.json)
records the focused results; the earlier card-connection report remains a
historical record of its original run.
