# Shadow-247 Governance Charter v0

## Status and scope

- **Shadow-247 / Paper-Shadow-247 readiness:** `not_ready`.
- **This document:** governance and activation-path **planning only**. It is **non-authorizing**.
- **It does not:** approve bounded Shadow smoke, 24h Shadow, 24/7 Shadow, daemon operation, scheduler execution, Paper runtime, Testnet, Live, broker, exchange, credentials, or order submission.
- **Current operational posture:** **STOP_IDLE** — no run is authorized by this file or by its mere existence in the repository.

**Companion (blocked preflight contract, field-level):** [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) — remains **BLOCKED** unless a **separate**, explicitly reviewed governance update says otherwise.

This charter **does not replace** the preflight contract, ops TOMLs, scheduler config, or tests. It **points to** them and records what **must still be decided** before any future stage can be considered.

**24h bounded Shadow dry-run candidate — evidence semantics (non-authorizing):** A completed **governed** run using the wrapper’s **24h candidate tier** (duration-capped local simulation; dry-run only; no network, broker, or **order submission**; evidence under a fresh `/tmp/peak_trade_…` root such as emitted manifest/steps) produces **documentary machine-readable evidence** only. That evidence may be cited as **input material** for future readiness or gap reviews; it **does not** satisfy the blocked [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) (status remains **BLOCKED**), **does not** move Shadow-247 / Paper-Shadow-247 readiness away from **`not_ready`**, **does not** authorize Testnet, Live, broker or exchange paths, credentials, daemon operation, or scheduler execution, and is **not** a substitute for an external operator approval record. Canonical gate definitions remain in **this repository**; out-of-repo narrative alone does not clear gates.

---

## Boundary statements (non-negotiable semantics)

| Surface | Meaning |
|--------|---------|
| **Docs ≠ Approval** | No document in-repo (including this charter) grants execution or promotion. |
| **Config ≠ Approval** | `paper_shadow_247_preflight.toml` and `shadow_247_futures_wrapper_skeleton.toml` are metadata/default-off planning; they do not authorize runs. |
| **Scheduler job ≠ Approval** | Entries in `config/scheduler/jobs.toml` are visibility/shape; `enabled` or `readonly` does not imply go-ahead (see preflight contract). |
| **Evidence ≠ Approval** | Logs, JSON, CI artifacts, or dashboards do not clear Live/Testnet/Shadow daemon paths. |
| **Dashboard ≠ Approval** | WebUI/read models are observability only unless a **separate** gate explicitly says otherwise. |
| **AI ≠ Authority** | No AI/LLM/coding agent is execution, risk, or governance authority. |
| **Signal ≠ Trade** | Strategy signals and forward tests are not order or Live authority. |

---

## Canonical references (read before any future stage)

- **Preflight contract (blocked):** [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md)
- **Preflight metadata TOML:** `config/ops/paper_shadow_247_preflight.toml` — `activation_authorized`, `daemon_activation_authorized`, `scheduler_execution_authorized`, `shadow_runtime_authorized`, etc. must remain **false** until an explicit operator-governed update.
- **Futures wrapper skeleton TOML:** `config/ops/shadow_247_futures_wrapper_skeleton.toml` — default-off (`enabled`, `armed`, `wrapper_daemon_start_allowed`, capability flags false); future gates (`final_operator_confirmation_gate_required`, …) document **requirements**, not satisfied approval.
- **Scheduler jobs:** `config/scheduler/jobs.toml` — preflight reporter vs placeholder vs quarantined paper-runtime jobs (see contract and tests).
- **Stop snapshot (read-only):** `scripts/ops/snapshot_operator_stop_signals.py` — `CONTRACT_ID` / `PT_STOP_KEYS`; does not authorize trading.
- **Wrapper skeleton (fail-closed):** `scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py`
  - **Standard bounded Shadow dry-run cap (default):** 10 minutes / 600 simulated steps — unchanged.
  - **Extended tier (governed, default-off):** optional CLI path up to 60 minutes / 3600 steps only with `--extended-bounded-shadow-validation` plus a **distinct** extended confirm token (separate from the base wrapper token). Still local dry-run Shadow only; still **non-authorizing**; does **not** satisfy Stage 3 or any Live/Testnet/broker/exchange/order path.
  - **24h candidate tier (governed, default-off):** optional CLI path up to 1440 minutes / 86400 steps only with `--candidate-24h-bounded-shadow-validation` plus a **distinct** `--candidate-24h-confirm-token` (separate from base and extended tokens; mutually exclusive with the extended flag). Preparation for bounded dry-run **candidate** validation only — **non-authorizing**, requires separate operator GO for any execution, does **not** imply 24/7 readiness or Stage 3+.
