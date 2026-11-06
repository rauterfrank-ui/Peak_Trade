---
docs_token: DOCS_TOKEN_MASTER_V2_SESSION_REVIEW_PACK_REAL_BINDING_DECISION_NOTE_V0
status: draft
scope: docs-only, non-authorizing Session Review Pack real-binding decision note
last_updated: 2026-04-27
---

# Master V2 Session Review Pack Real-Binding Decision Note V0

## 1. Executive Summary

This note records the decisions required before Session Review Pack data can be bound to real started/open bounded-pilot session sources.

The current Session Review Pack V0 remains static/template-like, read-only, and non-authorizing. Real binding is a separate contract/API decision, not a small implicit extension of the current `--session-review-pack` mode.

This note does not implement binding, edit registry JSONs, edit `out&#47;ops` artifacts, close sessions, infer PnL, grant live authorization, pass gates, establish strategy readiness, establish autonomy readiness, or complete external authority.

## 2. Purpose and Non-Goals

Purpose:

- identify the minimum decisions required before real SRP binding;
- prevent accidental coupling between static SRP V0 and started/open session sources;
- preserve missing/present execution-event pointer semantics;
- keep started/open session review separate from closeout and authority;
- define what must be decided before implementation work begins.

Non-goals:

- No code changes.
- No report implementation changes.
- No test changes.
- No workflow/config changes.
- No registry JSON changes.
- No `out&#47;ops` artifact changes.
- No real session binding.
- No manual closeout.
- No PnL or live-readiness inference.
- No live, paper, testnet, or bounded-pilot execution.

## 3. Current SRP V0 Static Posture

Primary anchors:

- [Session Review Pack Contract](./MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md)
- [Session Review Pack Started / Open Session Linkage Plan](./MASTER_V2_SESSION_REVIEW_PACK_STARTED_OPEN_SESSION_LINKAGE_PLAN_V0.md)
- [Session Review Pack Evidence / Provenance Precedence](./MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md)
- [Session Review Pack Invoke Runbook](../runbooks/RUNBOOK_SESSION_REVIEW_PACK_INVOKE_V0.md)

Current behavior:

- `scripts&#47;report_live_sessions.py --session-review-pack --json` emits a static/template-like SRP V0 surface.
- SRP V0 is intentionally read-only and non-authorizing.
- SRP V0 does not bind real registry session records.
- SRP V0 does not bind real `out&#47;ops` artifacts.
- SRP V0 does not choose among multiple started/open sessions.

Existing tests:

- `tests&#47;ops&#47;test_session_review_pack_report_contracts_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_precedence_synthetic_v0.py`
- `tests&#47;ops&#47;test_session_review_pack_started_open_linkage_synthetic_v0.py`

## 4. Observed Started/Open Session Situation

Started/open bounded-pilot session review is covered by:

- [Started Bounded-Pilot Session Review Runbook](../runbooks/RUNBOOK_STARTED_BOUNDED_PILOT_SESSION_REVIEW_V0.md)
- [Operator / Audit Flat Path Index](./MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md)
- [Registry / Evidence Surface Pointer Index](./MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md)

Current review surfaces have shown that started/open registry entries can exist with mixed scoped event-pointer states:

| Observed state | Meaning | Boundary |
| --- | --- | --- |
| started/open registry entry | Non-terminal registry state exists. | Not closeout approval. |
| scoped events present | Expected scoped event file exists. | Not proof of correctness or PnL. |
| scoped events missing | Expected scoped event file is absent. | Not permission to recreate or edit artifacts. |
| multiple started/open entries | There is no single obvious source by default. | Requires primacy decision. |

This note does not enumerate or modify specific historical session files.

## 5. Decision B1 — SRP Version / Form Before Code

Before implementation, decide whether real binding belongs in:

