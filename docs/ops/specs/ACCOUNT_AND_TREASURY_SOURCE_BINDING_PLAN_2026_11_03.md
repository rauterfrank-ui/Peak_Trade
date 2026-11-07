---
docs_token: DOCS_TOKEN_ACCOUNT_AND_TREASURY_SOURCE_BINDING_PLAN_2026_11_03
status: source-roles-specified-local-adapter-implemented
scope: Account-startup and Treasury input composition; subordinate to existing contracts
---

# Account and Treasury source binding — implementation specification

2026-11-03. Frank requests that the real source binding be determined now; GitHub and service setup are deferred. Revision inspected: 1397f5aa880cbedf562563b23bda78a232c7098b. This specification selects the source roles for the new composition. It does not claim that a deployed source exists or change any capital/learning policy.

## Local implementation update

The subsequent [observer adapter and exporter](ACCOUNT_OBSERVATION_STARTUP_SOURCE_V1.md) implements the local typed/callback/document connection with injected proof, including separate algo-order absence checks. The source selection below records the plan at the inspected base revision; references to a future exporter are historical. Actual signer/provider, account/SecretRef and installed factory remain provisioning work.

## Selected sources and consumers

1. **Account identity and mode:** authenticated OKX EEA account-config GET, compared with separately configured expected account identity. Feed the existing startup collector and pretrade account-mode checks. Neither a returned UID alone nor a historical fixture UID may choose the account. All private ports must prove the same configured account.
2. **Positions and pending orders:** authenticated account positions and pending-orders GETs over the complete supported account SWAP scope, with no selected-instrument filter hiding other positions/orders. Use the existing `collect_host_account_observation_v1` result, then `acquire_account_bound_n1_startup_v1` and the existing Cap24 binding gate. Preserve nonflat positions; unresolved orders block startup. Unknown native-to-canonical mappings block rather than dropping rows. The current N1 helper supplies only the selected-instrument map; another observed instrument therefore blocks. General multi-instrument coverage is not claimed.
3. **Legacy launcher observation port:** the same validated collector is the selected producer for a future exporter of the existing startup document. An exporter must preserve account, source, signed quantities, event/capture times and pending-order status, and must prove scope before declaring complete scope. Missing/failed reads cannot produce an empty book. The existing reader validates data shape and five-second age; it does not authenticate an exporter. No exporter or external document was installed in this step. Prefer the typed snapshot directly when composition remains in one process; file export is for existing CLI boundaries.
4. **Sizing capital:** a fresh decision-bound authenticated account-balance GET, selecting exactly the USDC details row and its availEq, enters the existing margin validator, Treasury single-source handoff and 29P producer. The numeric sizing authority remains that producer. Account-level availEq/totalEq, availBal, the first arbitrary currency detail, max-size and a cached private state record cannot substitute for this input. The baseline collector's first-detail balance normalization is observation only, not this sizing source. This specification does not alter U04/P01 or resolve their deferred semantics.
5. **Local commitments:** existing durable `PortfolioBudgetHostV1` and its single shared reservation owner provide local holds and execution links, from the stable configured private root. The venue balance cannot reconstruct these local commitments. Ordinary start is recover-only; explicit bootstrap remains separate. Pass the same owner through N1/S5 and one-shot prepare. Do not create another owner for a lane/run.
6. **Execution recovery:** the existing identity-bound read-only reconciliation provider supplies pending/history/fills/positions and exact-order lookup for persisted submission identities. Ambiguity retains the hold. Bounded history calls are not proof of complete historical fills or outcome learning. Private WebSocket state may support observation/recovery; it does not replace fresh decision-bound GETs.
7. **Public constraints and conversion:** keep the existing pretrade collector for the bound future's public instrument metadata and price limit, private max-size/leverage/mode checks, and explicit USDT/USDC conversion evidence. These constrain/normalize the decision; they do not choose capital. Market candles, current price, G17, universe and ranking source-completeness work remain the separate existing market-data workstream.

## Concrete code anchors

- [Collector and durable owner](../../../src/ops/portfolio_capital_reservation_budget_v1/host_v1.py).
- [N1 account-bound startup](../../../src/ops/n1_standing_pre_external_runtime_supervisor_v1/startup_binding_v1.py).
- [Baseline endpoints and normalization](../../../src/ops/okx_eea_private_account_state_runtime_v1/rest_baseline_v1.py).
- [Existing legacy document contract](LEGACY_STARTUP_OBSERVED_PORTFOLIO_PORTS_V1.md).
- [Fresh pretrade collector](../../../src/ops/full_core_live_path_composition_root_v1/fresh_pretrade_runtime_get_v1.py).
- [Decision-bound margin consumer](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py).
- [Treasury handoff](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_treasury_single_source_capital_handoff_v1.py).
- [Identity-bound execution reconciliation](../../../src/ops/full_core_live_path_composition_root_v1/full_core_exchange_reconciliation_okx_read_only_provider_v1.py).

