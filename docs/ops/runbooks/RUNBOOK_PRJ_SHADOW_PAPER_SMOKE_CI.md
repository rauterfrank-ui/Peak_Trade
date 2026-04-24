---
title: "PR-J Shadow/Paper Features Smoke CI Authority Boundary"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-24"
docs_token: "DOCS_TOKEN_PRJ_SHADOW_PAPER_SMOKE_CI_AUTHORITY_BOUNDARY_V1"
---

# PR-J Shadow/Paper Features Smoke CI Authority Boundary

## 1) Purpose

This runbook defines the authority boundary for the PR-J shadow/paper features smoke workflow.

The workflow is a CI smoke and artifact support surface. It is not a trading authority, not a Master V2 decision authority, not a Double Play decision authority, not an evidence authority, not a live enablement mechanism, and not an arming mechanism.

## 2) Workflow Surface

Canonical workflow path:

- `.github/workflows/prj-scheduled-shadow-paper-features-smoke.yml`

The workflow may run from scheduled automation when repository variables permit it, or from manual dispatch when explicitly invoked.

This runbook describes the authority boundary of that workflow. It does not change the workflow, does not approve any workflow run, and does not assert that any specific smoke result is sufficient for readiness or promotion.

## 3) Trigger Boundary

The workflow's schedule is a CI timing mechanism.

A scheduled run must not be interpreted as:

- readiness approval
- promotion approval
- live approval
- testnet approval
- strategy approval
- Double Play approval
- Master V2 approval
- operator arming
- order authority

A manual dispatch is also not approval. It is only an invocation path for the configured smoke workflow.

## 4) Variable and Input Boundary

The workflow can map repository variables or dispatch inputs into environment values used by the smoke script.

Names such as `PT_ARMED`, `PT_ENABLED`, and `PT_ALLOW_DOUBLE_PLAY` are CI smoke inputs in this workflow context.

They are not:

- live arming
- order arming
- exchange arming
- operator authorization
- strategy promotion
- Double Play authorization
- Master V2 handoff approval
- evidence approval

Those names must be read only inside the workflow's smoke-test boundary unless another explicitly reviewed governance artifact says otherwise.

## 5) Double Play Boundary

The workflow can exercise Double Play adjacent configuration or feature-smoke paths.

That does not make the workflow a Double Play decision surface.

The workflow must not be used to decide:

- which specialist is active
- whether a strategy is selected for live or testnet use
- whether leverage is allowed
- whether a candidate is ready for promotion
- whether a Master V2 handoff is valid

Any future connection between this smoke workflow and Double Play decisions requires a separate adapt-to-Master-V2 design and review.

## 6) Shadow / Paper Boundary

Shadow and paper references in this workflow are smoke and artifact context.

They do not imply:

- live trading
- exchange order authority
- real-money approval
- successful execution
- readiness for promotion
- readiness for first live
- readiness for bounded live
- readiness for Double Play

Paper or shadow smoke output can support later review. It is not review by itself.

## 7) Artifact Boundary

The workflow may upload artifacts from CI-runner paths such as smoke outputs or evidence-pack directories.

Artifact upload is provenance, not evidence approval.

Artifacts from this workflow must not be treated as validated evidence unless they are checked by the applicable evidence contract, registry pointer, validation command, or governance process.

The existence of an uploaded artifact does not prove:

- correctness
- completeness
- readiness
- promotion eligibility
- live safety
- Double Play authority
- Master V2 authority

## 8) Safe Operator Reading

Safe reading:

- "This workflow can run a scheduled or manually dispatched shadow/paper feature smoke."
- "`PT_ARMED`, `PT_ENABLED`, and `PT_ALLOW_DOUBLE_PLAY` are CI-smoke inputs in this workflow context."
- "Uploaded artifacts are provenance and may support later review."

Unsafe reading:

- "The scheduled run means the system is ready."
- "`PT_ARMED` means live arming."
- "`PT_ALLOW_DOUBLE_PLAY` means Double Play is approved."
- "A green smoke result is promotion approval."
- "Artifacts from this workflow are validated evidence without separate checks."
- "This workflow can substitute for Master V2 readiness."

## 9) Change Discipline

Any future change that expands this workflow's authority surface requires explicit review.

Examples requiring review include:

- new write permissions
- new secrets or privileged tokens
- new live, testnet, paper, or shadow side effects
- new arming-like input names
- changed schedule behavior
- changed repository variable gates
- new generated artifacts that appear authoritative
- new integration with Master V2, Double Play, promotion, readiness, or evidence validation

## 10) Validation

For documentation-only changes to this runbook, run from the repository root:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

If `uv` is not available, use the project's documented Python environment to execute the same scripts.