| Option | Meaning | Risk |
| --- | --- | --- |
| Keep SRP V0 static | `--session-review-pack` remains template-like. | Requires a separate future mode for source-bound review. |
| Extend SRP V0 | Add source binding to existing SRP V0. | High risk of changing a pinned contract. |
| Create a new source-bound SRP version | Preserve V0 and add a new contract/version later. | More explicit, safer for review. |

Default recommendation: preserve SRP V0 as static/template-like unless an explicit operator/product decision selects a new source-bound version.

## 6. Decision B2 — Source Selection / Primacy Before Code

Before implementation, decide how a source-bound SRP chooses among started/open sessions.

Possible primacy policies:

| Policy | Meaning | Risk |
| --- | --- | --- |
| newest started/open session | Choose newest non-terminal session. | May select a stale or rejected session. |
| explicit `--session-id` | Operator chooses the session. | Requires CLI/API design and validation. |
| latest bounded-pilot open report primary | Reuse existing report primary. | Must preserve report semantics. |
| all open sessions | SRP becomes a bundle/list. | Larger contract change. |
| no automatic primacy | Stop until operator selects a source. | Safest default. |

Default recommendation: no automatic primacy. Use explicit operator selection or a separate source-bound contract decision before binding real sessions.

## 7. Additional Required Decisions

| Decision | Question | Default until decided |
| --- | --- | --- |
| B3 missing events | Is `present=false` a blocker or a missing-field review signal? | Treat as explicit missing/needs-review. |
| B4 open session binding | May non-terminal `started` sessions be bound before closeout? | Treat as review-only; no closeout or authority. |
| B5 artifact scope | Which artifact classes may appear in source-bound SRP? | Registry + scoped events only until expanded. |
| B6 CLI shape | Is binding a new flag, new mode, or new version? | Do not overload existing static V0 implicitly. |

## 8. Preconditions Before Implementation

Implementation should not begin until these are true:

1. B1 is resolved: static V0 vs. new source-bound version.
2. B2 is resolved: explicit source selection / primacy.
3. Missing event-pointer semantics are retained.
4. Authority flags remain false/non-authorizing.
5. Tests use synthetic fixtures before real binding.
6. Historical registry and `out&#47;ops` artifacts remain immutable.
7. Operator review language remains separate from closeout approval and live authorization.

## 9. Authority Boundaries

| Surface | May do | Must not do |
| --- | --- | --- |
| Static SRP V0 | Provide template-like review shape. | Bind real sessions implicitly. |
| Future source-bound SRP | Present selected source references if authorized by contract. | Grant live authorization. |
| Registry session record | Provide session metadata. | Prove PnL or correctness. |
| Scoped events pointer | Indicate present/missing state. | Authorize artifact edits. |
| Closeout summary | Explain closeout posture. | Approve closeout. |
| Lifecycle consistency | Explain lifecycle posture. | Pass gates. |
| Operator decision | Select a source or defer. | Bypass Master V2 / Risk / Execution gates. |

## 10. Recommended Next Safe Step

The next safe step after this note is **not** direct report-code binding.

Recommended sequence:

1. Decide B1 and B2 explicitly.
2. If B1/B2 are resolved, create an implementation brief for a source-bound SRP contract or mode.
3. Add tests-only synthetic fixtures for the selected CLI/API shape.
4. Only then consider report implementation.

Until B1/B2 are resolved, STOP is valid.

## 11. STOP Alternative

Stop if any of these are unresolved:

- whether SRP V0 remains static;
- whether a new source-bound SRP version is required;
- how to select among multiple started/open sessions;
- whether `present=false` is a blocker or a review signal;
- whether non-terminal started sessions may be bound before closeout.

STOP here does not discard the work. It preserves a safe boundary before real-session binding.

## 12. Validation Notes

Validate this docs-only note with:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
uv run pytest tests/ops/test_session_review_pack_started_open_linkage_synthetic_v0.py tests/ops/test_report_live_sessions_started_bounded_pilot_open_sessions_v0.py tests/ops/test_session_review_pack_report_contracts_v0.py tests/ops/test_session_review_pack_precedence_synthetic_v0.py -q
```
