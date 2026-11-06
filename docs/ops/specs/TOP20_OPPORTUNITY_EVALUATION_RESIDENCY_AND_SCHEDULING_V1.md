---
docs_token: DOCS_TOKEN_TOP20_OPPORTUNITY_EVALUATION_RESIDENCY_AND_SCHEDULING_V1
status: active
scope: Cap2.2 Top20 evaluation continuity and non-preferential scheduling to ≤5 evaluation capacity
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
SELECTION_AUTHORITY: false
RANKING_AUTHORITY: false
TRADING_AUTHORITY: false
HARD_STOP: true
---

# Top20 Opportunity Evaluation Residency & Scheduling V1

```text
CAPABILITY_ID=TOP20_OPPORTUNITY_EVALUATION_RESIDENCY_V1
TOP20_EVALUATION_RESIDENCY_ENABLED=false
LIFECYCLE_SCHEMA=top20_opportunity_evaluation_residency.v2
COMPLETION_RELEASE=EVENT_DRIVEN
MAX_ACTIVE_EVALUATION_RESIDENTS=5
CONFIG_KEYS=top20_evaluation_residency_enabled;top20_evaluation_residency_max_pending
EVALUATION_COMPLETION=CANONICAL_INTEGRATED_OFFLINE_REPLAY_EXECUTED+VALID_GOVERNED_CYCLE_EVIDENCE
NATURAL_ENTER_REQUIRED_FOR_COMPLETION=false
```

Insert after FINAL VALID Cap2.2 persist; consume before staged N5 control plane orchestrator when enabled.

Admission snapshot duality: evaluation uses immutable `admission_snapshot_ref`; current Cap2.2 truth recorded separately in observations.

The only scheduling capacity config is `max_pending`. Residency has no duration,
deadline, expiry transition, or optional early-release switch. Elapsed time alone
neither completes nor discards an evaluation. A matching instrument + residency
epoch completion witness releases the slot immediately, including a valid HOLD
disposition; no entry is required. Structural hard invalidation still cancels a
record. The existing feedback orchestrator promotes the next pending record after
completion. Missing completion/invalidation events leave the record pending/active;
queue capacity remains bounded and overflow is explicitly rejected.

Admission timestamps, current ranking observations, source references, instrument
identity, epoch identity and measured latency remain durable evidence. These are
not holding-period controls. Market-data freshness and the separate Cap23
anti-churn policy retain their existing owners.

Storage schema v2 intentionally rejects every other schema before changing files.
Existing v1 stores and their evidence must be preserved. There is no automatic
conversion, empty reset, or reinterpretation of historical terminal states. A
deployment with existing v1 residency state requires a separately reviewed state
transition before use. Python callers supplying removed config keywords fail
explicitly instead of silently retaining old behavior.

Owner instruction, 2026-11-02: remove all code of the residency time model;
retain the adapter-provided comparison and persistence data. This change is local
code/config-contract work only, not runtime activation or permission to trade.

The B05 websocket consumer adapter supplies validated finalized PT1M mark data;
its required sample count is data completeness, not a residency countdown. Its
`ranking_safe` result is not a general future-safety or GGE-handoff verdict.
The inspection consumes existing adapter inputs and needs no websocket of its
own. The existing canonical replay completion contract above is preserved and is
distinct from the candidate-input inspection below. Live mark-price/Nulllinie
observations remain separate from finalized PT1M history.

## Owner correction: immediate rejection, no waiting (2026-11-02)

For a new candidate: a required input is absent/invalid, or a required check
fails → discard this candidate evaluation immediately. All required checks pass
→ forward the same input to GGE. No WAIT_DATA state, timer, retry loop, entry
requirement, websocket binding or permanent instrument blacklist is introduced.
Future selection remains with Cap23. Rejection of an evaluation is not authority
to liquidate or forget an existing position.

The local productive cycle host now inspects required numeric inputs before
conversion and consumes the existing CMC/typed-volatility eligibility verdict
before its first GGE/Layer-C call. Missing typed volatility is a candidate
rejection at this boundary rather than a later Replay block. Existing range,
identity/provenance, reconciliation and minimum-history checks remain in place.
The inspection applies only when the venue is flat with no existing position.

Non-interference requirement: the filter may refuse candidate handoff but may not
change accepted prices, features, policies, directions, confirmation counters,
Scope/SideState, sizing or runtime authorization. It performs no I/O, fetching,
queueing or persistence. Offline differential regression compares complete Replay
and cursor outputs for three cold/warm cycles with inspection active vs bypassed
in the test process; accepted results are equal. This is bounded evidence, not a
universal productive timing/non-interference proof.

This gate verifies supplied input validity and the existing canonical eligibility
contract. It cannot establish missing upstream source facts from numeric values
alone. The existing `_market_kwargs_from_observation_v1` helper still contains
fixed volume/OI/funding values and candle-derived bid/ask; genuine per-field
provenance and full productive coverage remain open. No arbitrary new economic
safety criteria or thresholds have been invented. Local changes remain
uncommitted and unactivated.

Owner package: `src/ops/top20_opportunity_evaluation_residency_v1/`.
