---
docs_token: DOCS_TOKEN_DDO_OUTCOME_TO_PROMOTION_PRODUCTIVE_BINDING_NORMATIVE_V1
status: active
scope: Normative adjudication only — whether productive N_BARS outcome_record may bind to Promotion/Eligibility; no activation, no join implementation
capability: DDO_OUTCOME_TO_PROMOTION_PRODUCTIVE_BINDING_NORMATIVE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# DDO Outcome → Promotion Productive Binding Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=WP_DDO_OUTCOME_TO_PROMOTION_PRODUCTIVE_BINDING_NORMATIVE_V1
SLICE_ID=S1_OUTCOME_PROMOTION_BOUNDARY_ADJUDICATION
OWNER_GO=OWNER_GO_WP_DDO_OUTCOME_TO_PROMOTION_PRODUCTIVE_BINDING_NORMATIVE_V1
BOUND_ORIGIN_MAIN_SHA=3279f991e155a5fc0a31df521ab72e5edc279778
ADJUDICATION=NO_N_BARS_TO_PROMOTION_BINDING
RUNTIME_AUTHORIZATION_EFFECT=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
PROMOTION_AUTHORITY_EFFECT=NONE
PROMOTION_AUTHORITY_ACTIVATION=false
LEARNING_PRODUCTIVE_AUTHORITY=NONE
OBSERVATION_NOT_PROMOTION=true
MEASUREMENT_NOT_DECISION=true
EVALUATION_ASSEMBLY_NOT_PROMOTION=true
EXTERNAL_EFFECT_AUTHORIZED=false
SELF_MODIFICATION_AUTHORIZED=false
IMPLEMENTATION_AUTHORIZED=false
PRODUCTIVE_PROMOTION_JOIN=false
ATLAS_AUTHORITY=NONE
OWNER_ADJUDICATION_BOUND=true
```

Navigation-only. Master Runbook remains SSOT. This contract **does not**
authorize promotion activation, productive promotion join, controller mutation,
outcome→pack mappers, deployment, execution, or trading authority.

Predecessor normative chain (N_BARS REAL path):

- [`docs/ops/specs/DDO_REAL_OUTCOME_EVALUATION_HORIZON_NORMATIVE_SEMANTICS_V1.md`](DDO_REAL_OUTCOME_EVALUATION_HORIZON_NORMATIVE_SEMANTICS_V1.md)
- [`docs/ops/specs/DDO_N_BARS_BAR_EVIDENCE_SUPPLIER_AUTHORITY_NORMATIVE_V1.md`](DDO_N_BARS_BAR_EVIDENCE_SUPPLIER_AUTHORITY_NORMATIVE_V1.md)
- [`docs/ops/specs/DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_NORMATIVE_V1.md`](DDO_O4_N_BARS_BAR_EVIDENCE_BRIDGE_NORMATIVE_V1.md)

Machine-readable decision:
`config/governance/ddo_outcome_to_promotion_productive_binding_decision_v1.json`

## 1. Domain census (binding)

### 1.1 Promotion / Eligibility domain

| Item | Ratified role | Authority |
| --- | --- | --- |
| `promotion_controller_v0` | Offline deterministic **eligibility** evaluation | No productive authority; `PROMOTION_ELIGIBILITY_DRY_RUN=true` |
| Inputs | `promotion_policy` + `candidate_artifact` + `validation_evidence_pack` | Controller contract; **no** `outcome_record` parameter |
| Output | `promotion_eligibility_record` | `deployment_authorized=false`, `execution_authorized=false` always |
| `PROMOTION_AUTHORITY_ACTIVATION` | Must remain **false** for controller entry | Hard guard: `PROMOTION_AUTHORITY_ACTIVATION_MUST_REMAIN_FALSE` |
| Promotion class | Learning **candidate** artifact class P0–P3 | Hypothesis lineage via `candidate_artifact.hypothesis_ref` |
| Semantic class | **Learning-artifact deployment eligibility** (dry-run gate stack), not trading decision | Gates = robustness/validation suite (replay, WF, MC, stress, safety, authority invariants, economic policy, etc.) |

```text
PROMOTION_DOMAIN=LEARNING_CANDIDATE_DEPLOYMENT_ELIGIBILITY_DRY_RUN
NOT_TRADING_DECISION_AUTHORITY=true
NOT_N_BARS_MEASUREMENT_AUTHORITY=true
```

### 1.2 `candidate_artifact`

Versioned learning candidate bound to a `learning_hypothesis` ref, declared
`promotion_class`, `artifact_hash`, optional experiment/dataset refs.
Rejected candidates remain auditable. **Not** a post-hoc N_BARS measurement row.

### 1.3 `validation_evidence_pack`

Aggregated **gate results** (`VALIDATION_GATE_IDS_V0`) for one
`candidate_artifact_ref`, optionally versus an incumbent. Gate meanings are
defined by gate id → validation artifact kind (provenance, replay, walk-forward,
Monte Carlo, stress, fault injection, safety regression, authority regression,
observability, shadow min evidence, economic policy, rollback, compatibility).
**Not** a substitute for REAL horizon measurement evidence.

### 1.4 N_BARS `outcome_record`

Product of `evaluation_engine_v0` **assembly** from `evaluation_observation_v0`
and `decision_event`. Stores opaque `actual_outcome_ref`, horizon token,
attribution-linked scores as declared tokens. **Does not** encode hypothesis
lineage, promotion class, or validation gate matrix.

```text
OUTCOME_RECORD_ROLE=EVALUATION_ASSEMBLY_ARTIFACT
REAL_MEASUREMENT_REF=actual_outcome_ref (opaque; supplier-backed)
```

### 1.5 Canonical cross-domain relationship

```text
CANONICAL_OUTCOME_TO_VALIDATION_PACK_MAPPING=ABSENT
CANONICAL_OUTCOME_TO_CANDIDATE_MAPPING=ABSENT
OUTCOME_RECORD_EQ_VALIDATION_EVIDENCE_PACK=FORBIDDEN_ASSUMPTION
REAL_OUTCOME_EQ_PROMOTION_ELIGIBILITY_EVIDENCE=FORBIDDEN_ASSUMPTION
```

No ratified spec, controller contract, or schema equivalence defines N_BARS
`outcome_record` as input to `evaluate_promotion_eligibility_v0`.

Horizon normative (subordinate, binding for REAL/N_BARS semantics):

```text
OBSERVATION_NOT_PROMOTION=true
MEASUREMENT_NOT_DECISION=true
EVALUATION_ASSEMBLY_NOT_SUPPLIER=true
```

## 2. Authority graph (productive N_BARS chain terminus)

```text
O4 evidence
  → [A] governed bridge TRANSLATE_AND_BIND_ONLY
  → [A] n_bars_bar_evidence_supplier_v1 (supplier_input authority)
  → [A] real_outcome_horizon_engine_v1 (observation supplier)
  → [A] capture seam real_outcome_horizon_engine (observation-only)
  → [A] evaluation_runtime_productive_host_v1 + evaluation_engine_v0
  → outcome_record + attribution_record + counterfactual_record
  → TERMINUS (this adjudication)
  ✗ (no ratified edge) → promotion_controller_v0
