---
docs_token: DOCS_TOKEN_MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_MODE_IMPLEMENTATION_BRIEF_V0
status: draft
scope: docs-only, non-authorizing source-bound Session Review Pack mode implementation brief
last_updated: 2026-04-27
---

# Master V2 Session Review Pack Source-Bound Mode Implementation Brief V0

## 1. Executive Summary

This brief defines the required shape for a future source-bound Session Review Pack mode.

It does not implement report code. It does not bind real sessions. It does not mutate registry JSONs, `out&#47;ops` artifacts, generated reports, paper/test data, or historical run artifacts.

The accepted posture is:

- Session Review Pack V0 remains static/template-like.
- Future source-bound behavior must use a new version, mode, or contract.
- Source selection must be explicit, for example a future `--session-id` selector.
- No automatic newest/open-session primacy is allowed by default.

## 2. Purpose and Non-Goals

Purpose:

- define a future source-bound SRP contract/mode boundary;
- preserve the existing static SRP V0 contract;
- require explicit operator source selection;
- describe fail-closed behavior for missing, ambiguous, or invalid source selection;
- define how registry/session and scoped event-pointer source classes may map into SRP-like output;
- specify tests-first implementation order.

Non-goals:

- No report implementation.
- No CLI implementation.
- No registry JSON mutation.
- No `out&#47;ops` artifact mutation.
- No generated artifact normalization.
- No real session binding.
- No closeout action.
- No PnL inference.
- No live/testnet/paper execution.
- No live authorization.
- No strategy readiness or autonomy readiness claim.

## 3. Accepted B1/B2 and Preconditions

This brief depends on the following accepted decisions and planning surfaces:

| Decision | Prerequisite (summary) |
| --- | --- |
| **B1-A** | Static SRP V0 stays template-like; source-bound SRP is a new contract/mode, not a silent extension of V0. |
| **B2-E / B2-A** | No automatic primacy among started/open sessions; an explicit operator-selected source (e.g. future `--session-id`) is required before any notional binding. |

Links:

- [SRP Contract V0](./MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md)
- [SRP Real-Binding Accepted Decision V0](./MASTER_V2_SESSION_REVIEW_PACK_REAL_BINDING_ACCEPTED_DECISION_V0.md)
- [SRP Real-Binding Decision Note V0](./MASTER_V2_SESSION_REVIEW_PACK_REAL_BINDING_DECISION_NOTE_V0.md)
- [SRP Started / Open Session Linkage Plan V0](./MASTER_V2_SESSION_REVIEW_PACK_STARTED_OPEN_SESSION_LINKAGE_PLAN_V0.md)
- [SRP Evidence / Provenance Precedence V0](./MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md)
- [Started Bounded-Pilot Session Review Runbook](../runbooks/RUNBOOK_STARTED_BOUNDED_PILOT_SESSION_REVIEW_V0.md)
- [Registry / Evidence Surface Pointer Index](./MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md)

Relevant tests (inline, escaped paths; not link targets):

- `tests&#47;ops&#47;test_session_review_pack_source_bound_session_id_shape_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_started_open_linkage_synthetic_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_report_contracts_v0.py`

## 4. Proposed Future Contract / Mode

Proposed future contract family (string id):

`report_live_sessions.session_review_pack_source_bound_v0`

This proposed contract is distinct from:

`report_live_sessions.session_review_pack_v0`

The static contract must remain stable. The source-bound contract may be introduced in code only after the tests and contract text are explicitly agreed.

## 5. Proposed Future CLI / API Shape

Future source-bound SRP should require an explicit operator-selected source. Final flag names are not fixed here; the following is an **illustrative** CLI shape (non-binding, not implemented by this brief):

```bash
uv run python scripts/report_live_sessions.py --session-review-pack-source-bound --session-id <SESSION_ID> --json
```

Requirements implied by the shape:

