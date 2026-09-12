---
docs_token: DOCS_TOKEN_CAP22_APPEND_ONLY_15M_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_V1
status: active
scope: Cap 2.2 WP1 append-only 15m PIT persistence and collection contracts; no scheduler; no collection start; no venue reads; no ranking activation
capability: CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-12
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
SELECTION_AUTHORITY: false
ALPHA_ALLOWED: false
ECONOMIC_RANK_ACTIVATED: false
HARD_STOP: true
---

# Cap 2.2 Append-Only 15m PIT Persistence And Collection Contracts V1

Owner-GO
`PEAK_TRADE_CAP22_WP1_APPEND_ONLY_15M_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_V1`
implements only the contracts and append-only PIT persistence seams
required before later prospective Cap-2.2 15-minute collection. This
document is subordinate to
`docs&#47;runbooks&#47;canonical&#47;PEAK_TRADE_MASTER_RUNBOOK.md`.
It does **not** replace §4.5–§4.5.12, does **not** start collection, does
**not** enable a scheduler, does **not** authorize venue or network
reads, does **not** run historical backfill, does **not** compute
forward labels, does **not** run walk-forward, does **not** ratify a
policy winner, does **not** activate ranking, does **not** close PDF
Step 5, does **not** authorize `apply_rotation`, does **not** allow PDF
Step 7, does **not** grant runtime, and does **not** join a host.

Typed contract and seam:
`src&#47;ops&#47;cap22_append_only_15m_pit_persistence_v1&#47;`.

Existing producers remain the object owners:

- Cap 2.1 `src&#47;ops&#47;governed_futures_universe_producer_v1&#47;`
- Economic-MD `src&#47;ops&#47;economic_md_input_producer_v1&#47;`

```text
DOCUMENT_CLASS=TYPED_CONTRACT_AND_APPEND_ONLY_PIT_PERSISTENCE_SEAM
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=PEAK_TRADE_CAP22_WP1_APPEND_ONLY_15M_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_V1
BOUND_ORIGIN_MAIN_SHA=b31c0398b71a9898ed73cf3bfde9cd3e113caa3b
CONTRACT_ID=CAP22_APPEND_ONLY_15M_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_V1
DECISION_ID=CAP22_APPEND_ONLY_15M_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_V1
SCHEMA_VERSION=cap22_append_only_15m_pit_persistence.v1
RUNTIME_AUTHORIZATION_EFFECT=NONE
AUTHORITY_EFFECT=OFFLINE_APPEND_ONLY_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_ONLY
AUTHORITY_SCOPE=OFFLINE_APPEND_ONLY_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_ONLY
COLLECTION_CADENCE_ID=PT1M_15_MINUTE_ANCHORS_V1
COLLECTION_NETWORK_AUTHORIZED=false
COLLECTION_SCHEDULER_ENABLED=false
PROSPECTIVE_COLLECTION_STARTED=false
CAP22_PROSPECTIVE_COLLECTION_CONTRACTS_IMPLEMENTED=true
CAP22_PROSPECTIVE_COLLECTION_STARTED=false
CAP22_90D_EVIDENCE_CLOCK_STARTED=false
CAP21_EXISTING_PRODUCER_AUTHORITY_PRESERVED=true
CAP21_APPEND_ONLY_AT_T_PERSISTENCE_IMPLEMENTED=true
CAP21_NEW_MEMBERSHIP_OWNER_CREATED=false
CAP22_MEMBERSHIP_AUTHORITY_ADDED=false
ECONOMIC_MD_EXISTING_PRODUCER_AUTHORITY_PRESERVED=true
ECONOMIC_MD_APPEND_ONLY_AT_T_PERSISTENCE_IMPLEMENTED=true
EXACT_T_BINDING_REQUIRED=true
NO_NEAREST_LATEST_FALLBACK=true
NO_TODAY_UNIVERSE_MEMBERSHIP_RETROACTIVE=true
NO_AS_OF_GUESSING=true
NO_IMPLICIT_FILL=true
APPEND_ONLY=true
IDENTICAL_DUPLICATE_IDEMPOTENT=true
CONFLICTING_OVERWRITE_FORBIDDEN=true
HISTORICAL_EVIDENCE_GENERATED=false
FORWARD_LABEL_EXECUTION_IMPLEMENTED=false
WALK_FORWARD_EXECUTION_IMPLEMENTED=false
POLICY_RATIFICATION_JUSTIFIED=false
ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false
ECONOMIC_RANK_ACTIVATED=false
PDF_STEP_5_STATUS=UNRESOLVED
ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5
PDF_STEP_7_STATUS=FORBIDDEN
RUNTIME_AUTHORITY_GRANTED=false
PRODUCTIVE_MF_HOST_JOIN=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK=true
NEXT_CANONICAL_DECISION=PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION
NEXT_CAP22_DEPENDENCY=SEPARATE_OWNER_GO_REQUIRED_FOR_PROSPECTIVE_15M_CAP21_AND_ECONOMIC_MD_COLLECTION
```

