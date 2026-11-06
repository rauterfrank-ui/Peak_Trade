---
docs_token: DOCS_TOKEN_DDO_N_BARS_BAR_EVIDENCE_SUPPLIER_AUTHORITY_NORMATIVE_V1
status: active
scope: Normative sole DDO authority for N_BARS bar/outcome evidence materialization into real_outcome_horizon_supplier_input; no producer; no bridge implementation; no capture/runtime
capability: DDO_N_BARS_BAR_EVIDENCE_SUPPLIER_AUTHORITY_NORMATIVE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# DDO N_BARS Bar Evidence Supplier Authority Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=WP_DDO_CANONICAL_N_BARS_BAR_EVIDENCE_SUPPLIER_AUTHORITY_NORMATIVE_V1
SLICE_ID=S1_S4_NORMATIVE_AUTHORITY_AND_REUSE_ADJUDICATION_PERSIST
OWNER_GO=OWNER_GO_WP_DDO_CANONICAL_N_BARS_BAR_EVIDENCE_SUPPLIER_AUTHORITY_NORMATIVE_V1
BOUND_ORIGIN_MAIN_SHA=5320a087f4c4d58a54b9710ac663bb9cd355bcea
DDO_N_BARS_BAR_EVIDENCE_SUPPLIER_AUTHORITY_NORMATIVE_V1=BOUND
RUNTIME_AUTHORIZATION_EFFECT=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
PROMOTION_AUTHORITY_EFFECT=NONE
LEARNING_PRODUCTIVE_AUTHORITY=NONE
EXTERNAL_EFFECT_AUTHORIZED=false
REAL_OUTCOME_HORIZON_ENGINE_WIRED=false
BLOCKED_CAPTURE_SEAMS_V0_UNCHANGED=true
CAPTURE_SEAM_UNLOCK=false
PRODUCTIVE_HOST_JOIN=false
ATLAS_AUTHORITY=NONE
OWNER_ADJUDICATION_BOUND=true
```

Navigation-only. Master Runbook remains SSOT. This contract does **not**
authorize Live, Testnet, orders, credentials, capture-seam unlock,
productive host join, runtime wiring, O4 producer mutation, bridge
implementation, or bar/measurement producer code.

Predecessor (normative REAL horizon semantics, closed):

[`docs/ops/specs/DDO_REAL_OUTCOME_EVALUATION_HORIZON_NORMATIVE_SEMANTICS_V1.md`](DDO_REAL_OUTCOME_EVALUATION_HORIZON_NORMATIVE_SEMANTICS_V1.md)

Validator binding (S2 schema, closed):

`src/learning/deterministic_decision_outcome_v0/real_outcome_horizon_contracts_v1.py`
→ `validate_real_outcome_horizon_supplier_input_v1`

Horizon engine (offline transform only; does **not** mint bars):

`src/learning/deterministic_decision_outcome_v0/real_outcome_horizon_engine_v1.py`

Machine-readable reuse/authority decision (S4):

`config/governance/ddo_n_bars_bar_evidence_supplier_authority_decision_v1.json`

## S1 — Contract gap matrix (normative required fields)

Fixtures, tests, and hand-built `supplier_input` payloads are **never**
productive authority. [F] Only persisted governed producers/adapters may
materialize fields below.

| Field | Existing authority | Missing authority | Required producer guarantee |
| --- | --- | --- | --- |
| `horizon_start_time_utc` | [A] Predecessor §3.1; [A] `validate_n_bars_observation_for_decision_v1` (`horizon_start >= decision.event_time_utc`) | DDO bar-evidence supplier declares anchor; no default from decision time alone | Explicit UTC anchor; MUST satisfy `>= decision_event.event_time_utc`; MUST anchor gapless bar chain under `bar_spec_ref` |
| `instrument_ref` | [A] Predecessor §3.1 opaque instrument identity ref; [A] `require_opaque_ref` in supplier validator | Authority to bind decision/instrument context to stable opaque `instrument_ref` | No implicit instrument from venue strings; FAIL_CLOSED if binding ambiguous |
| `bar_spec_ref` | [A] Predecessor §3.1; [A] supplier validator requires opaque ref | Authority defining bar duration/aggregation identity as opaque ref | No default interval/bar-size; MUST NOT infer from O4 `interval` without governed bridge |
| `n_bars` | [A] Predecessor §3.1 explicit positive **N**; [A] `require_positive_int` | Policy owner for **N** selection per evaluation request | `n_bars > 0`; MUST match `bar_close_times_utc` length when closes present |
| `bar_close_times_utc` | [A] Predecessor gapless N closes; [A] `validate_bar_close_chain_v1` (count, strict UTC increase, first close vs `horizon_start_time_utc`) | Materialization authority for UTC bar close timestamps | Exactly **N** closes; strict increase; gapless under `bar_spec_ref` on `instrument_ref`; any gap ⇒ not `OK` |
| `bar_identity_refs` | [A] Predecessor bar identity/continuity; [A] `validate_bar_identity_refs_v1` (optional in validator but required for REAL completeness when claiming full chain) | Authority minting unique opaque bar identity refs per close | Count equals **N** when provided; pairwise unique; continuity semantics per predecessor §3.1 |
| `horizon_observation_status` | [A] Predecessor §3.1 enum; [A] `classify_n_bars_real_eligibility_v1` | Supplier classifies bar/measurement defects | `OK` only when chain and measurement evidence complete; else `MISSING`/`STALE`/`GAP`/`PARTIAL` with reason |
| `outcome_scalar_kind` | [A] Predecessor §4 kind labels; [A] `OUTCOME_SCALAR_KIND_V0` enum | **OWNER_DECISION_REQUIRED:** governed evidence payload schema ref per kind (predecessor §4 cites S2 schema refs not fully persisted as separate artifacts) | Explicit kind only; no price-source default |
| `evaluation_time_information_set_ref` | [A] Predecessor §3.1 mandatory for REAL `N_BARS`; [A] `require_record_id` in supplier validator | **OWNER_DECISION_REQUIRED:** authority minting PIT information-set ref at horizon end | `record_id` shape; MUST represent evaluation-time information set, not decision-time set |
| `actual_outcome_ref` | [A] Predecessor §2–§3 supplier-declared measurement ref; [A] `SUPPLIER_MINTS_ACTUAL_OUTCOME_REF=false` on horizon **engine** | **OWNER_DECISION_REQUIRED:** measurement evidence producer + payload schema binding per `outcome_scalar_kind` | Required when `horizon_observation_status=OK`; opaque ref to REAL measurement payload; engine MUST NOT mint |
| `economic_score` | [A] Predecessor optional label | No numeric policy in v1 | Optional; independent of measurement |

```text
S1_GAP_MATRIX_RESULT=COMPLETE_WITH_EXPLICIT_OWNER_DECISION_REQUIRED_FIELDS
FIXTURE_AUTHORITY=false
HAND_INPUT_PRODUCTIVE_AUTHORITY=false
```

## S2 — Reuse / bridge adjudication

Evidence-only adjudication. O4/public-MD authority is a **separate domain**.
[A] `src/ops/canonical_public_md_and_ohlcv_transport_reconciliation_v1/authority_matrix_v1.py`
→ `canonical_public_md_bar_producer_v1` / `CanonicalPublicMdBarProducerV1` is
AUTHORITATIVE for CAPABILITY_O4 only.

| Option | Verdict | Basis |
| --- | --- | --- |
| **A** Existing producer directly reusable for DDO `supplier_input` | **REJECTED** | [F] O4 `AuthoritativeOhlcvBarEnvelopeV1` uses `canonical_instrument_id`, `interval`, unix `bar_close_time` — not DDO opaque `instrument_ref` / `bar_spec_ref` / `bar_close_times_utc` strings / `bar_identity_refs`. [F] No governed mapping artifact exists. [F] Horizon engine module forbids `src.ops` imports (learning stretch contract test). |
| **B** O4/public-MD producer reusable only via governed DDO bridge | **SELECTED (necessary, not sufficient)** | [A] O4 sole authoritative bar producer for public MD. [J] Cross-domain reuse MUST NOT reinterpret O4 envelopes as DDO authority without explicit bridge contract. Bridge MUST emit learning-consumable opaque bundle without horizon engine importing O4 types. |
| **C** Separate DDO learning-only bar-evidence supplier required | **SELECTED (required)** | [A] Predecessor §6 external evidence + supplier-declared refs. [A] Sole `AUTHORITY_OWNER` for `validate_real_outcome_horizon_supplier_input_v1` materialization MUST live in DDO learning surface. |

```text
S2_REUSE_DECISION=O4_VIA_GOVERNED_BRIDGE_REQUIRED_AND_DDO_LEARNING_SUPPLIER_REQUIRED
DIRECT_O4_TO_DDO_REUSE=FORBIDDEN
O4_AUTHORITY_DOMAIN=CAPABILITY_O4_UNCHANGED
BRIDGE_CONTRACT_STATUS=NOT_IMPLEMENTED
BRIDGE_NORMATIVE_OWNER_SLICE=DEFERRED_SEPARATE_OWNER_GO
```

**Owner decisions (closed by successor bridge normative slice):**

[`DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_NORMATIVE_V1.md`](DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_NORMATIVE_V1.md)

```text
OWNER_DECISION_REQUIRED_PREDECESSOR_FIELDS=CLOSED_VIA_BRIDGE_NORMATIVE_V1
```

## S3 — Normative authority contract

### 3.1 Sole authority owner

```text
AUTHORITY_OWNER=peak_trade.learning.ddo.n_bars_bar_evidence_supplier_v1
NORMATIVE_IMPLEMENTATION_PATH_FUTURE=src/learning/deterministic_decision_outcome_v0/n_bars_bar_evidence_supplier_v1.py
IMPLEMENTATION_STATUS=NOT_AUTHORIZED_THIS_SLICE
```

Exactly one authority owner materializes
`real_outcome_horizon_supplier_input` conformant to
`validate_real_outcome_horizon_supplier_input_v1`. No parallel SSOT.

### 3.2 Role separation (binding)

| Component | Role | REAL bar/measurement authority |
| --- | --- | --- |
| `n_bars_bar_evidence_supplier_v1` (future) | Materialize supplier input + evidence refs | **Yes** (sole DDO owner) |
| `real_outcome_horizon_engine_v1` | Offline observation transform → `evaluation_observation_v0` | **No** — consumes validated supplier input only |
| `evaluation_engine_v0` | Deterministic evaluation assembly | **No** |
| `CanonicalPublicMdBarProducerV1` (O4) | Public-MD authoritative bars | **No** for DDO until governed bridge |
| DDO capture / host decorators | DecisionEvent observation | **No** — downstream; seam remains blocked |

```text
DDO_CONSUMES_EVIDENCE=true
HORIZON_ENGINE_DOES_NOT_MATERIALIZE_BARS=true
NO_FIXTURE_PRODUCTIVE_AUTHORITY=true
NO_MARKET_PRICE_INSTRUMENT_INTERVAL_DEFAULTS=true
```

### 3.3 Fail-closed rules

When bar chain, information set, instrument/bar-spec binding, or measurement
evidence cannot be **governed-proven**:

- MUST NOT claim REAL (`horizon_observation_status` MUST NOT be `OK` for REAL).
- MUST NOT treat `actual_outcome_ref` as REAL in evaluation assembly.
- MAY emit audit lineage with explicit defect status/reason per predecessor §3.2.
- MUST NOT infer mid/last/mark or instrument/interval defaults.

```text
FAIL_CLOSED_RULE=MISSING_OR_UNPROVEN_EVIDENCE_IMPLIES_NO_REAL_CLAIM
HINDSIGHT_LEAKAGE_ALLOWED=false
```

### 3.4 Dependency order (preserved)

```text
A_BEFORE_B=true
A=canonical_n_bars_bar_evidence_supplier_authority
B=capture_seam_unlock_productive_wiring
CAPTURE_REMAINS_DOWNSTREAM_AND_BLOCKED=true
```

Bar-evidence supplier authority MUST precede capture/runtime productive wiring
for `real_outcome_horizon_engine`. Unlocking capture without supplier authority
does not confer REAL semantics.

### 3.5 Explicit non-goals (this workpackage)

- No capture-seam unlock; `real_outcome_horizon_engine` stays in
  `BLOCKED_CAPTURE_SEAMS_V0`.
- No `REAL_OUTCOME_HORIZON_ENGINE_WIRED=true`.
- No `SEAM_SPECS_V0` entry or host `observe_after_producer_v0` decorators.
- No producer, adapter, bridge, network, or runtime implementation.
- No O4 producer mutation.
- No Master V2, Double Play, Ranking, Vollautonomie, execution, risk, or live
  surface changes.

## S4 — Machine-readable decision and traceability

Persisted decision record (authoritative for reuse class and owner id):

`config/governance/ddo_n_bars_bar_evidence_supplier_authority_decision_v1.json`

Traceability:

| Artifact | Binding |
| --- | --- |
| Predecessor REAL horizon S1 | Field semantics §3.1 |
| `validate_real_outcome_horizon_supplier_input_v1` | Required supplier input shape |
| `supply_n_bars_evaluation_observation_v1` | Downstream consumer of supplier output |
| O4 authority matrix | Reuse boundary only — not DDO authority |

## Slice closure

```text
S1_CONTRACT_GAP_MATRIX=PERSISTED
S2_REUSE_BRIDGE_ADJUDICATION=PERSISTED
S3_NORMATIVE_AUTHORITY_CONTRACT=PERSISTED
S4_MACHINE_READABLE_DECISION=PERSISTED
NEXT_IMPLEMENTATION_SLICE=REQUIRES_SEPARATE_OWNER_GO
EARLIEST_REMAINING_BLOCKER=DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_AND_SUPPLIER_NOT_IMPLEMENTED
```
