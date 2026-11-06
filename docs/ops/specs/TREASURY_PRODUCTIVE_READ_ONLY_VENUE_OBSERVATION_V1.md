---
docs_token: DOCS_TOKEN_TREASURY_PRODUCTIVE_READ_ONLY_VENUE_OBSERVATION_V1
status: active
scope: Productive read-only OKX-EEA funding balance + account config GET → Treasury Phase-2/3/E4 offline chain; stops at E4 productive host join
capability: TREASURY_PRODUCTIVE_READ_ONLY_VENUE_OBSERVATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-21
---

# Treasury Productive Read-Only Venue Observation V1

Closes the census blocker **productive read-only treasury venue observation** under
scoped Owner-GO. Reuses **PL_TF_002** ephemeral K1 session + GET-only transport.
Stops at **E4 productive host join** (orchestration ingress not wired on productive host).

```text
WP_ID=TREASURY_PRODUCTIVE_READ_ONLY_VENUE_OBSERVATION_V1
OWNER_GO=OWNER_GO_TREASURY_PRODUCTIVE_READ_ONLY_VENUE_OBSERVATION_V1
SESSION_OWNER_GO=OWNER_GO_PL_TF_002_PRODUCTIVE_READ_ONLY_SESSION_EXECUTOR_V1
VENUE_HOST=eea.okx.com
READ_ONLY_ENDPOINT_CLASSES=PRIVATE_READ_ONLY_FUNDING_BALANCE,PRIVATE_READ_ONLY_ACCOUNT_CONFIG_IDENTITY
NETWORK_READ_ONLY_AUTHORIZED=true
TREASURY_MUTATION_AUTHORIZED=false
RISK_ADMISSIBLE_MINT=false
PDF_AUTHORITY=NONE
```

## Governed transition

```text
WP Owner-GO + SESSION Owner-GO
  -> pre_network_gate_v1
  -> open_pl_tf_002_productive_read_only_get_session_v1
  -> GET /api/v5/account/config (uid scope only)
  -> GET /api/v5/asset/balances
  -> TreasuryVenueObservationV1 (deposit history UNCONFIRMED)
  -> Phase-2 reconciliation join
  -> Phase-3 shadow enforcement
  -> E4 offline orchestration ingress
  -> evidence persist (sanitized)
```

## Non-claims

```text
observed_equity != reconciled_equity != risk_admissible_equity
No Treasury mutation, POST, withdrawal, transfer
No STEP-29P or sizing mint
No E4 productive host wiring in this WP
```
