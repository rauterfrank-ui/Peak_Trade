# MASTER_V2 Canonical Volatility Max-Age Productive Bridge Cycle Input Authorization and Accumulation Binding v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_MAX_AGE_PRODUCTIVE_BRIDGE_CYCLE_INPUT_AUTHORIZATION_AND_ACCUMULATION_BINDING_V1
STATUS: CAPABILITY_AVAILABLE
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
NUMERIC_MAX_AGE_DECIDED: false
THRESHOLD_STATUS: UNRESOLVED_MAX_AGE
ENFORCEMENT_ENABLED: false
ENFORCEMENT_APPLIED: false
HARD_STOP: true
---

> Productive bridge-cycle input authorization and accumulation binding only.
> Does **not** select a numeric threshold, rank candidates, enforce age gates,
> mutate Alpha &#47; policy &#47; config, or authorize orders.

## Machine summary

```
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_MAX_AGE_PRODUCTIVE_BRIDGE_CYCLE_INPUT_AUTHORIZATION_AND_ACCUMULATION_BINDING_V1
AUTHORITATIVE_INPUT=MASTER_V2_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_HARDENED_BRIDGE_CYCLE_OUTPUT
CLI_MODE=productive-bridge-accumulate
SYNTHETIC_FALLBACK=false
THRESHOLD_STATUS=UNRESOLVED_MAX_AGE
ENFORCEMENT_APPLIED=false
HARD_STOP=true
```

## Productive input graph

```
operator session plan (campaign_id, session_id, repository_sha)
  → MarketSampleIdentityV1 (event-time mark samples)
  → run_hardened_bridge_cycle_v2 (canonical Master-V2 / Double-Play call graph)
  → stamp productive_bridge_cycle_authority
  → authorize_productive_bridge_cycle_input_v1 (fail-closed)
  → accumulate_productive_research_evidence_from_cycle_v1
  → append-only productive ledger + join ledger (+ quarantine on invalid)
```

Runtime cycles are **not** market samples. Duplicate market-sample identities
cannot create a new age observation. Event time remains authoritative.

## Accumulation-state ownership

`HardenedBridgeSessionStateV2.productive_evidence_accumulation_state` is the
sole session-owned handle. Binding API:

```python
session_state = bind_accumulation_state_to_hardened_bridge_session_v1(
    session_state,
    accumulation_state=productive_accumulation_state,  # or create via kwargs
    campaign_id=...,
    repository_sha=...,
)
```

No global mutable singleton. Session and accumulation state are passed
explicitly. Restart &#47; reuse semantics come from productive lifecycle only.

## Session &#47; restart &#47; reuse lifecycle

- Independent sessions require an explicit new open (`session_id`).
- Process restart increments `restart_generation` and keeps `session_id`.
- Restored ledger history is tracked in `restored_history_record_ids` and is
  **not** counted as newly produced estimates.
- Reuse is derived from estimate identity across distinct cycles.
- Duplicate `market_sample_id` → `DUPLICATE_MARKET_SAMPLE_NO_NEW_AGE_OBSERVATION`.

## CLI &#47; runner

```
PYTHONPATH=src python3 scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py \
  --mode productive-bridge-accumulate \
  --campaign-id <campaign_id> \
  --repository-sha <sha> \
  --session-count 2 \
  --samples-per-session 62 \
  --evidence-root /tmp/isolated_evidence_root
```

Rules:

- never calls `_synthetic_probe_cycles_v1()`
- rejects synthetic &#47; fixture &#47; test provenance
- verifies repository SHA and preregistration digest before mutation
- append-only ledgers; chain validated before &#47; after append
- empty input → no ledger files &#47; no records
- bounded session &#47; cycle limits

`probe-accumulate` remains a non-productive diagnostic mode and is **not**
authorized for productive evidence campaigns.

## Contract and digest validation

Before mutation:

- `SOURCE_IS_AUTHORITATIVE_BRIDGE_CYCLE=true`
- `SYNTHETIC=false`, `FIXTURE=false`, `TEST_DATA=false`
- repository SHA match
- preregistration digest match
  (`965f6e09e50e434e363d380c2d62e43041a37ad7d87956e590609a16f011b537`)
- `canonical_volatility_typed_binding` present
- `max_age_policy_evidence` present
- session &#47; cycle &#47; campaign &#47; market-sample identity present

## Ledger transaction boundary

1. Validate &#47; authorize cycle
2. Produce + validate record
3. Atomic append to productive ledger (temp + fsync + replace)
4. Append join projection (bijection required)
5. Quarantine path on invalid records (never candidate evaluation)

Default relative ledger paths are defined by the accumulation constants module
(`DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH`, `DEFAULT_JOIN_LEDGER_RELATIVE_PATH`,
`DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH`) and may be absent until a later
authorized campaign. Operator CLI examples use temporary roots, for example:

```
--productive-ledger-path &#47;path&#47;to&#47;productive_research_evidence_ledger.jsonl
--join-ledger-path &#47;path&#47;to&#47;research_evidence_ledger.jsonl
--quarantine-ledger-path &#47;path&#47;to&#47;productive_research_evidence_quarantine.jsonl
```

Tests and capability probes **must** use temporary evidence roots.

## Capability probe vs later campaign

| Surface | Purpose | Default ledgers |
|---|---|---|
| Capability offline probe | Prove binding + integrity | temporary only |
| Authorized session campaign | Accumulate productive research evidence | default productive paths |

Probe records must not be committed as campaign evidence.

## Non-goals

- numeric max-age decision &#47; ranking &#47; promotion
- enforcement
- Alpha &#47; risk &#47; safety &#47; strategy mutation
- testnet &#47; paper &#47; live &#47; order activation
- synthetic &#47; fixture productive evidence

## Owners

| Artifact | Path |
|---|---|
| Binding | `src&#47;research&#47;canonical_volatility_max_age_productive_research_evidence_accumulation_v1&#47;productive_bridge_binding_v1.py` |
| Runner | `src&#47;research&#47;canonical_volatility_max_age_productive_research_evidence_accumulation_v1&#47;productive_bridge_runner_v1.py` |
| Bridge hook | `src&#47;ops&#47;wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2&#47;hardening_cycle_bridge_v2.py` |
| CLI | `scripts&#47;ops&#47;run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py` |
| Tests | `tests&#47;research&#47;test_canonical_volatility_max_age_productive_bridge_accumulation_binding_v1.py` |
| Spec | this document |
