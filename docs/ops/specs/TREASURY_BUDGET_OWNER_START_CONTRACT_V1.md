# Treasury budget-owner startup contract v1

docs_token: DOCS_TOKEN_TREASURY_BUDGET_OWNER_START_CONTRACT_V1

2026-11-03. Scoped implementation under the Master Runbook and Frank's new-system work order. No service activation or external-effect authority.

## Problem and resulting behavior

The host previously inferred create versus recover from directory existence and learned the first account identity from its observation. A lost/misconfigured state path could therefore become a new empty owner. Normal N1 startup now requires an explicitly configured account identity and opens the existing shared owner in recover mode. Missing, empty, incompatible or corrupt durable state cannot become genesis automatically.

`PortfolioBudgetHostV1` requires `expected_account_identity`; blank, padded and non-string identities are rejected. Each private observation is compared against this configured identity, independently of the cached observed-account field. The existing durable owner also retains its persisted account and lane-binding checks. A different account cannot bootstrap a store or reuse another account's state through this host.

The API distinguishes explicit `durable_mode="create"` from the default `"recover"`. Create refuses an existing scope. It initializes fenced owner metadata and does not admit capital. Recovery still requires fresh producer facts and reconciliation; previously committed holds remain holds. This is an explicit API setup capability, not proof that an account is physically new and not an installed bootstrap command.

## Root and lifecycle binding

The supervisor uses one resolved absolute owner root under the configured private-store root, with the existing `portfolio_budget_host_v1` child. Evidence/session identifiers do not select another budget. The private, public, evidence and lane roots must be absolute. The resolved owner root cannot overlap the evidence, public or lane roots in either direction; symlink aliases are resolved. Validation precedes both runtime and fault-notice writes.

Normal supervisor startup passes the configured account and literal recover mode. No N1 option automatically bootstraps a missing owner. An operator must keep the same private root across sessions. These checks reject structural overlap; they do not prove filesystem durability, prevent later symlink replacement, install a service manifest or identify the correct physical account/root on their own.

## Unchanged monetary meaning and open integration

This change does not redefine Treasury equity, available-for-sizing, reservation amounts or release rules. The current available-for-sizing calculation subtracts U04/P01 before the shared owner separately deducts active local holds. Substituting the local hold sum for U04 without proving its accounting domain could double-subtract. The existing zero-U04 witness in the default helper is not validated as a general account fact by this work. See [the unresolved U04 mapping](FULL_CORE_U04_PENDING_ORDER_RESERVATION_OR_ACCOUNT_EQUITY_MAPPING_V1.md).

The seven older Cap24 callers recorded in Blueprint section 18.4 remain pending explicit observed-portfolio migration. Real bootstrap/setup, service roots/manifest, complete Treasury close/custody/equity reconciliation, ambiguous-order handling and economic learning semantics remain separate work. No new empty capital source or second capital owner is introduced.

## Evidence

Implementation: [budget host](../../../src/ops/portfolio_capital_reservation_budget_v1/host_v1.py), [supervisor](../../../src/ops/n1_standing_pre_external_runtime_supervisor_v1/supervisor_v1.py). Tests use synthetic account identities and temporary stores. [Dated report](../evidence/TREASURY_BUDGET_OWNER_START_CONTRACT_2026_11_03.md) records passing recovery suites and unresolved broader entry diagnostics. They do not prove live venue behavior, whole-host power-loss durability or full-system readiness.

## Explicit K1 selection and lifecycle audit — 2026-11-03

Frank selected the already-configured K1 credential service. The [K1 source profile and capital lifecycle contract](K1_TREASURY_ACCOUNT_SOURCE_AND_CAPITAL_LIFECYCLE_V1.md) adds an explicit bounded alternative to the dedicated-observer profile, without relabeling credentials or adding fallback. Real account/Trading/Funding reads passed; durable post-close composition is injected-tested. Dedicated observer policy, U04/P01 and economic formulas remain unchanged. Independent real accounting/equity reconstruction and continuous service deployment remain open. Earlier unprovisioned-source statements describe their dated phase/profile.

## Clarified consumer scope — 2026-11-07

The [source/consumer correction](../evidence/TREASURY_CAPITAL_SOURCE_SEMANTICS_2026_11_07.md)
distinguishes CT's intermediate U04 subtraction from final 29P free margin.
The earlier summary above must not be read as proof that the final margin
producer subtracted U04: it did not. Funding still uses CT; free margin now
reaches its original 29P owner without constructing CT BASE. Nonempty U04 with
unproven venue coverage blocks that branch. Active local budget holds and the
fixed empty-witness default remain separate unresolved semantic boundaries.
The durable owner, recovery admission and reservation/release rules are unchanged.

## Original local commitment readback — 2026-11-07

The [local source/consumer proof](../evidence/LOCAL_COMMITMENT_SOURCE_BINDING_2026_11_07.md)
replaces the fixed empty-U04 helper in the productive ENTER caller with an atomic
readback of its existing shared budget owner. Canonical sizing holds retain their
original resulting-notional meaning; raw declared holds remain explicitly distinct.
The same owner/generation is checked through margin transport and at atomic reserve.
No local amount is credited as venue margin or substituted for Funding CT U04.
Existing sizing mathematics, persisted records, recovery and release authorities
remain unchanged. Venue/local netting and market-exposure policy remain open.
