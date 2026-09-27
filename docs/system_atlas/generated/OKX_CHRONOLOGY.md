<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# OKX Chronology

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

CURRENT venue chronology from modeled Atlas records. Historical domain census payloads were eradicated (legacy-only).

GIT_IS_SHALLOW=false

OKX_CURRENT_TREE_CENSUS_COMPLETE=true

| id | when | what | epistemic | evidence |
| --- | --- | --- | --- | --- |
| OKX_CHRONO:first_token | 2026-02-16 96d8195ac (#1424) | First origin/main commit whose diff contains token OKX (P99 guarded launcher docs) | STATUS=ADJUDICATED | git log origin/main --reverse -S OKX |
| OKX_CHRONO:p108_mocks_adapter | 2026-02-16 5c5889997 (#1436) | First OKX-named implementation; mocks-only execution adapter (still present) | STATUS=ADJUDICATED | src/execution/adapters/providers/okx_v1.py |
| OKX_CHRONO:eea_xperp_contracts | 2026-06-26 8457850cb (#4587) | OKX Europe X-Perp offline contracts; eea.okx.com / wss hosts enter config | STATUS=ADJUDICATED | src/ops/aws_shadow_paper_testnet_okx_europe_compatibility_contract_v0.py |
| OKX_CHRONO:kraken_off_okx_staged | 2026-06-27 da9b257bf (#4616) | Kraken deactivated; disabled OKX target staged | STATUS=FORENSIC_RAW | git log -S eea.okx.com |
| OKX_CHRONO:public_md_ingest | 2026-07-01 713db77d0 (#4726) | OKX public futures market-data ingest; first uly field-token in Python ingest path | STATUS=ADJUDICATED | scripts/ops/ingest_okx_futures_public_market_data_canonical_dataset_staging_v1.py |
| OKX_CHRONO:audit_2026_07_17 | 2026-07-17 f5114401f (#5298); document date matches git introduction | Read-only OKX integration audit claimed signed private REST absent | STATUS=FORENSIC_RAW | docs/audits/OKX_INTEGRATION_READ_ONLY_AUDIT_2026-07-17.md |
| OKX_CHRONO:dashboard_intrabar | 2026-07-25 6f38df4d8 (#5548) | Dashboard OKX futures intrabar OHLCV path; not proven as a live WebSocket session | STATUS=FORENSIC_RAW | src/ops/okx_public_market_data_client_v1.py |
| OKX_CHRONO:cap21_uly_base | 2026-08-02 02095305f Cap 2.1 GFU | _extract_base_quote uses uly for BASE only; quote never from uly (original behavior) | STATUS=ADJUDICATED | src/ops/governed_futures_universe_producer_v1/eligibility_v1.py |
| OKX_CHRONO:hmac_signer | 2026-08-08 35519be26 (#5830) | sign_okx_request_v1 HMAC primitive (K1 venue-auth; historical K2 execute client removed) | STATUS=FORENSIC_RAW | src/ops/full_core_live_path_composition_root_v1/checkout_independent_credential_okx_venue_auth_headers_v1.py |
| OKX_CHRONO:okx_named_deletions | census after unshallow | origin/main has zero deleted OKX-named paths (git log --diff-filter=D -- *okx*) | STATUS=ADJUDICATED | docs/system_atlas/census/okx_current_tree.yaml |
| OKX_CHRONO:shallow_artifact_corrected | 2026-08-06 ec0e0272d was local shallow root, not first OKX introduction | Prior Atlas chronology that treated ec0e0272d as first OKX bulk-add is superseded | STATUS=ADJUDICATED | git fetch --unshallow; earliest commit 78979ed413 2025-12-02 |


