---
title: "Dynamic Scope Governed REAL Market Evidence Spec v1"
status: "RESEARCH_EVIDENCE_ONLY"
owner: "trading.master_v2.dynamic_scope_governed_real_market_evidence_v1"
docs_token: "DOCS_TOKEN_DYNAMIC_SCOPE_GOVERNED_REAL_MARKET_EVIDENCE_V1"
---

# Dynamic Scope Governed REAL Market Evidence v1

```text
AUTHORITY=NONE
RUNTIME_AUTHORITY=NONE
PRODUCTIVE_D_T_FORMULA_SELECTED=false
MECHANICAL_CORE=execute_naked_mechanical_step_v1 (unchanged)
RESEARCH_HARNESS=dynamic_scope_empirical_calibration_research_v1 (unchanged)
```

## Phase 0 — Forensic discovery (READ_ONLY)

| Source | Class | Use in WP |
|--------|-------|-----------|
| `config/ops/fixtures/single_future_*` (cap51) | Fixture | Unit tests only — **not REAL evidence** |
| `exact_known_61_price_fixture_v1` (materializer) | Synthetic test vector | **not REAL evidence** |
| `docs/ops/artifacts/.../observation_pack.json` (Surface B) | **OBSERVED** OKX public PT1M ETH-USDT-SWAP | **Bound REAL series** |
| `scripts/ops/ingest_okx_futures_public_market_data_canonical_dataset_staging_v1.py` | Authorized fetcher (GO-gated) | Not invoked in CI; existing sealed pack reused |
| PIT OKX PT1H panel (`pit_okx_pt1h_panel_ohlcv_dataset_v1`) | Validation core | No long single-future PT1M panel committed beyond Surface B pack |

**Length justification:** Surface B pack = 299 contiguous finalized PT1M bars (~4h58m). Canonical volatility uses 60-bar warmup → 239 σ-valid bars (80% post-warmup), sufficient for tertile/regime splits and temporal segments without warmup dominating the full window.

## Volatility (DERIVED)

- Input: finalized `mark_price` series (OBSERVED)
- Owner: `canonical_volatility_estimate_materializer_v1`
- Transform: log returns on mark; rolling std (60 bars)
- Warmup: null σ → VOL_NORMALIZED candidates fail-closed per research harness
- No silent fallback to close price

## Evidence owner

`src/trading/master_v2/dynamic_scope_governed_real_market_evidence_v1.py`

Artifacts: `docs/evidence/dynamic_scope_governed_real_market_evidence_v1/`
