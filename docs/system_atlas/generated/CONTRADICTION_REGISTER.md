<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Contradiction Register

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

### C-CAP23-VS-CANARY-INSTRUMENT-001

- subject: `Productive selection exclusivity versus live canary instrument authority`
- claim_a (ADJUDICATED): Cap 2.1→2.4 is the exclusive productive selection path for the analytical Cap 7.2 host (Cap 2.3 sole selection authority)
- source_a: `docs/ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md`
- claim_b (FORENSIC_RAW): Section 11.13.5 canary uses hardcoded DEFAULT_INSTRUMENT_ID SUI-USD_UM_XPERP-310404 with no Cap 2.3 import on origin/main; parallel public-MD binding uses ETH-USD_UM_XPERP-310404
- source_b: `src/ops/section_11_13_5_live_canary_minimum_exposure_v1/constants_v1.py`
- resolved: `False`
- adjudication: Cap23 exclusivity is scoped to the governed analytical selection→binding chain. Live canary and fixed venue-binding MD paths are separate instrument authorities. Do not claim global exclusivity.

- next_proof: None for Atlas; wiring Cap23 into canary would be a separate owner-authorized change

### C-CYBER-GATE-PASS-VS-MANIFEST-001

- subject: `PRE_LIVE_CYBERSECURITY_GATE`
- claim_a (FORENSIC_RAW): Master §4.8 and Cybersecurity Runbook V2.1 header PRE_LIVE_CYBERSECURITY_GATE=PASS; SECTION_11_13_STARTED=true
- source_a: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`
- claim_b (FORENSIC_RAW): Ratification JSON pre_live_cybersecurity_gate=NOT_PASSED; section_11_13_started=false; LOCAL_DOCS_ONLY_GOVERNANCE_MANIFEST_PRECOMMIT
- source_b: `docs/runbooks/canonical/PEAK_TRADE_CANONICAL_CYBERSECURITY_RUNBOOK_V2_1_RATIFICATION.json`
- resolved: `False`
- adjudication: Cross-document field conflict preserved. Manifest may be stale relative to headers; not silently collapsed.
- next_proof: Which surface is current for gate status

### C-DP-ORDER-001

- subject: `Double Play versus Survival/Suitability order`
- claim_a (CANONICAL_AUTHORITY): Market State → Master V2 → Double Play → Survival/Suitability/Composition
- source_a: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`
- claim_b (HISTORICAL): Historical Vollautonomie Survival → Suitability → Double Play → Canonical Trading Decision
- source_b: `docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`
- resolved: `False`
- adjudication: Do not normalize order. Git chronology on origin/main shows ops.double_play specialists (#1535, 2026-02-20) before Master V2 tree (#2822, 2026-04-23) and pure composition (#3040). Current owner-bound chain remains Master Runbook. Pure-stack composition consumes survival+suitability in current code.
- next_proof: None for Atlas; owner-bound current chain is Master Runbook

### C-FAMILY-POLYVALENT-001

- subject: `Family`
- claim_a (FORENSIC_RAW): Dashboard family_id is a projection grouping
- source_a: `docs/ops/market_dashboard/market_dashboard_projection_octet_upstream_artifact_creation_v1/VERIFY.json`
- claim_b (OPEN): OKX instFamily is a venue field; architectural Master-V2 Family is unproven
- source_b: `src/ops/governed_futures_universe_producer_v1/eligibility_v1.py`
- resolved: `False`
- adjudication: Additional proven Family senses must not be collapsed: strategy visual-map Family names; projection-octet family_id (8 ids); confirm-token FAMILY_*; Gate-Familien F1–F6 (historical forensic); obligation_families; L1–L5 pointer families; GFU census endpoint family; NO_FAMILY_ONTOLOGY blocker; FAMILY_SCOPED suitability agreement; strategy_family field. SSOT_CHILD literal absent. Child senses include HISTORICAL_CHILD_LEDGER (88 SRC-*), NestedStructuralChild, Falls-Parent/Child — not equated.

- next_proof: Formal unified Families ontology if owner requires one; currently CONTRADICTED / NO_FAMILY_ONTOLOGY for 5-family projection completeness

### C-FUNCTIONAL-CORE-TOKEN-001

- subject: `FUNCTIONAL_CORE / HAS_FUNCTIONAL_CORE as Atlas labels`
- claim_a (INTERPRETATION): Owner Atlas workpackage and census kind FUNCTIONAL_CORE record Double Play as inner functional core of Master V2
- source_a: `docs/system_atlas/census/census_meta.yaml`
- claim_b (FORENSIC_RAW): Exact spellings FUNCTIONAL_CORE, HAS_FUNCTIONAL_CORE, inner core, Funktionskern not found on origin/main in scoped docs; proven wording is Modul-Owner of one Trading Core
- source_b: `docs/architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md`
- resolved: `False`
- adjudication: Preserve owner-bound same-system membership. Do not treat Atlas kind FUNCTIONAL_CORE as a Master Runbook token. origin/main full-history pickaxe for HAS_FUNCTIONAL_CORE and FUNCTIONAL_CORE is empty. Structural edge remains ADJUDICATED, not CANONICAL_AUTHORITY-from-token.

- next_proof: None unless owner later introduces the token in canonical text

### C-MMR-POLYVALENT-001

- subject: `MMR`
- claim_a (CANONICAL_AUTHORITY): Master Runbook defines MMR as Maintenance Margin Requirement (account-effective vs public-tier mmr / INSTRUMENT_FAMILY_DEPENDENT)
- source_a: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`
- claim_b (OPEN): Architectural Master-V2 MMR kind as a Family/Child hierarchy node
- source_b: `docs/ops/specs/`
- resolved: `False`
- adjudication: Scoped grep of MASTER_V2 specs and src/trading/master_v2 found no second non-OKX MMR acronym. Venue/margin sense is proven. Architectural MMR kind remains absent, not invented.

- next_proof: None unless owner later defines a distinct architectural MMR

### C-OKX-AUDIT-SIGNED-REST-001

- subject: `Signed private OKX REST`
- claim_a (HISTORICAL): 2026-07-17 audit claimed signed private REST absent
- source_a: `docs/audits/OKX_INTEGRATION_READ_ONLY_AUDIT_2026-07-17.md`
- claim_b (FORENSIC_RAW): BoundOkxTestnetHttpClientV1 HMAC signer exists and is reused by later 11.13.x modules
- source_b: `src/ops/section_11_12_8_real_productive_testnet_execute_path_unlock_v1/bound_testnet_http_client_v1.py`
- resolved: `False`
- adjudication: Supersession, not silent overwrite. Audit document date is not git-introduction proof.
- next_proof: None for Atlas usage; do not treat July-17 audit as current absence proof

### C-OKX-QUOTE-ULY-001

- subject: `Cap 2.1 quote/base identity versus never-defaulted invariant`
- claim_a (CANONICAL_AUTHORITY): Missing metadata is never defaulted
- source_a: `docs/ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md`
- claim_b (FORENSIC_RAW): _extract_base_quote defaults missing base from instId/uly; quote never from uly; XPERP instIds fail quote regex
- source_b: `src/ops/governed_futures_universe_producer_v1/eligibility_v1.py`
- resolved: `False`
- adjudication: Mapping gap in Cap 2.1 _extract_base_quote, not a new XPERP adapter and not an intentional product ban (SUPPORTED_INST_TYPES={SWAP,FUTURES}; no ruleType filter). quote NEVER from uly. Fresh EEA rows have empty quoteCcy; SWAP recovers via hyphen instId; underscored XPERP/USD_UM ids fail regex. Full origin/main history confirms this BASE-only uly handling from the first Cap 2.1 commit (02095305, 2026-08-02); no removed quote-from-uly parser found. Whether uly second segment may supply quote without violating "never defaulted" is OWNER-POLICY_OPEN. SETTLE_VS_QUOTE remains OPEN. XPERP_ADAPTER_REQUIRED=false. Local schema/field census (GFU instruments fixture includes quoteCcy and uly on the same row) adds no quote-from-uly owner and does not change this status. Public-MD capture envelopes for ADA-USDT-SWAP mark-price contain instId/instType/markPx only (no uly).

- next_proof: Owner policy on uly-derived quote vs never-defaulted; GFU membership of SUI XPERP (GAP-U-CAN-006); host split www.okx.com vs eea.okx.com identity fields

### C-VERSION-V2.2-V2.3-001

- subject: `Master Runbook display version token`
- claim_a (FORENSIC_RAW): Document H1 title uses V2.2 (Canonical Stateful No-Order System Finish V2.2)
- source_a: `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`
- claim_b (FORENSIC_RAW): REVISION field and Map of Truth §2 label use V2.3; ratification source_filename contains V2_3
- source_b: `docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md`
- resolved: `False`
- adjudication: Textual version-token mismatch preserved. Not adjudicated which display token is intended.
- next_proof: Owner/display-token reconciliation if required

