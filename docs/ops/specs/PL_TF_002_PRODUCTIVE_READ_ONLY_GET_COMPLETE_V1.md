---
docs_token: DOCS_TOKEN_PL_TF_002_PRODUCTIVE_READ_ONLY_GET_COMPLETE_V1
status: active
scope: PL-TF-002 bounded productive F1/F2 GET capture, offline verification, evidence persist, closure navigation
capability: PL_TF_002_PRODUCTIVE_READ_ONLY_GET_COMPLETE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-20
---

# PL-TF-002 Productive Read-Only GET Complete V1

## Goal

Close PL-TF-002 with **productive** F1 Fresh Pretrade GET evidence plus NE-TF-001
permission GET, offline verifier PASS, governed evidence persist, and standing
navigation token flip. No POST. No treasury mutation. No K1 authority change.

```text
WP_ID=PL_TF_002_PRODUCTIVE_READ_ONLY_GET_COMPLETE_V1
OWNER_GO=OWNER_GO_PL_TF_002_PRODUCTIVE_READ_ONLY_GET_COMPLETE_V1
SESSION_OWNER_GO=OWNER_GO_PL_TF_002_PRODUCTIVE_READ_ONLY_SESSION_EXECUTOR_V1
AUTHORIZED_HOST=eea.okx.com
TRANSPORT=FullCoreProductiveReadOnlyGetTransportV1
METHOD_ALLOWLIST=GET_ONLY
RUNTIME_AUTHORIZATION_EFFECT=NONE
NETWORK_EXECUTION_AUTHORIZED=false
```

## Governed transition

```text
OWNER_GO(WP) + SESSION_OWNER_GO
  -> pre_network_jit_v1 (non-secret)
  -> open_pl_tf_002_productive_read_only_get_session_v1 (K1 ephemeral)
  -> collect_fresh_pretrade_runtime_get_v1 (F1)
  -> NE-TF-001 GET /api/v5/account/config (F2, shared config fetch group)
  -> verify_pl_tf_002_network_evidence_v1
  -> evidence persist (sanitized)
  -> closure navigation flip (PL_TF_002_STATUS, venue permission tokens)
```

## Closure predicate

Same as `PL_TF_002_NETWORK_EVIDENCE_CONTRACT_V1`: verifier
`PL_TF_002_CLOSURE_RESULT.closed=true` with `PRODUCTIVE_VENUE_EVIDENCE`.

Closed navigation status:

```text
PL_TF_002_STATUS=CLOSED_TRADING_KEY_TREASURY_CAPABILITY_VENUE_PROVEN
VENUE_PERMISSION_UNKNOWN=false
VENUE_PERMISSION_GET_PERFORMED=true
```

## Non-claims

```text
No LIVE / RISK_ADMISSIBLE / Treasury authority mint
No POST / order / withdrawal / transfer
No standing NETWORK_EXECUTION_AUTHORIZED=true
No K1 credential authority change
Synthetic verifier PASS alone is not productive closure
PDF TARGET_AUTHORITY=NONE
```
