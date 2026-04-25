---
title: "PR-J Shadow/Paper Features Smoke CI Authority Boundary"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-25"
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

## 8) Real market data evidence (read-only interpretation)

This workflow can produce or surface smoke, CI, P5B evidence-pack, paper, or shadow artifacts. **Integrity and CI success** (for example, completed runs, file presence, or P5B hash checks) are **not** the same thing as **real market data provenance**. Treat those concepts separately.

Legitimate **fixture, mock, dry-run, synthetic, or offline** context can appear in smoke and CI. That is expected for repeatability. It does **not**, by itself, establish that any uploaded object reflects live exchange market data, or that it should be read as "real market evidence" without explicit metadata in the **artifact** you are reviewing.

**Orientation (code, not a gate here):** For trading data paths, the repository models explicit source usage via `DataSafetyGate` / `DataSafetyContext` and `DataSourceKind` values such as `real`, `historical`, and `synthetic_offline_rt` in `src/data/safety/data_safety_gate.py`. This runbook does not invoke that gate. Use it only as a vocabulary and design pointer when you need to reason about *declared* source semantics elsewhere—not as proof that a given CI artifact used live exchange feeds.

**S3 and evidence storage:** Inspect objects or registry pointers **read-only** when your process allows. Do not dump credentials, do not run write operations, and do not start production pipelines or live flows from this runbook. This document is a navigation and interpretation aid, not a signoff, gate, or live enablement.

**Warning signs** that an output may **not** be real-market evidence on its own (non-exhaustive):

- paths under `tests/fixtures/`, or other repository fixture files named as inputs
- flags or labels such as `--dry-run`, or environment smoke inputs (for example `PT_DRY_RUN`) when present
- `mock` / `fake` / `synthetic` / `sample` / `demo` / `offline` in paths, scripts, or logs
- missing **provider** / **source_kind** / **data_source** / **fetched_at** / **symbol** / **timeframe** (or similar) fields **when** the artifact class you are using is supposed to carry them, and the absence is unexplained

If provenance is unclear, **do not** count the object as real-market evidence. That is conservative interpretation, not a claim that any specific artifact in storage is wrong.

**Read-only operator checklist**

1. Read artifact and manifest **metadata** (if present) before drawing conclusions.
2. Check **source** fields such as `provider`, `source_kind` / `DataSourceKind`, and `data_source` **when** the artifact or report schema includes them.
3. Check for **mock**, **fixture**, **dry-run**, and **synthetic** flags and file paths in workflow logs, script arguments, and output paths.
4. Use **S3** or **registry** references only in **read-only** ways permitted by your environment; do not expose secrets in tickets or runbooks.
5. Never print or share **secrets** to prove a point; use redaction and separate secure channels.
6. If you cannot establish real-market provenance to your standard, **treat the material as not established** for that purpose. Escalation belongs under your governance, not as an implicit approval from this workflow.

## 9) Safe Operator Reading

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
- "CI or P5B integrity (for example, matching hashes) means the data is real exchange market evidence."

## 10) Change Discipline

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

## 11) Validation

For documentation-only changes to this runbook, run from the repository root:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

If `uv` is not available, use the project's documented Python environment to execute the same scripts.
