---
docs_token: DOCS_TOKEN_RUNBOOK_MASTER_V2_FIRST_LIVE_PILOT_SEQUENCE_V0
status: draft
scope: docs-only, non-authorizing Master V2 First Live pilot sequence runbook
last_updated: 2026-04-28
---

# Runbook: Master V2 First Live Pilot Sequence V0

## 1. Executive Summary

This runbook is an operator-facing, **non-authorizing** sequence for preparing and reviewing a **future** bounded First Live pilot.

It follows the [Master V2 Go-Live Roadmap V0](../specs/MASTER_V2_GO_LIVE_ROADMAP_V0.md) and [Master V2 First Live Execution Sequence V0](../specs/MASTER_V2_FIRST_LIVE_EXECUTION_SEQUENCE_V0.md). It does **not** authorize live trading, enable live configuration, arm live mode, approve bounded-pilot entry, approve closeout, or grant strategy/autonomy readiness.

Every step is fail-closed. If a prerequisite, evidence item, authority decision, preflight, kill criterion, or closeout path is unclear, **STOP**.

## 2. Purpose and Non-Goals

Purpose:

- give operators one bounded-pilot preparation and review sequence aligned to Master V2 docs;
- keep evidence, SRP, gate, readiness, and authority checks visible;
- define a safe **posture** before any bounded pilot (without substituting external or program signoff);
- make kill criteria and STOP explicit;
- separate preparation/review from authorization.

Non-goals:

- No live authorization.
- No live config enablement.
- No order placement instructions that bypass governance in [Bounded Pilot Live Entry](./RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md).
- No dry-run bypass.
- No registry JSON mutation.
- No `out&#47;ops` artifact mutation.
- No session closeout mutation from this runbook alone.
- No strategy readiness claim.
- No autonomy readiness claim.
- No external authority completion claim.

## 3. Relationship to the Go-Live Roadmap and First Live Execution Sequence

**Go-Live Roadmap** ([`MASTER_V2_GO_LIVE_ROADMAP_V0.md`](../specs/MASTER_V2_GO_LIVE_ROADMAP_V0.md)) defines **staged** progression (research through post-pilot promotion). This runbook does **not** advance a stage; it helps operators **prepare and review** work that aligns with stages **6–9** of the roadmap in spirit (bounded pilot preparation through closeout).

**First Live Execution Sequence** ([`MASTER_V2_FIRST_LIVE_EXECUTION_SEQUENCE_V0.md`](../specs/MASTER_V2_FIRST_LIVE_EXECUTION_SEQUENCE_V0.md)) defines an ordered **review and decision** sequence. This runbook maps to execution-sequence steps **6–9** (preparation, preflight, handoff, closeout) as **checklists**, not as automatic progression. If anything here conflicts with the execution sequence or roadmap, **the specs win**.

**Primary anchors:**

