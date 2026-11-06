---
docs_token: DOCS_TOKEN_MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_CLI_API_TEST_PLAN_V0
status: draft
scope: docs-only, non-authorizing source-bound Session Review Pack CLI/API test plan
last_updated: 2026-04-27
---

# Master V2 Session Review Pack Source-Bound CLI/API Test Plan V0

## 1. Executive Summary

This document defines the test plan for a future source-bound Session Review Pack CLI/API surface.

It is docs-only and non-authorizing. It does not implement parser flags, report behavior, registry binding, artifact reads, closeout, live authorization, strategy readiness, autonomy readiness, or external authority.

The proposed future surface remains **illustrative** (final names TBD); the working example is:

```bash
uv run python scripts/report_live_sessions.py --session-review-pack-source-bound --session-id <SESSION_ID> --json
```

Existing **synthetic** coverage in `tests&#47;ops&#47;test_session_review_pack_source_bound_session_id_shape_v0.py` models JSON shape and selector errors. This test plan describes what **future** CLI-level and **future** integration tests should assert once implementation exists—**after** this plan and the [source-bound implementation brief](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_MODE_IMPLEMENTATION_BRIEF_V0.md) are accepted.

## 2. Purpose and Non-Goals

Purpose:

- enumerate CLI/API scenarios and expected fail-closed outcomes;
- bind test design to [SRP Real-Binding Accepted Decision](./MASTER_V2_SESSION_REVIEW_PACK_REAL_BINDING_ACCEPTED_DECISION_V0.md) and the implementation brief;
- separate static SRP V0 from source-bound mode in test cases;
- specify fixture boundaries (isolated temp inputs only).

Non-goals:

- No code or parser changes from this document alone.
- No edits to real registry JSONs, `out&#47;ops` trees, or production report outputs.
- No live/testnet/paper execution, PnL inference, or authority claims in fixtures.

## 3. Relationship to Implementation Brief and Accepted Decision

| Anchor | Role in this test plan |
| --- | --- |
| [Source-Bound Mode Implementation Brief](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_MODE_IMPLEMENTATION_BRIEF_V0.md) | Contract id, fail-closed table, mapping intent. |
| [Real-Binding Accepted Decision](./MASTER_V2_SESSION_REVIEW_PACK_REAL_BINDING_ACCEPTED_DECISION_V0.md) | B1-A (V0 static); B2-E/A (no auto primacy; explicit source). |
| [SRP Contract V0](./MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md) | Baseline for static `--session-review-pack` behavior in negative combination tests. |
| [Started/Open Linkage Plan](./MASTER_V2_SESSION_REVIEW_PACK_STARTED_OPEN_SESSION_LINKAGE_PLAN_V0.md) | Context for session lists; tests must not auto-pick. |
| [Evidence / Provenance Precedence](./MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md) | Expected pointer/review_state language for event JSONL references. |

Relevant existing tests (escaped inline paths):

- `tests&#47;ops&#47;test_session_review_pack_source_bound_session_id_shape_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_started_open_linkage_synthetic_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_report_contracts_v0.py`

## 4. Proposed Future CLI / API Shape

Illustrative invocation (non-final flag spelling):

```bash
uv run python scripts/report_live_sessions.py --session-review-pack-source-bound --session-id <SESSION_ID> --json
```

Expectations for **future** tests against a real parser (not yet implemented):

- `--session-review-pack-source-bound` opts into `report_live_sessions.session_review_pack_source_bound_v0` output path.
- `--session-id` is **required** when source-bound is requested; omission or blank must fail closed.
- Static `--session-review-pack` (V0 template) must **not** be combined with source-bound in a way that silently merges contracts; conflicting combination should error or reject with explicit, non-authorizing message.

## 5. Test Scenarios

| # | Scenario | Minimum expectation (future implementation) |
| --- | --- | --- |
| 1 | Missing `--session-id` with source-bound enabled | Non-zero exit or structured error; `explicit_session_id_required`-class error; no session auto-selected. |
| 2 | Blank `--session-id` (after trim) | Same as missing selector; fail closed. |
| 3 | Session id not found in registry/view | `selected_session_id_not_found_or_not_unique`-class; no partial bind. |
| 4 | Duplicate session id / ambiguous source (multiple rows same id) | Fail closed; not unique. |
| 5 | Selected session; execution events **present** | Output includes reference with `review_state: reference_candidate` (or equivalent); authority false. |
| 6 | Selected session; execution events **missing** | `needs_review` / explicit `missing_fields`; authority false. |
| 7 | Unknown / unresolved event pointer state | `present: null`, `review_state: missing`, `missing_fields` includes present-bit; no authority. |
| 8 | Invalid combination with static `--session-review-pack` (V0) | Reject or explicit error; must not emit mixed contract as if single mode. |
| 9 | Multiple open/started sessions exist; source-bound without auto path | No implicit newest/open-session selection; operator must pass `--session-id`. |
| 10 | Non-authorizing output | All authority flags false; no signoff/live/gate-ready strings in JSON (align with shape tests). |

## 6. Expected Fail-Closed Behavior

- Any selector or registry ambiguity → **no** successful “bound” pack; JSON or stderr must state error class; exit non-zero where CLI convention requires.
- No repair of registry; no defaulting to “first” or “newest” session.
- Output must remain `non_authorizing` for all cases in this plan.

## 7. Fixture Strategy (Future Integration Tests)

When implementation adds integration tests (out of scope for this doc’s approval alone):

- Use **temporary** registry-like JSON and **temporary** scoped execution-events paths **only** under test harness directories (e.g. `tmp_path` / fixture dirs), never real `reports&#47;...` production trees or `out&#47;ops` in unit tests.
- Prefer **copy** minimal schema fragments from contracts rather than mutating repo registries.
- Keep synthetic shape tests as the fast, hermetic baseline; integration tests validate wiring only after parser exists.

## 8. Out of Scope

- Implementing `argparse` or report module changes.
- Reading or writing real operator registries or historical run artifacts.
- WebUI/dashboard routes, paper/live execution, broker calls.
- Performance or load testing.

## 9. Validation Notes

Until a source-bound CLI exists, **regression** is limited to existing tests:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
uv run pytest \
  tests/ops/test_session_review_pack_source_bound_session_id_shape_v0.py \
  tests/ops/test_session_review_pack_started_open_linkage_synthetic_v0.py \
  tests/ops/test_session_review_pack_report_contracts_v0.py -q
```

After implementation, add targeted CLI/parser tests and integration tests that reference this plan by name.
