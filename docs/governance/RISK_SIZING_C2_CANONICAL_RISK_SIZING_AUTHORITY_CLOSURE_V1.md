# C2 + Canonical Risk Sizing Authority Closure v1

**Workpackage:** `C2_CANONICAL_RISK_SIZING_AUTHORITY_CLOSURE_V1`  
**Owner-GO:** `OWNER_GO_C2_CANONICAL_RISK_SIZING_AUTHORITY_CLOSURE_V1` (**CONSUMED**)  
**Machine contract:** [`config/governance/risk_sizing_c2_canonical_risk_sizing_authority_closure_v1.json`](../../config/governance/risk_sizing_c2_canonical_risk_sizing_authority_closure_v1.json)

C2 here is **Companion Shadow/Live Fraction→Units** (`COMPANION_SHADOW_LIVE_FRACTION_TO_UNITS_CONVERSION_INPUT_AUTHORITIES`), not Master-V2 directional confirmation C2.

## Verdict (authority roles only)

```text
AUTHORITY_CLOSURE_CASE=CASE_B_MECHANICAL_CONTRACT_GAP
CANONICAL_RISK_SIZING_OWNER=src.governance.capital_risk_sizing_v1
CANONICAL_RISK_SIZING_OWNER_COUNT=1
CANONICAL_RISK_SIZING_OWNER_SCOPE=productive_authoritative_full_core_mv2_governance_intent_bound
Q1_OWNER=src.governance.capital_risk_sizing_v1
C2_VERDICT=C2_AUTHORITY_ROLE_RATIFIED
C2_STATUS=PARTIAL_CONVERSION_NOT_READY
C2_FRACTION_AUTHORITY_OWNER=COMPANION_SESSION_POSITION_FRACTION_CONFIG_SURFACE_V1
C2_FRACTION_TO_UNITS_OWNER=COMPANION_SHADOW_LIVE_FRACTION_TO_UNITS_INPUT_BINDING_V1
C2_EXECUTION_NORMALIZATION_OWNER_FULL_CORE=src.ops.full_core_live_path_composition_root_v1.venue_translation_v1
CONVERSION_READY=false
DUPLICATE_RISK_SIZING_AUTHORITY_COUNT=0
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
```

## Q1 vs Companion C2

| Lane | Owner / role | Competes with Q1? |
|------|----------------|-------------------|
| Full-Core enter-live MV2 intent-bound quantity | `src.governance.capital_risk_sizing_v1` (Q1) | — |
| Companion fraction intent | Session config surface (`position_fraction`) | **No** — config transport, not risk-sized |
| Companion Fraction→Units | Binding `COMPANION_SHADOW_LIVE_FRACTION_TO_UNITS_INPUT_BINDING_V1` (not implemented) | **No** — conversion absent; not a second sizing decision |
| Parallel inventory bypass paths | Fate-adjudicated (exclude / keep-parallel / research) | **No** — non-canonical inventory scopes |

Q1 is the **canonical productive Risk/Sizing authority** on the Full-Core path. Companion C2 is a **separate support runtime** that does not block Q0/Q1/Treasury/MV2+DP and does not constitute a duplicate canonical sizing authority.

## Explicit non-claims

- No Fraction→Units math implementation  
- No Companion conversion-input PROVEN_CURRENT promotion  
- No activation, external effect, or Multi-Future authorization  
- No trading, selection, treasury mutation, or execution algorithm change  
