---
docs_token: DOCS_TOKEN_DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_NORMATIVE_V1
status: active
scope: Normative O4→DDO N_BARS bar-evidence bridge; closes supplier OWNER_DECISION_REQUIRED; no bridge/supplier implementation; no capture/runtime
capability: DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_NORMATIVE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# DDO O4 → N_BARS Bar Evidence Bridge Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=WP_DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_NORMATIVE_V1
SLICE_ID=S1_S4_BRIDGE_NORMATIVE_AND_IMPLEMENTATION_READY_CONTRACT
OWNER_GO=OWNER_GO_WP_DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_NORMATIVE_V1
BOUND_ORIGIN_MAIN_SHA=5320a087f4c4d58a54b9710ac663bb9cd355bcea
DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_NORMATIVE_V1=BOUND
RUNTIME_AUTHORIZATION_EFFECT=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
LEARNING_PRODUCTIVE_AUTHORITY=NONE
EXTERNAL_EFFECT_AUTHORIZED=false
REAL_OUTCOME_HORIZON_ENGINE_WIRED=false
BLOCKED_CAPTURE_SEAMS_V0_UNCHANGED=true
CAPTURE_SEAM_UNLOCK=false
PRODUCTIVE_HOST_JOIN=false
ATLAS_AUTHORITY=NONE
OWNER_ADJUDICATION_BOUND=true
A_BEFORE_B=true
```

Navigation-only. Master Runbook remains SSOT. This contract does **not**
authorize bridge/supplier implementation, capture unlock, runtime wiring,
O4 producer mutation, or network/exchange effects.

Predecessors (closed normative chain):

- [`DDO_REAL_OUTCOME_EVALUATION_HORIZON_NORMATIVE_SEMANTICS_V1.md`](DDO_REAL_OUTCOME_EVALUATION_HORIZON_NORMATIVE_SEMANTICS_V1.md)
- [`DDO_N_BARS_BAR_EVIDENCE_SUPPLIER_AUTHORITY_NORMATIVE_V1.md`](DDO_N_BARS_BAR_EVIDENCE_SUPPLIER_AUTHORITY_NORMATIVE_V1.md)

Machine-readable bridge decision:

`config/governance/ddo_o4_n_bars_bar_evidence_bridge_decision_v1.json`

## S1 — `evaluation_time_information_set_ref` (closed)

### S1.1 Minting authority

```text
EVALUATION_TIME_INFORMATION_SET_MINTING_AUTHORITY=peak_trade.learning.ddo.n_bars_bar_evidence_supplier_v1
DECISION_TIME_INFORMATION_SET_REUSE_FOR_EVALUATION=FORBIDDEN
```

Only the DDO N_BARS bar-evidence **supplier** mints
`evaluation_time_information_set_ref`. The bridge MUST NOT mint this ref.
The horizon engine MUST NOT mint this ref. [A] Predecessor REAL horizon §3.1
requires evaluation-time PIT ref distinct from decision-time safety pit.

### S1.2 Persisted artifact (binding)

Each minted ref MUST point to a persisted, content-addressed artifact:

```text
SCHEMA_NAME=ddo_n_bars_evaluation_time_information_set
SCHEMA_VERSION=ddo_n_bars_evaluation_time_information_set_v1
```

Required bound identities (all MUST be present; no defaults):

| Field | Requirement |
| --- | --- |
| `decision_event_ref` | Opaque link to evaluated DecisionEvent (`record_id`); lineage only — not PIT content |
| `instrument_ref` | MUST equal supplier `instrument_ref` |
| `bar_spec_ref` | MUST equal supplier `bar_spec_ref` |
| `horizon_start_time_utc` | MUST equal supplier anchor |
| `n_bars` | MUST equal supplier **N** |
| `bar_close_times_utc` | Full length-**N** UTC close chain |
| `bar_identity_refs` | Full length-**N** unique bar identity refs |
| `evaluation_boundary_time_utc` | MUST equal last element of `bar_close_times_utc` |
| `last_bar_last_observation_identity` | Copy of O4 `last_observation_identity` for final bar in chain |
| `o4_provenance` | `session_id`, `repository_sha`, `config_digest` from O4 snapshot input |
| `bridge_contract_id` | `peak_trade.learning.ddo.o4_n_bars_bar_evidence_bridge_v1` |
| `information_set_kind` | Constant token `N_BARS_HORIZON_END_PIT` |

### S1.3 Mint timing

Minting MUST occur **only after**:

1. Bridge translation reports `chain_completeness=GAPLESS_FINALIZED`.
2. All **N** O4 bars are `FINALIZED_BAR` or `CORRECTED_BAR` (not `IN_PROGRESS_BAR`).
3. `horizon_start_time_utc >= decision_event.event_time_utc` is satisfied.

The ref string MUST be a DDO `record_id`:

```text
evaluation_time_information_set_ref=ddo.eval_info_set.<content_hash_hex>
```

where `content_hash_hex` is `compute_content_hash_v0` over canonical JSON of the
artifact payload (excluding the ref field itself). [A] `require_record_id` shape.

### S1.4 Hindsight / PIT guard

```text
PIT_BOUNDARY=evaluation_boundary_time_utc
POST_BOUNDARY_OBSERVATIONS_IN_SET_FORBIDDEN=true
```

The information-set artifact MUST NOT include any observation or market event
whose authoritative event time is **strictly after**
`evaluation_boundary_time_utc`. If post-boundary data would be required to
compute the ref, minting MUST fail closed (supplier emits non-`OK` status).

Reusing `decision_time_information_set_ref` as `evaluation_time_information_set_ref`
is **FORBIDDEN** unless the persisted artifact bytes are identical (otherwise
`treat as FAIL_CLOSED`).

### S1.5 Failure → NO REAL

| Condition | `horizon_observation_status` | REAL claim |
| --- | --- | --- |
| Information-set artifact absent | `MISSING` | **No** |
| Artifact hash / field mismatch vs supplier input | `PARTIAL` | **No** |
| Post-boundary observation bound | `STALE` | **No** |
| Decision-time ref substituted | `PARTIAL` | **No** |
| Chain not gapless-finalized at mint time | `GAP` / `PARTIAL` | **No** |

```text
S1_INFORMATION_SET_REF_DECISION=CLOSED
```

## S2 — Measurement evidence per `outcome_scalar_kind` (closed)

Kinds are fixed to [A] `OUTCOME_SCALAR_KIND_V0`:

`LOG_RETURN`, `ABS_RETURN`, `HIT_TARGET` only. No new kinds in this slice.

Each `actual_outcome_ref` MUST reference a persisted payload with:

```text
SCHEMA_NAME=ddo_n_bars_outcome_measurement_evidence
SCHEMA_VERSION=ddo_n_bars_outcome_measurement_evidence_v1
```

Shared required fields (all kinds):

| Field | Requirement |
| --- | --- |
| `outcome_scalar_kind` | Enum token |
| `instrument_ref` | Matches supplier |
| `bar_spec_ref` | Matches supplier |
| `horizon_start_time_utc`, `n_bars` | Matches supplier |
| `bar_close_times_utc`, `bar_identity_refs` | Matches supplier when REAL chain claimed |
| `evaluation_time_utc` | MUST equal last bar close UTC |
| `price_basis_kind` | **Explicit** token; MUST NOT be mid/last/mark unless explicitly named in payload |
| `start_bar_identity_ref`, `end_bar_identity_ref` | First/last bar in chain |
| `start_price`, `end_price` | Explicit numeric prices used for measurement |
| `o4_provenance` | Same session/sha/digest binding as bridge input |
| `bridge_contract_id` | Bridge id constant |
| `measurement_producer_id` | `peak_trade.learning.ddo.n_bars_bar_evidence_supplier_v1` |

Allowed `price_basis_kind` tokens (v1 closed set):

```text
O4_BAR_CLOSE_FINALIZED
O4_BAR_CLOSE_CORRECTED
```

Selection rule: use `close` from start/end O4 bar snapshots; if bar state is
`CORRECTED_BAR`, kind MUST be `O4_BAR_CLOSE_CORRECTED`. No other price source
without separate Owner-GO.

Kind-specific required fields:

| Kind | Additional required fields |
| --- | --- |
| `LOG_RETURN` | `log_return` (float); MUST equal ln(end_price/start_price) with same price basis |
| `ABS_RETURN` | `abs_return` (float); MUST equal abs(end_price-start_price)/start_price |
| `HIT_TARGET` | `target_value` (float), `comparator` ∈ {`GE`, `LE`, `EQ`}, `hit_result` (bool), `compared_price` (= `end_price`) |

If any required measurement field cannot be populated from governed O4 evidence
without defaulting price/instrument/interval: supplier MUST NOT set
`horizon_observation_status=OK`.

```text
S2_MEASUREMENT_EVIDENCE_DECISION=CLOSED
OUTCOME_SCALAR_KIND_EXTENSION=FORBIDDEN_THIS_SLICE
```

## S3 — Bridge package / boundary (closed)

### S3.1 Package placement

```text
BRIDGE_PACKAGE=src/learning/deterministic_decision_outcome_v0
BRIDGE_CONTRACTS_PATH_FUTURE=src/learning/deterministic_decision_outcome_v0/o4_n_bars_bar_evidence_bridge_contracts_v1.py
BRIDGE_TRANSLATOR_ID_FUTURE=peak_trade.learning.ddo.o4_n_bars_bar_evidence_bridge_v1
BRIDGE_IMPLEMENTATION_AUTHORIZED=false
```

Rationale [J]: [F] Horizon-engine learning stretch forbids `src.ops` imports;
DDO supplier authority lives in learning; bridge output type is DDO supplier
input field bindings. O4 remains CAPABILITY_O4 domain. [A] Supplier authority
spec forbids direct O4 envelope reuse without bridge.

O4 code MUST NOT be mutated in this program. Bridge consumes **read-only
serializable snapshots** extracted offline from O4 envelopes [A] predecessor
§6 external evidence refs.

### S3.2 Authority boundary

| Role | Id | May mint REAL fields? |
| --- | --- | --- |
| O4 bar producer | `CanonicalPublicMdBarProducerV1` | O4 bars only — not DDO |
| Bridge translator | `peak_trade.learning.ddo.o4_n_bars_bar_evidence_bridge_v1` | **No** — translate/bind only |
| DDO supplier | `peak_trade.learning.ddo.n_bars_bar_evidence_supplier_v1` | **Yes** — sole `supplier_input` authority |
| Horizon engine | `real_outcome_horizon_engine_v1` | **No** — validates/transforms supplier input |

```text
PARALLEL_PRODUCER_AUTHORITY_FORBIDDEN=true
BRIDGE_DECISION_AUTHORITY=false
O4_AUTHORITY_DOMAIN_UNCHANGED=true
```

### S3.3 Dependency invariant

```text
A_BEFORE_B=true
CAPTURE_REMAINS_BLOCKED=true
```

```text
S3_BRIDGE_PACKAGE_DECISION=CLOSED
```

## S4 — Implementation-ready bridge contract

### S4.1 Pipeline (normative)

```text
O4_OFFLINE_SNAPSHOT
  -> validate_o4_n_bars_bar_evidence_snapshot_v1
  -> translate_o4_snapshot_to_ddo_n_bars_bindings_v1
  -> (supplier) mint evaluation_time_information_set + measurement evidence
  -> materialize_real_outcome_horizon_supplier_input_v1
  -> validate_real_outcome_horizon_supplier_input_v1
  -> supply_n_bars_evaluation_observation_v1
