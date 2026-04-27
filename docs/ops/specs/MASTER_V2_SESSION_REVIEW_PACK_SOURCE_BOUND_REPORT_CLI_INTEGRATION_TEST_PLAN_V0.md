---
docs_token: DOCS_TOKEN_MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_REPORT_CLI_INTEGRATION_TEST_PLAN_V0
status: draft
scope: docs-only, non-authorizing source-bound Session Review Pack report CLI integration test plan
last_updated: 2026-04-27
---

# Master V2 Session Review Pack Source-Bound Report CLI Integration Test Plan V0

## 1. Executive Summary

This document defines the integration test plan for a future source-bound Session Review Pack report CLI mode.

It is docs-only and non-authorizing. It does not implement parser flags, report behavior, source binding, registry reads against production trees, artifact reads against production `out&#47;ops`, closeout mutation, live authorization, strategy readiness, autonomy readiness, or external authority.

The purpose is to define how a later implementation should be tested with temporary fixtures before any real registry or artifact source is used.

## 2. Purpose and Non-Goals

Purpose:

- define report-level CLI integration tests before implementation;
- protect static SRP V0 from source-bound behavior changes;
- require explicit `--session-id` source selection for source-bound mode;
- verify parser, resolver, and payload builder expectations together at the CLI boundary once implemented;
- preserve missing/present event-pointer semantics;
- keep output non-authorizing.

Non-goals:

- No report implementation.
- No CLI/parser implementation from this document alone.
- No production code changes from this document alone.
- No registry JSON edits.
- No `out&#47;ops` edits.
- No generated artifact normalization.
- No real session binding.
- No closeout mutation.
- No live, paper, testnet, or bounded-pilot execution.

## 3. Relationship to Existing Plans and Tests

This plan builds on:

- [Source-Bound SRP Report Implementation Plan](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_REPORT_IMPLEMENTATION_PLAN_V0.md)
- [Source-Bound SRP CLI/API Test Plan](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_CLI_API_TEST_PLAN_V0.md)
- [Source-Bound SRP Mode Implementation Brief](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_MODE_IMPLEMENTATION_BRIEF_V0.md)
- [Source-Bound SRP Registry / Evidence Linkage Plan](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_REGISTRY_EVIDENCE_LINKAGE_PLAN_V0.md)
- [Static SRP Contract V0](./MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md)

Current synthetic tests (inline escaped paths; not link targets):

- `tests&#47;ops&#47;test_session_review_pack_source_bound_cli_shape_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_source_bound_temp_resolver_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_source_bound_payload_builder_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_report_contracts_v0.py`

Additional coverage for session selector JSON shape (cross-reference only):

- `tests&#47;ops&#47;test_session_review_pack_source_bound_session_id_shape_v0.py`

## 4. Planned Integration Test Phases

| Phase | Test goal | Required fixture boundary |
| --- | --- | --- |
| 1. CLI argument integration | Future flags are parsed and validated end-to-end at the CLI boundary. | Synthetic argv or isolated subprocess harness against fixtures only. |
| 2. Temp registry resolution | Selected `--session-id` resolves exactly one temp registry record. | Temp directory only (`tmp_path`). |
| 3. Temp event pointer resolution | Scoped temp execution-events path present/missing state is preserved. | Temp directory only. |
| 4. Payload construction | Source-bound payload has distinct contract id and explicit missing/`needs_review` fields. | Synthetic resolver output or temp resolver fixtures only. |
| 5. Static SRP compatibility | Static `--session-review-pack` remains unchanged by source-bound mode. | Existing static SRP tests + negative combinations per brief. |
| 6. Non-authority assertions | Output never implies approval, readiness, gate passage, or external authority. | Serialized JSON inspection (fixtures). |

Phases **1–4** align with implementation phases in the report implementation plan; this document specifies **integration-level** expectations across those layers without prescribing production module layout.

## 5. Command Shapes to Test

Illustrative future commands (flag spelling non-final; see CLI/API test plan):

Source-bound Session Review Pack:

```bash
uv run python scripts/report_live_sessions.py --session-review-pack-source-bound --session-id <SESSION_ID> --json
```