Endpoint names and EEA host are the inspected repository contracts, not a fresh venue compatibility attestation. Current endpoint behavior must be checked when provisioning is performed.

## Credential and transport composition

The private observation plane requires the dedicated observation-read credential class and explicitly rejects trade-credential fallback. Its policy currently has an unbound SecretRef. The credential join returns a declared observation handle; by itself that is not proof of a functioning OS-store acquisition/signing transport. The baseline collector accepts an injected callback and labels its provenance; that label does not authenticate the callback.

The existing K1 context manager supplies a separate bounded GET-only pretrade transport. Retain its existing authorization/lifetime rules. It is a candidate for the pretrade port, not permission to use a trade credential for the dedicated private observer. The future runtime factory must bind each capability explicitly, validate successful fresh acquisition evidence and the same expected account, enforce the appropriate endpoint/method scope, and close both lifetimes correctly. Never expose keys or fabricate GET-success evidence. Do not merge credential classes or policies to fill this gap.

Code/policy anchors: [observation credentials](../../../src/ops/okx_eea_private_account_state_runtime_v1/credentials_v1.py), [observation policy](../../../config/governance/okx_eea_private_account_state_runtime_v1_policy_v1.json), [K1 GET-only binding](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1.py), [productive GET transport](../../../src/ops/full_core_live_path_composition_root_v1/productive_read_only_get_transport_v1.py).

## Implementation order and remaining provisioning

First resolve the dedicated observer's real authorized signing/transport acquisition and separately expected account identity; do not infer them from old fixture values. Then bind the typed collector to startup and, where required, a document exporter. Verify complete supported scope, paging/truncation, identities, freshness and failure propagation before any complete-scope assertion. Configure stable private/public/lane/lock roots and explicit bootstrap separately. Compose the same durable owner and fresh pretrade capability, with bounded request quota sufficient for the actual attempt. Finally perform authorized read-only acceptance before service installation.

The current baseline performs individual recovery endpoint calls without a pagination loop. A successful single response therefore does not prove unbounded account/history completeness. Existing SWAP-only observation is not coverage of dated FUTURES or every contract admitted by GGE. The new instrument interpretation must not be narrowed merely to conceal that provisioning gap; missing account-scope coverage must block admission. Private-state policy still contains older single-position/multi-future limits; this plan does not silently ratify or relax them for the new target.

Concrete account identity, bound secret reference, real transport factory/exporter, absolute deployment roots, verified paging/contract-type coverage, service activation and remote CI remain unprovisioned or unproven. Source roles are determined; these values and their runtime proof remain explicit implementation work. U04, accounting/custody close, and learning/outcomes remain deferred or separately open.

## Verification scope at plan creation

Documentation-only change. Source contracts and consumers were inspected at the stated revision; no source module, policy, credential binding or runtime state changed. The previous [68-case injected flow proof](../evidence/FIVE_FULL_FLOW_REPAIRS_2026_11_03.md) remains scoped evidence for existing consumers, not an authenticated live-source proof. No redundant suite run was performed. [Source manifest](../evidence/account_treasury_source_binding_plan_2026_11_03.json) binds the inspected code and this specification. No real GET, keychain lookup, service installation, GitHub push, order or transfer occurred.

## Explicit K1 selection and lifecycle audit — 2026-11-03

Frank selected the already-configured K1 credential service. The [K1 source profile and capital lifecycle contract](K1_TREASURY_ACCOUNT_SOURCE_AND_CAPITAL_LIFECYCLE_V1.md) adds an explicit bounded alternative to the dedicated-observer profile, without relabeling credentials or adding fallback. Real account/Trading/Funding reads passed; durable post-close composition is injected-tested. Dedicated observer policy, U04/P01 and economic formulas remain unchanged. Independent real accounting/equity reconstruction and continuous service deployment remain open. Earlier unprovisioned-source statements describe their dated phase/profile.

## Source-specific consumer correction — 2026-11-07

The [source/consumer evidence](../evidence/TREASURY_CAPITAL_SOURCE_SEMANTICS_2026_11_07.md)
binds the follow-up at d2615064e7bf757999b6ea0884a51526d5114b6b. The fresh
Trading USDC free-margin observation now retains its source through Treasury/E4/C08
and enters the original 29P producer without being labeled as Funding CT BASE.
Funding retains its existing CT consumer. Nonempty U04 without venue-coverage
identity is fenced on the margin branch. This does not resolve the zero-witness
default, local-hold accounting domains, complete accounting or host recovery.
