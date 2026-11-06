---
docs_token: DOCS_TOKEN_TREASURY_K1_AND_CAPITAL_LIFECYCLE_2026_11_03
status: scoped-real-read-and-injected-lifecycle-proof
scope: Source reconstruction, explicit K1 reads and capital/close/accounting audit; U04 deferred
---

# Treasury K1 and capital lifecycle — 2026-11-03

Base: 3bfd8e64024f8bbae96e52cdbfbb52a65499c1c3. Frank requested completion of feasible source/account and capital/bookkeeping work, explicitly retained U04 deferral, identified K1 as the credential service and requested external/recovery comparison.

## Reconstructed configuration

The M2DATA backup at commit 242b7974fc93f0bdb47706556101bd6f0c497414 has byte-identical K1 identifier binding and GET-only session binder, plus the same unbound dedicated observation policy, as the starting checkout. Two recovered Markdown specs corroborate the K1 service/account/provider tuple. The alternate M1_5 worktree has a distinct K1 admission variant with mixed tracked/dirty GET-path files; it was not copied or executed. [Paths, hashes and search limits](treasury_k1_and_capital_lifecycle_v1_2026_11_03/external_configuration_sources.json).

A broad MD-recovery query encountered an I/O error in an unrelated AppleDouble file and was stopped. No repair, remount, scan regeneration or external write occurred. The two already-found small spec files were then read. This is not exhaustive recovery completeness or evidence that no other configuration exists.

## Real acquisition results

[Real account-scope receipt](treasury_k1_and_capital_lifecycle_v1_2026_11_03/real_readiness.json): **PASS**, seven private GET attempts through the existing K1 session. Configured account matched. Unfiltered position rows, ordinary pending orders and each of four documented untriggered algo classes were empty within a 1.22-second observation window. This is a dated account observation, not a permanent flat guarantee or coverage of every bot/subaccount.

[Real Treasury-input receipt](treasury_k1_and_capital_lifecycle_v1_2026_11_03/real_treasury_inputs.json): **PASS**, three private GET attempts in a separate purpose-bound session. Trading USDC availEq was observed numerically. Funding USDC was ABSENT_NOT_ZERO; no balance was invented or transferred. Account-equity target was observed; equity reconstruction and capital admission stayed false.

Total real attempts: **10**, with no automatic retries, orders, transfers, currency conversion, portfolio adoption or service activation. API values, raw rows, key material and UID are absent from the receipts. The independently configured account is retained in the identifier-only config; it was not learned from the response.

The actual probes preceded the final config-loader/numeric-validation refinements. The exact source snapshots and hashes of the second, Treasury-input probe are preserved in [real-probe source bindings](treasury_k1_and_capital_lifecycle_v1_2026_11_03/real_probe_source_bindings.json). A whole-source digest was not captured for the first scope probe; source/CLI gained the separate Treasury check before the saved snapshot. The first receipt proves that dated observation, not an exact whole-source build. Current code is separately bound and unit-tested. No redundant real read was performed merely to reseal evidence. The real probes do not prove every final code revision in live runtime.

## Implementation and local verification

[Contract](../specs/K1_TREASURY_ACCOUNT_SOURCE_AND_CAPITAL_LIFECYCLE_V1.md) and [configuration](../../../config/ops/treasury_k1_account_source_v1.json). The explicit K1 profile reuses existing native acquisition, signing and GET transport, common collector and export. The dedicated observation policy remains unchanged and no artificial observation credential is minted. Redirects are rejected before signed headers can be forwarded; a real urllib handler-chain test verifies a single request only.

[Final integrated JUnit](treasury_k1_and_capital_lifecycle_v1_2026_11_03/integration_current_tests.xml): **178 passed**, including K1 parse/sign/HTTP composition with injected OS/HTTP boundaries, source/export negatives, redirect isolation, actual post-close feedback joined to a durable owner, restart/replay/recovery, partial-close custody retention, execution uncertainty/reconciliation and existing accounting/Treasury regressions. The earlier 163/177-case runs predate the final input/config or request-attempt-quota refinements and are historical; overlapping counts are not added.

The durable full-close proof releases the original hold using the existing canonical 75-unit test producer output, preserves its close marker across reopening, then requires fresh canonical recovery before readmission. A repeated close cannot bypass the restart fence. Partial close retains the 40-unit fixture hold and custody. These are isolated synthetic test values, never live capital inputs. No capital/learning/Double-Play or U04 policy formula changed.

## Completed versus still open

Completed: reconstruction of the existing K1 configuration from multiple sources; explicit local K1 source/config/launcher; actual authenticated read connection and supported account-scope check; actual Trading/Funding source-presence check; scoped causal audit and durable composition proof for the existing close/custody/canonical-capital feedback.

**Not complete: independent real accounting/equity reconstruction.** The [accounting bridge](../../../src/ops/productive_futures_accounting_runtime_binding_v1/bridge_binding_v1.py) applies intended actions through simulated fills and an analytical shell. Its [constants](../../../src/ops/productive_futures_accounting_runtime_binding_v1/constants_v1.py) include synthetic default initial equity and a bound-not-activated status. The [equity source architecture](../../../src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_account_equity_source_architecture_v1.py) keeps stock reconstruction distinct from sizing, and the current stock source is unbound. Observed totalEq is the reconciliation target, not a substitute source. The implementation/call path, not only a status label, is the basis for this limitation. Actual event completeness, source semantics, genesis and real fee/funding/liability attribution remain unproven. No new accounting algorithm or default opening stock was invented to make the report green.

U04 remains expressly deferred. Unattended/service deployment, continuous-run composition/quota, whole-system restart atomicity, broad repo documentation alignment and GitHub CI remain later work. Existing entry and close contracts are not a fully activated Treasury/bookkeeping system. [Verification manifest](treasury_k1_and_capital_lifecycle_v1_2026_11_03/verification_manifest.json) records preservation and source bindings.
