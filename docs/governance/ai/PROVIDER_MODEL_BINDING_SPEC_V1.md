# Provider / Model Binding Spec v1

## Purpose
This document canonically defines how provider and model binding claims must be interpreted in Peak_Trade.

It is a truth-first architecture note and does not imply runtime implementation beyond current evidence.

## Status Vocabulary
- `IMPLEMENTED`
- `PARTIAL`
- `DOC-ONLY`
- `UNKNOWN`
- `NOT ALLOWED`

## Canonical Principle
Provider or model references do not by themselves prove:
- runtime binding
- execution authority
- final trade authority
- live self-improving autonomy

## Binding Evidence Classes

### code-wired
A provider/model binding may be treated as implemented only when directly evidenced in executable code.

### config-wired
A provider/model binding may be treated as implemented only when directly evidenced in active config and tied to a known runtime path.

### docs-only
A provider/model reference that exists only in documentation, architecture language, or comments is not a runtime binding.

### unknown
If a provider/model reference exists but exact ownership, runtime path, or binding mechanism is unresolved, it remains `UNKNOWN`.

## Canonical Binding Slots

| Slot | Meaning | What Is Known Today | What Remains Unknown | Status |
|---|---|---|---|---|
| provider slot | names the provider family or runtime source | provider references exist in repo-near scans | exact provider assignment per component | UNKNOWN |
| model slot | names the concrete model identifier | model terminology may appear in scans | exact model identifier per component | UNKNOWN |
| component ownership slot | identifies which module owns the binding | AI-adjacent concepts exist | exact component ownership for each binding | UNKNOWN |
| fallback slot | identifies fallback behavior if primary binding is absent | fallback concept is architecturally useful | exact fallback semantics | UNKNOWN |
| runtime path slot | identifies where the binding is exercised in runtime | no explicit canonical runtime path is fully documented | exact binding call path | UNKNOWN |

## What Provider / Model Binding May Mean Today
- a future integration point
- a referenced architecture slot
- a partial or unresolved AI-adjacent concept
- a non-execution advisory or supervisory placeholder

## What Provider / Model Binding Must Not Mean Today
- final trade authority
- automatic execution authority
- self-improving live capability
- implied runtime implementation without direct evidence

## Binding Interpretation Rules
A provider/model binding may only be called `IMPLEMENTED` when all of the following are true:
1. exact provider is evidenced
2. exact model is evidenced
3. exact owning component is evidenced
4. exact runtime path is evidenced
5. authority boundary is explicitly consistent with current guarded execution truth

If any of these are missing, the binding must remain `PARTIAL`, `DOC-ONLY`, or `UNKNOWN`.

## Current Repo-Near Truth
- provider references exist
- exact provider bindings remain unresolved
- exact model bindings remain unresolved
- no explicit model-final trade authority is currently evidenced
- closest-to-trade execution remains deterministic gated

## Authority Boundary
Provider/model binding clarity must not weaken these facts:
- `NO_TRADE` baseline remains controlling
- deny-by-default remains controlling
- treasury separation remains controlling
- strategy environment gating remains controlling
- proposer remains advisory-only unless future evidence proves otherwise
- critic remains supervisory-only unless future evidence proves otherwise
- no provider/model reference currently proves final trade authority

## Unknown-Reduction Backlog
1. identify provider ownership per AI-adjacent component
2. identify model ownership per AI-adjacent component
3. identify any config-wired binding path
4. identify any code-wired binding path
5. identify fallback semantics
6. identify any execution-adjacent binding with explicit evidence

## Not Allowed
- claiming provider binding without exact owner/path evidence
- claiming model binding without exact owner/path evidence
- claiming execution authority from provider/model presence alone
- claiming final trade authority from provider/model presence alone
- implying self-improving live autonomy from binding references

## Canonical Reading Order
- `docs&#47;governance&#47;ai&#47;AI_LAYER_CANONICAL_SPEC_V1.md`
- `docs&#47;governance&#47;ai&#47;AI_UNKNOWN_REDUCTION_V1.md`
- `docs&#47;governance&#47;ai&#47;CRITIC_PROPOSER_BOUNDARY_SPEC_V1.md`
- `out&#47;ops&#47;peak_trade_truth_model_*`
- `out&#47;ops&#47;ai_layer_model_matrix_v1_*`
