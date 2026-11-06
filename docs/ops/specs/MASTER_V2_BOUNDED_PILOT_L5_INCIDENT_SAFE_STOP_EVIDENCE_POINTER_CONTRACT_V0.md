# MASTER V2 — Bounded Pilot L5 Incident / Safe-Stop Evidence Pointer Contract v0 (Canonical, Read-Only)

status: ACTIVE
last_updated: 2026-04-20
owner: Peak_Trade
purpose: Docs-only minimal metadata discipline for externally retained L5 incident and safe-stop artifacts (bounded pilot); mapping and review aid only
docs_token: DOCS_TOKEN_MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0

## 1) Purpose

This contract defines **one** conservative, **L5-only** pattern for how operators or governance may **describe** externally retained **incident, safe-stop, abort, or drill/tabletop** evidence using **pointers and metadata** only — without importing incident tickets, logs, recovery transcripts, or secrets into this repository.

It supports **review orientation** and **retention discipline** aligned with gate index `G8` / Level 5 — Incident, Abort, and Safe-Stop Discipline. It does **not** assert that any incident occurred, was handled correctly, or that policy/kill-switch posture was safe at any time.

## 2) Scope and Non-Goals

**In scope (bounded pilot, L5 only):**

- **pointer classes** for externally retained material consistent with gate index §4.5 (summary, incident-response bundle, optional drill/tabletop bundle)
- **minimal metadata fields** for external pointer records
- explicit **non-claims** and **forbidden payload** rules

**Out of scope:**

- L1–L4 pointer discipline (see [`MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md`](MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md) through [`MASTER_V2_BOUNDED_PILOT_L4_SESSION_FLOW_EVIDENCE_POINTER_CONTRACT_V0.md`](MASTER_V2_BOUNDED_PILOT_L4_SESSION_FLOW_EVIDENCE_POINTER_CONTRACT_V0.md))
- rewriting or “hardening” draft-heavy incident runbooks in this slice
- live unlock, promotion, eligibility, or authorization claims
- runtime, policy, CI, workflow, code, or evidence file ingestion into this repo

## 3) Allowed pointer classes (L5)

Each class names **what** external material exists for **review linkage**, not **that** a production incident happened or that safe-stop was effective.

| pointer_class | Typical external artifact (held outside repo) |
|---|---|
| `L5_INCIDENT_SAFE_STOP_SUMMARY_CAPTURE` | Short, review-oriented record of incident posture, drill scenario, or safe-stop narrative **without** raw logs, ticket bodies, or cockpit/policy dumps |
| `L5_INCIDENT_RESPONSE_SUPPORTING_BUNDLE` | Opaque handle to externally stored incident-response evidence (timelines, comms summaries stored outside git, controlled attachments) |
| `L5_SAFE_STOP_DRILL_OR_TABLETOP_BUNDLE` | Opaque handle to **preparedness** material (drill/tabletop) — must **not** be presented as proof of production incident handling unless governance labels it that way **outside** this repo |

Do not use drill/tabletop pointers to imply live eligibility.

## 4) Minimal metadata fields

When recording a pointer **outside** this repository, use the following fields. Values MUST avoid secrets, credentials, full incident payloads, broker identifiers, kill-switch state dumps, and unnecessary personal data.

| field | requirement | notes |
|---|---|---|
| `pointer_class` | required | one of §3 |
| `bounded_pilot_scope` | required | **first strictly bounded real-money pilot** per [`BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`](BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md) (title and §1–2); do **not** invent candidate labels unless governance already did outside this repo |
| `incident_safe_stop_scope_reference` | required | literal reference to **§5 Abort / Rollback / NO_TRADE** of the entry contract, [`MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md`](MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md), and/or Level 5 of [`MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md`](MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md); optionally name **runbook titles** only (no operational IDs in-repo) |
| `artifact_summary` | required | one non-sensitive line (what the external object is), not its contents |
| `retrieval_reference` | required | opaque handle — **never** paste payloads into git |
| `git_head_at_capture` | required when repo state matters | commit SHA of this repo at capture time |
| `captured_at_utc` | required | UTC timestamp |
| `retention_owner` | required | role label only |
| `change_control_anchor` | optional | change-control ID or link |

## 5) Forbidden content and non-claims

**Forbidden to commit inside this repository:**

- full incident logs, full ticket exports, policy/kill-switch JSON, recovery playbooks with live values
- any “pointer” that is effectively a **payload**

**This contract explicitly does not claim:**

- that any incident response was exercised successfully in production
- that kill-switch, `NO_TRADE`, or policy posture was correct at a point in time
- that `G8` is closed, passed, or `Verified`, or that draft-heavy runbooks are production-complete
- live authorization, live unlock, eligibility, or promotion approval
- anything beyond [`MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) and [`MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md`](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md) §4.6 on external authority

**Retention:** incident and safe-stop evidence remains under operator or governance change control **outside** this repo.

## 6) Relationship to other First Live surfaces

- **Gate index `G8` / §4.5:** vocabularizes external L5 pointers; does **not** change `G8` status or runbook maturity.
- **Session flow (`G7`):** incident discipline **attaches** to execution context per §4.5; L4 pointers cover session material — L5 pointers cover **incident/safe-stop** material **without** duplicating L4 session bundles unless governance scopes one external object for both (clear `artifact_summary`).
- **Gate-Status Report Surface:** non-authorizing; [`MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md`](MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md) §3.2.
- **`G10` / `G11`:** not final authorization; not a cross-gate consolidated bundle.

## 7) Illustrative pointer record (non-binding)

```yaml
pointer_class: L5_INCIDENT_SAFE_STOP_SUMMARY_CAPTURE
bounded_pilot_scope: "First strictly bounded real-money pilot (see entry contract title and §1–2)"
incident_safe_stop_scope_reference: "ENTRY_CONTRACT §5; FAILURE_TAXONOMY_SAFE_FALLBACKS_V1; Readiness Ladder L5"
artifact_summary: "Operator incident posture summary only; no ticket payload"
retrieval_reference: "CHANGE_CONTROL_RECORD_ID_REDACTED"
git_head_at_capture: "abc1234deadbeef..."
captured_at_utc: "2026-04-20T20:00:00Z"
retention_owner: "operator_role"
change_control_anchor: "TICKET_REF_REDACTED"
```

## 8) Operator / reviewer use

Align external retention with the Level 5 incident runbooks linked from gate index [§4.5](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md#45-l5-candidate-incident-safe-stop-pointer-record-g8) and entry contract §5. This contract does **not** replace those runbooks or close draft gaps. Authorization remains external.