- [Go-Live Roadmap](../specs/MASTER_V2_GO_LIVE_ROADMAP_V0.md)
- [First Live Execution Sequence](../specs/MASTER_V2_FIRST_LIVE_EXECUTION_SEQUENCE_V0.md)
- [Readiness Ladder](../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md)
- [Gate Status Index](../specs/MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md)
- [Operator / Audit Flat Path Index](../specs/MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md)
- [Decision Authority Map](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [Promotion State Machine](../specs/MASTER_V2_PROMOTION_STATE_MACHINE_V1.md)
- [Session Review Pack Contract](../specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md)
- [Source-Bound SRP Report Implementation Plan](../specs/MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_REPORT_IMPLEMENTATION_PLAN_V0.md)
- [Bounded Pilot Live Entry Runbook](./RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md)
- [Started Bounded-Pilot Session Review Runbook](./RUNBOOK_STARTED_BOUNDED_PILOT_SESSION_REVIEW_V0.md)

**Relevant focused tests** (characterization only; not live proof):

- `tests/ops/test_session_review_pack_source_bound_cli_shape_v0.py`
- `tests/ops/test_session_review_pack_source_bound_temp_resolver_v0.py`
- `tests/ops/test_session_review_pack_source_bound_payload_builder_v0.py`
- `tests/ops/test_session_review_pack_report_contracts_v0.py`

## 4. Operator Prerequisites

Before using this runbook, confirm:

| Prerequisite | Required posture |
|---|---|
| Repo state | `main`, clean working tree, current with origin. |
| Roadmap | Go-Live roadmap present and understood. |
| Execution sequence | First Live execution sequence present and understood. |
| Readiness surfaces | Ladder / gate status are available for read. |
| SRP surfaces | Static SRP V0 and source-bound planning are understood. |
| Bounded-pilot runbook | [Bounded Pilot Live Entry](./RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) is available for **actual** bounded-pilot mechanics; this runbook does not replace it. |
| Authority owner | External/operator decision owner for Go/No-Go is **known**. |
| STOP owner | Who may STOP or abort is **known** and reachable. |

## 5. Read-Only Preparation Checklist

Run as **read-only** checks when building context (no registry/`out` mutation):

- [ ] `git status` — working tree clean for doc review; note any local-only artifacts without committing operational secrets.
- [ ] Docs and links resolve locally:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

- [ ] Optional SRP characterization (same as roadmap/execution-sequence notes):

```bash
uv run pytest tests/ops/test_session_review_pack_source_bound_cli_shape_v0.py \
  tests/ops/test_session_review_pack_source_bound_temp_resolver_v0.py \
  tests/ops/test_session_review_pack_source_bound_payload_builder_v0.py \
  tests/ops/test_session_review_pack_report_contracts_v0.py -q
```

- [ ] [Gate Status Index](../specs/MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md) — read for **visibility** only; not a pass/fail signoff from this runbook.
- [ ] [Readiness Ladder](../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md) — read for **steering** only.

## 6. Evidence / SRP / Source-Bound Review Checklist

- [ ] Evidence package for the candidate window is **listed**; gaps are **explicit** (not treated as green).
- [ ] If Session Review Pack is used, shape matches [Session Review Pack Contract](../specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md) (static/template posture as documented).
- [ ] Source-bound review (when applicable) requires **explicit** session selection per governance docs — no implicit “newest” or “open” primacy.
- [ ] [Source-Bound SRP Report Implementation Plan](../specs/MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_REPORT_IMPLEMENTATION_PLAN_V0.md) — understood as **planning** surface, not runtime permission.
- [ ] No claim that SRP or review **alone** approves live, closeout, or gate passage.

### Pre-Live package status and bounded-pilot open-session triage (read-only)

These two commands print **read-only JSON** to stdout (use **`--log-level ERROR`** so logs do not mix with the JSON block):

```bash
uv run python scripts/report_live_sessions.py --pre-live-package-status --json --log-level ERROR
uv run python scripts/report_live_sessions.py --bounded-pilot-open-session-triage --json --log-level ERROR
```

**GLB-018 (blocker):** when either payload lists **`GLB-018`** under **`blockers`**, treat it as the **bounded-pilot open-session / non-terminal closeout posture** signal (open bounded-pilot sessions or equivalent gap items per the Pre-Live contract). It is **not** an instruction to change registry or `out/ops` files from the CLI, and it is **not** live authorization.

**Per-session `triage_state` (bounded-pilot open-session triage):**

| Value | Meaning (operator read) |
|---|---|
| `REVIEW_WITH_EVENTS` | Session-scoped execution-events pointer is present; still review under authority (not “green” by itself). |
| `EVIDENCE_POINTER_MISSING` | Session-scoped execution-events pointer is absent; evidence path must be addressed under authority before treating the session as review-complete. |
| `CLOSEOUT_REVIEW_NEEDED` | Registry/closeout posture is non-terminal or otherwise requires explicit closeout/review per policy before narrowing to events-only vs pointer-missing semantics. |

**Hard constraints:** do **not** mutate tracked registry JSON or `out&#47;ops` artifacts from these read-only reports. **`non_authorizing`** remains **true**; all **`authority_boundary`** flags stay **false**. These outputs do **not** grant live authorization, bounded-pilot approval, closeout approval, **or** gate passage.

**STOP** if who may close or defer sessions, wire evidence, or clear blockers under your program is **unclear** — ambiguity defaults to **STOP** (see §11).

## 7. Preflight Checklist

Before any handoff toward bounded pilot **as described in the bounded-pilot runbooks**, complete **their** preflight; this list is a **companion** only:

- [ ] Preflight and readiness scripts referenced in [Bounded Pilot Live Entry](./RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) are identified (read the bounded-pilot runbook for the **authoritative** command surface).
- [ ] Operator preflight packet / stop-snapshot posture in that runbook is understood — **ambiguity → STOP**.
- [ ] Capital, instrument, and session scope for the **bounded** pilot are **written down** (external/program constraints may apply).
- [ ] [Decision Authority Map](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) — who can say Go/No-Go is clear.

**Hard STOP if:** preflight cannot be run as documented, or pass/fail is unclear.

## 8. Kill Criteria Checklist

Stop immediately (do not proceed to handoff) if **any** apply:

- [ ] Kill switch or risk posture is **uncertain** (see risk docs and bounded-pilot runbook).
- [ ] **Live vs dry-run** semantics for the next action are **ambiguous**.
- [ ] `live_order_execution` / bounded-pilot governance keys or pipeline posture are **unclear** relative to [Bounded Pilot Live Entry](./RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md).
- [ ] Evidence or session lifecycle is **non-reviewable** (missing event pointers, unclear registry posture).
- [ ] **External** Go/No-Go for the pilot is missing where your program requires it.
- [ ] **Master V2 / Double Play** boundary would need to be “interpreted around” to proceed — that is a STOP.

## 9. Bounded Pilot Handoff Checklist

**This runbook does not perform handoff**; it lists posture before using the **bounded-pilot** runbooks:

- [ ] [Bounded Pilot Live Entry](./RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) — follow for **entry** path, gates, and session runner semantics (Ist-Zustand im Repo).
- [ ] Authority for **this** pilot window matches the documented **bounded** context (not broad live).
- [ ] Operator understands **no** automatic promotion after a single session (see [Promotion State Machine](../specs/MASTER_V2_PROMOTION_STATE_MACHINE_V1.md) as a **read model** only).

**Hard STOP if:** handoff would exceed declared scope, or governance/env tokens do not match the bounded-pilot path.

## 10. Closeout / Post-Pilot Checklist

- [ ] [Started Bounded-Pilot Session Review](./RUNBOOK_STARTED_BOUNDED_PILOT_SESSION_REVIEW_V0.md) — use for post-hoc review posture when applicable.
- [ ] Session end state, artifacts, and **closeout** path are **reviewable**; missing items stay visible.
- [ ] PnL or outcome is **not** the sole input to “success.”
- [ ] [Operator / Audit Flat Path Index](../specs/MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md) — use to locate evidence/review surfaces; index does not grant authority.

**Hard STOP if:** closeout is missing, or execution anomalies are unreviewed.

## 11. STOP / Abort Posture

- **Default:** ambiguity → **STOP** (no trade, no handoff, no “push through”).
- **Abort** paths in bounded-pilot and incident runbooks take precedence over any narrative in this file.
- **This runbook** may be used to **refuse** progression when checklists are incomplete; it does **not** grant permission to **continue** when risk or authority is unclear.
- Re-read [First Live Execution Sequence](../specs/MASTER_V2_FIRST_LIVE_EXECUTION_SEQUENCE_V0.md) §12–14 for hard-STOP language consistent with handoff and closeout.

## 12. Authority Boundaries

| Surface | May do | Must not do |
|---|---|---|
| This pilot-sequence runbook | Structure checklists and pointers. | Authorize live trading or pilot entry. |
| Go-Live Roadmap / Execution Sequence | Define stage and review order. | Replace external signoff. |
| Bounded Pilot Live Entry | Describe Ist-Zustand entry path. | Bypass governance or confirm tokens. |
| SRP / source-bound plans | Review shape and planning. | Approve live or closeout. |
| Operator | Decline/STOP when unsafe. | Override kill/risk or fabricate evidence. |

## 13. Validation Notes

After editing this runbook in a PR:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
uv run pytest tests/ops/test_session_review_pack_source_bound_cli_shape_v0.py \
  tests/ops/test_session_review_pack_source_bound_temp_resolver_v0.py \
  tests/ops/test_session_review_pack_source_bound_payload_builder_v0.py \
  tests/ops/test_session_review_pack_report_contracts_v0.py -q
```

Optional: reread [Bounded Pilot Live Entry](./RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) and align section references if the bounded-pilot stack changes on `main`.
