---
docs_token: DOCS_TOKEN_UNIFIED_BLUEPRINT_PHASE_17_NORMATIVE_NON_PRICE_CMC_CONTRACT_NORMATIVE_V1
status: active
scope: Unified Blueprint Phase 17 MARKET_CONTEXT_V1 normative non-price CMC contract
capability: UNIFIED_BLUEPRINT_PHASE_17_NORMATIVE_NON_PRICE_CMC_CONTRACT_V1
last_updated: 2026-09-26
---

# Unified Blueprint Phase 17 — Normative Non-Price CMC Contract Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=UNIFIED_BLUEPRINT_PHASE_17_NORMATIVE_NON_PRICE_CMC_CONTRACT_V1
BLUEPRINT_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Owner decision (ratified):
`config/governance/normative_non_price_cmc_contract_owner_decision_v1.json`

Contract owner (offline typed record):
`src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_v1.py`

Integration closure:
`config/governance/unified_blueprint_phase_17_normative_non_price_cmc_contract_v1.json`

## Purpose

Close `NORMATIVE_NON_PRICE_CMC_CONTRACT_OWNER_DECISION` by implementing
`MARKET_CONTEXT_V1` as a compositional typed representation on the MI/Learning
information path only. Canonical market facts remain SSOT; the contract references
governed fact/adapters, preserves explicit missing semantics, PIT rules, provenance,
feature-version lineage, and information-set identity without altering N_BARS or
MV2/Double Play trading authority.

## Verification

- `tests/learning/test_market_context_v1.py`
- `tests/governance/test_unified_blueprint_phase_17_normative_non_price_cmc_contract_v1.py`
- `prove_unified_blueprint_phase_17_normative_non_price_cmc_contract_v1`
