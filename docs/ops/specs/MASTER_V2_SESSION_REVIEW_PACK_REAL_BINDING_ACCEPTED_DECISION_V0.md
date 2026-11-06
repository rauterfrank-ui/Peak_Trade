---
docs_token: DOCS_TOKEN_MASTER_V2_SESSION_REVIEW_PACK_REAL_BINDING_ACCEPTED_DECISION_V0
status: draft
scope: docs-only, non-authorizing Session Review Pack real-binding accepted decision
last_updated: 2026-04-27
---

# Master V2 Session Review Pack Real-Binding Accepted Decision V0

## 1. Executive Summary

This note records the accepted B1/B2 posture for future Session Review Pack real binding.

Accepted decision:

- **B1-A:** Session Review Pack V0 remains static/template-like.
- Future source-bound SRP behavior must use a new version, mode, or contract rather than implicitly changing SRP V0.
- **B2-E / B2-A:** There is no automatic primacy among started/open sessions. A future source-bound SRP requires explicit operator-selected source input, for example a future `--session-id` style selector.

This note is docs-only and non-authorizing. It does not implement source binding, edit registry JSONs, edit `out&#47;ops` artifacts, close sessions, infer PnL, grant live authorization, pass gates, establish strategy readiness, establish autonomy readiness, or complete external authority.

## 2. Decision Context

This accepted posture follows the decision requirements recorded in:

- [SRP Real-Binding Decision Note](./MASTER_V2_SESSION_REVIEW_PACK_REAL_BINDING_DECISION_NOTE_V0.md)
- [SRP Contract V0](./MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md)
- [SRP Started / Open Session Linkage Plan](./MASTER_V2_SESSION_REVIEW_PACK_STARTED_OPEN_SESSION_LINKAGE_PLAN_V0.md)
- [SRP Evidence / Provenance Precedence](./MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md)
- [Started Bounded-Pilot Session Review Runbook](../runbooks/RUNBOOK_STARTED_BOUNDED_PILOT_SESSION_REVIEW_V0.md)
- [Operator / Audit Flat Path Index](./MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md)

Relevant tests remain:

- `tests&#47;ops&#47;test_session_review_pack_report_contracts_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_precedence_synthetic_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_started_open_linkage_synthetic_v0.py`
- `tests&#47;ops&#47;test_report_live_sessions_started_bounded_pilot_open_sessions_v0.py`

## 3. Accepted B1 Decision — Preserve SRP V0 Static Form

Accepted B1 posture:

| Decision | Accepted posture |
|---|---|
| B1 | Keep SRP V0 static/template-like. |
| Source-bound behavior | Must use a new version, mode, or contract. |
| Existing `--session-review-pack` V0 | Must not be silently changed into a real-source binding mode. |
| Contract compatibility | Existing V0 tests and missing-field behavior remain protected. |

Rationale:

- SRP V0 is already pinned as a conservative read-only contract.
- Extending V0 with real binding risks changing semantics under an existing surface.
- A new source-bound mode/version makes authority, source selection, and missing-field behavior explicit.

## 4. Accepted B2 Decision — Explicit Operator Source Selection

Accepted B2 posture:

| Decision | Accepted posture |
|---|---|
| B2 | No automatic primacy among started/open sessions. |
| Required source selection | Explicit operator-selected source, such as future `--session-id`. |
| Newest session auto-pick | Not accepted. |
| Latest open-report primary auto-pick | Not accepted without a later explicit decision. |
| Bind all open sessions by default | Not accepted. |

Rationale:

- Multiple started/open sessions may exist.
- Some sessions may have scoped execution events and others may not.
- Automatic primacy could bind the wrong stale/rejected/incomplete session.
- Operator-selected source preserves review clarity and avoids false authority.

## 5. What This Allows Next

This accepted decision allows only bounded follow-up work:

1. tests-only CLI/API-shape fixtures for a future source-bound SRP mode;
2. docs-only implementation brief for a new source-bound SRP contract;
3. synthetic fixture expansion for explicit `session_id` selection;
4. later report implementation only after the new source-bound contract and tests are agreed.

This decision does not authorize immediate report-code binding.

## 6. What This Blocks

This decision blocks:

- implicit extension of SRP V0 into real binding;
- automatic newest/open-session source selection;
- binding all open sessions by default;
- direct source-bound report implementation without a new contract/mode decision;
- artifact mutation during binding;
- closeout mutation from SRP;
- PnL or live-readiness inference from event-pointer presence.

## 7. Source-Bound SRP Preconditions

Before code implementation, the next source-bound SRP slice must define:

| Required item | Minimum expectation |
|---|---|
| Contract name | Distinct from static SRP V0. |
| CLI/API shape | Explicit operator source selector. |
| Source selector | Future `--session-id` or equivalent. |
| Missing events | Preserved as explicit missing/needs-review fields. |
| Authority flags | All false/non-authorizing by default. |
| Real artifacts | Not mutated. |
| Tests | Synthetic fixtures before real-source use. |

## 8. Authority Boundaries

| Surface | May do | Must not do |
|---|---|---|
| Static SRP V0 | Provide template-like review structure. | Bind real sessions. |
| Future source-bound SRP | Present explicitly selected source references. | Authorize trades. |
| Operator source selection | Choose a review source. | Close sessions or approve live. |
| Event-pointer presence | Signal reference availability. | Prove PnL or correctness. |
| Missing event pointer | Preserve review gap. | Authorize artifact repair. |
| Synthetic tests | Pin mapping/CLI semantics. | Read real registry or `out&#47;ops` data. |

## 9. STOP / Rollback Posture

STOP remains correct if any of these are not yet specified:

- source-bound contract name;
- explicit selector shape;
- selector validation behavior;
- missing-event handling;
- whether non-terminal sessions may be bound for review;
- authority boundary tests.

Rollback posture:

- SRP V0 remains static.
- Existing reports remain read-only.
- Existing registry and `out&#47;ops` artifacts remain untouched.
- No live/testnet/paper execution is implied.

## 10. Validation Notes

Validate this docs-only accepted decision with:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
uv run pytest tests/ops/test_session_review_pack_started_open_linkage_synthetic_v0.py tests/ops/test_report_live_sessions_started_bounded_pilot_open_sessions_v0.py tests/ops/test_session_review_pack_report_contracts_v0.py tests/ops/test_session_review_pack_precedence_synthetic_v0.py -q
```