- A dedicated opt-in to the **source-bound** SRP path (separate from static `--session-review-pack` V0), so V0 is not overloaded.
- A mandatory `session_id` (or equivalent explicit selector) when source-bound SRP is requested; omission must **fail closed** (see §6).
- **No** “newest started session”, “default primary from open report”, or bundle-all-open selection unless a **later** explicit decision and contract revision say otherwise.

## 6. Fail-Closed Session Selection

Behavior aligned with the synthetic helper in `test_session_review_pack_source_bound_session_id_shape_v0.py`:

| Condition | Outcome (conceptual) |
| --- | --- |
| Source-bound mode requested without explicit `session_id` | `valid: false`, error e.g. `explicit_session_id_required`, missing e.g. `selection.session_id`. |
| `session_id` does not match exactly one known candidate session (none or duplicate registry rows) | `valid: false`, error e.g. `selected_session_id_not_found_or_not_unique`, fail closed, non-authorizing. |
| More than one open/started session exists in reports but operator gave no `session_id` | Same as first row: no auto-pick. |

Implementation must not invent primacy, repair registry data, or normalize ambiguity into an implicit choice.

## 7. Mapping: Registry Record and Event Pointer to SRP-Like Output

A future implementation should map:

1. **Registry session record** (selected by explicit `session_id`) into a `session` object with `source_class: registry_session_record` (or equivalent) and read-only status fields.
2. **Scoped execution event pointer** (if present) into `references.execution_events_session_jsonl` with `review_state` and `source_class` consistent with provenance rules in [SRP Evidence / Provenance Precedence](./MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md) and pointer classes in [Registry / Evidence Surface Pointer Index](./MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md).

The JSON output should carry `static_contract` pointing at V0 and `contract` pointing at the source-bound id so reviewers see separation of template vs. source-bound view.

## 8. Missing Event Pointer Semantics

- If the pointer is **known false** (no events for session): `present: false`, `review_state: needs_review`, list explicit `missing_fields` (e.g. `references.execution_events_session_jsonl`), authority flags false.
- If the pointer is **known true** (path resolvable in principle): `present: true`, `review_state: reference_candidate` — still not an authority or live claim.
- If presence is **unknown** (unresolved I/O, ambiguous scope): `present: null`, `review_state: missing`, include `references.execution_events_session_jsonl.present` in `missing_fields`.

## 9. Authority Boundaries

- All `authority` / `authority_boundary` fields remain **false**; output remains `non_authorizing: true` at the source-bound pack level.
- No wording may imply signoff, gate pass, live approval, or strategy/autonomy readiness.
- The pack is a **read-model** for triage, not a trading or closeout action surface.

## 10. Tests-First Implementation Sequence

1. Expand or pin synthetic tests for invalid/duplicate `session_id` and error codes before touching production.
2. Add a minimal, flag-gated code path that only assembles the shape using synthetic fixtures; keep **no** real registry/`out&#47;ops` reads in unit tests.
3. Wire real reads only with explicit “real binding” follow-on decision and additional tests.
4. Update operator docs/runbooks when behavior is real, not in this brief alone.

## 11. Out of Scope for This Brief

- Implementing or merging CLI flags in `scripts/report_live_sessions.py`.
- Writing registry migration or backfill.
- WebUI/dashboard binding.
- Paper/live execution or broker interaction.

## 12. STOP Conditions

Stop implementation work if any of the following is undefined or disputed:

- final contract string and schema key names for source-bound SRP;
- exact CLI spelling for the source-bound opt-in and `session_id`;
- behavior when session is **non-terminal** for review;
- required fields for `missing_fields` in edge cases;
- sign-off for reading real `out&#47;ops` in CI or production-like environments.

## 13. Validation Notes

Validate this brief with:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
uv run pytest \
  tests/ops/test_session_review_pack_source_bound_session_id_shape_v0.py \
  tests/ops/test_session_review_pack_started_open_linkage_synthetic_v0.py \
  tests/ops/test_session_review_pack_report_contracts_v0.py -q
```
