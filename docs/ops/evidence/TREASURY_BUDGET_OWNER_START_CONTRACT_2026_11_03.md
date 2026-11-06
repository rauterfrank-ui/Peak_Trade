# Treasury budget-owner startup: scoped implementation evidence

docs_token: DOCS_TOKEN_TREASURY_BUDGET_OWNER_START_CONTRACT_2026_11_03

Date: 2026-11-03. Base revision: `c17ffa3f9`. Scope: explicit expected-account binding, explicit bootstrap/recovery and a shared durable root for the normal N1 host. [Contract](../specs/TREASURY_BUDGET_OWNER_START_CONTRACT_V1.md). No live readiness claim.

## Implemented

Normal startup uses recovery only. Lost state fails closed instead of implicitly creating an empty owner. Expected account identity is mandatory and checked before store creation/opening. Explicit create mode cannot reopen an existing scope and does not admit capital. Public, evidence and lane roots cannot overlap the resolved private budget-owner root. Rotating the evidence/session identity preserves the same owner and existing committed reservations. Test fixtures now initialize their own synthetic metadata explicitly; production has no matching automatic setup fallback.

Only the budget host and standing supervisor production files change. Capital production, sizing equations, reservation/release semantics and private transport permissions remain unchanged.

## Validation and limits

- `start_host_tests.xml`: 84 passed. Start-contract tests (24 at that point), budget host, standing supervisor, account-bound startup and runtime liveness. This run preceded the extra test that prevents a lost observation cache from resetting the configured identity.
- `recovery_capital_tests.xml`: 131 passed on the final host implementation, including all 25 new start-contract cases, durable budget recovery, execution recovery, outer-entry policy, Treasury handoff, post-close feedback and budget host. Includes existing subprocess SIGKILL coverage and preserved reservation/sizing identities; this is not whole-host/power-loss or real exchange evidence.
- `launcher_controller_tests.xml`: 13 passed, including real disposable N1 process SIGKILL and bounded restart. Temporary owner metadata is created once before the first test process; restarted workers only recover it.
- Ruff passes for all ten changed Python files. Atlas generation, documentation checks and source hashes are recorded in the adjacent verification manifest.
- Changed-document reference check passes: 10 Markdown files, 671 references. Two older directory mentions in the runbook were reworded as directory descriptions because this gate expects file targets; no gate code or ignore rule changed.

Test groups overlap and are not additive. All private observations, account IDs, state roots and transports in these runs are injected fixtures. No credentials were loaded, no real private GETs/orders/capital movements or service activation were performed.

Broader entry diagnostics: the two unchanged cursor/29P test files produce 4 passed and 18 failed in `entry_baseline_diagnostic_tests.xml.gz`. Early failures are in their replay fixtures before Treasury-host startup; other failures include the historical origin/main protected-file comparison and old Atlas heading assertion. A temporary fixture modernization probe yielded 18 passed/4 failed, but was withdrawn from this change because the remaining sizing/join and historical-gate differences require their own investigation. Those two test files are byte-identical to base HEAD. The diagnostic is not a Treasury pass and the whole repository is not green. Raw XML bytes are preserved with lossless gzip because failure text contains trailing whitespace; no assertions or production gates were relaxed.

## Remaining Treasury work

The default U04 helper still asserts an empty reservation witness. Its domain versus the shared owner's active holds is unresolved; blindly feeding the same hold sum into both could double-subtract. This work neither validates the zero witness nor changes the capital formula. Seven older Cap24 startup callers still require their explicit portfolio observation. Real account/root provisioning, controlled initial bootstrap, service manifest and the full Close/custody/equity loop remain pending. The broader repository/Map alignment and GitHub CI are also unfinished.

Working status is recorded in Blueprint section 24. Historical reports/ledgers are retained. This is a local implementation checkpoint, not a GitHub backup or runtime authorization.
