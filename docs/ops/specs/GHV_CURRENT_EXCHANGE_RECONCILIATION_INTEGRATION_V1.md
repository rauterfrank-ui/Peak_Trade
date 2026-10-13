---
docs_token: DOCS_TOKEN_GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1
status: active
scope: Full-Core exchange reconciliation (offline stub integration)
capability: GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-10-13
---

# GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1

Offline-only Full-Core exchange reconciliation after submit boundary. `GHV_AUTHORITY=NONE`.

## Boundary

After: Full-Core capital guard join, atomic reservation, submit transport boundary (simulated offline).

Before: any productive private GET or live POST.

## Provider

`RECONCILIATION_PROVIDER=OFFLINE_STUB` for fixture-only runs.

`RECONCILIATION_PROVIDER=OKX_EEA_READ_ONLY_GET_V1` via
`full_core_exchange_reconciliation_okx_read_only_provider_v1.py` uses injected
`FullCoreFreshPretradeGetTransportV1` only (tests and offline reproof). No new HTTP
client. `PRODUCTION_PROVIDER_WIRING=NOT_AUTHORIZED` until scoped Owner-GO.

## Owners

- Identity + FSM: `full_core_exchange_reconciliation_v1.py`
- Offline fixtures: `full_core_exchange_reconciliation_offline_provider_v1.py`
- Handoff: `full_core_exchange_reconciliation_integration_v1.py`
- Post-submit lifecycle join: `full_core_post_submit_exchange_reconciliation_lifecycle_join_v1.py`
  (Cap 11.1 / §11.2.1.DW → `LocalSubmitOutcome` → reconciliation pipeline → atomic recovery)
- Orchestration entry: `full_core_orchestrated_post_submit_lifecycle_reconciliation_v1.py`
- Governed Cycle Host wiring (offline-only, ContextVar-gated): `full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1.py`
- Productive GET validation (explicit session): `ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py`
- GHV stages: `ghv_full_core_exchange_reconciliation_observability_v1.py`

## Invariants

`UNKNOWN_REMAINS_UNKNOWN`, no automatic resubmit, no automatic flatten, `POST_COUNT=0`, reconciliation does not reauthorize Owner-GO.

OKX adapter records `identity_conflicts` on the snapshot when relevant contradictory
venue identity is observed (same `clOrdId`, mismatched `instId`/`ordId`). Adjudication
fail-closes before terminal reconciliation; contradictory evidence must not be silently
dropped.

## Post-COMPLETED hook evidence (Cycle Host)

S5 `COMPLETED` ledger state means the governed cycle reached `PRE_EXTERNAL_EFFECT` or a
valid non-trade terminal — **not** post-submit reconciliation success. Optional lifecycle
wiring observations are persisted via append-style supplement on
`governed_cycle_orchestrator_ledger_v1.json` (`POST_COMPLETED_HOOK_EVIDENCE_V1`).
`POST_SUBMIT_RECONCILIATION_SUCCEEDED=false` is always recorded when the supplement is
written. Atomic One-Shot durable state remains authoritative for submission attempts;
lifecycle fields are observational only and do not authorize POST.

## Phase-7 readiness (productive GET activation)

Phase 7 is evidence-bound before Phase 8 (K1 + scoped read-only GET):

- Offline reproof: frozen pytest owners (Full-Core recon chain + orchestration + validation tests) via `scripts/pt`, with `HEAD == origin&#47;main == declared SHA`.
- Adversarial review: static manifest `config/governance/ghv_current_okx_productive_get_activation_readiness_v1/phase7_adversarial_contract_review_v1.json` plus `docs/ops/evidence/GHV_CURRENT_OKX_PHASE7_ADVERSARIAL_CONTRACT_REVIEW_V1.md` (not runner-generated).
- Review baseline: `review_baseline_origin_main_sha` must be a git ancestor of current `origin/main` (squash-merge successor allowed). Ancestor alone is insufficient — contract bytes, review scope, open defects, and provenance anchors must still match.
- Manifest integrity: substantive manifest fields are bound via `MANIFEST_PROVENANCE_BODY_SHA256` in the review document (trust anchor). Cross-linked digests (`review_evidence_sha256`, `reviewed_contract_paths_sha256`) are verified independently. The manifest entry in `reviewed_contract_paths_sha256` uses the provenance-body digest (not raw file bytes) to avoid self-referential hash cycles.
- No hardcoded `offline_reproof_pass` / `adversarial_review_pass` booleans.

`--skip-network` remains network-free (no K1, no HTTP). Phase-7 PASS is not productive GET authorization.

## Phase-8 authorization and session boundary

- CLI Owner-GO flags have **no GRANTED defaults**. Missing, partial, or invalid tokens fail closed before K1/HTTP.
- Network path requires explicit `--k1-session-owner-go` matching `K1_SESSION_OWNER_GO`.
- **Derived session ceiling (not a historical Session-SSOT constant):**  
  `VALIDATION_SESSION_MONOTONIC_WALLCLOCK_SECONDS = MAX_VALIDATION_GET_REQUESTS × (CONNECT_TIMEOUT_SECONDS + VALIDATION_TIMEOUT_SECONDS)`  
  At CURRENT constants: **8 × (10 + 20) = 240 seconds** worst-case charged-GET budget.
- Phase-8 validation performs **two** GET probes (`account/config`, `orders-pending`). The request **upper bound** remains **8** (`MAX_VALIDATION_GET_REQUESTS`).
- `HARD_TIMEOUT_GUARANTEE_SCOPE=PHASE8_GATES_AND_HTTP_ONLY`: monotonic deadline gates entry and HTTP; connect/read clamp to remaining budget; **no retry** per GET.
- **Residual limit:** in-flight macOS Keychain acquisition is **not** reliably interruptible; no full hard-deadline guarantee; **no** guaranteed cleanup if a native Keychain call blocks indefinitely. Normal K1 context-manager exit retains existing wipe semantics.
