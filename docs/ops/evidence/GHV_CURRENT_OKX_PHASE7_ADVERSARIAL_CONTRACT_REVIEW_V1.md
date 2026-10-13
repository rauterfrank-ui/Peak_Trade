---
docs_token: DOCS_TOKEN_GHV_CURRENT_OKX_PHASE7_ADVERSARIAL_CONTRACT_REVIEW_V1
status: active
scope: Offline adversarial contract review for Phase-7 to Phase-8 entry boundary only
authority_effect: NONE
ghv_authority: NONE
---

# GHV CURRENT OKX Phase-7 Adversarial Contract Review V1

`WORK_PACKAGE=GHV_CURRENT_OKX_PRODUCTIVE_GET_ACTIVATION_READINESS_V1`  
`REVIEW_SCOPE=PHASE_7_TO_PHASE_8_ENTRY_BOUNDARY`  
`REVIEW_BASELINE_ORIGIN_MAIN_SHA=adfa1efdec0e1ef1d288866ae444cb795c1d3e19`  
`MANIFEST_PROVENANCE_BODY_SHA256=de612b7ce4d09e04dcf45ae1f537a39b4ecddc78a8c7e175484dc650c5347e95`

## Trust boundary

- **Trust anchor (independent of manifest self-assertions):** this review document embeds
  `MANIFEST_PROVENANCE_BODY_SHA256` for the canonical manifest body (excluding cross-linked
  digests `review_evidence_sha256` and `reviewed_contract_paths_sha256`). The manifest
  cross-links back via `review_evidence_sha256`; contract bytes bind via `reviewed_contract_paths_sha256`.
- **Not claimed:** PKI/signing; manifest fields alone do not prove integrity.
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
- `docs/ops/specs/GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1.md`

## Adversarial findings (bounded)

| ID | Check | Result |
| --- | --- | --- |
| A1 | Runner `--skip-network` must not import K1 before early return | PASS (lazy import after gate) |
| A2 | Hardcoded reproof/review booleans | REMEDIATED (evidence adjudicator) |
| A3 | CLI cannot supply unbound PASS booleans | PASS |
| A4 | Phase 8 without `overall=PASS` | BLOCKED (exit 2) |
| A5 | Runner self-attestation | FAIL if attempted |
| A6 | Contract byte drift | FAIL_CLOSED (`reviewed_contract_paths_sha256`) |
| A7 | Post-squash SHA with unchanged contracts | PASS via ancestor baseline + provenance anchor |
| A8 | Pytest fail/timeout | FAIL_CLOSED |
| A9 | HEAD != origin/main during proof | FAIL_CLOSED |
| A10 | Manifest metadata tamper without review doc | FAIL_CLOSED (provenance anchor mismatch) |

## Open defects

None for Phase-7/Phase-8 boundary after post-squash and manifest-integrity remediation.

## Verdict

`ADVERSARIAL_REVIEW_VERDICT=PASS`

Static evidence only — not runner-generated. Update this document and manifest provenance
anchors when reviewed contract bytes change.
