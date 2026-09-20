# FULL_CORE_U05_P1_FUTURES_BOUND_INTEREST_ACCRUED_USDC_SCOPED_GET_ACQUISITION_V1

scope: P1-only one GET `GET https://eea.okx.com/api/v5/account/interest-accrued?type=2&limit=100&ccy=USDC` for FUTURES_MODE; material scope differs from CD (`ccy` unbound); P4/U05 primary proof unchanged; max one GET; zero retries; CB offline qualification; P1 adjudication fail-closed

OWNER_GO=`FULL_CORE_U05_P1_FUTURES_EVENT_SURFACE_DISCOVERY_BIND_AND_SINGLE_GET_TO_FIRST_HARD_BLOCKER_V1`

EXACT_REQUEST=GET https://eea.okx.com/api/v5/account/interest-accrued?type=2&limit=100&ccy=USDC

P1_EVENT_SURFACE_ROLE=INDEPENDENT_LIABILITY_EVENT_EVIDENCE_ONLY

owner=src/ops/governed_productive_account_equity_authority_producer_v1/u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1.py
