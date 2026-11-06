---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_29P_CHAIN_BASELINE_CONTRACT_V1
status: active
scope: Merge-stable execution identity and authorized Cap-24 persisted repository baseline for CURRENT_PRODUCTIVE 29P chain; fail-closed; no network
capability: FULL_CORE_CURRENT_PRODUCTIVE_29P_CHAIN_BASELINE_CONTRACT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-22
---

# Full Core Current Productive 29P Chain Baseline Contract V1

Derived spec. Non-SSOT. Unifies per-slice origin-main drift between Cap-24 writer,
Cap-2.4 provenance handoff, 29P common-epoch handoff, and EEA adapter.

```text
OWNER=current_productive_29p_chain_baseline_contract_v1
RUNTIME_INTEGRITY=current_productive_29p_chain_runtime_integrity.v1
EXECUTION_IDENTITY=declared_origin_main_sha == git_rev_parse_origin_main AND HEAD == origin/main
OPTIONAL=PROTECTED_CHAIN_SURFACE_DRIFT (git diff origin/main on closed path set)
PERSISTED_PROVENANCE=HISTORICAL_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS (closed set; no per-merge growth)
FRESH_PERSIST=repository_sha must equal validated execution identity unless historical bind
RESOLVER=resolve_cap24_persisted_repository_sha_v1
COMMON_EPOCH_CAP24_JOIN=repository_sha from manifest or selection (not a static slice pin)
POST_MERGE_CODE_PIN=NOT_REQUIRED (merge-stable trusted-ref binding)
ATLAS_AUTHORITY=NONE
```

Historical persisted Cap-2.1–2.3 snapshots may retain earlier authorized repository
baselines (`8379a278…`, `e539620…`) without rewriting provenance. New productive
writes bind `repository_sha` to the validated execution identity at publish time.
