---
docs_token: DOCS_TOKEN_MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_REPORT_IMPLEMENTATION_PLAN_V0
status: draft
scope: docs-only, non-authorizing source-bound Session Review Pack report implementation plan
last_updated: 2026-04-27
---

# Master V2 Session Review Pack Source-Bound Report Implementation Plan V0

## 1. Executive Summary

This document defines the implementation plan for a future source-bound Session Review Pack report mode.

It is docs-only and non-authorizing. It does not implement parser flags, report behavior, source binding, registry reads against production trees, artifact reads against production `out&#47;ops`, closeout mutation, live authorization, strategy readiness, autonomy readiness, or external authority.

The intended future mode remains separate from static SRP V0 and must require explicit operator-selected source identity. Phases below order **tests and isolation before** any behavior that touches real registry JSON, real evidence indexes, or real session artifacts.

## 2. Purpose and Non-Goals

Purpose:

- define the implementation phases before source-bound SRP report code ships;
- protect static SRP V0 from silent behavior changes;
- preserve explicit `session_id` source selection (no automatic primacy);
- require temp-fixture and synthetic resolver coverage before any real-source behavior;
- preserve Registry / Evidence pointer semantics from the linkage plan;
- keep outputs explicitly non-authorizing where authority fields exist in shared shapes.

Non-goals:

- No code changes from this document alone.
- No parser implementation from this document alone.
- No report implementation from this document alone.
- No registry JSON edits for convenience.
- No `out&#47;ops` edits or normalization of generated artifacts.
- No real session binding in tests except behind explicit future acceptance criteria not defined here.
- No closeout mutation, live, paper, testnet, or bounded-pilot execution driven by this plan.

## 3. Prerequisites Already in Place

This plan builds on:

- [Source-Bound SRP Mode Implementation Brief](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_MODE_IMPLEMENTATION_BRIEF_V0.md)
- [Source-Bound SRP CLI/API Test Plan](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_CLI_API_TEST_PLAN_V0.md)
- [Source-Bound SRP Registry / Evidence Linkage Plan](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_REGISTRY_EVIDENCE_LINKAGE_PLAN_V0.md)
- [SRP Real-Binding Accepted Decision](./MASTER_V2_SESSION_REVIEW_PACK_REAL_BINDING_ACCEPTED_DECISION_V0.md)
- [Static SRP Contract V0](./MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md)
- [Started Bounded-Pilot Session Review Runbook](../runbooks/RUNBOOK_STARTED_BOUNDED_PILOT_SESSION_REVIEW_V0.md)

Relevant tests (inline escaped paths; not link targets):

- `tests&#47;ops&#47;test_session_review_pack_source_bound_cli_shape_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_source_bound_session_id_shape_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_report_contracts_v0.py`

## 4. Proposed Future Report Mode / Contract

Proposed future contract family (string id; implementation TBD):

`report_live_sessions.session_review_pack_source_bound_v0`

Illustrative future CLI shape (flag names non-final; aligns with the CLI/API test plan):

```bash
uv run python scripts/report_live_sessions.py --session-review-pack-source-bound --session-id <SESSION_ID> --json
```

This contract must remain **distinct** from static `--session-review-pack` (SRP V0). Combination and mutual-exclusion rules follow the implementation brief and existing synthetic tests; implementation must not collapse modes.

## 5. Implementation Phases

Work should land in approximately this order. Each phase should add tests **before** expanding production reads.

| Phase | Deliverable intent | Safety gate |
| --- | --- | --- |
| **1** | Parser / argv validation tests | Fail-closed errors for missing/ambiguous `session_id`, illegal combinations with static SRP V0 flags; **no** filesystem reads of real registry/`out&#47;ops`. |
| **2** | Temp-fixture registry / source resolver tests | Resolver logic exercised against **isolated** `tmp_path` fixtures only; deterministic missing/ambiguous session behavior. |
| **3** | Source-bound payload builder tests | Pure construction of linkage/payload sections consistent with [Registry/Evidence Linkage Plan](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_REGISTRY_EVIDENCE_LINKAGE_PLAN_V0.md); explicit missing/`needs_review` fields preserved. |
| **4** | Report CLI integration tests | End-to-end CLI invocation against **fixtures** or mocks per test plan; still **no** dependency on production registry paths unless explicitly accepted later. |
| **5** | Docs / runbook update | Describe operator-visible invocation, limitations, and human review posture; reference the bounded-pilot runbook; **no** authority claims. |

Skipping phases or merging real reads before phase **2** completes violates this plan’s safety model.

## 6. Strict No-Real-Artifact Rule Until After Temp-Fixture Tests

Until phase **2** is complete and reviewed:

- Do not add code paths that read production registry JSON, production evidence indexes, or production `out&#47;ops` trees as part of automated tests.
- Do not commit registry snapshots from real environments into the repo for test convenience.
- Prefer synthetic argv tests (existing), then `tmp_path` fixtures with minimal fake registry shards constructed in-test.

After phase **2**, any expansion toward real paths requires a **separate** explicitly scoped decision (out of scope for this document).

## 7. Static SRP V0 Protection

- Default/static Session Review Pack behavior remains governed by [SRP Contract V0](./MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md).
- Source-bound mode must not change static SRP V0 output shape, flags, or exit behavior without a version/mode bump.
- Negative combination tests (static + source-bound flags) must continue to fail closed as today’s tests describe.

## 8. Source Selector Behavior

Implementation must preserve:

- explicit `--session-id` (or finalized equivalent) **required** for source-bound mode;
- fail-closed behavior when `session_id` is missing, malformed, ambiguous, or not found in the resolver’s fixture scope;
- no automatic selection of newest, open, or “primary” session without operator intent.

## 9. Registry / Evidence Linkage Behavior

Implementation should mirror pointer classes and missing/present semantics from:

- [Source-Bound SRP Registry / Evidence Linkage Plan](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_REGISTRY_EVIDENCE_LINKAGE_PLAN_V0.md)

Rules:

- Pointers are references and navigation context only; they do not imply gate passage, readiness, or authorization.
- Conflicting or incomplete pointers surface as explicit missing/`needs_review` or fail-closed errors—no silent repair.

## 10. Authority Boundaries

- Session Review Pack outputs remain non-authoritative for live trading, kill-switch posture, execution permission, Double Play readiness, dashboard truth, AI/strategy authority, or external signoff.
- Operator review remains human-led per runbook; automation may prepare artifacts but must not claim completion of authority workflows.

## 11. Validation Plan

Before merge of any future implementation PR touching this mode:

- `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`
- `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`
- focused pytest suites including at minimum:
  - `tests&#47;ops&#47;test_session_review_pack_source_bound_cli_shape_v0.py`
  - `tests&#47;ops&#47;test_session_review_pack_source_bound_session_id_shape_v0.py`
  - `tests&#47;ops&#47;test_session_review_pack_report_contracts_v0.py`
- additional tests added per phases **1–4** must not violate sections **6** and **10**.

## 12. STOP Conditions

Stop implementation work when:

- real registry / `out&#47;ops` reads would be required to proceed without first completing phases **1–2** with fixtures;
- tests would normalize or rewrite historical artifacts;
- static SRP V0 would be altered without an explicit contract/mode decision;
- output would imply live readiness, strategy readiness, autonomous readiness, gate passage, or completed external authority.

When in doubt, remain fail-closed and preserve explicit missing/`needs_review` states.
