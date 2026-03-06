# AI Layer Canonical Spec v1

## Purpose
This document defines the current canonical truth for Peak_Trade AI-layer semantics and execution authority boundaries.

It is a truth-first architecture note, not a marketing document.

## Status Vocabulary
- `IMPLEMENTED`
- `PARTIAL`
- `DOC-ONLY`
- `UNKNOWN`
- `NOT ALLOWED`

## Current Truth Summary
Peak_Trade is currently:
- strong as a system
- strong as a governance and ops stack
- strong in reproducibility
- strong in guarded execution

Peak_Trade is not yet evidenced as:
- a fully autonomous self-improving AI operating system
- an LLM-final trade executor
- a proven online self-improving live system

## Canonical Layer Matrix

| Layer | Purpose | Inputs | Outputs | Gate Level | Authority Class | Current Status |
|---|---|---|---|---|---|---|
| L0 | Base system / deterministic infra layer reference | UNKNOWN | UNKNOWN | infrastructure | non-decisioning | UNKNOWN |
| L1 | Early analysis / support layer reference | UNKNOWN | UNKNOWN | pre-decision | advisory | UNKNOWN |
| L2 | Mid-level analysis / support layer reference | UNKNOWN | UNKNOWN | pre-decision | advisory | UNKNOWN |
| L3 | Higher-level analysis / support layer reference | UNKNOWN | UNKNOWN | pre-decision | advisory | UNKNOWN |
| L4 | Advanced supervisory / orchestration layer reference | UNKNOWN | UNKNOWN | pre-execution | supervisory | UNKNOWN |
| L5 | Highest referenced layer in current repo signals; exact semantics not yet canonicalized | UNKNOWN | UNKNOWN | pre-execution | UNKNOWN | UNKNOWN |

## Canonical Role Definitions

### proposer
- Intended meaning: proposal / generation role
- Authority class: advisory
- Current status: `UNKNOWN`
- Exact runtime implementation path: `UNKNOWN`

### critic
- Intended meaning: pre-execution critique / policy-gate influence
- Authority class: supervisory
- Inputs: policy context / execution preconditions
- Outputs: gate signal / policy influence
- Gate level: pre-execution
- Current status: `PARTIAL`

### provider
- Intended meaning: model/provider binding reference
- Authority class: none by itself
- Current status: `UNKNOWN`
- Exact runtime provider assignment: `UNKNOWN`

## Model / Provider Binding Truth
Explicit model/provider bindings must only be treated as `IMPLEMENTED` when directly evidenced in code or config.

Current repo-near truth:
- provider references exist
- exact model assignments per layer remain unresolved
- explicit LLM-final trade authority is not evidenced

## Execution Authority Boundary
The current closest-to-trade authority is treated as a deterministic gated path.

Current evidenced execution safeguards include:
- `NO_TRADE` baseline
- deny-by-default routing
- treasury separation
- strategy environment gating
- policy / critic influence in the pre-execution path
- execution-event persistence
- enabled / armed / confirm-token style live controls

## Not Allowed
- unguarded live activation
- bypassing enabled / armed / confirm-token style controls
- bypassing treasury separation
- treating stale evidence as current proof
- claiming model-final trade authority without explicit evidence
- implying a self-improving live AI engine without explicit implementation evidence

## Learning Reality
Current evidence supports offline / research-oriented learning such as:
- training
- walk-forward
- experiment tracking
- registry-based workflows

Current evidence does not yet prove:
- online self-improving live learning
- autonomous model updating
- model-final trade authority

## Dashboard Truth Guidance

### Dashboard may show today
- system state
- guard state
- evidence / snapshots / incident state
- testnet / pilot status
- readiness / routing / health
- strategy environment gating
- offline research / experiment history

### Dashboard must not imply today
- fully autonomous AI operating system
- self-improving live engine
- LLM as final trade authority
- implemented model assignments where repo evidence is missing

## Unknowns Backlog
- exact semantics for L0-L5
- exact proposer runtime path
- exact provider bindings
- exact model assignments per component
- any execution-adjacent model with final trade authority

## Source Truth Inputs
This spec should be read together with the latest truth artifacts under `out&#47;ops&#47;peak_trade_truth_model_*` and `out&#47;ops&#47;ai_layer_model_matrix_v1_*`.
