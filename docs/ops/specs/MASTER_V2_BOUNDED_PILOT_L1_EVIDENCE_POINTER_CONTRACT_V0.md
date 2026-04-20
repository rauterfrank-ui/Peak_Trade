# MASTER V2 — Bounded Pilot L1 Evidence Pointer Contract v0 (Canonical, Read-Only)

status: ACTIVE
last_updated: 2026-04-20
owner: Peak_Trade
purpose: Docs-only minimal metadata discipline for externally retained L1 dry-validation artifacts (bounded pilot); mapping and review aid only
docs_token: DOCS_TOKEN_MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0

## 1) Purpose

This contract defines **one** conservative, **L1-only** pattern for how operators or governance may **describe** externally retained dry-validation evidence using **pointers and metadata**, without importing payloads into this repository.

It supports **review orientation** and **retention discipline** aligned with gate index `G4` / Level 1 — Dry Validation Readiness. It is **not** a substitute for storing real logs, JSON, or secrets.

## 2) Scope and Non-Goals

**In scope (bounded pilot, L1 only):**

- three **pointer classes** matching dry-validation Steps 1–3 (artifact **kinds**, not file formats mandated here)
- **minimal metadata fields** that may accompany an external reference in a review packet or change-control system
- explicit **non-claims** and **forbidden payload** rules
- **reference discipline** (opaque handles, no secrets in-repo)

**Out of scope:**

- L2–L5 or cross-gate bundles (see gate index and cross-gate index for separate posture)
- live unlock, promotion decisions, or eligibility claims
- runtime, policy, CI, workflow, code, or evidence file ingestion into this repo
- defining a specific external storage product, vendor, or mandatory tooling

## 3) Allowed pointer classes (L1)

Each class names **what** was captured, not **whether** a run succeeded or entry is permitted.

| pointer_class | Maps to dry-validation step | Typical external artifact (held outside repo) |
|---|---|---|
| `L1_STEP1_DRILL_CAPTURE` | Step 1 | Drill output (text or structured capture as produced by the drill flow) |
| `L1_STEP2_GO_NO_GO_EVAL_CAPTURE` | Step 2 | Go/no-go eval verdict and optional machine-readable capture from the eval entry point |
| `L1_STEP3_EXECUTION_DRY_RUN_LOG` | Step 3 | Execution session dry-run log |

Optional Step 4–5 material from the dry-validation runbook is **not** part of this v0 contract unless a later slice extends the class table.

## 4) Minimal metadata fields

When recording a pointer **outside** this repository (for example in a governance ticket or object store), the following fields are the **minimum** recommended for **cross-review legibility**. All values MUST avoid secrets, credentials, raw log bodies, and unnecessary personal data.

| field | requirement | notes |
|---|---|---|
| `pointer_class` | required | one of §3 |
| `bounded_pilot_scope` | required | literal label only: use the **first strictly bounded real-money pilot** scope wording from [`BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`](BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md) (title and §1–2); do **not** assert a extra candidate identifier unless governance already introduced one outside this repo |
| `artifact_summary` | required | one short non-sensitive line (what the capture is), not the payload |
| `retrieval_reference` | required | opaque handle acceptable to your change-control system (ticket ID, object key, URI) — **never** paste the secret-bearing payload into git |
| `git_head_at_capture` | required when repo state matters | commit SHA of this repo at capture time (see dry-validation Evidence section) |
| `captured_at_utc` | required | timestamp in UTC |
| `retention_owner` | required | role label only (for example operator vs governance steward), not a home address or direct personal identifier |
| `change_control_anchor` | optional | link or ID to the governing change-control record, if one exists |

No additional speculative fields are required by this v0 contract.

## 5) Forbidden content and non-claims

**Forbidden to commit inside this repository as part of “satisfying” this contract:**

- full drill transcripts, full go/no-go JSON bodies, or full dry-run logs
- API keys, tokens, cookies, broker identifiers, account numbers
- any field value that would turn a pointer record into a **payload dump**

**This contract explicitly does not claim:**

- that any L1 step completed successfully
- that any verdict is acceptable for real-money entry
- that `G4` is closed, passed, or `Verified` in the gate-status index
- live authorization, live unlock, eligibility, or promotion approval
- parity with external governance actors beyond what [`MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) and [`MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md`](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md) §4.6 already state

**Retention:** artifacts remain **operator- or governance-held** under your change-control rules. This repo document does not assert immutability or completeness of external stores.

## 6) Relationship to other First Live surfaces

- **Gate index `G4` / §4.1:** this contract **narrows vocabulary** for “what a future repo-resolvable or review-pointer record may contain” for L1 only; it does **not** change `G4` status by itself.
- **Gate-Status Report Surface:** report rows and narratives remain **non-authorizing**; see [`MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md`](MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md) §3.2.
- **`G10` / live authorization:** pointer metadata is **visibility for review**, not final authorization; see gate index §4.6 and the authority map §4 / §7.
- **`G11` cross-gate bundles:** this contract is **single-level (L1)** only; it does not materialize a cross-gate evidence bundle.

## 7) Illustrative pointer record (non-binding)

The following is a **shape example** only. Values are illustrative placeholders.

```yaml
pointer_class: L1_STEP2_GO_NO_GO_EVAL_CAPTURE
bounded_pilot_scope: "First strictly bounded real-money pilot (see entry contract title and §1–2)"
artifact_summary: "Machine-readable eval capture produced by the documented eval entry point"
retrieval_reference: "CHANGE_CONTROL_RECORD_ID_REDACTED"
git_head_at_capture: "abc1234deadbeef..."  # illustrative only
captured_at_utc: "2026-04-20T12:00:00Z"
retention_owner: "governance_steward_role"
change_control_anchor: "TICKET_REF_REDACTED"
```

## 8) Operator / reviewer use

Use this contract to keep **language alignment** between the dry-validation runbook Evidence section, the `G4` pointer record, and external retention practice. Any promotion, pass, or authorization decision remains outside this document.
