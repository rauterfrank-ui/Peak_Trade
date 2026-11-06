---
docs_token: DOCS_TOKEN_K1_TREASURY_ACCOUNT_SOURCE_AND_CAPITAL_LIFECYCLE_V1
status: implemented-scoped-proof-with-open-accounting-boundary
scope: Explicit K1 account-read profile, source configuration and existing close lifecycle verification
---

# K1 account source and capital lifecycle v1

Frank identified the existing K1 as the intended credential service and requested checks of M2DATA and recovery sources before replacement. This selects an **explicit K1 GET-only profile** for the new composition. The separate dedicated-observer profile and its trade-key rejection remain intact; K1 is never relabeled as its observation credential. No fallback from that separate profile is introduced.

## Configuration and factory

[Identifier-only configuration](../../../config/ops/treasury_k1_account_source_v1.json) binds the already-existing K1 service/account/provider reference, independently expected account identity, EEA host and bounded request quota. The tuple is corroborated by a dated external backup and recovery documents. The identity is not inferred from an API response. Service activation remains false.

[Source factory](../../../src/ops/okx_eea_private_account_state_runtime_v1/k1_source_v1.py) composes the existing K1 OS-native acquisition/signing session with the existing productive GET transport and the shared account collector/export adapter. The paired handle must be the transport's actual K1 handle. The adapter validates that handle under its real class, rather than fabricating a dedicated observation handle. Existing source-class checks still reject a trade class in the dedicated route. The profile's narrow transport has no order/transfer/withdraw endpoint or POST method.

The lifecycle clears adapter access, transport caches and the borrowed handle reference when the existing K1 session ends. Its existing session owner releases the signing material. This is reuse of K1; it does not prove OS-wide process isolation or that the underlying exchange key itself has exclusively read permissions.

The productive GET transport now rejects redirects through urllib's redirect handler before signed headers can be forwarded to a second request. The final-host check remains. Failed redirect/error attempts consume the existing request quota, so retrying an exception cannot evade the count. A real opener-chain test proves that a redirect to a foreign host produces no second request.

## Operator entrypoint

[Readiness launcher](../../../scripts/ops/run_k1_account_observation_readiness_v1.py) accepts an explicit configuration or explicit expected account. With neither, it rejects. Config-only validation does not open Keychain or contact the venue. Unknown config fields, duplicate keys, conflicting account overrides, changed K1 tuple, host, profile, quota or service-activation scope fail closed.

```sh
./scripts/pt scripts/ops/run_k1_account_observation_readiness_v1.py --config config/ops/treasury_k1_account_source_v1.json
```

Adding `--observe-once` performs one explicit bounded K1 read session without automatic retry. Its default audit uses seven GETs: account config, unfiltered positions, unfiltered ordinary pending orders, and the four documented untriggered algo classes without an instrument-type filter. Unsupported/unknown position product types and existing pending custody are blockers for the current SWAP consumers. It does not adopt positions or activate a host.

Adding `--treasury-inputs` to that explicit observation selects a separate three-GET check: account config, Trading account balance and Funding account balances. It checks the exact Trading USDC availEq row using the existing numeric margin validator and reuses the existing Funding parser. Missing currency rows are not zero; Funding availBal, USD, USDT and account totalEq cannot substitute for Trading USDC free margin. Zero is a valid observed number, not proof of sufficient admission capital. Account totalEq is observed only as a reconciliation target.

An optional new absolute output file is created with mode 0600 and cannot replace an existing path. Output contains statuses/counts, not API material, raw account rows, quantities, amounts or UID. The source supports the existing callback and export interfaces; consumers must pass it explicitly while its session is open. The bounded readiness configuration is not an installed continuous N1 service manifest or an aggregate continuous-run quota.

## Capital, close, custody and accounting boundaries

The current entry capital source remains fresh USDC free margin through the existing Treasury/E4/C08/29P producer, followed by the single durable reservation owner and sizing/admission gates. U04/P01 formulas and the default helper are not changed or declared resolved. Raw observed equity and the separate simulated accounting portfolio do not mint sizing capital.

The existing post-close feedback already requires a matching closing execution, complete reconciliation, flat-position proof with causal chronology, clear pending custody and fresh canonical capital after the position evidence. It then invokes the existing durable owner refresh. Partial close retains custody and capital. Ranking review is a separate owner and does not automatically persist membership.

New composition tests now exercise this feedback through a durable owner, restart, close replay and fresh canonical recovery. The persisted release and refresh marker survive. Replaying the same close is idempotent and does not clear restart admission fencing. The fresh reconciliation/capital gate must still run before readmission. No new capital or PnL formula is introduced.

**Accounting limit remains explicit:** the existing productive accounting bridge consumes simulated fills, permits default synthetic initial equity and projects into an analytical portfolio shell. Its green arithmetic tests are not a real-account ledger. The independent equity-stock source remains unbound; raw venue totalEq is a reconciliation target under the existing source architecture. No complete real event stream, genesis, fee/funding/liability coverage or running real equity reconstruction is established here. Closing this requires that source/semantic construction; it cannot be achieved by routing the simulated default or raw totalEq into Q0. This is distinct from deferred U04. The capital/custody audit has been performed, but complete real bookkeeping must not be marked finished.

[Detailed evidence and remaining boundaries](../evidence/TREASURY_K1_AND_CAPITAL_LIFECYCLE_2026_11_03.md). No service, trading session, order or transfer is authorized by this specification.

Further reconstruction (2026-11-03): [historical accounting replay and real unfiltered bills observations](ACCOUNT_BILLS_OBSERVATION_AND_HISTORICAL_REPLAY_V1.md). Historical stock was found, but its bridge to current stock and classified event completeness remain unproven.

Fortschreibung vom 03.11.2026: [privates Originaljournal, aktueller Anker-/Kontoverbund und vollständiger beobachteter Bewegungsweg](REAL_EQUITY_WINDOW_RECONCILIATION_V1.md). Der damalige Beobachtungsschritt bleibt als Nachweis erhalten. Die neue Prüfung schließt die pauschale Anker-/Journal-/Klassifikationslücke für das datierte Fenster; der exakte allgemeine Venue-Präzisionsvertrag bleibt unbelegt.
