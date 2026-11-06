# MASTER_V2 Canonical Volatility Max-Age Productive Research Evidence Accumulation Capability v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_MAX_AGE_PRODUCTIVE_RESEARCH_EVIDENCE_ACCUMULATION_CAPABILITY_V1
STATUS: CAPABILITY_AVAILABLE
scope: productive non-enforcing research evidence production, validation, ledger accumulation, and coverage readiness
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
NUMERIC_MAX_AGE_DECIDED: false
NUMERIC_MAX_AGE_SECONDS: null
THRESHOLD_STATUS: UNRESOLVED_MAX_AGE
ENFORCEMENT_ENABLED: false
ENFORCEMENT_APPLIED: false
NUMERIC_THRESHOLD_SELECTED: false
PARAMETER_PROMOTED: false
ALPHA_MUTATION_OCCURRED: false
REGIME_LABEL_IS_RESEARCH_METADATA_ONLY: true
HARD_STOP: true
---

> **Productive research-evidence accumulation only.** Produces, validates,
> deduplicates, and persistiert join-compatible evidence for later research
> execution. Does **not** select a numeric threshold, recommend candidates,
> mutate Alpha &#47; policy &#47; config, enforce age gates, or authorize orders.

## Machine summary

```
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_MAX_AGE_PRODUCTIVE_RESEARCH_EVIDENCE_ACCUMULATION_CAPABILITY_V1
EVIDENCE_SCHEMA_VERSION=canonical_volatility_max_age_productive_research_evidence_record/v1
LEDGER_SCHEMA_VERSION=canonical_volatility_max_age_productive_research_evidence_ledger/v1
JOIN_CONTRACT_VERSION=canonical_volatility_numeric_max_age_research_evidence_join/v1
AGE_REFERENCE_CLOCK=MARKET_EVENT_TIME
THRESHOLD_STATUS=UNRESOLVED_MAX_AGE
ENFORCEMENT_APPLIED=false
REGIME_LABEL_IS_RESEARCH_METADATA_ONLY=true
EVIDENCE_WRITE_FAILURE_BEHAVIOR=DIAGNOSTIC_ONLY_NO_TRADING_MUTATION
HARD_STOP=true
```

## Evidence Authority Graph

```
typed public&#47;shadow cycle (diagnostic)
  → productive evidence producer
  → validation &#47; quarantine
  → append-only productive ledger (chain + atomic write)
  → join projection (existing join contract)
  → research evidence ledger (PR #5616 loader)
  → coverage readiness (preregistered minima only)
```

No node in this graph is Alpha, Risk, Safety, TradingGate, order, or
threshold-selection authority.

## Schema and version

Productive records use
`canonical_volatility_max_age_productive_research_evidence_record&#47;v1` and
include session, venue&#47;instrument, repository SHA, digests, event-time age
fields, volatility provenance, restart&#47;reuse, research regime metadata,
trust states, validation, and `record_digest`.

Join projection reuses
`canonical_volatility_numeric_max_age_research_evidence_join&#47;v1` without a
second competing evidence specification.

## Session identity

Sessions are explicit: `session_id`, start&#47;end lifecycle, repository SHA,
venue&#47;instrument binding, resume token, and `restart_generation`.

- Process restart increments `restart_generation` and keeps `session_id`.
- Independent sessions require an explicit new open.
- Silent merge or split on restart is forbidden.

## Regime metadata

Labels are research metadata only:

`UP_DIRECTIONAL`, `DOWN_DIRECTIONAL`, `HIGH_VOLATILITY`, `LOW_VOLATILITY`,
`CHOP_OR_RANGE`, `STRESS_OR_GAP`, `UNCLASSIFIED`, `INSUFFICIENT_DATA`.

`REGIME_LABEL_MUTATES_ALPHA=false`,
`REGIME_LABEL_MUTATES_POLICY=false`,
`REGIME_LABEL_MUTATES_POSITION=false`.

Unprovable classification stays `UNCLASSIFIED` or `INSUFFICIENT_DATA`.

## Ledger format and recovery

Productive ledger envelopes are append-only JSONL with:

- explicit ledger schema version
- monotonic sequence
- previous &#47; current chain digest
- productive evidence payload
- optional research join payload
- quarantine reasons for invalid rows

