# ENTER 29P / cursor: current-configuration alignment

docs_token: DOCS_TOKEN_ENTER_29P_CURRENT_CONFIGURATION_ALIGNMENT_2026_11_03

2026-11-03, base revision `040db81400cfde273258bb600447e3f04bc8bdb4`. This closes the **18 failures in the two cursor/ENTER-29P files** recorded by the preceding Treasury checkpoint. It does not close all Treasury accounting or repository-wide CI work.

## Cause and correction

Replay fixtures conflated internal canonical identity with venue-native contract ID and supplied G17 estimates dated after their first C1. They now use a coherent identity pair, the existing G17 producer with history ending at the first C1, and a cache keyed by both identities. Envelope assertions distinguish internal decision identity from native wire identity. No production identity or future-time guard changed.

Old calls expected ENTER to pass without the mandatory shared reservation owner. Fixtures now use the explicit test owner/slot composition; the negative test without an owner remains and must fail. The host already supplies pre-join offline algebra. Tests require its subsequent replacement with account-bound canonical sizing. The generic ENTER helper now rejects non-ENTER input instead of rewriting the decision outcome.

Protective-stop tests previously assumed a fixed 80-unit distance and historical fixture prices. They now check the evaluated GGE-based adverse distance, a positive correctly directed stop, and the actual native stop supplied to monetary normalization while invoking the real normalizer. At-mark/above-mark rejection cases follow the actual fixture mark. Both Long and Short traverse account-bound sizing. No production runtime file, stop formula or sizing policy changed.

The old source guards required zero diff against moving origin/main, rejecting the already approved GGE-only changes. They now pin SHA256 values for **every listed core/ranking/selection/sizing/config file** at `c17ffa3f9`. No path exemptions. Negative tests prove rejection of a later edit and an unreviewed protected path. Atlas tests use stable component IDs instead of removed heading strings. A venue-plan test pins the runbook's existing reviewed closure SHA; the runbook header remains unchanged.

The wider consumer check also exposed short/unready histories, unknown harness native IDs, a future-dated G17 fixture and an occupied account without its required cursor. Setups now use coherent histories/identities/timestamps; the missing-cursor test explicitly requires blocked replay and no invented cursor. Production safeguards are preserved.

## Validation and limits

- `focused_tests.xml`: **51 passed**, covering both original files, host stop binding, Layer-C distance and source-protection negative cases. The original 18 failures are resolved.
- `consumer_remediation_tests.txt`: **85 passed**, covering all six consumer files updated after the wider check: bilateral natural entry, C1 duplicate/cursor carry, occupied-state safety, venue-plan fields, WP2 and P5 startup.
- `impact_diagnostic_tests.xml.gz`: initial wider check, **233 passed / 10 failed across 243 cases**. All ten failed cases belong to the six files subsequently passing the 85-case remediation run. This diagnostic is retained as chronology, not represented as a clean full-suite run. Other passing cases include reservation/contention/restart, outer budget and productive causal joins. Groups overlap and are not summed.
- Ruff passes for all 11 changed Python files. Source hashes, documentation checks, Atlas generation/drift and the unchanged historical learning ledger are bound in the verification manifest.

All account observations/transports are injected and state is temporary. No credentials, actual private GET, orders, transfers, service activation or GitHub push. Deterministic regression evidence does not prove live account behavior, complete Treasury or whole-repository/GitHub CI readiness.

U04 attribution versus separately deducted active reservations, seven older Cap24 callers, real bootstrap/service-root provisioning and complete Treasury close/custody/equity reconciliation remain open. Prior reports and raw diagnostics retain their original meaning. Blueprint section 25 records the correction to section 24's earlier entry failures.