```

### S4.2 Bridge input — `o4_n_bars_bar_evidence_snapshot_v1`

Read-only evidence carrier. Serializable dict/JSON only. MUST NOT require
importing `src.ops` types at runtime in learning modules.

Required top-level fields:

- `schema_name` / `schema_version`
- `decision_event_ref`
- `horizon_start_time_utc` (UTC; supplier-declared anchor validated against bars)
- `n_bars` (positive int)
- `o4_interval_id` (normalized O4 interval token from snapshot)
- `o4_bars` (length **N** ordered list)

Each `o4_bars[]` element MUST carry minimum O4 envelope fields [F]
`AuthoritativeOhlcvBarEnvelopeV1`:

`canonical_instrument_id`, `venue_instrument_id`, `venue`, `interval`,
`bar_open_time`, `bar_close_time`, `finalization_state`, `quality_state`,
`last_observation_identity`, `session_id`, `repository_sha`, `config_digest`,
`close`, `revision`.

Optional defect markers MUST preserve O4 `MISSING_BAR` / `STALE_BAR` semantics.

### S4.3 Bridge output — `ddo_n_bars_bridge_translation_v1`

| Output field | Source rule |
| --- | --- |
| `instrument_ref` | `ddo.o4.inst.` + content hash of `(canonical_instrument_id, venue, venue_instrument_id)` |
| `bar_spec_ref` | `ddo.o4.barspec.` + content hash of normalized `o4_interval_id` |
| `bar_close_times_utc[]` | Each O4 `bar_close_time` converted to UTC `event_time_utc` string (fail closed on invalid) |
| `bar_identity_refs[]` | `ddo.o4.bar.` + content hash of `(canonical_instrument_id, interval, bar_open_time, revision)` per bar |
| `chain_completeness` | `GAPLESS_FINALIZED` iff count==N, strict interval grid, all finalized/corrected, no missing/stale slot |
| `horizon_observation_status` | `OK` only if `GAPLESS_FINALIZED`; map O4 missing→`MISSING`, stale→`STALE`, gap→`GAP`, else `PARTIAL` |
| `horizon_observation_reason` | Required when status ≠ `OK` |
| `o4_provenance` | Aggregated session/sha/digest from input |

Bridge MUST NOT emit `evaluation_time_information_set_ref`,
`actual_outcome_ref`, or `outcome_scalar_kind`.

### S4.4 Gaplessness / time semantics

Gapless chain under `bar_spec_ref` [A] REAL horizon predecessor:

- Bars sorted by `bar_open_time` ascending.
- For each consecutive pair: `next.bar_open_time == prev.bar_open_time + interval_duration_seconds`.
- Each bar window: `bar_close_time - bar_open_time == interval_duration_seconds`.
- First bar: `bar_close_times_utc[0] >= horizon_start_time_utc`.
- `horizon_start_time_utc >= decision_event.event_time_utc` enforced at supplier.

### S4.5 Provenance / failure modes

```text
FAIL_CLOSED_RULE=MISSING_OR_UNPROVEN_EVIDENCE_IMPLIES_NO_REAL_CLAIM
SILENT_GAP_FILL_FORBIDDEN=true
FIXTURE_PRODUCTIVE_AUTHORITY=false
```

Bridge translation failure MUST propagate non-`OK` status; supplier MUST NOT
upgrade to REAL.

### S4.6 Explicit non-goals

- No bridge/supplier Python implementation in this slice.
- No capture unlock; `real_outcome_horizon_engine` stays blocked.
- No `REAL_OUTCOME_HORIZON_ENGINE_WIRED=true`.
- No O4 producer mutation.

## Slice closure

```text
OWNER_DECISION_REQUIRED_PREDECESSOR_FIELDS=CLOSED
S1_INFORMATION_SET_REF=CLOSED
S2_MEASUREMENT_EVIDENCE_SCHEMA=CLOSED
S3_BRIDGE_PACKAGE_PLACEMENT=CLOSED
S4_IMPLEMENTATION_READY_CONTRACT=CLOSED
EARLIEST_REMAINING_BLOCKER=DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_AND_SUPPLIER_NOT_IMPLEMENTED
NEXT_IMPLEMENTATION_SLICE=REQUIRES_SEPARATE_OWNER_GO
```
