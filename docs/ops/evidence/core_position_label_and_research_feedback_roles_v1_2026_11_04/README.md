# Core position, DDO label and research feedback roles — 2026-11-04

Pin 9dd176b62; Blueprint 74. Read-only continuation after the scoped HOLD repair.

## Existing operational-state return versus learning

The inspected offline qualification and bounded differential-walk scripts have an
actual next-epoch state path: capture the simulated filled position after the
replay/action, retain it as pending observation, apply it to next sequence state
and attach it to next replay input. The replay's dynamic capital context consumes
that observation for open quantity/exposure/side/count through existing owners.
This is static producer→intermediate→consumer evidence, not an invoked run. It
returns observed simulated position state; it is not strategy optimization or a
claim that Learning may change core policy. No new parallel position owner is needed.

DDO's separate ratified next-cycle seam consumes only next_cycle_economic_score_label.
The reducer copies an opaque outcome token into state. The bridge checks the current
resolved configuration before applying it, and passes it to the N_BARS horizon
observation producer after canonical replay/capture. It does not become a numerical
feature, candidate, sizing decision or learning algorithm. The subordinate original
contract explicitly limits it to evaluation-observation label feedback. Preserve
that boundary instead of treating it as missing direct trading adaptation.

## Existing core-native simulated measurement and its identity limit

The replay-to-portfolio adapter and round-trip collector provide numeric simulated
lifecycle economics. The collector distinguishes completed trips and open-position
economics, stores fees/slippage/funding/net PnL and optional epoch/timestamp/decision/
strategy/context descriptions, then emits a content-bound document with caller
bindings. Parent document/run bindings can carry context absent from an individual
row; row-level absence alone does not prove a missing join.

The bounded walk's metadata builder assigns composition_status to the field named
market_regime_at_entry and emits NOT_EMITTED for volatility context. These are not
by themselves the canonical runtime regime or a measured volatility feature.
Round-trip IDs are local collector identities. Before any Learning/Meta join,
resolve actual enclosing run/dataset/config/decision records and their versions;
do not mint a missing canonical experiment identity from these names.

The integrated economic policy counts completed FLAT→NONZERO→FLAT round trips,
not fills or entries. That differs from Phase11's comparable experiment sample.
The single-epoch completion builder is also not the multi-epoch qualification
script: it uses a baseline input, literal dataset/implementation labels, one
portfolio application and a one-fold artifact with the same net PnL on both
in/out fields and walk_forward_pass=True. These bounded output constructions do
not establish measured separated OOS research or a trained next hypothesis.
They must not substitute for actual observation/split provenance at M4/Phase11.
No new rejection rule or retroactive verdict was imposed on that older contract.

The old simulator and productive futures accounting are distinct owners. Simulation
parameters, per-action funding behavior or simulated field presence do not certify
real funding/accounting. The existing funding structural overlay itself preserves
that distinction; its current productive applicability is not adjudicated here.

## Minimum transition implication

Several inner/outer returns already exist with intentional distinct effects:
position state, label transport, numeric simulated diagnostics and optional research
history inputs. Reuse them by role. The unresolved research transition is to a
versioned, comparable experiment/observation with the actual chosen hypothesis,
not simply another arrow back to the decision core. Whole-system learning and
natural numerical effect remain open. [Sources](sources.json), [receipt/checks](receipt.json).
No runtime code change, run, account/network operation, original-ledger write or
new authority in this review. U04 and GAP-0370 remain deferred.