```

| Edge | Owner | Input | Output | Effect | Fail-closed | Mode |
| --- | --- | --- | --- | --- | --- | --- |
| Evaluation runtime → outcome bundle | `evaluation_engine_v0` | decision + observation + identity | outcome/attribution/counterfactual | NONE | missing REAL fields → UNKNOWN refs | PRODUCTIVE (when wired) |
| outcome_record → promotion eligibility | **UNRATIFIED / FORBIDDEN** | — | — | — | any assumed mapping | **NO BINDING** |

Promotion eligibility remains reachable only via **separate** offline inputs
(policy + candidate + pack), not via automatic consumption of N_BARS productive
runtime output.

## 3. Adjudication (Owner S1)

```text
ADJUDICATION=NO_N_BARS_TO_PROMOTION_BINDING
ADJUDICATION_CODE=C
```

**Rationale (evidence-backed):**

1. Structural input contracts diverge (hypothesis/candidate/gates vs decision/horizon/measurement ref).
2. Horizon normative forbids treating observation/evaluation assembly as promotion evidence.
3. Promotion controller ratifies dry-run eligibility with activation permanently false at entry.
4. No repository authority mandates a transformation from N_BARS productive `outcome_record` to promotion inputs.

**Rejected alternatives:**

- **A GOVERNED_BINDING_REQUIRED:** No ratified authority requires an outcome→promotion input transform.
- **B SEPARATE_DRY_RUN_OUTCOME_ELIGIBILITY_PATH:** No normative source defines an outcome-record-based eligibility path; inventing one would be new semantics (forbidden under this Owner-GO).

## 4. Productive chain closure

For the governed N_BARS productive path (O4 → … → evaluation runtime), the
**intentional terminal artifact family** is:

`outcome_record` / `attribution_record` / `counterfactual_record`.

Promotion remains an **independent learning-control domain** requiring its
own artifact lineage.

## 5. Explicitly forbidden (this adjudication)

- Productive or offline automatic feed of N_BARS `outcome_record` into
  `evaluate_promotion_eligibility_v0` without a **future** separate Owner-GO and
  normative binding spec.
- Setting `PROMOTION_AUTHORITY_ACTIVATION=true` to “enable” outcome bridging.
- Equating `actual_outcome_ref` with validation pack or gate PASS semantics.
- Trading, ranking, execution, or self-modification effects from this slice.

## 6. Future work (requires separate Owner-GO; not authorized here)

If operators later require outcome-informed promotion, they must choose explicitly among:

- New governed binding spec (would be adjudication A), or
- New separate dry-run outcome eligibility module (adjudication B),

each with its own Owner-GO — **not** assumed by this document.

```text
S1_ADJUDICATION_PERSIST=COMPLETE
IMPLEMENTATION_AUTHORIZED=false
PRODUCTIVE_PROMOTION_JOIN=false
```
