---
title: "PR-CD AWS Export Write-Smoke CI Authority Boundary"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-24"
docs_token: "DOCS_TOKEN_PRCD_AWS_EXPORT_WRITE_SMOKE_CI_AUTHORITY_BOUNDARY_V1"
---

# PR-CD AWS Export Write-Smoke CI Authority Boundary

## 1) Purpose

This runbook defines the authority boundary for the PR-CD AWS export write-smoke workflow.

The workflow is an export and remote-storage smoke support surface. It is not an evidence approval authority, not an external signoff authority, not a release authority, not a Master V2 decision authority, not a Double Play authority, and not a live enablement mechanism.

## 2) Workflow Surface

Canonical workflow path:

- `.github/workflows/prcd-aws-export-write-smoke.yml`

This runbook describes the authority boundary of that workflow. It does not change the workflow, does not approve any workflow run, and does not assert that any export target, artifact, or remote object is valid evidence.

## 3) Dispatch Boundary

The workflow is a manually invoked export write-smoke surface.

A manual dispatch is only an invocation mechanism. It must not be interpreted as:

- release approval
- evidence approval
- external signoff
- live readiness
- bounded-live readiness
- first-live readiness
- Master V2 approval
- Double Play approval
- operator approval
- promotion approval

A successful dispatch only means the configured workflow path ran to its reported conclusion.

## 4) Write-Smoke Boundary

Terms such as `YES_WRITE_SMOKE` and `PT_EXPORT_SMOKE_WRITE_ENABLED` must be read as export-smoke controls in this workflow context.

They are not:

- permission to publish canonical evidence
- permission to approve evidence
- permission to approve release artifacts
- permission to authorize live trading
- permission to authorize bounded live
- permission to authorize first live
- permission to promote a candidate
- permission to bypass review or signoff

Write-smoke behavior is operational verification of an export path. It is not a governance decision.

## 5) Secret and Remote-Storage Boundary

The workflow can depend on repository secrets, variables, or remote-storage tooling.

Secret availability, remote connectivity, rclone behavior, write behavior, or delete-smoke behavior must not be treated as external signoff.

External storage output is an artifact location or transport result unless a separate evidence contract or signoff process explicitly gives it another role.

## 6) Artifact Boundary

The workflow may produce local status reports, uploaded artifacts, or remote-storage objects.

Those outputs are provenance and diagnostics.

They do not prove:

- evidence validity
- artifact completeness
- release readiness
- live readiness
- bounded-live readiness
- first-live readiness
- Master V2 readiness
- Double Play readiness
- external approval
- successful paper, shadow, testnet, or live behavior

Any evidence claim requires the applicable evidence contract, registry pointer, validation command, artifact retrieval, or governance process.

## 7) Master V2 / Double Play Boundary

PR-CD export write-smoke must not be treated as a Master V2 or Double Play decision surface.

It cannot approve a decision packet, validate a handoff, override a veto, approve a specialist, approve leverage, promote a strategy, or authorize live behavior.

If future work proposes remote export outputs as inputs to Master V2, Double Play, or first-live governance, that requires a separate adapt-to-Master-V2 design and review. This runbook does not provide that design.

## 8) Safe Operator Reading

Safe reading:

- "This workflow can manually test export write behavior under configured controls."
- "Remote-storage output is transport or provenance until separately validated."
- "Write-smoke success can support later review."

Unsafe reading:

- "The workflow succeeded, so evidence is approved."
- "The remote object is external signoff."
- "`YES_WRITE_SMOKE` means release approval."
- "`PT_EXPORT_SMOKE_WRITE_ENABLED` means live or first-live readiness."
- "Export success can substitute for Master V2, Double Play, or evidence governance."

## 9) Change Discipline

Any future change that expands export behavior, write behavior, secrets usage, remote targets, artifact naming, or integration with evidence or release systems requires explicit review.

Examples requiring review include:

- new write targets
- new secrets or privileged tokens
- new remote storage paths
- broader delete behavior
- new generated files that appear authoritative
- changes that make export output look like evidence approval
- integrations with Master V2, Double Play, readiness, release, or live workflows

## 10) Validation

For documentation-only changes to this runbook, run from the repository root:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

If `uv` is not available, use the project's documented Python environment to execute the same scripts.
