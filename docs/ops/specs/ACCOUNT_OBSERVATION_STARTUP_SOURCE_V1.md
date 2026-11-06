---
docs_token: DOCS_TOKEN_ACCOUNT_OBSERVATION_STARTUP_SOURCE_V1
status: local-implementation-injected-proof
scope: Dedicated observer adapter and existing startup document producer
---

# Account observation startup source v1

The local adapter implements the source-to-consumer connection selected in the [source plan](ACCOUNT_AND_TREASURY_SOURCE_BINDING_PLAN_2026_11_03.md). It does not acquire or install a real credential/session provider. Production module: [startup source](../../../src/ops/okx_eea_private_account_state_runtime_v1/startup_source_v1.py).

## Composition API

`open_account_observation_source_v1` requires an explicit caller-owned context-manager factory. That provider yields the dedicated observation credential handle and its paired GET transport, and owns their acquisition, host restriction, credential binding, quota, revocation and release. There is no default provider or K1 fallback. The adapter validates the existing observation class and rejects mutation capabilities/K2. It does not turn matching declarations into proof of authentication or mint DataSafety REAL metadata.

Within that context, pass the yielded callable source as the existing `private_rest_fetch` argument to account-bound N1 startup, private recovery or the shared budget host. The callable preserves their existing raw-response interface and delegates actual position/account normalization to the existing host collector. No replacement capital ledger, collector or reservation owner is created.

For legacy launchers, call its `export_startup_document_v1` with an absolute destination in a pre-existing caller-chosen private directory and an explicit native-to-canonical instrument map. It acquires new data, uses the same collector, preserves signed position quantities and observation timestamps, and validates its document through the existing reader before atomic publication. The destination is new for each export; existing files, symlinks and concurrent creations cannot be replaced. The file has mode 0600. Failures before publication leave no new destination or temporary file. Parsing/exporting does not renew observation age.

The context closes the adapter before provider release, including consumer failure. A closed adapter rejects reuse. Provider acquisition/cleanup failures propagate; no automatic substitute session or synthetic response is created.

## Source checks and supported scope

All reads require GET evidence: exact requested endpoint including query, HTTP success, authentication-header-sent and venue-contact flags, no historical reuse or error, valid body-digest format and successful structured venue response. These checks consume producer evidence, not cryptographic independent authentication. Unknown response-envelope extensions fail closed for review. The declared source of truth is still the explicitly supplied trusted transport/provider.

The public callable accepts the six existing recovery endpoints. Position reads require the account SWAP scope. Older recovery callers supply instId for pending/history/fills; the adapter removes that filter, as the existing shared collector does, so other instruments are not hidden. Unknown filters, derivative types and paths are rejected. Returned unknown/duplicate positions are rejected by the existing collector. Unmapped positions are never discarded.

An ordinary nonempty pending-order response blocks immediately; completing its pagination is unnecessary to prove that startup is blocked. An empty first unfiltered page is the absence case under the documented endpoint contract. Before returning that empty response, the adapter additionally reads untriggered algo orders for conditional, OCO, trigger and trailing-stop types in SWAP scope. Any returned algo, failed read or unknown envelope blocks. This is an extra local GET-only source check; no global policy allowlist or runtime authorization is changed. The actual provider must explicitly permit these extra read endpoints. A successful baseline needs **10 GETs**, repeated whenever its consumers request another baseline; request quota must be supplied for the whole authorized attempt.

The ordinary and algo lists are separate API surfaces in the [official OKX API documentation](https://www.okx.com/docs-v5/en/). This adapter checks the four documented algo types. It does not prove all venue products, grid/signal/bot subaccounts, dated-FUTURES coverage, unbounded historical fills or an atomic venue-wide snapshot. Live acceptance must bind the configured account to the supported product scope and separately address any other obligations. Existing SWAP-only input contracts and broader GGE instrument admission are not declared equivalent.

## Existing authority preserved

Account-config UID must equal the independently expected identity; the collector also rejects conflicting account evidence. Five-second snapshot/reader freshness remains active. Pending orders and algos are not adopted, cancelled or released. Fresh USDC capital remains the separate decision-bound Treasury/29P path; baseline balance normalization is not elevated into sizing authority. U04/P01, capital formulas, learning/promotion behavior and the dedicated observation policy are unchanged.

[Evidence](../evidence/ACCOUNT_OBSERVATION_STARTUP_SOURCE_2026_11_03.md) records the injected integration proof and remaining provisioning. No real provider, SecretRef/UID value, deployment directory, CLI auto-acquisition, service or trading activity is installed by this module.

## Explicit K1 selection and lifecycle audit — 2026-11-03

Frank selected the already-configured K1 credential service. The [K1 source profile and capital lifecycle contract](K1_TREASURY_ACCOUNT_SOURCE_AND_CAPITAL_LIFECYCLE_V1.md) adds an explicit bounded alternative to the dedicated-observer profile, without relabeling credentials or adding fallback. Real account/Trading/Funding reads passed; durable post-close composition is injected-tested. Dedicated observer policy, U04/P01 and economic formulas remain unchanged. Independent real accounting/equity reconstruction and continuous service deployment remain open. Earlier unprovisioned-source statements describe their dated phase/profile.
