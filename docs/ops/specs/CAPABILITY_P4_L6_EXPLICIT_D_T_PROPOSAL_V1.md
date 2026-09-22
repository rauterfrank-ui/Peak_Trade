---
docs_token: DOCS_TOKEN_CAPABILITY_P4_L6_EXPLICIT_D_T_PROPOSAL_V1
status: active
scope: governed explicit D_t proposal contract for naked L6 ingress; charter and validation only
capability: CAPABILITY_P4_L6_EXPLICIT_D_T_PROPOSAL_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-22
---

# Capability P4 L6 — Explicit D_t Proposal V1 (Charter)

Governed **proposal contract only** for transporting an externally authorized
numeric distance into naked layered core L6 as `proposed_d_t`. This capability
does **not** compute, calibrate, default, or derive `value`.

```text
AUTHORITY=PROPOSAL_CONTRACT_ONLY
NUMERIC_FORMULA_AUTHORITY=NONE
PRODUCTIVE_BINDING_AUTHORIZED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
NO_DEFAULT=true
NO_FORMULA=true
NO_FALLBACK=true
CORE_LOGIC_CHANGE=false
P5_AUTHORITY_CUTOVER=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Role

| Layer | Owner |
| --- | --- |
| Proposal DTO + validation | `ops.p4_l6_explicit_d_t_proposal_v1` |
| L6 validate/pass-through | `trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l6_dynamic_scope_generator_v1` |
| L7 scope materialization | `trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l7_scope_state_v1` |
| L10 switch rule | `trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l10_bull_bear_switch_v1` |

## Forbidden proposal sources (non-exhaustive)

Integrated Replay scope distances, Cap 6.2/Cap 6.3 config distances,
`derive_scope_event_distances_v1`, research `compute_research_d_t_v1`,
fixtures, config defaults, optimizer/promotion backflow.

## Fail-closed

Without a valid `ExplicitDtProposalV1` matching P4 identity context, downstream
runtime must not invent `proposed_d_t`. Missing proposal ⇒ fail-closed only.

## Code

- `src/ops/p4_l6_explicit_d_t_proposal_v1/`
