---
docs_token: DOCS_TOKEN_RUNBOOK_STARTED_BOUNDED_PILOT_SESSION_REVIEW_V0
status: draft
scope: docs-only, non-authorizing started bounded-pilot session review runbook
last_updated: 2026-04-27
---

# Runbook: Started Bounded-Pilot Session Review V0

## 1. Purpose

This runbook gives an operator a **safe, read-only** way to inspect **started** bounded-pilot session records already present under the live-sessions registry.

It is for **observation and review** only. It is **not** live authorization, **not** closeout approval, **not** gate passage, **not** strategy or autonomy readiness, **not** signoff or external authority completion, and it does not substitute governance or the Session Review Pack contract.

## 2. Non-Goals

This runbook does **not** instruct anyone to:

- edit `reports&#47;experiments&#47;live_sessions&#47;*.json` (registry JSONs);
- edit `out&#47;ops&#47;**` or other execution / export trees;
- manually close, patch, or “fix” `started` sessions;
- create or backfill `execution_events.jsonl` under `out&#47;ops`;
- change report code, workflows, configs, or runtime behavior;
- run paper, testnet, live, or new bounded-pilot execution;
- infer PnL, live readiness, closeout sufficiency, or that any gate has passed;
- use JSON output as proof of operator approval, system health, or trading permission.

## 3. Read-Only Commands

Run from the repository root:

```bash
uv run python scripts/report_live_sessions.py --open-sessions --bounded-pilot-only --json
uv run python scripts/report_live_sessions.py --bounded-pilot-closeout-status-summary --json
uv run python scripts/report_live_sessions.py --bounded-pilot-lifecycle-consistency --json
```

- **`--open-sessions --bounded-pilot-only --json`:** lists `started` bounded-pilot rows with closeout and pointer hints (per implementation). The top-level list is under the `sessions` key.
- **`--bounded-pilot-closeout-status-summary --json`:** read-only **closeout** / terminal-status *signals* in the read model (e.g. `closeout_signal_summary`); read embedded `disclaimer` and operator notes. **Not** a closeout approval.
- **`--bounded-pilot-lifecycle-consistency --json`:** read-only **lifecycle** consistency block; read `lifecycle_consistency_summary` and any mismatch hints. **Not** a gate or readiness verdict.

## 4. Interpreting `execution_events_session_jsonl.present`

In each open-session row, `execution_events_session_jsonl` includes an expected path and `present: true` or `present: false`.

- **`present: true`** — a file exists at the resolved scoped path (repo-relative: `out&#47;ops&#47;execution_events&#47;sessions&#47;<session_id>&#47;execution_events.jsonl`) in the **local workspace** where you ran the report. It does **not** prove the strategy is sound, the session is safe to touch, PnL, or that any external authority is satisfied. It is a **pointer and presence** bit only.
- **`present: false`** — the expected scoped `execution_events.jsonl` is missing or not readable. That is **not** a directive to create or hand-edit `out&#47;ops` (or the registry) from this runbook. Do not mutate historical artifacts to “fix” a report line.

## 5. Warnings (Do Not)

- **Do not** hand-edit registry JSONs or `out&#47;ops` artifacts to satisfy curiosity or to change report output; preserve historical and evidence posture per governance and existing incident / abort runbooks.
- **Do not** treat JSON as **live authorization**, **closeout approval**, **gate passage**, or **readiness** for real-money operation.
- **Do not** infer PnL, profitability, or that execution was correct from registry or pointer fields alone.
- **Do not** use this runbook to perform manual **session closeout**; closing or reconciling live/bounded work product must follow the appropriate operational path outside this document.

## 6. What This Read Model Does *Not* Imply

Output from these flags remains **read-only, non-authorizing**:

- **Not** live authorization, **not** signoff, **not** go-live or execution enablement;
- **Not** closeout approval or statement that a session may be considered finished;
- **Not** passage of any automated gate, risk **kill switch** disarm, or **Master V2** / **Double Play** handoff;
- **Not** **strategy** readiness, **autonomy** readiness, or “external authority completion”;
- **Not** a substitute for the Session Review Pack or evidence contracts where those apply.

## 7. Related Documents (pointers)

- [Session Review Pack V0 — contract](../specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md) — `docs/ops/specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md`
- [Session Review Pack V0 — invoke (read-only) runbook](RUNBOOK_SESSION_REVIEW_PACK_INVOKE_V0.md) — `docs/ops/runbooks/RUNBOOK_SESSION_REVIEW_PACK_INVOKE_V0.md`
- [Paper / Testnet Readiness Gap Map V0](../specs/MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0.md) — `docs/ops/specs/MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0.md`
- [Operator / audit flat path index V0](../specs/MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md) — `docs/ops/specs/MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md`

## 8. Contract / characterization tests (implementation)

- `tests/ops/test_report_live_sessions_started_bounded_pilot_open_sessions_v0.py` — `tests&#47;ops&#47;test_report_live_sessions_started_bounded_pilot_open_sessions_v0.py`
- `tests/ops/test_report_live_sessions_lifecycle_consistency.py` — `tests&#47;ops&#47;test_report_live_sessions_lifecycle_consistency.py`

## 9. Validation (for doc changes)

From the repository root:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
uv run pytest tests/ops/test_report_live_sessions_started_bounded_pilot_open_sessions_v0.py tests/ops/test_report_live_sessions_lifecycle_consistency.py -q
```