- **Static drift tests (non-authorizing):** e.g. `tests/ops/test_shadow_247_futures_config_job_skeleton_v0.py`, `tests/ops/test_offline_crosslink_invariant_contract_v0.py`, `tests/ops/test_shadow_247_futures_start_wrapper_skeleton_v0.py`

---

## Activation ladder

Each stage requires **operator approval** recorded **outside** this document (e.g. ticket, LB-APR-style artifact, or other **explicit** org process). **Implied approval is invalid.**

### Stage 0 — STOP_IDLE / blocked (current)

| Dimension | Requirement |
|-----------|-------------|
| **Entry** | Default; matches preflight **BLOCKED** and TOML all-false authorization flags. |
| **Forbidden** | Any Shadow/Paper-247 **run**, daemon, bounded smoke, Testnet, Live, broker, exchange, orders, credential use for trading. |
| **Evidence** | N/A (no run). |
| **Stop** | N/A. |
| **Operator approval** | None for runs; **STOP** remains until Stage 1+ explicitly approved for **planning only**. |

### Stage 1 — Governance charter absorbed, **no run**

| Dimension | Requirement |
|-----------|-------------|
| **Entry** | Org acknowledges this charter + preflight contract; activation path and owners documented; **still zero runs**. |
| **Forbidden** | Same as Stage 0 for any executable path. |
| **Evidence** | Charter + contract reviewed; decision record that Stage 1 is satisfied **without** conflating review with run approval. |
| **Stop** | Revert to Stage 0 if ambiguity remains on authority boundaries. |
| **Operator approval** | **Required** to exit Stage 0 for planning discipline only — **not** a run approval. |

### Stage 2 — Bounded dry Shadow **planning only** (no execution)

| Dimension | Requirement |
|-----------|-------------|
| **Entry** | Stage 1 complete; written plan: duration caps, mode (dry/bounded), abort criteria, evidence locations, **no-order** posture; Futures/perp scope per preflight §3/§3b if applicable. |
| **Forbidden** | Actual smoke execution, daemon, Testnet, Live, real broker/exchange, order submission. |
| **Evidence** | Plan document + checklists; config snapshot **as planning**; **no** runtime evidence claims. |
| **Stop** | Any drift from default-off TOML or blocked contract without a new governed change. |
| **Operator approval** | **Required** for the **plan** — explicitly **not** execution approval. |

### Stage 3 — Bounded Shadow smoke (**future-only**, explicit approval per event)

| Dimension | Requirement |
|-----------|-------------|
| **Entry** | Stage 2 plan approved; **separate explicit go** for **one** bounded attempt; kill/stop path rehearsed; evidence and closeout owners named. |
| **Forbidden** | 24h or 24/7 operation; expanding scope without new approval; Testnet/Live/broker unless future charter amend. |
| **Evidence** | Events, logs, heartbeats/stale rules as defined in plan; config snapshot; operator decision record per run; closeout/postrun analysis **as specified before start**. |
| **Stop** | Emergency stop; stale process; heartbeat failure; unexpected orders/fills; network/API degradation; **fail-closed** behavior per wrapper/preflight/runbooks. |
| **Operator approval** | **Required per run** — no standing approval. |

### Stage 4 — 24h Shadow **candidate** (future)

| Dimension | Requirement |
|-----------|-------------|
| **Entry** | Repeated successful **bounded** runs; on-call; incident path; SLOs for heartbeat/stale; **separate** governance package. |
| **Forbidden** | Treating 24h as “soft launch” Live; credential expansion without gate. |
| **Evidence** | 24h evidence pack; postrun sign-off; incident replay capability. |
| **Stop** | Same as Stage 3 + escalation for sustained degradation. |
| **Operator approval** | **Explicit** promotion decision — not implied by Stage 3 success alone. |

