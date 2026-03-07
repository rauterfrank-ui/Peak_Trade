# Critic / Proposer Boundary Spec v1

## Purpose
This document canonically defines the current boundary between proposer and critic roles in Peak_Trade.

It is a truth-first architecture note and does not imply runtime implementation beyond current evidence.

## Status Vocabulary
- `IMPLEMENTED`
- `PARTIAL`
- `DOC-ONLY`
- `UNKNOWN`
- `NOT ALLOWED`

## Current Boundary Summary
- proposer is treated as an advisory role slot
- critic is treated as a supervisory role slot
- neither proposer nor critic is currently evidenced as final trade authority
- closest-to-trade execution remains a deterministic gated path

## proposer

### Role Intent
- proposal / generation / candidate-production slot

### Authority Ceiling
- advisory only

### Allowed Influence
- may shape candidate ideas, hypotheses, proposals, or pre-decision artifacts
- may inform upstream reasoning or operator visibility

### Not Allowed
- must not directly execute trades
- must not override deterministic gates
- must not bypass `NO_TRADE`
- must not bypass treasury separation
- must not act as model-final trade authority

### Evidence Class
- `UNKNOWN`

### Known Today
- proposer terminology is referenced in the architecture language

### Unresolved Fields
- exact runtime module
- exact repo ownership
- exact input contract
- exact output contract
- exact model/provider binding

## critic

### Role Intent
- pre-execution critique / policy influence / supervisory gate-adjacent slot

### Authority Ceiling
- supervisory only

### Allowed Influence
- may emit gate-adjacent signals
- may influence pre-execution policy evaluation
- may block or downgrade proposals only if and where future runtime evidence explicitly supports that path

### Not Allowed
- must not directly execute trades
- must not become implicit model-final authority
- must not weaken deterministic guarded execution wording

### Evidence Class
- `PARTIAL`

### Known Today
- critic semantics are consistent with pre-execution critique
- critic semantics are consistent with policy / gate influence
- critic is the clearest partially evidenced AI-adjacent supervisory component

### Unresolved Fields
- exact runtime ownership
- exact data contract
- exact provider/model binding
- exact blocking semantics in runtime

## Placeholder Data Contracts

### proposer inputs
- UNKNOWN

### proposer outputs
- UNKNOWN

### critic inputs
- policy context / execution preconditions

### critic outputs
- gate signal / policy influence

## Execution Authority Boundary
The canonical execution boundary remains:

- `NO_TRADE` baseline
- deny-by-default routing
- treasury separation
- strategy environment gating
- policy / critic influence before execution where evidenced
- deterministic gated closest-to-trade path

## Not Allowed
- treating proposer as execution authority
- treating critic as execution authority
- implying proposer or critic is model-final trade authority
- weakening the deterministic gated execution statement
- claiming implemented proposer / critic runtime bindings without code/config evidence

## Unknown-Reduction Backlog
1. locate or explicitly mark proposer runtime path
2. define critic data contract more precisely
3. identify any provider/model binding locations
4. identify repo ownership for proposer / critic semantics
5. document any future execution-adjacent AI boundary only with explicit evidence

## Canonical Reading Order
- `docs&#47;governance&#47;ai&#47;AI_LAYER_CANONICAL_SPEC_V1.md`
- `docs&#47;governance&#47;ai&#47;AI_UNKNOWN_REDUCTION_V1.md`
- `out&#47;ops&#47;peak_trade_truth_model_*`
- `out&#47;ops&#47;ai_layer_model_matrix_v1_*`
