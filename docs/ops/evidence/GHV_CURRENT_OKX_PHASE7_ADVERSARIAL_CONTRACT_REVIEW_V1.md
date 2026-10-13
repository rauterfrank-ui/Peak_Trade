---
docs_token: DOCS_TOKEN_GHV_CURRENT_OKX_PHASE7_ADVERSARIAL_CONTRACT_REVIEW_V1
status: active
scope: Offline adversarial contract review for Phase-7 to Phase-8 entry boundary only
authority_effect: NONE
ghv_authority: NONE
---

# GHV CURRENT OKX Phase-7 Adversarial Contract Review V1

`WORK_PACKAGE=GHV_CURRENT_OKX_PRODUCTIVE_GET_ACTIVATION_READINESS_V1`  
`CLOSURE_WORK_PACKAGE=GHV_CURRENT_OKX_PHASE8_FINAL_PRE_PR_CONTRACT_CLOSURE_V1`  
`REVIEW_SCOPE=PHASE_7_TO_PHASE_8_ENTRY_BOUNDARY`  
`REVIEW_DATE=2026-10-13`  
`REVIEW_BASELINE_ORIGIN_MAIN_SHA=adfa1efdec0e1ef1d288866ae444cb795c1d3e19`  
`REVIEWED_DIFF_BASE=origin&#47;main@d39ff98a92a3f6a6c3878f6fc7bcfac06df9fac3 + Phase-8 closure worktree`  
`REVIEWER_CLASS=CURSOR_AGENT_OFFLINE_CONTRACT_REVIEW (no independent human reviewer)`  
`MANIFEST_PROVENANCE_BODY_SHA256=6b0e2cb559d7804fa908bb8881cb6263a88ba8f778399c54dc014102e4ae7971`

## Trust boundary

- **Trust anchor (independent of manifest self-assertions):** this review document embeds
  `MANIFEST_PROVENANCE_BODY_SHA256` for the canonical manifest body (excluding cross-linked
  digests `review_evidence_sha256` and `reviewed_contract_paths_sha256`). The manifest
  cross-links back via `review_evidence_sha256`; contract bytes bind via `reviewed_contract_paths_sha256`.
- **Not claimed:** PKI/signing; manifest fields alone do not prove integrity; independent human reviewer.
- **Runtime:** `HEAD == origin&#47;main == declared SHA` remains mandatory; review baseline must
  be a git ancestor of current `origin/main` (squash-merge successor allowed when contract bytes
  and provenance anchors still match).

## Scope

This review covers only whether Phase 7 may gate Phase 8 (K1 + productive read-only GET)
for the Full-Core post-submit reconciliation validation runner. It does **not** authorize
POST, productive provider wiring, or trading semantics.

Reviewed contracts (minimum):

- `config/governance/ghv_current_okx_productive_get_activation_readiness_v1/phase7_adversarial_contract_review_v1.json`
- `scripts/ops/run_ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py`
- `src/ops/full_core_live_path_composition_root_v1/ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py`
- `src/ops/full_core_live_path_composition_root_v1/ghv_current_okx_phase7_readiness_adjudication_v1.py`
- `src/ops/full_core_live_path_composition_root_v1/full_core_orchestrated_post_submit_lifecycle_reconciliation_v1.py`
- `src/ops/full_core_live_path_composition_root_v1/productive_read_only_get_transport_v1.py`
- `docs/ops/specs/GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1.md`

## Adversarial scenarios exercised (2026-10-13 closure)

| Scenario | Method | Disposition |
| --- | --- | --- |
| Owner-GO CLI bypass (missing defaults) | Code + pytest | PASS — fail closed before K1/HTTP |
| Partial Owner-GO (K1 missing) | Code + pytest | PASS — STOP_BEFORE_KEYCHAIN_AND_NETWORK |
| Invalid Owner-GO token | Code + pytest | PASS — fail closed |
| Phase 8 without Phase-7 overall PASS | Runner order | PASS — exit 2 |
| Session deadline before K1 entry | Runner + mock deadline | PASS — K1 open count 0 |
| K1 enter within budget, deadline expires before GET | Mock slow K1 `__enter__` + monotonic | PASS — no GET; SESSION_WALLCLOCK_EXCEEDED |
| HTTP timeout during GET | Transport mock `opener.open` | PASS — one attempt, TIMEOUT, no retry |
| Request budget exceeded | Validation session | PASS — fail closed |
| Demo account config flag | Validation session | PASS — DEMO_MODE_DETECTED |
| Transport deadline clamp | Transport + deadline helper | PASS — bounded connect/read |
| K1→HTTP TOCTOU | Deadline assert after K1 `__enter__`, before transport | PASS — no GET after expiry |
| Secret leakage in timeout evidence | JSON report grep | PASS — no credential fields |
| Single session attempt (no auto-restart) | Runner structure + spy | PASS |
| Stale contract hash / scope tamper | phase7 adjudicator tests | PASS — FAIL_CLOSED |
| Business/API code≠0 | Existing validation disposition | PASS — VALIDATION_INCOMPLETE, no retry |

## Adversarial findings (bounded)

| ID | Check | Result |
| --- | --- | --- |
| A1 | Runner `--skip-network` must not import K1 before early return | PASS (lazy import after gate) |
| A1b | No permissive GRANTED CLI defaults on Owner-GO flags | PASS (explicit tokens required) |
| A1c | Phase-8 monotonic session wall-clock budget | PASS (derived 240s; not Session-SSOT) |
| A1d | Transport deadline pass-through and timeout clamp | PASS (`productive_read_only_get_transport_v1.py`) |
| A2 | Hardcoded reproof/review booleans | REMEDIATED (evidence adjudicator) |
| A3 | CLI cannot supply unbound PASS booleans | PASS |
| A4 | Phase 8 without `overall=PASS` | BLOCKED (exit 2) |
| A5 | Runner self-attestation | FAIL if attempted |
| A6 | Contract byte drift | FAIL_CLOSED (`reviewed_contract_paths_sha256`) |
| A7 | Post-squash SHA with unchanged contracts | PASS via ancestor baseline + provenance anchor |
| A8 | Pytest fail/timeout | FAIL_CLOSED |
| A9 | HEAD != origin/main during proof | FAIL_CLOSED |
| A10 | Manifest metadata tamper without review doc | FAIL_CLOSED (provenance anchor mismatch) |

## Limits of guarantee (residual, not defects)

- `HARD_TIMEOUT_GUARANTEE_SCOPE=PHASE8_GATES_AND_HTTP_ONLY`
- In-flight macOS Keychain acquisition is **not** reliably interruptible.
- No full hard-deadline guarantee across Keychain + HTTP.
- Cleanup/wipe on K1 context **normal exit** only; **not** proven if native Keychain blocks forever.

## Open defects

None for Phase-7/Phase-8 boundary after Owner-GO hardening, session deadline, transport scope closure, and targeted regression tests.

## Verdict

`ADVERSARIAL_REVIEW_VERDICT=PASS`

Static evidence only — not runner-generated. Update this document and manifest provenance
anchors when reviewed contract bytes change.
