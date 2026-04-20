# MASTER V2 — Bounded Pilot Cross-Gate Candidate Evidence Bundle Pointer Contract v0 (Canonical, Read-Only)

status: ACTIVE
last_updated: 2026-04-20
owner: Peak_Trade
purpose: Docs-only minimal metadata discipline for externally retained, candidate-scoped cross-gate evidence bundle references (bounded pilot); mapping and review aid only
docs_token: DOCS_TOKEN_MASTER_V2_BOUNDED_PILOT_CROSS_GATE_CANDIDATE_EVIDENCE_BUNDLE_POINTER_CONTRACT_V0

## 1) Purpose

This contract defines a **single conservative pattern** for how operators or governance may **describe** an **externally retained** consolidated evidence bundle that is **candidate-scoped** and **cross-gate** in intent, using **pointers and metadata** only — without importing payloads, logs, JSON bodies, or secrets into this repository.

It supports **review orientation** and **retention discipline** aligned with gate index **`G11`** (compact cross-gate evidence bundle visibility) and the [Cross-Gate Evidence Bundle Index](MASTER_V2_FIRST_LIVE_CROSS_GATE_EVIDENCE_BUNDLE_INDEX_V1.md). It is **not** a substitute for storing real bundle contents or for any live-authorization decision.

## 2) Scope and Non-Goals

**In scope (bounded pilot, candidate-scoped cross-gate bundle references only):**

- **pointer classes** for externally held consolidation (artifact **kinds**, not mandated file formats)
- **minimal metadata fields** that may accompany an external reference in a review packet or change-control system
- explicit **non-claims** and **forbidden payload** rules
- **reference discipline** (opaque handles, no secrets in-repo)
- **L1–L5** referenced **only** as the **scope / coverage catalog** of bounded-pilot pointer-contract families (see §6.2); this contract does **not** restate or merge those per-level records

**Out of scope:**

