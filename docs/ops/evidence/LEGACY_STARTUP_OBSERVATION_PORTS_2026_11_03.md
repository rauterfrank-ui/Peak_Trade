# Legacy startup observation-port migration

docs_token: DOCS_TOKEN_LEGACY_STARTUP_OBSERVATION_PORTS_2026_11_03

2026-11-03; base `aadba02744b20de9fa2129765b53a8504933b757`. [Contract and trust limits](../specs/LEGACY_STARTUP_OBSERVED_PORTFOLIO_PORTS_V1.md). U04 is deferred and its production source is unchanged.

## Implemented and bounded

All seven original direct Cap24 calls now forward explicit observed portfolio and clock inputs: pre-live convergence, one-shot prepare, persistent preflight, Full-Core closure CLI, both Golden offline witness sites and M01. Their API/CLI parents carry those inputs without inventing a flat account. The common document reader preserves canonical signed positions, checks claimed account/scope/order/freshness fields and rejects malformed or ambiguous input. Parent CLIs require explicit document/account configuration. Only the three explicitly offline diagnostic runners expose a frozen clock.

There is no new authenticated acquisition, automatically provisioned private source or operational deployment. A document is a trusted input contract, not proof of exchange authenticity. Core reconciliation and existing capture hooks remain unchanged. No U04/CT, P01, capital/risk/sizing, reservation, training, horizon or promotion implementation changed.

## Verification

- `migration_contract_and_consumer_tests.txt.gz`: 55 cases, **50 passed / 5 failed**. Includes all 34 new document/forwarding cases, positive real preflight/observed-state and pre-live fixture calls, negative wrong-account/stale/pending/duplicate/position cases and unchanged consumer checks. The five failures are listed below, not hidden by exclusions or changed assertions. Raw diagnostic bytes are compressed losslessly because failure text contains trailing spaces.
- `startup_regressions.xml`: **51 passed**, existing account-bound N1 startup, standing supervisor, Cap24 provenance handoff and M01/F1/M9/G17 connection tests. Groups can overlap and are not added.
- `baseline_five_failure_reproof.xml.gz`: all five remaining cases fail on the original three API modules loaded from Git base in an isolated process, without checkout writes. Two persistent-flow cases fail unknown harness-native identity or natural ENTER expectation; three old one-shot full-compose cases return `MARKET_STATE_HOLD_NOT_ENTER`. These remain open; no fabricated ENTER or trading-core repair is used to green them. `baseline_reproof_sources.json` binds the loaded module bytes and method.
- CLI help checks cover all six parent launchers. Source review/AST inventory verifies all seven explicit forwards. Ruff checks all 14 changed production/CLI/test Python files. Docs and Atlas checks, source hashes and unchanged U04/learning-ledger hashes are in the verification manifest.

The initial API regression work exposed missing explicit input in four fixtures. Those fixtures now supply their own declared temporary/frozen account snapshot; this does not install a default in production.

Tests and causal probes use temporary stores, declared synthetic observations and injected transports. No actual private GET, credential lookup, orders, transfers or service activation; no GitHub push. Real account observer/document provisioning, non-SWAP account scope, the five baseline full-flow failures, complete startup/Treasury semantics and whole-repository CI remain open. This closes the missing-argument migration of seven sites, not productive readiness.
