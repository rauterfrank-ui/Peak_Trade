---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_29P_CHAIN_BASELINE_CONTRACT_V1
status: active
scope: Unified origin-main and authorized Cap-24 persisted repository baseline for CURRENT_PRODUCTIVE 29P chain; fail-closed; no network
capability: FULL_CORE_CURRENT_PRODUCTIVE_29P_CHAIN_BASELINE_CONTRACT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-22
---

# Full Core Current Productive 29P Chain Baseline Contract V1

Derived spec. Non-SSOT. Closes per-slice `EXPECTED_ORIGIN_MAIN_SHA` drift
between Cap-24 writer (#6738/#6739), Cap-2.4 provenance handoff (#6737),
and 29P common-epoch handoff (#6736).

```text
OWNER=current_productive_29p_chain_baseline_contract_v1
CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA=8379a278517b23240ca1cdad02fe041b7d618874
AUTHORIZED_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS=8379a278…,e539620…
RESOLVER=resolve_cap24_persisted_repository_sha_v1
COMMON_EPOCH_CAP24_JOIN=repository_sha from manifest or selection (not slice origin_main_sha)
POST_MERGE_REPIN_SURFACE=SINGLE_CONSTANT_ONLY
ATLAS_AUTHORITY=NONE
```

Update ``CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA`` only on
dependency-ordered chain completion PRs. Persisted Cap-2.1–2.3 snapshots
may retain earlier authorized repository baselines until republished.