- asserting that any gate is closed, passed, or `Verified`
- live unlock, promotion decisions, eligibility, or final authorization (see [Report Surface §3.2](MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md#32-interpretation-lock-promotion-readiness-visibility-vs-live-authorization) and gate index [§4.6 G10 note](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md#46-g10-authority-handoff-legibility-note-g10))
- runtime, policy, CI, workflow, code, or evidence file ingestion into this repo
- defining a specific external storage product, vendor, or mandatory tooling
- replacing operator-held bundles or external sign-off; this remains **vocabulary for pointers**, not proof

## 3) Allowed pointer classes (cross-gate candidate bundle)

Each class names **what** is being pointed at, not **whether** any level succeeded, any gate closed, or entry is permitted.

| pointer_class | Typical external artifact (held outside repo) |
|---|---|
| `G11_CROSS_GATE_CANDIDATE_BUNDLE_SUMMARY` | Short, non-sensitive description of what the consolidated bundle is claimed to cover (prose or structured summary **outside** git) |
| `G11_CROSS_GATE_CANDIDATE_BUNDLE_RETRIEVAL` | Opaque handle to the consolidated bundle location (ticket, object key, controlled URI) — **never** the bundle body in-repo |
| `G11_CROSS_GATE_CANDIDATE_BUNDLE_SCOPE_NOTE` | Optional separate note that the external bundle is **intended** to span multiple gate-readiness families; still **no** pass/fail or closure language |

Use **at most one** row of each class per candidate-scoped consolidation **episode** you are documenting outside the repo, unless your change-control system explicitly versions multiple summaries; this v0 does not prescribe versioning.

## 4) Minimal metadata fields

When recording pointers **outside** this repository, the following fields are the **minimum** recommended for **cross-review legibility**. All values MUST avoid secrets, credentials, raw log bodies, full transcripts, and unnecessary personal data.

| field | requirement | notes |
|---|---|---|
| `pointer_class` | required | one of §3 |
| `bounded_pilot_scope` | required | literal label only: use the **first strictly bounded real-money pilot** scope wording from [`BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`](BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md) (title and §1–2); do **not** invent or paste a live candidate identifier into this repo unless governance already introduced one outside this repo |
| `artifact_summary` | required | one short non-sensitive line (what the pointer refers to), not the payload |
| `retrieval_reference` | required for `G11_CROSS_GATE_CANDIDATE_BUNDLE_RETRIEVAL`; optional for summary-only rows | opaque handle acceptable to your change-control system |
| `l1_l5_pointer_family_catalog_reference` | required once per **set** of pointers describing the same consolidation episode | **Coverage catalog only:** name or link (outside git) to the five bounded-pilot pointer-contract families — [L1](MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md), [L2](MASTER_V2_BOUNDED_PILOT_L2_GO_NO_GO_EVIDENCE_POINTER_CONTRACT_V0.md), [L3](MASTER_V2_BOUNDED_PILOT_L3_ENTRY_PREREQUISITE_EVIDENCE_POINTER_CONTRACT_V0.md), [L4](MASTER_V2_BOUNDED_PILOT_L4_SESSION_FLOW_EVIDENCE_POINTER_CONTRACT_V0.md), [L5](MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md) — as the **review vocabulary** for what “cross-gate” may mean in-repo; **do not** assert that every family is populated, satisfied, or closed |
| `git_head_at_capture` | required when repo state matters | commit SHA of this repo at capture time |
| `captured_at_utc` | required | timestamp in UTC |
| `retention_owner` | required | role label only (for example operator vs governance steward), not direct personal identifiers |
| `change_control_anchor` | optional | link or ID to the governing change-control record, if one exists |

No additional speculative fields are required by this v0 contract.

## 5) Forbidden content and non-claims

**Forbidden to commit inside this repository as part of “satisfying” this contract:**

- full bundle exports, log dumps, JSON bodies, drill transcripts, or incident timelines
- API keys, tokens, cookies, broker identifiers, account numbers
- operator-held bundle IDs treated as authoritative proof in git narrative
- any field value that turns a pointer record into a **payload dump**

**This contract explicitly does not claim:**

- that a cross-gate bundle exists, is complete, or is acceptable
- that **L1–L5** pointer families are all satisfied or that **`G4`–`G8`** are closed
- that **`G11`** moves beyond `Partial` in the gate-status index
- live authorization, live unlock, eligibility, or promotion approval
- parity with external governance actors beyond what [`MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) and the gate index §4.6 already state

**Retention / reference discipline:** consolidated bundles remain **operator- or governance-held** under change control. References in-repo (if any future slice adds them) must stay **non-authorizing**. Prefer **opaque handles** and **short summaries**; rotate or redact handles in documentation if they become sensitive.

## 6) Relationship to other First Live surfaces

### 6.1 `G11`, cross-gate index, report surface, `G10`

- **`G11` / compact table:** this contract **adds vocabulary** for how an **external** candidate-scoped cross-gate bundle may be **described** with pointers; it does **not** assert material bundles in-repo or change `G11` status by itself.
- **[Cross-Gate Evidence Bundle Index](MASTER_V2_FIRST_LIVE_CROSS_GATE_EVIDENCE_BUNDLE_INDEX_V1.md):** remains the compact mapping surface; this contract does not duplicate its interpretation locks.
- **Report Surface [§3.2](MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md#32-interpretation-lock-promotion-readiness-visibility-vs-live-authorization):** visible readiness or promotion language is **not** live authorization; pointer metadata must not be read as a green light.
- **`G10`:** authority-handoff legibility stays separate; cross-gate bundle pointers **do not** complete the external authorization chain.

### 6.2 L1–L5 pointer contracts (scope family only)

The L1–L5 contracts define **per-level** pointer discipline. This cross-gate contract **references them only as a catalog** of bounded-pilot evidence-pointer **families** that a consolidation bundle **might** span in external storage. It does **not**:

- merge L1–L5 records into one in-repo artifact
- imply that all levels are evidenced or acceptable
- substitute reading the per-level contracts when reviewing a specific level

## 7) Illustrative pointer records (non-binding)

The following are **shape examples** only. Values are illustrative placeholders.

```yaml
# Summary row for an external consolidation episode
pointer_class: G11_CROSS_GATE_CANDIDATE_BUNDLE_SUMMARY
bounded_pilot_scope: "First strictly bounded real-money pilot (see entry contract title and §1–2)"
artifact_summary: "Operator-held index of L1–L5 family pointers for one candidate consolidation review"
retrieval_reference: ""
l1_l5_pointer_family_catalog_reference: "L1–L5 bounded-pilot pointer contracts (repo paths per §4)"
git_head_at_capture: "abc1234deadbeef..."  # illustrative only
captured_at_utc: "2026-04-20T12:00:00Z"
retention_owner: "governance_steward_role"
change_control_anchor: "TICKET_REF_REDACTED"
```

```yaml
# Retrieval row for the same episode (handle only)
pointer_class: G11_CROSS_GATE_CANDIDATE_BUNDLE_RETRIEVAL
bounded_pilot_scope: "First strictly bounded real-money pilot (see entry contract title and §1–2)"
artifact_summary: "Opaque handle to consolidated bundle store object"
retrieval_reference: "OBJECT_KEY_OR_TICKET_REDACTED"
l1_l5_pointer_family_catalog_reference: "Same catalog reference as paired summary row"
git_head_at_capture: "abc1234deadbeef..."
captured_at_utc: "2026-04-20T12:05:00Z"
retention_owner: "operator_role"
```

## 8) Operator / reviewer use

Use this contract to **speak consistently** about **external** candidate-scoped cross-gate bundles when preparing review packets or change-control entries. It is a **pointer and metadata discipline** document only; all authorization and bundle truth remain **outside** this repository.
