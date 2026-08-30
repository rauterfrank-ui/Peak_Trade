<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Data Lineage Map

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

| id | value | origin | raw_field | unit | current_path | epistemic |
| --- | --- | --- | --- | --- | --- | --- |
| LINEAGE:base_currency | base_currency | OKX instruments row | baseCcy / instId group 1 / uly fallback | currency_code | eligibility_v1._extract_base_quote → GovernedUniverseInstrumentV1.base_currency | STATUS=CONTRADICTED (both sides preserved) |
| LINEAGE:mark_px | mark_price | OKX public mark-price | markPx | price | OkxPublicMarketDataClientV1 GET /api/v5/public/mark-price | STATUS=FORENSIC_RAW |
| LINEAGE:quote_currency | quote_currency | OKX instruments row | quoteCcy else instId regex group 2 | currency_code | eligibility_v1._extract_base_quote → GovernedUniverseInstrumentV1.quote_currency | STATUS=FORENSIC_RAW |
| LINEAGE:venue_native_id | venue_native_id | Cap 2.3 selection / Cap 2.4 binding | venue native instId | identity | selection snapshot → BoundInstrumentV1.venue_native_id | STATUS=FORENSIC_RAW |

