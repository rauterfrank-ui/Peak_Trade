# MASTER V2 — Bounded Pilot L2 Go/No-Go Evidence Pointer Contract v0 (Canonical, Read-Only)

status: ACTIVE
last_updated: 2026-04-20
owner: Peak_Trade
purpose: Docs-only minimal metadata discipline for externally retained L2 go/no-go eval artifacts (bounded pilot); mapping and review aid only
docs_token: DOCS_TOKEN_MASTER_V2_BOUNDED_PILOT_L2_GO_NO_GO_EVIDENCE_POINTER_CONTRACT_V0

## 1) Purpose

This contract defines **one** conservative, **L2-only** pattern for how operators or governance may **describe** externally retained **go/no-go eval** evidence using **pointers and metadata**, without importing verdict bodies, `--json` captures, or secrets into this repository.

It supports **review orientation** and **retention discipline** aligned with gate index `G5` / Level 2 — Go/No-Go Interpretation. It is **not** a substitute for storing real eval output or for entry-contract authorization.

## 2) Scope and Non-Goals

**In scope (bounded pilot, L2 only):**

- **pointer classes** for go/no-go **eval outcome material** retained outside the repo (human-readable summary and/or optional machine-readable capture from the documented eval entry point)
- **minimal metadata fields** for external pointer records
- explicit **non-claims** and **forbidden payload** rules
- **reference discipline** (opaque handles, no secrets in-repo)

**Out of scope:**

- L1 dry-validation drill or execution dry-run artifacts (see [`MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md`](MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md) for Step 1 and Step 3 classes; see that document’s Step 2 class when the capture is framed **strictly** as dry-validation Step 2 only)
- L3–L5 or cross-gate bundles
- live unlock, promotion decisions, or eligibility claims
- runtime, policy, CI, workflow, code, or evidence file ingestion into this repo
- mandating a specific external storage vendor or product

## 3) Allowed pointer classes (L2)

Each class names **what** was captured, not **whether** a verdict is acceptable for real-money entry.

| pointer_class | Typical external artifact (held outside repo) |
|---|---|
| `L2_GO_NO_GO_EVAL_SUMMARY_CAPTURE` | Short, review-oriented record of the eval outcome (for example operator transcript of verdict classes) without pasting full checklist or cockpit dumps |
| `L2_GO_NO_GO_EVAL_JSON_CAPTURE` | Optional machine-readable capture when the documented eval entry point supports it (for example `--json` as referenced in gate index §4.2) — **stored only outside git** |

One real-world eval run may produce **one** external bundle referenced by both rows **only if** governance distinguishes summary vs machine capture cleanly; do not duplicate contradictory handles.

## 4) Minimal metadata fields

Same minimum discipline as L1 pointers: when recording a pointer **outside** this repository, use the following fields. All values MUST avoid secrets, credentials, full verdict payloads, raw JSON bodies, and unnecessary personal data.

| field | requirement | notes |
|---|---|---|
| `pointer_class` | required | one of §3 |
| `bounded_pilot_scope` | required | literal label only: **first strictly bounded real-money pilot** per [`BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`](BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md) (title and §1–2); do **not** invent a candidate ID unless governance already did outside this repo |
| `artifact_summary` | required | one short non-sensitive line; must **not** embed verdict JSON or secrets |
| `retrieval_reference` | required | opaque handle (ticket, object key, URI) — **never** paste eval payload into git |
| `git_head_at_capture` | required when repo state matters | commit SHA of this repo at capture time |
| `captured_at_utc` | required | timestamp in UTC |
| `retention_owner` | required | role label only |
| `change_control_anchor` | optional | change-control ID or link |

## 5) Forbidden content and non-claims

**Forbidden to commit inside this repository:**

- full go/no-go eval JSON, full console transcripts, or checklist line-by-line dumps
- API keys, tokens, broker or account identifiers
- any value that turns a “pointer” into a **payload**

**This contract explicitly does not claim:**

- that any eval produced `GO_FOR_NEXT_PHASE_ONLY` or any other contract-named verdict class
- that prerequisites in [`BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`](BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md) §3 are satisfied
- that `G5` is closed, passed, or `Verified` in the gate-status index
- live authorization, live unlock, eligibility, or promotion approval
- anything beyond [`MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) and [`MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md`](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md) §4.6 regarding external actors

**Retention:** artifacts stay under operator or governance change control outside this repo.

## 6) Relationship to other First Live surfaces

- **Gate index `G5` / §4.2:** this contract **vocabularizes** external go/no-go eval pointer records; it does **not** change `G5` status.
- **Gate-Status Report Surface:** remains **non-authorizing**; see [`MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md`](MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md) §3.2.
- **`G10`:** pointer metadata is not final live authorization.
- **`G11`:** L2-only; not a cross-gate bundle.
- **L1 contract:** dry-validation [**C.** Operator sequence (ordered)](../runbooks/RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md#c-operator-sequence-ordered) item **2** (Pilot go/no-go eval) uses the **same** eval entry point as documented in gate index §4.2; a single external capture may be referenced for **both** L1 Step 2 framing and **L2/G5** framing if governance agrees one object satisfies both review questions — use consistent `retrieval_reference` and clear `artifact_summary` scope.

## 7) Illustrative pointer records (non-binding)

```yaml
# Summary-only example
pointer_class: L2_GO_NO_GO_EVAL_SUMMARY_CAPTURE
bounded_pilot_scope: "First strictly bounded real-money pilot (see entry contract title and §1–2)"
artifact_summary: "Operator-facing summary of eval verdict classes (no payload)"
retrieval_reference: "CHANGE_CONTROL_RECORD_ID_REDACTED"
git_head_at_capture: "abc1234deadbeef..."
captured_at_utc: "2026-04-20T14:00:00Z"
retention_owner: "operator_role"
change_control_anchor: "TICKET_REF_REDACTED"
```

```yaml
# Optional machine capture pointer (object lives outside git)
pointer_class: L2_GO_NO_GO_EVAL_JSON_CAPTURE
bounded_pilot_scope: "First strictly bounded real-money pilot (see entry contract title and §1–2)"
artifact_summary: "External file produced by eval entry point optional machine output"
retrieval_reference: "OBJECT_STORE_KEY_REDACTED"
git_head_at_capture: "abc1234deadbeef..."
captured_at_utc: "2026-04-20T14:00:01Z"
retention_owner: "governance_steward_role"
```

## 8) Operator / reviewer use

Align external retention with [`PILOT_GO_NO_GO_CHECKLIST.md`](PILOT_GO_NO_GO_CHECKLIST.md), [`PILOT_GO_NO_GO_OPERATIONAL_SLICE.md`](PILOT_GO_NO_GO_OPERATIONAL_SLICE.md), and runbook ordering in [`RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md`](../runbooks/RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md) (**sections A–G**; [**C.** Operator sequence (ordered)](../runbooks/RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md#c-operator-sequence-ordered), item **2** — Pilot go/no-go eval) / [`RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`](../runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md). Authorization remains external.
