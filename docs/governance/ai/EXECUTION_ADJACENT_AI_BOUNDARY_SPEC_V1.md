# Execution-Adjacent AI Boundary Spec v1

## Purpose
This document canonically defines the boundary between AI-adjacent components and actual trade execution in Peak_Trade.

It is a truth-first architecture note and does not imply runtime implementation beyond current evidence.

## Status Vocabulary
- `IMPLEMENTED`
- `PARTIAL`
- `DOC-ONLY`
- `UNKNOWN`
- `NOT ALLOWED`

## Canonical Boundary Categories

### AI-adjacent
Components, concepts, roles, or references that may influence analysis, proposals, critique, policy interpretation, or operator understanding.

AI-adjacent does not imply execution authority.

### execution-adjacent
Components that sit close enough to execution that their outputs may affect pre-execution gating, routing interpretation, readiness interpretation, or policy posture.

Execution-adjacent does not imply final trade authority.

### execution-authoritative
The component set that can actually permit, route, or materially advance a trade into the real execution path.

Current repo-near truth does not evidence any AI component as model-final execution-authoritative.

## Current Truth Summary
Current closest-to-trade authority is treated as a deterministic gated path.

Current safeguards evidenced in the execution boundary include:
- `NO_TRADE` baseline
- deny-by-default routing
- treasury separation
- strategy environment gating
- policy / critic influence before execution where evidenced
- enabled / armed / confirm-token style live controls
- execution-event persistence

## Canonical Authority Rules
- advisory influence is not execution authority
- supervisory influence is not execution authority
- provider/model reference is not execution authority
- proposer is not execution authority
- critic is not execution authority
- unresolved runtime slots are not execution authority
- no provider/model binding currently proves final trade authority
- no AI-adjacent reference currently proves self-improving live execution

## Closest-to-Trade Boundary
The closest-to-trade path remains canonically described as:
- deterministic
- gated
- guardrail-controlled
- not evidenced as LLM-final

## Not Allowed
- claiming AI-adjacent as execution-authoritative without explicit evidence
- claiming execution-adjacent as model-final trade authority without explicit evidence
- weakening deterministic guarded execution language
- bypassing `NO_TRADE`
- bypassing treasury separation
- bypassing enabled / armed / confirm-token style controls
- treating provider/model references as proof of execution authority

## Unknown-Reduction Backlog
1. identify exact execution-authoritative component chain
2. identify any execution-adjacent AI outputs with explicit runtime contracts
3. identify any policy/critic runtime blocking semantics
4. identify any explicit routing or readiness data contracts tied to AI-adjacent components
5. document any future model-final authority only if explicit evidence exists

## Canonical Reading Order
- `docs/governance/ai/AI_LAYER_CANONICAL_SPEC_V1.md`
- `docs/governance/ai/AI_UNKNOWN_REDUCTION_V1.md`
- `docs/governance/ai/CRITIC_PROPOSER_BOUNDARY_SPEC_V1.md`
- `docs/governance/ai/PROVIDER_MODEL_BINDING_SPEC_V1.md`
- `out/ops/peak_trade_truth_model_*`
- `out/ops/ai_layer_model_matrix_v1_*`
