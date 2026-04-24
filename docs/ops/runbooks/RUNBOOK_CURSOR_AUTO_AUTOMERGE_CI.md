---
title: "Cursor AutoMerge CI Authority Boundary"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-24"
docs_token: "DOCS_TOKEN_CURSOR_AUTO_AUTOMERGE_CI_AUTHORITY_BOUNDARY_V1"
---

# Cursor AutoMerge CI Authority Boundary

## 1) Purpose

This runbook defines the authority boundary for the Cursor AutoMerge workflow.

The workflow is a merge automation support surface. It is not a trading authority, not a Master V2 decision authority, not an evidence authority, not a gate authority, and not a live enablement mechanism.

## 2) Workflow Surface

Canonical workflow path:

- `.github/workflows/cursor_auto_automerge.yml`

This runbook describes the authority boundary of that workflow. It does not change the workflow, does not approve any workflow run, and does not assert that any specific pull request is safe to merge.

## 3) Automation Boundary

The workflow may automate a squash merge when its configured conditions are met.

Those conditions can include pull request state, labels, draft status, mergeability, check conclusions, and manual dispatch inputs as defined by the workflow file.

Automation eligibility must not be interpreted as product readiness, trading readiness, live readiness, evidence completeness, external signoff, or Master V2 readiness.

## 4) Label Boundary

Labels such as `cursor-auto` and `automerge` are automation inputs.

They are not:

- strategy approval
- live approval
- evidence approval
- risk approval
- Master V2 approval
- Double Play approval
- external signoff
- permission to bypass review discipline

A label can select a merge automation path only within the configured workflow behavior. It does not create new authority outside that workflow.

## 5) Checks Boundary

A check-green condition is a merge automation predicate.

It must not be read as proof that the pull request is semantically correct, live-ready, evidence-complete, safe for trading, or aligned with every governance document.

A green check state can support merge eligibility. It is not a substitute for the scope, review, and authority rules that govern the changed files.

## 6) Merge Boundary

A successful automated merge means the repository accepted a squash merge under the configured workflow conditions.

It does not mean:

- live trading is authorized
- paper, shadow, testnet, or live behavior is proven
- Master V2 promotion has occurred
- Double Play readiness has been approved
- evidence artifacts are complete
- external signoff has been granted
- operator review requirements are removed

For any trading-adjacent change, the relevant runbook, spec, evidence contract, or readiness document remains authoritative.

## 7) Master V2 / Double Play Boundary

Cursor AutoMerge must not be treated as a Master V2 or Double Play decision surface.

It can merge documentation, tests, code, or workflow changes only according to repository rules. It cannot approve a decision packet, authorize a handoff, override a veto, arm a system, or promote a strategy.

If a future process proposes Cursor AutoMerge as part of a Master V2 or Double Play governance path, that requires a separate adapt-to-Master-V2 design and review. This runbook does not provide that design.

## 8) Evidence Boundary

The workflow's merge action is provenance, not evidence.

A merged pull request may point to checks, logs, artifacts, or reviews. Those items must be interpreted under their own contracts.

The merge event itself does not prove:

- successful runtime behavior
- correct live or testnet behavior
- evidence validity
- risk acceptance
- strategy readiness
- operator approval
- external approval

## 9) Safe Operator Reading

Safe reading:

- "This workflow can automate a squash merge under configured repository conditions."
- "Labels and check results are automation predicates."
- "A merge is provenance, not product or live authority."

Unsafe reading:

- "AutoMerge means the change is broadly safe."
- "AutoMerge means the change is live-ready."
- "AutoMerge can substitute for Master V2 or Double Play governance."
- "Labels can authorize trading behavior."
- "Green checks can replace evidence or external signoff."

## 10) Change Discipline

Any future change that expands merge behavior, permissions, label semantics, required predicates, manual dispatch behavior, or check interpretation requires explicit review.

Examples requiring review include:

- new write permissions
- new merge modes
- broader label matching
- weaker check evaluation
- changes to draft handling
- changes to manual dispatch semantics
- integration with evidence, readiness, live, or trading-adjacent systems
- integration with Master V2 or Double Play governance

## 11) Validation

For documentation-only changes to this runbook, run from the repository root:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

If `uv` is not available, use the project's documented Python environment to execute the same scripts.
