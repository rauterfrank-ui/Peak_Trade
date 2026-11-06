---
docs_token: DOCS_TOKEN_MONETARY_NORMALIZATION_IMPLEMENTATION_V1
status: active
scope: GHV/productive PRE_EXTERNAL USDT-instrument → USDC-numeraire normalization seam
authority_effect: NONE
trading_authority: NONE
---

# Monetary Normalization Implementation V1

Derived governance note. Non-SSOT. Master Runbook remains sole canonical SSOT.

```text
CANONICAL_INTERNAL_RISK_NUMERAIRE=USDC
PHYSICAL_USDC_REQUIRED_FOR_NUMERAIRE=false
MONETARY_NORMALIZATION_AUTHORITY=ops.governed_productive_monetary_normalization_v1
USDT_USDC_RATE_AUTHORITY=OKX /api/v5/market/index-tickers USDC-USDT idxPx
RAW_RATE_UNIT=USDT/USDC
NORMALIZED_RATE_UNIT=USDC/USDT
INVERSION_REQUIRED=true
TRADING_AUTHORITY=NONE
COMPOSITE_CONVERSION_AUTHORIZED=false
```

USDC internal numeraire ≠ physical USDC-only trading universe. Multi-collateral
aggregation (BTC/EUR/totalEq) is explicitly out of scope for this slice.

Owner seam: `src/ops/governed_productive_monetary_normalization_v1/normalize_v1.py`
(wired at `current_productive_enter_live_29p_join_v1` before CRS capital context).
