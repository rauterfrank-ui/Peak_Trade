# RUNBOOK — Session Review Pack V0 (read-only) — Invoke

status: DOCS-ONLY / NON-AUTHORIZING
scope: Operator discovery for static Session Review Pack V0 JSON from `report_live_sessions`
last_updated: 2026-04-27
owner: Peak_Trade
docs_token: DOCS_TOKEN_RUNBOOK_SESSION_REVIEW_PACK_INVOKE_V0

## 1. Executive Summary

This runbook documents how to run the **read-only** Session Review Pack V0 path on `scripts/report_live_sessions.py` so operators can print the **static** JSON pack shape. It is **not** a trading instruction, not a go-live, not signoff, and not a substitute for the Session Review Pack contract. **V0** does not read, query, or bind real session registry data; output fields stay null or empty until a future implementation changes the script.

## 2. When to Use

- You need a **machine-readable** `session_review_pack` payload for post-hoc review, audit notes, or tooling that consumes JSON **without** expecting populated session or reference fields yet.
- You want a **smoke** check that the CLI mode is available and that stdout is **only** JSON (using `--log-level ERROR` keeps INFO logs off stderr for clean capture).

Do **not** use this as evidence of live permission, execution readiness, gate pass, or operator approval. See the contract: [`MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md`](../specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md).

## 3. Command

From the repository root:

```bash
uv run python scripts/report_live_sessions.py --session-review-pack --json --log-level ERROR
```

- `scripts/report_live_sessions.py` — report CLI; v0 pack mode is static JSON with **no** registry I/O and **no** `--registry-base` in this path.
- `--log-level ERROR` — suppresses INFO on stderr so **stdout** remains parseable as JSON in typical capture setups.

## 4. Expected Output Shape

- **Content type:** Single JSON object on **stdout** (pretty-printed with sorted keys in current implementation), exit code `0`.
- **Contract identity:** `contract` is `report_live_sessions.session_review_pack_v0` and `schema_version` is the literal `master_v2&#47;session_review_pack&#47;v0` (per implementation).
- **Non-authorization flags:** `non_authorizing` is `true`; `authority_boundary` has `live_authorization`, `signoff_complete`, `gate_passed`, `autonomy_ready`, and `strategy_ready` all `false`.
- **Session and references:** `session.*` and most `references.*` are `null` or empty; `missing_fields` lists unpopulated contract slots. `source_contract` points at `docs/ops/specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md`.
- **Stability note:** The pinned shape is also asserted in `tests/ops/test_session_review_pack_report_contracts_v0.py`.

## 5. What This Does Not Mean

This document and the JSON it describes **do not**:

- change runtime, registry, execution, or risk behavior;
- read or bind **real** session or production data in **v0** (unless a **later** change to `scripts/report_live_sessions.py` explicitly does so and documents it in the same contract);
- grant or imply **live** authorization, **signoff**, **gate** pass, **approval**, **strategy** readiness, or **autonomy** readiness;
- override Master V2 / Double Play contracts, Live Gates, dashboard or cockpit **authority** boundaries, or the Evidence / Navigation / Registry specs listed below.

## 6. Validation / Smoke Check

- Run the command in §3; confirm exit code `0` and `jq` (if installed) accepts stdout: e.g. `... | python -m json.tool` / `jq .`.
- For docs changes in pull requests, run from repo root:

```bash
python3 scripts/ops/validate_docs_token_policy.py --changed
bash scripts/ops/verify_docs_reference_targets.sh
```

(Use your team’s default scope flags, e.g. the token policy’s `--base` with your default remote branch, if you only validate diffs.)

## 7. Related References

- [Session Review Pack V0 contract](../specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md)
- [Open-first triage checklist](../specs/MASTER_V2_OPERATOR_TRIAGE_OPEN_FIRST_CHECKLIST_V0.md)
- [Dashboard, cockpit, observer surface inventory](../specs/MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0.md)
- [Evidence packet and index navigation map](../specs/MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md)
- [KB / registry / evidence taxonomy](../specs/MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md)

Contract tests (implementation detail): `tests/ops/test_session_review_pack_report_contracts_v0.py`.