Writes use temp-file + `fsync` + atomic replace. Corrupt tails fail closed.
Duplicate `evidence_record_id` &#47; semantic identity with identical digest is
idempotent; divergent digest fails closed.

## Validation &#47; quarantine

Records are quarantined for missing session&#47;SHA, negative age, non-finite
volatility, unknown unit&#47;horizon, event-time formula violations, missing
source digest, digest mismatch, untrusted clock&#47;data, schema mismatch,
instrument&#47;venue mismatch, or contradictory restart&#47;reuse semantics.

Quarantined rows never enter candidate evaluation paths.

## Join compatibility

The join ledger is consumed directly by
`load_research_evidence_records_v1` from PR #5616. Compatibility covers
schema, digest, nullability, versioning, session&#47;regime keys, age fields,
volatility provenance, restart&#47;reuse, and reject semantics.

## Coverage metrics

Coverage reports valid&#47;invalid&#47;quarantined&#47;duplicate counts, session and
regime coverage, observation histograms, event-time span, restart&#47;reuse&#47;
fallback&#47;trust counts, gaps, and `ready_for_research_execution`.

Readiness uses only existing authority:

- `MINIMUM_EVIDENCE_REQUIREMENTS_V1`
- research-execution `MINIMUM_SESSION_COUNT`, `MINIMUM_REGIME_COUNT`,
  `MINIMUM_EVIDENCE_COUNT`

No improvised minima. Missing authority remains blocked &#47; unresolved.

## Operator process — controlled evidence accumulation

Productive (authoritative bridge cycles only):

```
PYTHONPATH=src python3 scripts&#47;ops&#47;run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py \
  --mode productive-bridge-accumulate \
  --campaign-id &#60;campaign_id&#62; \
  --evidence-root &#47;tmp&#47;isolated_or_default_root \
  --productive-ledger-path &#47;path&#47;to&#47;productive_research_evidence_ledger.jsonl \
  --join-ledger-path &#47;path&#47;to&#47;research_evidence_ledger.jsonl \
  --quarantine-ledger-path &#47;path&#47;to&#47;productive_research_evidence_quarantine.jsonl
```

`probe-accumulate` remains a non-productive diagnostic helper and must not be
used for authorized productive evidence campaigns.

Productive bridge binding: set
`HardenedBridgeSessionStateV2.productive_evidence_accumulation_state`
via `bind_accumulation_state_to_hardened_bridge_session_v1(...)`.
See also
`MASTER_V2_CANONICAL_VOLATILITY_MAX_AGE_PRODUCTIVE_BRIDGE_CYCLE_INPUT_AUTHORIZATION_AND_ACCUMULATION_BINDING_V1`.
Evidence write failures remain diagnostic and do not alter trading behavior.

## Operator process — later research execution

After `ready_for_research_execution=true`:

```
PYTHONPATH=src python3 scripts&#47;ops&#47;run_canonical_volatility_numeric_max_age_parameter_research_execution_v1.py \
  --ledger-path &#47;path&#47;to&#47;research_evidence_ledger.jsonl
```

That later run still must not select, promote, or enforce a threshold without
a separate operator GO.

## Non-goals

- numeric max-age decision or recommendation
- candidate ranking as promotion
- policy &#47; config mutation
- enforcement
- Alpha &#47; position &#47; risk &#47; sizing &#47; safety mutation
- testnet &#47; live &#47; order activation
- economic validity claims

## Owners

| Artifact | Path |
|---|---|
| Accumulation package | `src&#47;research&#47;canonical_volatility_max_age_productive_research_evidence_accumulation_v1&#47;` |
| CLI | `scripts&#47;ops&#47;run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py` |
| Spec | this document |
| Numeric productive accumulation review-mode | `docs&#47;ops&#47;specs&#47;MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_RESEARCH_EVIDENCE_ACCUMULATION_V1.md` |
| Tests | `tests&#47;research&#47;test_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py` |
| Numeric focused tests | `tests&#47;research&#47;test_canonical_volatility_numeric_max_age_productive_research_evidence_accumulation_v1.py` |
| Join &#47; preregistration owner | `src&#47;trading&#47;master_v2&#47;canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1.py` |
| Research execution consumer | `src&#47;research&#47;canonical_volatility_numeric_max_age_parameter_research_execution_v1&#47;` |