## 1. Cadence

Snapshots are indexed by the already-ratified cadence
`PT1M_15_MINUTE_ANCHORS_V1`. The canonical key is the exact UTC RFC3339
value `YYYY-MM-DDTHH:MM:00Z` where `minute % 15 == 0`. Non-15-minute
timestamps, offsets other than `Z`, and any rounding or nearest-T guess
are fail-closed.

## 2. Cap-2.1 universe-at-T seam

Cap 2.1 remains the sole structural/safety eligibility owner. Latest-state
persistence is unchanged. This seam only archives an already-produced
Cap-2.1 snapshot as "this was the Cap-2.1 snapshot for T".

Required preserved fields include `generated_at_event_time`,
`generated_at_wall_time`, `snapshot_id`, `payload_digest`,
`source_event_time`, producer/schema versions, and the existing
instrument/eligibility payload.

Fail closed on invalid T, missing/inconsistent event time, digest/schema
error, or a conflicting payload at the same T. Identical digest replay
is idempotent.

## 3. Economic-MD snapshot-at-T seam

The existing Economic-MD producer remains the observation owner. This
seam archives an already-produced `economic_md_input_snapshot.v1`
object. It does **not** add venue-fetch logic and does **not** compute
ranking features.

Required preserved provenance includes the Cap-2.1 snapshot
reference/digest, finalized contiguous PT1M marks, same-cycle
`bidPx`/`askPx`, event/capture timestamps, Economic-MD snapshot id and
digest, and producer/schema versions.

Persisting Economic-MD at T requires the exact Cap-2.1 snapshot already
archived at the same T. Missing binding, event-time mismatch, incomplete
snapshots, digest/schema errors, and conflicting duplicates fail closed.

## 4. Exact T binding

```text
Economic-MD snapshot at T -> exact Cap-2.1 governed-universe snapshot at T
```

No nearest/latest fallback. No today's universe. No as-of guessing. No
implicit fill. Binding is digest-verifiable and offline replayable.

## 5. Later collection flow (not executed)

```text
Cap2.1 snapshot(T)
→ Economic-MD observation(T) bound to exact Cap2.1 snapshot(T)
→ append-only persistence
→ manifest verification
```

```text
COLLECTION_NETWORK_AUTHORIZED=false
COLLECTION_SCHEDULER_ENABLED=false
PROSPECTIVE_COLLECTION_STARTED=false
CAP22_90D_EVIDENCE_CLOCK_STARTED=false
```

## 6. Authority boundary

```text
PDF_STEP_5_STATUS=UNRESOLVED
ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5
PDF_STEP_7_STATUS=FORBIDDEN
RUNTIME_AUTHORITY_GRANTED=false
PRODUCTIVE_MF_HOST_JOIN=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
THIS_SLICE_GRANTS_APPEND_ONLY_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_ONLY=true
```

## 7. Forbidden overreads

```text
OVERREAD_AS_COLLECTION_STARTED=FORBIDDEN
OVERREAD_AS_SCHEDULER_ENABLED=FORBIDDEN
OVERREAD_AS_90D_CLOCK_STARTED=FORBIDDEN
OVERREAD_AS_HISTORICAL_EVIDENCE_GENERATED=FORBIDDEN
OVERREAD_AS_WALK_FORWARD_EXECUTED=FORBIDDEN
OVERREAD_AS_RANKING_ACTIVATED=FORBIDDEN
OVERREAD_AS_POLICY_WINNER=FORBIDDEN
OVERREAD_AS_PDF_STEP_5_CLOSED=FORBIDDEN
OVERREAD_AS_NEW_CAP21_MEMBERSHIP_OWNER=FORBIDDEN
```
