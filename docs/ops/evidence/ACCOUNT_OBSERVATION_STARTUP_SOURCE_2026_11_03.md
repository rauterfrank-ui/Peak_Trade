---
docs_token: DOCS_TOKEN_ACCOUNT_OBSERVATION_STARTUP_SOURCE_2026_11_03
status: scoped-local-proof
scope: Injected observer adapter, startup, document export and existing host recovery
---

# Account observation startup source — 2026-11-03

Base: dfa3b4f982ff3b469759fa98c4ad7831a536ec67. Frank authorized the next local implementation step. The new [source adapter](../../../src/ops/okx_eea_private_account_state_runtime_v1/startup_source_v1.py) accepts an explicitly paired dedicated observation credential and GET transport, feeds the existing collector/consumers and exports the existing startup document atomically. [Contract and composition API](../specs/ACCOUNT_OBSERVATION_STARTUP_SOURCE_V1.md).

## Demonstrated behavior

The [final integrated run](account_observation_startup_source_v1_2026_11_03/adapter_final_tests.xml) has **124 passed** tests across the new adapter and existing N1 account-startup, budget host, legacy document ingress, private observation runtime and Treasury single-source handoff. The new test module contributes 41 cases. Earlier 118/119-case runs precede the final compatibility/algo changes and are retained as history; overlapping counts are not added.

The tests exercise actual collector normalization and actual startup-document parsing for flat, long and short books; the actual N1 Cap24 gate with an existing short position; private restart with its legacy instrument filter removed; and actual durable host recovery/admission/reservation followed by wrong-account refresh. The failed refresh fences the owner while keeping the prior reservation and amount. No closure or capital gate is replaced to obtain these results.

Negative cases cover invalid GET evidence, wrong/missing account, malformed/error/continuation responses, pending ordinary orders, each of the four untriggered algo types, unavailable algo reads, foreign/duplicate positions, stale acquisition and late pre-publication expiry. Tests also demonstrate no file on failure, mode 0600, no overwrite/symlink/concurrent-target replacement and provider cleanup/closed-session denial. Dedicated trade-credential fallback and mutation capability are rejected.

## Material boundaries

Injected transports deliberately simulate acquisition evidence. These tests do not authenticate an actual exchange session or provision a signer. The paired provider remains the trust boundary for real host/account/credential provenance. Actual observer SecretRef, expected UID, real authorized signing/GET session, request quota, deployment roots and runtimefactory installation remain open. The new context manager is the explicit composition API, not a complete installed N1 factory. Existing CLIs still read their supplied startup document; they do not acquire credentials automatically.

The supported read scope is SWAP positions, ordinary pending orders and four documented algo types. Other derivative types, bot/subaccount obligations, unbounded history and complete live scope are not proven. Historical/fill reads retain their bounded baseline role. The [official OKX endpoint documentation](https://www.okx.com/docs-v5/en/) distinguishes ordinary and untriggered algo order lists; the source contract records the deliberately bounded use. Unsupported/failed reads cannot be treated as empty. No productive dataset or policy was rewritten to expand scope.

U04/P01, sizing/learning/promotion semantics and original runtime ledgers remain unchanged. [Verification manifest](account_observation_startup_source_v1_2026_11_03/verification_manifest.json) binds source hashes and preservation checks. No real private GET, OS-store lookup, order, transfer, service activation or GitHub push occurred. No complete system/remote-CI readiness claim.
