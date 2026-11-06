---
title: "InfoStream CI Authority Boundary"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-24"
docs_token: "DOCS_TOKEN_INFOSTREAM_CI_AUTHORITY_BOUNDARY_V1"
---

# InfoStream CI Authority Boundary

## 1) Purpose

This runbook defines the authority boundary for the InfoStream automation workflow.

The workflow is a documentation and automation support surface. It is not a trading authority, not a Master V2 decision authority, not an evidence authority, not a gate authority, and not a live enablement mechanism.

## 2) Workflow Surface

Canonical workflow path:

- `.github/workflows/infostream-automation.yml`

The workflow may run from scheduled automation or manual dispatch, depending on the workflow configuration in the repository.

This runbook describes the authority boundary of that workflow. It does not change the workflow, does not approve the workflow, and does not assert that any specific run has succeeded.

## 3) Write Boundary

The workflow can have repository write behavior when its configured conditions are met.

That write capability is limited to the workflow's documented automation purpose. It must not be interpreted as permission to change trading state, arm trading, enable live execution, promote a candidate, or bypass review.

If the workflow updates documentation, reports, or InfoStream outputs, those outputs remain documentation artifacts until independently reviewed under the relevant governance path.

## 4) Schedule and Manual Dispatch Boundary

A manual dispatch input such as a dry-run toggle only governs the workflow behavior for that dispatch path.

A scheduled run must be interpreted from the workflow file itself. This runbook does not imply that scheduled runs are dry-run-only.

Operators must not infer safety, approval, or live readiness from the existence of a schedule, a successful run, or a generated commit.

## 5) Non-Authority Constraints

The InfoStream workflow must not be treated as any of the following:

- a Master V2 decision packet
- a Double Play authority source
- a live readiness gate
- a first-live enablement gate
- a bounded-live approval
- an external signoff
- an evidence validation source
- an order, arming, or execution control plane
- a substitute for branch protection, required checks, or human review

Any output produced by the workflow is advisory documentation unless another explicitly named governance artifact says otherwise.

## 6) Master V2 / Double Play Boundary

InfoStream content can support operator awareness, review preparation, or future documentation work.

It must not drive Double Play decisions directly. It must not override Master V2 readiness, risk, safety, veto, or handoff rules.

If InfoStream output is ever proposed as an input to a Master V2 or Double Play process, that proposal requires a separate adapt-to-Master-V2 design and review. This runbook does not provide that design.

## 7) Evidence Boundary

Workflow output is not evidence by itself.

A workflow run, generated report, documentation update, or commit may be useful provenance, but it does not prove:

- trading readiness
- live readiness
- strategy readiness
- evidence completeness
- external signoff
- successful paper, shadow, testnet, or live behavior
- correctness of generated content

Evidence claims require the relevant evidence contract, registry pointer, validation command, artifact retrieval, or governance process.

## 8) Safe Operator Reading

Safe reading:

- "The InfoStream workflow may update documentation or reports under configured conditions."
- "Generated content can be reviewed as an input to operator awareness."
- "A successful automation run is provenance, not authority."

Unsafe reading:

- "The workflow can push to main, therefore its output is approved."
- "The workflow ran successfully, therefore the system is live-ready."
- "InfoStream output can promote, arm, or unlock trading."
- "Generated content is evidence without separate validation."

## 9) Change Discipline

Any future change that expands the workflow's write behavior, secrets usage, generated outputs, or integration with trading-adjacent systems requires explicit review.

Examples requiring review include:

- new repository write targets
- new secrets or privileged tokens
- new generated files that appear authoritative
- links to readiness, live, or evidence claims
- integrations with Master V2, Double Play, paper, shadow, testnet, or live systems
- changes that make scheduled runs create broader updates than before

## 10) Validation

For documentation-only changes to this runbook, use the standard docs validation path:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

Run from the repository root. If `uv` is not available, use the project's documented Python environment to execute the same scripts.
