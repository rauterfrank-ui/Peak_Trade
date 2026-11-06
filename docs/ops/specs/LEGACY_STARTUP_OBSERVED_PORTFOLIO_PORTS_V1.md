# Explicit portfolio observations at the seven legacy startup calls

docs_token: DOCS_TOKEN_LEGACY_STARTUP_OBSERVED_PORTFOLIO_PORTS_V1

2026-11-03. Subordinate interface alignment under the existing observed-portfolio Cap24 contract. No new account truth, capital, learning or execution authority.

## Scope and behavior

The seven direct handoff calls recorded in Blueprint section 18.4 now forward their caller-supplied `observed_portfolio` and `observation_now_unix`. The pre-live convergence API, one-shot prepare API and persistent preflight accept these inputs explicitly. Missing snapshots are rejected before their new state directories are created. The existing explicit bound-instrument override of the one-shot API remains a separate existing fixture/override path; it is not introduced or extended by this change.

The six parent CLIs require `--startup-portfolio` and `--expected-account-identity`. Their common reader validates an explicit observation document; it never creates an empty book from absent or invalid input. Pending/unknown orders, wrong claimed account, missing scope declaration, stale/future/nonfinite times, malformed/duplicate positions, quantity/side mismatch, duplicate JSON keys and unknown fields fail closed. Valid signed open positions remain positions, not an inferred flat account. Snapshots retain their source and observation times.

The productive closure, one-shot prepare and M01 launcher use the actual wall clock and expose no replay-clock option. Freshness is checked again by the existing binding gate at the later call time; parsing a file does not renew its age. Only the explicitly offline persistent preflight, synthetic pre-live convergence runner and offline Golden witness accept the required `--startup-observation-unix` frozen clock. These observations remain replay evidence and do not prove the current account state.

## Document contract and trust boundary

Schema `peaktrade.startup_portfolio_observation.v1` requires exactly these fields: `schema`, `account_identity`, `instrument_type`, `complete_account_scope`, `pending_orders`, `source_id`, `event_time_unix`, `wall_time_unix`, `positions`.

The instrument scope is the existing account-observation **SWAP** scope; this is not proof of all derivatives or dated-FUTURES coverage. The account must equal the separately configured expected identity, complete scope must be Boolean true, and pending orders must be Boolean false. The event must be no more than five seconds old relative to the applicable observation clock, with event time ≤ capture time ≤ now. Position rows contain exactly canonical `instrument_id`, decimal-string `signed_quantity` and its matching `side` (LONG/SHORT/FLAT). No quantities are aggregated, filtered out or replaced with defaults.

**This is a trusted input port, not authentication.** A document can declare an account and complete scope; this reader cannot prove that the producer actually observed the exchange. Existing authenticated account-observation infrastructure must supply it. No public/default account document is installed, no real UID inferred, no acquisition or credential capability added, and no account files are read by these changes themselves. A live document belongs to the configured private data plane. Real source/service provisioning and startup readiness remain open.

The document carries position truth only. It cannot set capital, cash, margin, risk policy or sizing. The existing Cap24 reconciliation/binding gate and its observation hooks remain in use; no synthetic reconciliation success or new capture context is injected. U04, P01, budget formulas, reservation semantics, DDO/learning and promotions remain unchanged. U04 is explicitly deferred at Frank's request; [investigation](../evidence/U04_ORIGINAL_INTENT_AND_LEARNING_PATH_DEFERRED_2026_11_03.md).

## Validation and remaining limits

[Dated evidence](../evidence/LEGACY_STARTUP_OBSERVATION_PORTS_2026_11_03.md) records interface tests, existing startup regressions and the five independently reproduced baseline full-flow failures. Static forwarding of seven calls and deterministic injected tests are not a complete live-start proof. No previous closed-loop or whole-repository completion claim is extended here.

## Local producer implementation — 2026-11-03

The [dedicated observer source adapter](ACCOUNT_OBSERVATION_STARTUP_SOURCE_V1.md) now exports this existing document through the shared collector, revalidates freshness before atomic non-overwriting publication and checks ordinary plus four documented algo pending-order classes. It retains the existing reader and schema. Injected proof is not provisioning of an authenticated provider or full coverage of every venue product.

## Explicit K1 selection and lifecycle audit — 2026-11-03

Frank selected the already-configured K1 credential service. The [K1 source profile and capital lifecycle contract](K1_TREASURY_ACCOUNT_SOURCE_AND_CAPITAL_LIFECYCLE_V1.md) adds an explicit bounded alternative to the dedicated-observer profile, without relabeling credentials or adding fallback. Real account/Trading/Funding reads passed; durable post-close composition is injected-tested. Dedicated observer policy, U04/P01 and economic formulas remain unchanged. Independent real accounting/equity reconstruction and continuous service deployment remain open. Earlier unprovisioned-source statements describe their dated phase/profile.