### Stage 5 — 24/7 Shadow **candidate** (future)

| Dimension | Requirement |
|-----------|-------------|
| **Entry** | Daemon lifecycle defined (start/stop/upgrade/orphan recovery); 24h path stable; security and capacity reviewed; **heavyweight** governance sign-off. |
| **Forbidden** | Permanent operation without runbooked maintenance and STOP semantics. |
| **Evidence** | Long-horizon logs/metrics; audit trail; periodic re-certification process (org-defined). |
| **Stop** | Org-wide STOP / incident commander per runbooks. |
| **Operator approval** | **Highest tier** — explicit 24/7 charter amendment; not derivable from tests or CI. |

---

## Preconditions before **any** bounded Shadow smoke (Stage 3)

- **Explicit operator decision record** for **that** attempt (scope, timebox, rollback).
- **Duration and scope** caps fixed in writing; **no-order** / dry posture as applicable.
- **Instrument / universe** consistent with Futures/perp planning boundary in preflight contract if derivatives context applies.
- **Stop command availability** understood — see `paper_shadow_247_preflight.toml` `stop_command` / `emergency_stop_command` (paths only; execution is operator responsibility when and if ever allowed).
- **Heartbeat / stale-process handling** defined operationally (not merely “tests pass”).
- **Evidence output paths** and retention agreed.
- **Closeout / postrun analysis** owner and checklist defined **before** start.
- **No** Live / Testnet / broker / exchange / order permissions unless a **future** governed layer explicitly permits (currently default **denied** in TOMLs).

---

## Preconditions before **24h** Shadow (Stage 4)

- Repeatable bounded runs with **documented** abort outcomes.
- Heartbeat/stale semantics **operationally** owned, not only config-coded.
- On-call / incident alignment with `incident_stop_freeze_rollback` and kill-switch policy as applicable.
- Futures/perp evidence gaps (preflight §3b) addressed **if** Futures Shadow is in scope.

---

## Preconditions before **24/7** Shadow (Stage 5)

- Daemon model: orphan detection, restart policy, resource limits, security boundary.
- Long-term evidence, patching, and **re-charter** cadence defined.
- **No** implication that CI or static tests substitute for org sign-off.

---

## Stop and incident semantics (planning requirements)

Organizational clarity (not just repo flags) is required for:

- **Emergency stop** — who invokes, what tools (`snapshot_operator_stop_signals`, kill switch, env flags).
- **Stale process** — definition of “stuck” vs “slow”; escalation.
- **Heartbeat failure** — measurement and timeout policy.
- **Missing evidence** — treat as **failure**, not **skip**.
- **Unexpected fills or orders** — in no-order paths, **immediate STOP** and incident posture.
- **Network/API degradation** — fail-closed vs degrade rules **per org**, aligned with default-off repo posture.
- **Fail-closed** — default remains **deny/exit** (wrapper skeleton philosophy); **no** silent continuation.

---

## Evidence requirements (categories)

For any **future** authorized run stage, the org should specify how these are satisfied; this list is **not** approval:

- **Events** — structured run/event stream where applicable.
- **Logs** — correlation IDs, run id, time bounds.
- **Fills** — if any execution path exists in scope; **unexpected fills** = incident.
- **Metrics / heartbeats** — as defined for that stage.
- **Config snapshot** — TOML/job list relevant to the attempt (read-only capture).
- **Operator decision record** — per Stage 3+.
- **Closeout report** — end-state, anomalies, sign-off.
- **Postrun analysis** — retrospective against plan; feeds **next** approval only.

---

## Explicit next-state

- **Repository and org state after merging this document:** **STOP_IDLE** for Shadow-247 execution. Readiness remains **`not_ready`**.
- **Next implementation** (config, code, scheduler enablement, or run) requires a **separately approved** slice; **not** implied by this charter PR.
- **No run** is authorized by this document.

---

## Document control

- **Canonical owner:** ops governance / paper-shadow-247 readiness (align with `canonical_owner` in `paper_shadow_247_preflight.toml` for process ownership).
- **Version:** v0 — amend only via reviewed docs PR; do not fork parallel “charter” documents.
