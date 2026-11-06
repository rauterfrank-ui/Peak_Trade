---
docs_token: DOCS_TOKEN_K1_PRODUCTIVE_MACOS_CREDENTIAL_STORE_PROVISIONING_AUTHORITY_V1
status: active
scope: Bounded K1 macOS Keychain provisioning authority; Owner-GO gated upsert only; no standing write
capability: K1_PRODUCTIVE_MACOS_KEYCHAIN_PROVISIONING_AUTHORITY_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-20
---

# K1 Productive macOS Keychain Provisioning Authority V1

## Goal

Establish a **single** bounded Operator provisioning authority for the canonical
DZ Keychain tuple (`peak-trade.full-core.venue-credentials` /
`okx-eea.productive`). Enable a **later**, separately Owner-GO-scoped write to
replace wrong/stub material with operator-supplied OKX-EEA credential JSON.

This capability does **not** perform standing Keychain writes, venue GET/POST,
credential rotation, or secret persistence.

```text
WP_ID=K1_PRODUCTIVE_KEYCHAIN_PROVISIONING_AUTHORITY_V1
OWNER_GO=OWNER_GO_K1_PRODUCTIVE_MACOS_KEYCHAIN_PROVISIONING_V1
WRITE_AUTHORIZATION_DEFAULT=false
REAL_KEYCHAIN_WRITE_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
NETWORK_EXECUTION_AUTHORIZED=false
K2_REINTRODUCED=false
```

## Target (closed world)

```text
KEYCHAIN_SERVICE_ID=peak-trade.full-core.venue-credentials
KEYCHAIN_ACCOUNT_ID=okx-eea.productive
PROVIDER_REF_IDENTIFIER=okx-eea-productive
SOURCE_REF_URI=fullcore-cred://provider-ref/okx-eea-productive
```

## Allowed operation

- One bounded **upsert** of opaque UTF-8 JSON with closed fields
  `apiKey`, `secretKey`, `passphrase` (non-empty; placeholder classes rejected)
- Requires explicit `OWNER_GO` per call and ephemeral provisioning scope
- Injectable backend for tests; no production write in contract tests

## Forbidden

- Other Keychain items, wildcard queries, delete-all, credential discovery
- Alternate backends (SecretRef, file vault, K2/Legacy)
- Repo/evidence/logging of plaintext material
- Venue wire, auto rotation, auto key generation

## Verification contract

Post-write verification (future WPs) uses shape/fingerprint only — never
secret emission.
