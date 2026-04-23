# MASTER V2 — Bounded Pilot L4 Session-Flow Evidence Pointer Contract v0 (Canonical, Read-Only)

status: ACTIVE
last_updated: 2026-04-20
owner: Peak_Trade
purpose: Docs-only minimal metadata discipline for externally retained L4 first-candidate-session-flow artifacts (bounded pilot); mapping and review aid only
docs_token: DOCS_TOKEN_MASTER_V2_BOUNDED_PILOT_L4_SESSION_FLOW_EVIDENCE_POINTER_CONTRACT_V0

## 1) Purpose

This contract defines **one** conservative, **L4-only** pattern for how operators or governance may **describe** externally retained **first bounded-pilot candidate session-flow** evidence using **pointers and metadata** only — without importing session logs, registry exports, closeout bodies, or secrets into this repository.

It supports **review orientation** and **retention discipline** aligned with gate index `G7` / Level 4 — First Candidate Session Flow (Operator Execution Surface). It does **not** assert that any session ran, completed, or was safe.

## 2) Scope and Non-Goals

**In scope (bounded pilot, L4 only):**

- **pointer classes** for externally retained material matching the gate index’s session-flow evidence shape (summary, registry/trace bundle, closeout/reconciliation bundle)
- **minimal metadata fields** for external pointer records
- explicit **non-claims** and **forbidden payload** rules

**Out of scope:**

- L1–L3 pointer discipline (see [`MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md`](MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md), [`MASTER_V2_BOUNDED_PILOT_L2_GO_NO_GO_EVIDENCE_POINTER_CONTRACT_V0.md`](MASTER_V2_BOUNDED_PILOT_L2_GO_NO_GO_EVIDENCE_POINTER_CONTRACT_V0.md), [`MASTER_V2_BOUNDED_PILOT_L3_ENTRY_PREREQUISITE_EVIDENCE_POINTER_CONTRACT_V0.md`](MASTER_V2_BOUNDED_PILOT_L3_ENTRY_PREREQUISITE_EVIDENCE_POINTER_CONTRACT_V0.md))
- L5 incident-only bundles (separate slice/contract family for `G8`)
- live unlock, promotion, eligibility, or authorization claims
- runtime, policy, CI, workflow, code, or evidence file ingestion into this repo

## 3) Allowed pointer classes (L4)

Each class names **what** external material exists for **review linkage**, not **that** execution succeeded or handoff was correct.

| pointer_class | Typical external artifact (held outside repo) |
|---|---|
| `L4_SESSION_FLOW_SUMMARY_CAPTURE` | Short, review-oriented record of session-flow posture or outcome framing (for example operator narrative of steps taken) **without** raw logs, registry JSON, or cockpit dumps |
| `L4_SESSION_REGISTRY_OR_TRACE_BUNDLE` | Opaque handle to externally stored registry exports, execution-event extracts, or similar **trace** material referenced in gate index §4.4 |
| `L4_SESSION_CLOSEOUT_RECONCILIATION_BUNDLE` | Opaque handle to externally stored closeout and reconciliation material (per candidate-flow **E.** Evidence and pointers (L4 discipline) intent) — **never** committed to git |

One session may justify multiple rows with distinct `pointer_class` values; use **consistent** `session_flow_scope_reference` and do not publish contradictory `retrieval_reference` values for the same logical object.

## 4) Minimal metadata fields

When recording a pointer **outside** this repository, use the following fields. Values MUST avoid secrets, credentials, raw logs, full registry payloads, session identifiers that are sensitive in your threat model, and unnecessary personal data.

| field | requirement | notes |
|---|---|---|
| `pointer_class` | required | one of §3 |
| `bounded_pilot_scope` | required | **first strictly bounded real-money pilot** per [`BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`](BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md) (title and §1–2); do **not** invent candidate labels unless governance already did outside this repo |
| `session_flow_scope_reference` | required | literal reference to **§4 First Bounded Real-Money Step** of the entry contract and/or the canonical candidate session sequence (sections **A–G**) in [`RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md`](../runbooks/RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md); do **not** paste operational IDs into this repo |
| `artifact_summary` | required | one non-sensitive line (what the external object is), not its contents |
| `retrieval_reference` | required | opaque handle — **never** paste payloads into git |
| `git_head_at_capture` | required when repo state matters | commit SHA of this repo at capture time |
| `captured_at_utc` | required | UTC timestamp |
| `retention_owner` | required | role label only |
| `change_control_anchor` | optional | change-control ID or link |

## 5) Forbidden content and non-claims

**Forbidden to commit inside this repository:**

- full session logs, registry exports, execution event dumps, or closeout transcripts
- API keys, tokens, broker or account identifiers
- any “pointer” that is effectively a **payload**

**This contract explicitly does not claim:**

- that [`BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`](BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md) §3 or §4 preconditions held at runtime
- that `G7` is closed, passed, or `Verified`
- that handoff, bounded-pilot wrapper, or execution session completed successfully
- live authorization, live unlock, eligibility, or promotion approval
- anything beyond [`MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) and [`MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md`](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md) §4.6 on external authority

**Retention:** session-flow evidence remains under operator or governance change control **outside** this repo.

## 6) Relationship to other First Live surfaces

- **Gate index `G7` / §4.4:** vocabularizes external session-flow pointers; does **not** change `G7` status.
- **Gate-Status Report Surface:** non-authorizing; [`MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md`](MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md) §3.2.
- **`G10`:** pointer metadata is not final live authorization.
- **`G11`:** L4-only; not a cross-gate consolidated bundle index.
- **Upstream L1–L3:** prerequisite and eval captures may **inform** session readiness; reuse external objects with explicit scope in `artifact_summary` instead of duplicating contradictory handles.

## 7) Illustrative pointer record (non-binding)

```yaml
pointer_class: L4_SESSION_FLOW_SUMMARY_CAPTURE
bounded_pilot_scope: "First strictly bounded real-money pilot (see entry contract title and §1–2)"
session_flow_scope_reference: "ENTRY_CONTRACT §4; RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW § E (Evidence and pointers (L4 discipline))"
artifact_summary: "Operator session-flow summary only; no log payload"
retrieval_reference: "CHANGE_CONTROL_RECORD_ID_REDACTED"
git_head_at_capture: "abc1234deadbeef..."
captured_at_utc: "2026-04-20T18:00:00Z"
retention_owner: "operator_role"
change_control_anchor: "TICKET_REF_REDACTED"
```

## 8) Operator / reviewer use

Align external retention with [`RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md`](../runbooks/RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md) — [**E.** Evidence and pointers (L4 discipline)](../runbooks/RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md#e-evidence-and-pointers-l4-discipline) (full operator sequence: sections **A–G**) — and [`RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`](../runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md). Cross-check gate index [§4.4](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md#44-l4-candidate-session-flow-pointer-record-g7). Authorization remains external.
