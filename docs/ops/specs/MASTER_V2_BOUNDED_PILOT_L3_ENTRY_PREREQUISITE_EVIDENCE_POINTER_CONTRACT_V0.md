# MASTER V2 — Bounded Pilot L3 Entry-Prerequisite Evidence Pointer Contract v0 (Canonical, Read-Only)

status: ACTIVE
last_updated: 2026-04-20
owner: Peak_Trade
purpose: Docs-only minimal metadata discipline for externally retained L3 entry-prerequisite confirmation artifacts (bounded pilot); mapping and review aid only
docs_token: DOCS_TOKEN_MASTER_V2_BOUNDED_PILOT_L3_ENTRY_PREREQUISITE_EVIDENCE_POINTER_CONTRACT_V0

## 1) Purpose

This contract defines **one** conservative, **L3-only** pattern for how operators or governance may **describe** externally retained evidence that **relates to** [`BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`](BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md) §3 (Pre-Entry Prerequisites), using **pointers and metadata** only.

It supports **review orientation** and **retention discipline** aligned with gate index `G6` / Level 3 — First Live Enablement Entry Contract. It does **not** import confirmation bundles, Ops Cockpit dumps, or secrets into this repository and does **not** assert that any prerequisite is met.

## 2) Scope and Non-Goals

**In scope (bounded pilot, L3 only):**

- **pointer classes** for externally retained **prerequisite confirmation material** tied to contract §3 (summary attestation and/or optional supporting bundle handle)
- **minimal metadata fields** for external pointer records
- explicit **non-claims** and **forbidden payload** rules

**Out of scope:**

- substituting L1 or L2 pointer discipline (see [`MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md`](MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md) and [`MASTER_V2_BOUNDED_PILOT_L2_GO_NO_GO_EVIDENCE_POINTER_CONTRACT_V0.md`](MASTER_V2_BOUNDED_PILOT_L2_GO_NO_GO_EVIDENCE_POINTER_CONTRACT_V0.md) for dry-validation and go/no-go eval captures)
- L4–L5 or cross-gate consolidated bundles
- live unlock, promotion decisions, eligibility, or authorization claims
- runtime, policy, CI, workflow, code, or evidence ingestion into this repo

## 3) Allowed pointer classes (L3)

Each class names **what** external material exists for **review linkage**, not **that** any §3 item is satisfied.

| pointer_class | Typical external artifact (held outside repo) |
|---|---|
| `L3_ENTRY_PREREQUISITE_ATTESTATION_SUMMARY` | Short, review-oriented record that a §3 confirmation pass was performed (for example governance/operator sign-off line) **without** item-by-item cockpit exports or full checklists |
| `L3_ENTRY_PREREQUISITE_SUPPORTING_BUNDLE` | Optional opaque handle to an external bundle (ticket attachments, controlled store objects) that **holds** detailed confirmation material — **never** committed to git |

Do not use these classes to smuggle payloads: if the “summary” contains raw state blobs, it violates §5.

## 4) Minimal metadata fields

When recording a pointer **outside** this repository, use the following fields. Values MUST avoid secrets, credentials, full Ops Cockpit JSON, treasury identifiers, and unnecessary personal data.

| field | requirement | notes |
|---|---|---|
| `pointer_class` | required | one of §3 |
| `bounded_pilot_scope` | required | **first strictly bounded real-money pilot** per entry contract (title and §1–2); do **not** invent candidate IDs unless governance already did outside this repo |
| `prerequisite_scope_reference` | required | literal reference to **§3 Pre-Entry Prerequisites** of [`BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`](BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md) only; do **not** encode per-item pass/fail in this repo |
| `artifact_summary` | required | one non-sensitive line describing what the external object is (not its contents) |
| `retrieval_reference` | required | opaque handle — **never** paste bundle bodies into git |
| `git_head_at_capture` | required when repo state matters | commit SHA of this repo at capture time |
| `captured_at_utc` | required | UTC timestamp |
| `retention_owner` | required | role label only |
| `change_control_anchor` | optional | change-control ID or link |

## 5) Forbidden content and non-claims

**Forbidden to commit inside this repository:**

- full prerequisite checklists with live values, Ops Cockpit snapshots, treasury balances, or config secrets
- any “pointer” that is effectively a **data dump**

**This contract explicitly does not claim:**

- that any §3 item (1–6) is true or acceptable for entry
- that `G6` is closed, passed, or `Verified`
- live authorization, live unlock, eligibility, or promotion approval
- anything beyond [`MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) and [`MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md`](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md) §4.6 on external authority

**Retention:** confirmation material remains under operator or governance change control **outside** this repo.

## 6) Relationship to other First Live surfaces

- **Gate index `G6` / §4.3:** vocabularizes external §3 confirmation pointers; does **not** change `G6` status.
- **Boundary note:** entry vs first real-money framing stays in [`BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE.md`](BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE.md); this contract does not move the boundary.
- **Gate-Status Report Surface:** non-authorizing; [`MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md`](MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md) §3.2.
- **`G10` / `G11`:** pointers are not final authorization and not a cross-gate material bundle.

## 7) Illustrative pointer record (non-binding)

```yaml
pointer_class: L3_ENTRY_PREREQUISITE_ATTESTATION_SUMMARY
bounded_pilot_scope: "First strictly bounded real-money pilot (see entry contract title and §1–2)"
prerequisite_scope_reference: "BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md §3 Pre-Entry Prerequisites"
artifact_summary: "External attestation line only; no checklist payload"
retrieval_reference: "CHANGE_CONTROL_RECORD_ID_REDACTED"
git_head_at_capture: "abc1234deadbeef..."
captured_at_utc: "2026-04-20T16:00:00Z"
retention_owner: "governance_steward_role"
change_control_anchor: "TICKET_REF_REDACTED"
```

## 8) Operator / reviewer use

Use alongside [`RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`](../runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) and gate index [§4.3](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md#43-l3-candidate-prerequisite-pointer-record-g6). Pointer discipline under [`MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md`](MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md) and [`MASTER_V2_BOUNDED_PILOT_L2_GO_NO_GO_EVIDENCE_POINTER_CONTRACT_V0.md`](MASTER_V2_BOUNDED_PILOT_L2_GO_NO_GO_EVIDENCE_POINTER_CONTRACT_V0.md) may produce captures that **overlap** evidence used to **inform** §3 items 1–2; reuse external objects with clear scope in `artifact_summary` instead of duplicating contradictory handles. Authorization remains external.