Static Session Review Pack baseline (must remain independently valid):

```bash
uv run python scripts/report_live_sessions.py --session-review-pack --json --log-level ERROR
```

Integration tests should eventually cover:

- successful invocation shape when fixtures supply a unique session and optional temp events file;
- fail-closed exits when `session_id` is missing, malformed, or non-unique relative to temp registry shards;
- JSON exit shape consistency with contracts referenced in the implementation brief.

## 6. Temp Fixture Strategy

- Use **`tmp_path`** (or equivalent isolated directories) for registry shards and scoped execution-events files **only**.
- Do not point tests at repository-tracked registry JSON or production `out&#47;ops` trees unless a separate, explicitly scoped decision exists outside this document.
- Prefer composing tests from existing synthetic helpers/patterns (`cli_shape`, temp resolver, payload builder tests) before introducing parallel abstractions.
- Keep fixtures **minimal**: one session id per happy path; duplicate/missing/malformed cases as separate tests.

## 7. Static / Source-Bound Mutual Exclusion

- Static `--session-review-pack` and source-bound `--session-review-pack-source-bound` must remain **mutually exclusive** combinations where required by the implementation brief.
- Negative combination tests must fail closed without emitting a merged mode or silently upgrading static SRP V0 output.
- Integration tests must assert distinct contract identifiers for static vs source-bound outputs when both modes are exercised in separate cases.

## 8. Source Selection Behavior

- Source-bound integration tests must require **explicit** `--session-id` (or finalized equivalent).
- Fail-closed when selection is missing, empty, ambiguous in fixture scope, or does not resolve exactly one registry record.
- No automatic newest/open-session primacy.

## 9. Resolver / Payload Integration Expectations

- Resolver output feeds payload construction consistent with [Registry / Evidence Linkage Plan](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_REGISTRY_EVIDENCE_LINKAGE_PLAN_V0.md): pointer semantics, explicit missing fields, no silent repair.
- Integration tests should verify **propagation**: resolver `missing_fields` and execution-events `present`/`review_state` surface in CLI JSON output once implemented—not just intermediate dict equality in isolation tests.

## 10. Non-Authority Assertions

Future integration JSON must remain consistent with non-authorizing posture:

- authority/truth/readiness-style flags remain **false** or explicitly missing where applicable;
- no strings implying live authorization, completed closeout approval, gate passage as fact, strategy readiness, autonomy readiness, or external authority completion.

Serialized-output substring guards may complement structured assertions (pattern established in synthetic tests).

## 11. No-Real-Artifact Rule

Until an explicit future acceptance expands scope:

- integration tests must not **read** production registry entries, production evidence indexes, or production `out&#47;ops` artifacts as prerequisites for pass/fail;
- no rewriting or normalizing historical generated artifacts inside tests.

## 12. Out-of-Scope List

- Implementing `report_live_sessions.py` behavior beyond what tests describe as contracts.
- Binding real sessions or validating live/testnet/paper execution outcomes.
- Editing docs outside this planning chain except follow-on runbook/update slices.
- Performance benchmarking, dashboard routing, AI/strategy authority, Double Play readiness claims.

## 13. STOP Conditions

Stop expanding integration test scope when:

- tests would require real registry/`out&#47;ops` reads to proceed;
- static SRP V0 outputs would change without an explicit contract/version decision;
- integration assertions would imply readiness, authorization, or gate passage beyond explicit non-authorizing JSON fields.

## 14. Validation Notes

Before merge of any implementation PR referencing this plan:

- run docs gates on tracked Markdown:
  - `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`
  - `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`
- run focused pytest suites including at minimum:

```bash
uv run pytest \
  tests/ops/test_session_review_pack_source_bound_payload_builder_v0.py \
  tests/ops/test_session_review_pack_source_bound_temp_resolver_v0.py \
  tests/ops/test_session_review_pack_source_bound_cli_shape_v0.py \
  tests/ops/test_session_review_pack_report_contracts_v0.py -q
```

Additional suites such as `test_session_review_pack_source_bound_session_id_shape_v0.py` should remain green when touching CLI/session surface areas.
