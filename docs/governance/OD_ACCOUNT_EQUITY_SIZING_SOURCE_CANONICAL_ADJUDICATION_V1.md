# OD_ACCOUNT_EQUITY_SIZING_SOURCE — Canonical Adjudication v1

**Status:** BINDING scoped Owner-GO adjudication (docs + static contract only)  
**Owner decision boundary:** `OD_ACCOUNT_EQUITY_SIZING_SOURCE`  
**Machine contract:** [`config/governance/od_account_equity_sizing_source_canonical_adjudication_v1.json`](../../config/governance/od_account_equity_sizing_source_canonical_adjudication_v1.json)  
**Baseline:** `origin&#47;main @ 570c437eb45295929128a13b2bc194bfb1fc063a`

```text
OWNER_GO=OWNER_GO_OD_ACCOUNT_EQUITY_SIZING_SOURCE_BOUNDED_WP_V1
OWNER_GO_STATUS=CONSUMED
DECISION_CASE=A
AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
EXTERNAL_EFFECT_AUTHORIZED=false
NUMERIC_CURRENT_VENUE_VALUE_BOUND=false
```

## Adjudicated semantics (Full-Core CURRENT productive)

`available_for_sizing` is the typed semantic dimension **`RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING`**, not a raw venue field alias. The productive source chain is:

1. **Observation surface (typed evidence only):** `details[ccy=USDC].availEq` (USDC-scoped cross free margin).
2. **Producer wrap (authority boundary):** `CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1`.
3. **Transform:** `DETAILS_USDC_AVAILEQ_MINUS_CONDITIONAL_P01_USDC_V1` (conditional Peak_Trade P01 reduction only when applicable).
4. **U04:** not subtracted again (already netted in venue free margin).

Consumed Owner-GO lineage (Master Runbook): `OWNER_DECISION_1=C` / parallel-decoupled tracks → Source→Semantic mapping bind → B05 Full-Core owner ratification → 29P risk-capital model OPTION_B alignment.

## Explicit non-claims

- No numeric CURRENT venue bind from this adjudication alone (`NUMERIC_CURRENT_VENUE_VALUE_BOUND=false`).
- No fresh trusted GET authorization.
- No Companion C2 equity handoff.
- No risk fraction / cap applied at the observation layer (downstream sizing only).
- Sealed CS source-selection persist (`SELECTED_SOURCE=NONE`) remains a **superseded historical baseline**; mapping ratification is authoritative for CURRENT semantics.

## SEM-SURF-DIV-00003 resolution

**PROVEN_CURRENT** with scoped reconciliation: CSIA `account_equity_mapping_unbound` PARTIAL refers to **numeric venue bind / implementation absence**, not absence of a ratified Source→Semantic mapping. B05 “chain closed” markers apply to **Full-Core authority-owner + producer-wrap + transform binding**, not to claiming fresh GET or Companion conversion readiness.
