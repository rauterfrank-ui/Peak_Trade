---
docs_token: DOCS_TOKEN_DDO_REAL_OUTCOME_EVALUATION_HORIZON_NORMATIVE_SEMANTICS_V1
status: active
scope: Normative REAL-outcome and evaluation-horizon semantics for offline DDO v1; N_BARS only; no engine implementation; no capture/runtime/promotion
capability: DDO_REAL_OUTCOME_EVALUATION_HORIZON_NORMATIVE_SEMANTICS_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# DDO Real Outcome / Evaluation Horizon Normative Semantics V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=WP_DDO_REAL_OUTCOME_EVALUATION_HORIZON_NORMATIVE_SEMANTICS_V1
SLICE_ID=S1_NORMATIVE_CONTRACT_PERSIST
OWNER_GO=OWNER_GO_S1_DDO_REAL_OUTCOME_EVALUATION_HORIZON_NORMATIVE_SEMANTICS_V1
BOUND_ORIGIN_MAIN_SHA=b976b2400ab0d3370bd9d67259c1e5caf8742393
DDO_REAL_OUTCOME_EVALUATION_HORIZON_NORMATIVE_SEMANTICS_V1=BOUND
RUNTIME_AUTHORIZATION_EFFECT=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
PROMOTION_AUTHORITY_EFFECT=NONE
LEARNING_PRODUCTIVE_AUTHORITY=NONE
DDO_TRADING_AUTHORITY=NONE
PROMOTION_AUTHORITY_ACTIVATION=false
EVALUATION_RUNTIME_WIRING=false
REAL_OUTCOME_HORIZON_ENGINE_WIRED=false
BLOCKED_CAPTURE_SEAMS_V0_UNCHANGED=true
EXTERNAL_EFFECT_AUTHORIZED=false
ATLAS_AUTHORITY=NONE
HINDSIGHT_LEAKAGE_ALLOWED=false
CODE_MUTATION_THIS_SLICE=false
NEXT_SLICE=S2_CONTRACT_SCHEMA_V1
NEXT_SLICE_AUTHORIZED=false
```

Navigation-only. Master Runbook remains SSOT. This contract **does not**
authorize Live, Testnet, orders, credentials, capture-seam unlock,
productive host join, runtime wiring, promotion activation, economic-score
numeric policy, price-source defaults, or computation of `actual_outcome_ref`.

Predecessor context:
[`docs/ops/specs/LEARNING_CURRENT_DECISION_CONTRACT_REALIGNMENT_V1.md`](LEARNING_CURRENT_DECISION_CONTRACT_REALIGNMENT_V1.md)
closed CURRENT decision join; REAL-outcome horizon semantics were explicitly
deferred (`NO_REAL_OUTCOME_SEMANTICS=true`). This persist closes that semantic
gap at the **normative contract** layer only.

## 1. Owner adjudication (binding)

```text
OWNER_ADJUDICATION_BOUND=true
D1=A  REAL outcome = horizon-complete measurement; never decision_outcome/decision_score
D2=B  Horizon start = explicit horizon_start_time_utc (validated)
D3=A  v1 REAL-capable evaluation_horizon token = N_BARS only
D4=A  N_BARS = N bar closes of explicit bar_spec_ref + instrument_ref
D5=A2+B  COMPLETE only on full valid bar chain; else audit UNKNOWN + explicit status
D6=B  Outcome scalar kind explicitly bound; evaluation_time_information_set_ref required
D7=B  MISSING/STALE/GAP/PARTIAL => no REAL claim; explicit observation status
D8=A  v1 REAL direction-neutral; no later side inference
D9=A  real_outcome_horizon_engine = offline observation supplier only
D10=A  Pure offline library; no capture decorator; not wired
D11=A  observation_horizon (drift) decoupled from evaluation_horizon (outcome)
```

## 2. Terminology and separation of concerns

| Concept | Role | Authority |
| --- | --- | --- |
| REAL outcome | Horizon-complete **measurement** of market/position economics | Evidence behind `actual_outcome_ref` only; not computed by DDO v0 record builders |
| `actual_outcome_ref` | Opaque ref to REAL measurement payload | Supplier-declared; engine does not mint or derive |
| `economic_score` | Separate **evaluation label** (opaque token) | Optional; no implicit formula or numeric policy in v1 |
| `decision_score` / authoritative `decision_outcome` | **DECISION_TIME** decision semantics (e.g. Double-Play producer token) | Never REAL economic outcome |
| `evaluation_observation_v0` | Offline engine input | Consumed by `evaluation_engine_v0` |
| `real_outcome_horizon_engine` | **Offline observation supplier** (future module) | Produces observation payloads only; blocked capture seam unchanged |
| `evaluation_engine_v0` | Deterministic evaluation **assembly** (outcome/attribution/counterfactual records) | No trading authority; no REAL computation |

```text
MEASUREMENT_NOT_DECISION=true
OBSERVATION_NOT_PROMOTION=true
EVALUATION_ASSEMBLY_NOT_SUPPLIER=true
DECISION_TIME_SAFETY_PIT_UNCHANGED=true
```

## 3. Horizon matrix (normative)

| Horizon (`evaluation_horizon`) | REAL v1 | Start anchor | Completion (eligible for REAL) | Evidence / PIT | Defect behavior |
| --- | --- | --- | --- | --- | --- |
| `DECISION_TIME` | **No REAL** (structural / safety / current decision only) | N/A for REAL | N/A for REAL | `decision_time_information_set_ref` on DecisionEvent (existing) | Later economics must not populate REAL fields; `actual_outcome_ref` and REAL `economic_score` remain UNKNOWN for REAL purposes |
| `N_BARS` | **Yes** (only REAL-capable v1 token) | **`horizon_start_time_utc`** declared by supplier; MUST satisfy `horizon_start_time_utc >= decision_event.event_time_utc` | Exactly **N** consecutive bar **close** times (UTC), one close per bar, from **`bar_spec_ref`** on **`instrument_ref`**; **N** explicit positive integer; **gapless** bar identity/continuity | **`actual_outcome_ref`** + **`outcome_scalar_kind`** + mandatory **`evaluation_time_information_set_ref`** at horizon end; scalar kind selects interpretation; **no** default mid/last/mark | If `horizon_observation_status` is `MISSING`, `STALE`, `GAP`, or `PARTIAL`: **no REAL outcome claim**; evaluation may emit OutcomeRecord with UNKNOWN measurement refs and explicit status/reason; must not assert COMPLETE |
| `IMMEDIATE_POST_EVENT` | **EXPLICITLY_DEFERRED** | — | — | — | Enum token remains; REAL semantics unbound until separate Owner-GO |
| `EVENT_RECOVERY` | **EXPLICITLY_DEFERRED** | — | — | — | Same |
| `POSITION_LIFECYCLE` | **EXPLICITLY_DEFERRED** | — | — | — | No lifecycle boundary defined in v1; must not invent |
| `UNKNOWN` | **No REAL** | — | — | — | Fail-closed; no later-economics ingestion (existing engine behavior) |

### 3.1 N_BARS parameters (v1)

Supplier observation MUST declare (normative names; schema binding in S2):

- `horizon_start_time_utc` (UTC timestamp)
- `instrument_ref` (opaque instrument identity ref)
- `bar_spec_ref` (opaque bar specification ref; defines bar duration/aggregation identity)
- `n_bars` (positive integer **N**)
- `horizon_observation_status` ∈ {`OK`, `MISSING`, `STALE`, `GAP`, `PARTIAL`}
- `outcome_scalar_kind` (explicit kind token; see §4)
- `evaluation_time_information_set_ref` (required when claiming REAL for `N_BARS`)
- `actual_outcome_ref` (required when `horizon_observation_status=OK` and REAL claimed)
- `economic_score` (optional evaluation label; independent of measurement)

Bar continuity: the N closes MUST form a single gapless chain anchored at
`horizon_start_time_utc` under `bar_spec_ref`. Any missing bar, stale bar,
parser defect, or partial window ⇒ status not `OK` ⇒ no REAL claim.

### 3.2 Outcome assembly when incomplete (D5 A2)

When status is not `OK` or completion rules fail:

- Evaluation assembly MAY still run offline for audit lineage.
- **`actual_outcome_ref`** MUST NOT be treated as REAL; OutcomeRecord stores
  UNKNOWN (or null per schema rules) for REAL measurement fields.
- **`horizon_observation_status`** and explicit reason MUST be preserved on
  the observation input (S2 schema).
- Safety correctness MUST continue to use **DECISION_TIME** information set only.

## 4. Outcome scalar kinds (D6 B — kind binding without price-source defaults)

v1 binds **kind labels only**. Each kind maps to an evidence payload schema
ref (S2); this contract does **not** select mid, last, mark, or venue default.

Initial kind tokens (extensible only via governed enum persist):

| `outcome_scalar_kind` | Meaning (normative) | Price source |
| --- | --- | --- |
| `LOG_RETURN` | Log return over the horizon per bound evidence schema | **Explicit in evidence payload** referenced by `actual_outcome_ref`; not implied by DDO |
| `ABS_RETURN` | Absolute return over the horizon per bound evidence schema | Same |
| `HIT_TARGET` | Binary or categorical hit/miss vs declared target in evidence | Same |

```text
OUTCOME_SCALAR_KIND_DEFAULT_FORBIDDEN=true
IMPLICIT_MID_LAST_MARK_FORBIDDEN=true
ECONOMIC_SCORE_NUMERIC_POLICY=UNBOUND
EVALUATION_HORIZON_NUMERIC_BAR_COUNT=EXPLICIT_N_IN_OBSERVATION
```

## 5. Direction neutrality (D8 A)

v1 REAL scalars are **direction-neutral** (magnitude-style kinds only).
Mapping REAL outcomes to decision direction, `selected_side`, or producer
`decision_outcome` is **out of scope** for v1 and MUST NOT use later prices
or position state for side inference.

## 6. Engine roles (D9 A, D10 A)

```text
REAL_OUTCOME_HORIZON_ENGINE_ROLE=OFFLINE_OBSERVATION_SUPPLIER_ONLY
REAL_OUTCOME_HORIZON_ENGINE_CAPTURE_SEAM=real_outcome_horizon_engine
REAL_OUTCOME_HORIZON_ENGINE_CAPTURE_SEAM_STATUS=BLOCKED_UNCHANGED
EVALUATION_ENGINE_V0_ROLE=DETERMINISTIC_EVALUATION_ASSEMBLY
SUPPLIER_MINTS_ACTUAL_OUTCOME_REF=false
SUPPLIER_COMPUTES_ECONOMIC_SCORE=false
EVALUATION_ENGINE_COMPUTES_REAL_MEASUREMENT=false
PRODUCTIVE_HOST_JOIN=false
BATCH_OFFLINE_INVOCATION_ONLY=true
```

Inputs: append-only DDO ledger records + **read-only external evidence refs**
(no exchange POST, no credential use, no trading core calls).

Outputs: **`evaluation_observation_v0`-conform** payloads (extended in S2),
passed to `evaluation_engine_v0` by an offline orchestrator.

## 7. Drift horizon decoupling (D11 A)

`observation_horizon` on drift records (`drift_contracts_v0`) and
`evaluation_horizon` on outcome/evaluation paths are **normatively decoupled**.
Equal string values are coincidental only. Drift observations MUST NOT
implicitly trigger or define REAL outcome horizons.

## 8. EXPLICITLY_DEFERRED

- REAL semantics for `IMMEDIATE_POST_EVENT`, `EVENT_RECOVERY`, `POSITION_LIFECYCLE`
- Direction-signed REAL outcomes (D8 B path)
- Unified horizon registry between drift and outcome paths (D11 C)
- Capture-seam unlock for `real_outcome_horizon_engine`
- Runtime / productive host wiring (`EVALUATION_RUNTIME_WIRING` remains false)
- `economic_score` formulas and numeric policies
- Automatic stale root-cause inference (`stale_root_cause_inference` seam blocked)
- Promotion activation or learning trading authority

## 9. FORBIDDEN

- Treating `decision_outcome`, `decision_score`, or DECISION_TIME replay match
  as REAL economic outcome
- REAL `N_BARS` without `horizon_start_time_utc`, `bar_spec_ref`, `instrument_ref`,
  explicit `n_bars`, gapless continuity, `outcome_scalar_kind`, and
  `evaluation_time_information_set_ref`
- Implicit or default price source (mid/last/mark) without evidence payload binding
- Claiming COMPLETE or REAL under `MISSING` / `STALE` / `GAP` / `PARTIAL`
- Using later-horizon economics to relabel safety (`HINDSIGHT_LEAKAGE_ALLOWED=false`)
- Coupling `observation_horizon` to `evaluation_horizon` in engine logic
- Unlocking `BLOCKED_CAPTURE_SEAMS_V0`, wiring `REAL_OUTCOME_HORIZON_ENGINE_WIRED=true`,
  or any EXTERNAL_EFFECT without separate scoped Owner-GO
- Mutating Master V2, Double Play policy, Trading Core, Ranking/Universe,
  Vollautonomie, Execution, Risk, or Live surfaces under this slice

## 10. Explicit non-goals (S1)

- No implementation of `real_outcome_horizon_engine`
- No S2 schema/code changes
- No Master Runbook mutation in this slice
- No Map-of-Truth authority elevation; Atlas remains navigation only

## 11. Slice closure

```text
S1_NORMATIVE_CONTRACT_PERSIST=COMPLETE
D1_D11_BOUND=true
TRUE_BLOCKER_SEMANTICS_NORMATIVE_LAYER=CLOSED_FOR_S2_SCHEMA_WORK
IMPLEMENTATION_BLOCKER=real_outcome_horizon_engine_NOT_IMPLEMENTED
```

S2 (`S2_CONTRACT_SCHEMA_V1`) requires separate Owner-GO before code/schema mutation.
