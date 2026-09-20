---
docs_token: DOCS_TOKEN_PL_TF_002_NETWORK_EVIDENCE_CONTRACT_V1
status: active
scope: PL-TF-002 network evidence contract; NE-TF-001 permission GET semantics; offline verifier; no network; no runtime status flip
capability: PL_TF_002_NETWORK_EVIDENCE_CONTRACT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-20
---

# PL-TF-002 Network Evidence Contract V1

## Goal

Materialize the deterministic contract required **before** any PL-TF-002
productive network-evidence session. This persist does not perform GETs,
load credentials, or flip standing runtime status tokens.

```text
PL_TF_002_STATUS_STANDING=FROZEN_PENDING_NETWORK_EVIDENCE
NAVIGATION_PL_TF_002_STATUS_AFTER_GOVERNED_CLOSURE=CLOSED_TRADING_KEY_TREASURY_CAPABILITY_VENUE_PROVEN
VENUE_PERMISSION_UNKNOWN=true
VENUE_PERMISSION_GET_PERFORMED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
NETWORK_EXECUTION_AUTHORIZED=false
```

This capability keeps `PL_TF_002_STATUS_STANDING` frozen in-package. Governed
closure navigation (`PL_TF_002_STATUS`, venue permission tokens) flips only in
`treasury_phase_1_offline_contracts_v1`, Master Runbook, and bound specs via
`apply_pl_tf_002_closure_status_navigation_v1` after productive evidence (#6662).

## NE-TF-001 evidence surface

```text
NE_TF_001_TASK_ID=NE-TF-001
NE_TF_001_HTTP_METHOD=GET
NE_TF_001_ENDPOINT_PATH=/api/v5/account/config
NE_TF_001_RESPONSE_PERM_FIELD=data[0].perm
```

Provenance (canonical repo contract evidence, not Atlas authority):

- `section_11_13_2_live_private_read_only_v1` GET allowlist includes
  `&#47;api&#47;v5&#47;account&#47;config`.
- `PEAK_TRADE_ACCOUNT_MODE_FORENSIC_BINDING_AND_CLOSURE_V1` documents
  authenticated `GET &#47;api&#47;v5&#47;account&#47;config` as the read-permission
  account-configuration surface.
- `PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1`
  documents same-GET field `perm` on `data[0]` (observed, not POS_MODE-bound).
- Repository captures/tests show `perm` comma-tokens `read_only` and `trade`.

§11.13.2 `REQUIRED_PERMISSION_ATTESTATION` owner input is **not**
equivalent to NE-TF-001 venue permission GET.

## Normalization contract

RAW `data[0].perm` comma-separated tokens (closed world):

| Token | READ | TRADE | WITHDRAW |
|-------|------|-------|----------|
| read_only | true | — | — |
| trade | — | true | — |
| withdraw | — | — | true |

Unknown tokens fail closed. Empty/missing `perm` fails closed.

PL-TF-002 required normalized facts:

```text
READ=true
TRADE=false
WITHDRAW=false
```

## Evidence layers

```text
RAW_VENUE_RESPONSE
NORMALIZED_PERMISSION_FACTS
EVIDENCE_PROVENANCE
VERIFICATION_RESULT
PL_TF_002_CLOSURE_RESULT
```

## F1–F4 bindings

- **F1** productive venue GET: Full-Core Fresh Pretrade item ids
  (`INSTRUMENT_STATE` … `AVAILABLE_MARGIN`) each `get_performed=true`,
  `method=GET`, productive transport, `venue_live_contact=true`.
- **F2** NE-TF-001 permission GET: governed GET of `&#47;api&#47;v5&#47;account&#47;config`
  with raw venue JSON bound under `F2_NE_TF_001`.
- **F3** venue-side treasury-negative proof: normalized `WITHDRAW=false` and
  `TRADE=false` for trading-key separation.
- **F4** `VENUE_PERMISSION_UNKNOWN` cleared only when F2+F3 pass under
  productive evidence class (standing constants flip only in a separate
  governed persist).

## Closure predicate

Verifier `verify_pl_tf_002_network_evidence_v1` returns
`PL_TF_002_CLOSURE_RESULT.closed=true` only when F1–F4 pass and evidence class
is `PRODUCTIVE_VENUE_EVIDENCE`. Future closed status token:

```text
PL_TF_002_STATUS_CLOSED=CLOSED_TRADING_KEY_TREASURY_CAPABILITY_VENUE_PROVEN
```

Standing `treasury_phase_1_offline_contracts_v1` constants remain frozen until
an explicit authorized status-flip persist.

## Non-claims

```text
No network execution in this capability
No credential load
No LIVE / RISK_ADMISSIBLE / Treasury authority mint
No §11.13.2 attestation substitution for NE-TF-001
Fixture/synthetic verifier PASS is not productive PL-TF-002 evidence
PDF TARGET_AUTHORITY=NONE
```
