# RUNBOOK — Bounded Pilot Incident / §5 Abort Triage Compass v0

status: DRAFT
last_updated: 2026-04-23
owner: Peak_Trade
purpose: Single canonical orientation surface mapping symptoms and Entry Contract §5 abort posture to pilot incident runbooks, L5 evidence-pointer discipline, and read-only registry/report CLIs (bounded pilot)
docs_token: DOCS_TOKEN_RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS

## 1) Purpose, scope, and non-goals

**Purpose:** Under time pressure, route from **what you observe** to **conservative posture** (`NO_TRADE` / safe stop), the **nearest matching** bounded-pilot **incident runbook**, **external L5 evidence** expectations, and **read-only** CLI snapshots — without inventing new incident classes or frameworks.

**Scope:** The **first strictly bounded real-money pilot** ([`BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), title and §1–2) and **pilot-scoped** incident runbooks under `docs&#47;ops&#47;runbooks&#47;RUNBOOK_PILOT_INCIDENT_*.md`.

**Non-goals (explicit):**

- This compass **does not** authorize live trading, close any gate, or claim that an incident is generically “resolved.”
- It **does not** replace the [Entry contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), [Failure taxonomy](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md), [Decision authority map](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), or external governance.
- It **does not** import operator-held evidence into git or assert immutable in-repo bundles (see [Gate index `G8`](../specs/MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md) and [Report surface §3.2](../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md#32-interpretation-lock-promotion--readiness-visibility-vs-live-authorization)).

## 2) Non-authorization note

Using this compass **does not** mean:

- `G8` or any gate is closed, passed, or `Verified`;
- the pilot is eligible for the next phase or live-authorized;
- a chosen runbook path is sufficient for compliance or safety.

Readiness or promotion **visibility** (including gate-index or report-surface rows) is **not** live authorization ([`MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) §4 / §7; report surface §3.2).

## 3) How to use this compass

1. **Default safe posture:** If unsure whether trading is allowed, apply [Entry contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria): **ambiguity => `NO_TRADE` / safe stop**.
2. **Match symptoms** to the [§5 contract mapping](#4-entry-contract-5--decision-directions-mapping-anchor) and the **[trigger groups](#5-symptom--trigger-groups-operator-facing)** (§5); open the **primary runbook** from that section or the [runbook index](#6-incident-runbook-index-all-bounded-pilot-pilot-incidents) (§6). If several apply, prioritize **exposure uncertainty** and **session-end / reconciliation** ambiguity first.
3. **Record external evidence** using [L5 pointer contract](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md) classes only — **no** payloads in git ([§7](#7-l5-pointer--evidence-expectations-external-only)).
4. **Use read-only CLIs** to improve visibility, not to prove safety ([§8](#8-read-only-cli--report-hints-scriptsreport_live_sessionspy)); read JSON `disclaimer` fields.
5. **Stop and escalate** when classification stays partial or ambiguous ([§10](#10-escalation-unresolved-and-stop-conditions)).

## 4) Entry Contract §5 — decision directions (mapping anchor)

[§5 Abort / Rollback / NO_TRADE Criteria](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria) requires **no entry** or **immediate abort** when any listed condition holds. The table below links each **contract bullet** to **typical symptom groups** and **orientation** (not a legal interpretation).

| §5 condition (summary) | Typical symptom / situation | Primary triage (this doc §5–§6) |
|---|---|---|
| Go/no-go ≠ `GO_FOR_NEXT_PHASE_ONLY` | Eval not re-`GO`, conditional/no-go | **Not** a pilot incident runbook: stop; re-run go/no-go path per [Live entry](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md) Phase A–B; no new risk |
| Kill switch active | Trading blocked by kill-switch posture | **Not** pilot-incident-specific: follow org kill-switch runbooks (e.g. [`KILL_SWITCH_RUNBOOK.md`](../../risk/KILL_SWITCH_RUNBOOK.md)); remain `NO_TRADE` |
| Policy posture blocked | Cockpit/policy denial | Same as kill-switch / governance visibility; **no** new risk; [Live entry §6](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md#6-abbruchkriterien-vor-oder-während-der-session) |
| Stale state unresolved | State lags, inconsistent snapshots | Often overlaps **reconciliation** or **exchange degraded**; see §5.3 / §5.1 |
| Session-end mismatch unresolved | Closeout vs broker truth disagrees | §5.4 → [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md) |
| Transfer ambiguity unresolved | Transfer status unknown | §5.5 → [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md) |
| Evidence/dependency posture degraded | Telemetry/observability gaps, dependency failures | §5.6 → [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md); venue flakiness may instead be §5.1 |
| Operator cannot determine bounded posture | Cannot answer “are we within pilot envelope?” | **Stop**; use [§8](#8-read-only-cli--report-hints-scriptsreport_live_sessionspy) overview/closeout/lifecycle CLIs; then **reconciliation** or **unexpected exposure** if exposure unclear |
| Any ambiguity whether trading allowed | Any doubt | **§5 rule:** `NO_TRADE` / safe stop — do not “interpret around” ambiguity |

## 5) Symptom / trigger groups (operator-facing)

### 5.1 Exchange / broker path unhealthy

Timeouts, elevated rejects, rate-limit signals, unreliable order/ack state — **not** necessarily a reconciliation bug yet.

→ Primary: [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md).

### 5.2 Exposure or cap surprise

Position or notional **outside** intended pilot envelope, or unexplained exposure growth.

→ Primary: [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md).

### 5.3 Local vs broker truth disagree (general)

Order/fill/position/balance mismatch **during** the session or outside a narrow “session end only” scope.

→ Primary: [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md) (may overlap session-end or transfer).

### 5.4 Session end / closeout disagreement

Registry or local closeout view **disagrees** with broker truth **at session boundary**.

→ Primary: [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md) (also named in §5).

### 5.5 Transfer / funding ambiguity

Withdraw/deposit/internal transfer status unclear.

→ Primary: [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md) (also named in §5).

### 5.6 Observability or dependency degradation

Missing signals, broken pipelines, cannot verify drills/evidence paths — **without** a clear venue outage pattern.

→ Primary: [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md).

### 5.7 Mid-session restart / continuity break

Process or operator continuity interrupted mid-session; need disciplined re-entry to truth.

→ Primary: [Restart mid-session](RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md).

## 6) Incident runbook index (all bounded-pilot pilot incidents)

| Runbook | docs_token (reference) |
|---|---|
| [Exchange degraded](RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md) | `DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED` |
| [Unexpected exposure](RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md) | `DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE` |
| [Reconciliation mismatch](RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md) | `DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH` |
| [Session end mismatch](RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md) | `DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH` |
| [Transfer ambiguity](RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md) | `DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY` |
| [Telemetry degraded](RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md) | `DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED` |
| [Restart mid-session](RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md) | `DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION` |

All indexed **`RUNBOOK_PILOT_INCIDENT_*.md`** runbooks use **`OPERATOR-READY`** in their headers and remain **operator aids** only — **not** live authorization. **This compass** remains **`status: DRAFT`** and **does not** supersede the [Entry contract](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md), governance, or external sign-off.

## 7) L5 pointer / evidence expectations (external only)

After stabilizing posture per the chosen runbook, retain **review-oriented** material **outside** git using [L5 incident / safe-stop pointer contract v0](../specs/MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md):

- **`L5_INCIDENT_SAFE_STOP_SUMMARY_CAPTURE`** — short summary only (no full logs/tickets in-repo).
- **`L5_INCIDENT_RESPONSE_SUPPORTING_BUNDLE`** — opaque handle to externally stored bundles.
- **`L5_SAFE_STOP_DRILL_OR_TABLETOP_BUNDLE`** — preparedness only; do not imply live eligibility.

Required metadata fields and forbidden payloads: see contract §4–5.

## 8) Read-only CLI / report hints (`scripts/report_live_sessions.py`)

These commands are **read-only**; they **do not** unlock live trading or assert gate closure. Prefer `--json` and read embedded disclaimers.

| Use | Command (from repo root) |
|---|---|
| Evidence pointers for one session or latest bounded pilot | `python scripts/report_live_sessions.py --evidence-pointers --session-id <id>` / `--evidence-pointers --latest-bounded-pilot [--json]` |
| Open registry rows (`started`) | `python scripts/report_live_sessions.py --open-sessions [--bounded-pilot-only] [--latest-bounded-pilot-open] [--json]` |
| Readiness + preflight packet + registry focus | `python scripts/report_live_sessions.py --bounded-pilot-readiness-summary [--json]` |
| Closeout / terminal registry signals + derived `abort_triage_hints` (JSON) | `python scripts/report_live_sessions.py --bounded-pilot-closeout-status-summary [--json]` — top-level `abort_triage_hints`; same derivation discipline as lifecycle (read-only; not authorization) |
| Combined operator snapshot | `python scripts/report_live_sessions.py --bounded-pilot-operator-overview [--json]` |
| Compact gate / enablement index block | `python scripts/report_live_sessions.py --bounded-pilot-gate-index [--json]` |
| Frontdoor + canonical subcommand hints | `python scripts/report_live_sessions.py --bounded-pilot-first-live-frontdoor [--json]` |
| Lifecycle / handoff consistency + derived `abort_triage_hints` (JSON) | `python scripts/report_live_sessions.py --bounded-pilot-lifecycle-consistency [--json]` — field `lifecycle_consistency.abort_triage_hints` is read-only navigation only; not authorization |

Full usage lines also appear in the script module docstring at `scripts/report_live_sessions.py`. The lifecycle JSON may include machine-readable `abort_triage_hints` derived strictly from existing lifecycle/closeout signals; see script implementation.

## 9) Failure taxonomy cross-read

When classifying **why** progression must remain blocked, cross-check [Failure taxonomy §4](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md#4-failure-taxonomy-table) (e.g. safety-boundary veto, evidence/provenance gap, operator-visibility failure). The taxonomy is **non-authorizing** ([§7](../specs/MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md#7-non-authorizing-constraint)).

## 10) Escalation, unresolved, and stop conditions

- **Escalate** when exposure is unknown, reconciliation is partial, or §5 conditions remain true after initial steps.
- **Unresolved:** maintain `NO_TRADE` / blocked posture; record **external** L5 pointers; do **not** claim “all clear” from CLI output alone.
- **If unsure:** default to **no new risk** and [Entry contract §5](../specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md#5-abort--rollback--no_trade-criteria); involve governance **outside** this repository as required.

## 11) Related operator entry path

End-to-end bounded-pilot entry (non-incident): [RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md](RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md).

Candidate session flow (context): [RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md](RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md).
