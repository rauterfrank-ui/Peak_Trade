# Forensic evaluation — §11.12.8 OKX EEA Demo XPerp campaign `20260810T181703Z`

## Binding
- ORIGIN_MAIN_SHA=`a04d6effa689d9a2d68ee7904a23b9aa1f7b2435`
- PRIMARY=`evidence/ops/section_11_12_8_bounded_okx_eea_demo_xperp_campaign_execute_v1/20260810T181703Z/`
- VENUE=`OKX_EEA_DEMO` HOST=`https://eea.okx.com` ENV=`DEMO` INSTID=`BTC-USD_UM_XPERP-310328` ORDER_SZ=`0.0001`

## Distinctions
- CAMPAIGN_EXECUTION_PASS=`true` (duration bound reached, sealed, reconcile clean, Live blocked)
- ORDER_LIFECYCLE_PROOF_PASS=`false` (ACK=0, exchange_order_id absent, fill=0)
- SECTION_11_12_8_CLOSED=`false`

## Duration
- planned=3600s actual=3600.677587791 bound_reached=`DURATION_BOUND` cycles=60/120

## Authorization / preflight
- owner_go_scope=`EXECUTE_BOUNDED_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN`
- confirm latched/consumed; credential vault_resolved; account binding verified
- ephemeral write gate PASS (`EPHEMERAL_XPERP_CAMPAIGN_PRIVATE_WRITE_GATE_PASS`)
- network_effect/order_effect=`TESTNET`; live_order_effect=`NONE`

## Single order attempt
- wire_sent=true; instrument=`BTC-USD_UM_XPERP-310328`; ordType=limit; px=10000; sz=0.0001; tdMode=cross
- clOrdId=`coid-campaign-0` (hyphenated; violates `^[A-Za-z0-9]+$`)
- HTTP=200 code=`1` msg=`All operations failed` sCode=`51000` sMsg=`Parameter clOrdId error`
- classification=`EXCHANGE_REJECTED`; exchange_order_id=null; ACK=0; FILL=0

## Classification
- **C_IMPLEMENTATION_OR_GOVERNANCE_DEFECT**
- Root cause: invalid Peak_Trade clOrdId formatting → OKX `51000 Parameter clOrdId error`

## Final reconcile
- FINAL_OPEN_ORDER_COUNT=0 FINAL_OPEN_POSITION_COUNT=0 ok=true unresolved=false

## Closeout recommendation
`KEEP_SECTION_11_12_8_OPEN_ORDER_LIFECYCLE_NOT_PROVEN_CLORDID_PARAMETER_REJECT`

## Minimal next Owner step (do not execute here)
`OWNER_GO_FIX_SECTION_11_12_8_OKX_CLORDID_SERIALIZATION_TO_ALPHANUMERIC_CONTRACT_AND_RETRY_BOUNDED_XPERP_ACK_PROOF`

## Hard preserves
LIVE_AUTHORIZED=false; PRE_LIVE_CYBERSECURITY_GATE=NOT_PASSED; SECTION_11_13_STATUS=UNSTARTED
