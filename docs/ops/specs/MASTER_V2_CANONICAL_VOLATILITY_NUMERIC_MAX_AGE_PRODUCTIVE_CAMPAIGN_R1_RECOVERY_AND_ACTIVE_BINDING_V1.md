# MASTER_V2 Canonical Volatility Numeric Max-Age Productive Campaign
# R1 Recovery and Active Binding v1
#
# ATLAS_AUTHORITY=NONE
# RUNTIME_AUTHORIZATION_EFFECT=NONE
# OWNER_POLICY=R1_ABANDON_OLD_CAMPAIGN_AND_START_NEW_CAMPAIGN_FROM_FRESH_S01

## Purpose

Governed recovery contract that abandons the incomplete historical productive
evidence campaign as a terminal non-authoritative tombstone and binds exactly
one ACTIVE authorized campaign identity for a fresh S01→S02 natural-age path.

## Bound owner fields

```text
OLD_CAMPAIGN_DISPOSITION=ABANDONED_INCOMPLETE_NON_AUTHORITATIVE
OLD_CAMPAIGN_COMPLETION_ALLOWED=false
OLD_CAMPAIGN_REACTIVATION_ALLOWED=false
OLD_SESSION_REUSE_ALLOWED=false
NEW_CAMPAIGN_ID_REQUIRED=true
NEW_SESSION_IDS_REQUIRED=true
FRESH_S01_REQUIRED=true
FRESH_AUTHORIZATION_REQUIRED=true
CROSS_SHA_REUSE_ALLOWED=false
SYNTHETIC_S01_ALLOWED=false
MISSING_PERSISTENCE_TREATED_AS_ABSENT=true
NATURAL_AGE_SOURCE=FRESH_PERSISTED_S01_LIFECYCLE_HISTORY_ONLY
EXACTLY_ONCE_REQUIRED=true
ADDITIONAL_EVIDENCE_RECLASSIFICATION=false
ACTIVE_CAMPAIGN_CARDINALITY=1
```

## Authority seam

Sole active identity is the governed active-binding artifact under
`config/governance/`. Runner/preflight and campaign-authorization issuance
consume only that ACTIVE binding. Unknown, missing, or multiple ACTIVE
bindings fail closed. Abandoned campaign/session IDs cannot be reactivated
or completed.

## Preserved semantics

- S01 = fresh early estimate producer under the new campaign
- Durable typed volatility persistence under the new campaign
- S02 = late-age observation of the same new campaign
- `natural_age = market_event_time - estimate.as_of_event_time`
- No Additional-Evidence reclassification
- No Auth-v2 reuse as substitute
- No Trading / Optimization / Promotion / External-Effect authority change

## Non-goals

This capability does not authorize network, session execution, campaign runs,
S01/S02 consume, threshold selection, enforcement, or live/testnet orders.
