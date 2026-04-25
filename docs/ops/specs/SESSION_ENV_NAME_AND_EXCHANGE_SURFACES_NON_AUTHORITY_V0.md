# Session env_name and exchange surfaces non-authority v0

## Purpose

This note defines a narrow non-authority rule for session environment labels, exchange surface names, and dashboard capability labels.

It exists to prevent names such as `kraken_futures_testnet` from being read as proof that Peak_Trade has a governed, futures-aware exchange adapter or a permitted futures execution path.

## Audit basis

This note is based on the read-only Kraken futures testnet classification audit (operator session; **not** a repo gate or merge artifact). The audit referenced these **filenames** (content may exist only in operator-local working copies, not in this repository unless separately published):

- `KRAKEN_FUTURES_TESTNET_CLASSIFICATION_V0.md`
- `KRAKEN_FUTURES_TESTNET_CALLPATH_MAP_V0.md`
- `MARKET_DASHBOARD_KRAKEN_FUTURES_IMPLICATIONS_V0.md`

Supporting recommendation: `NEXT_ACTION_RECOMMENDATION.md` from the same audit bundle. <!-- pt:ref-target-ignore -->

Those files are local operator or audit artifacts, not repo-canonical evidence and not gate approvals.

## Definitions

### `env_name`

`env_name` is session or registry metadata unless a governed adapter or runner contract binds it to an executable exchange surface.

An `env_name` value is not, by itself, authority to route orders, select an exchange adapter, enable testnet, enable futures, or authorize Live.

### `mode`

`mode` is the pipeline or session mode that controls how the runner selects execution semantics.

`mode` and `env_name` are separate concerns. A futures-like `env_name` does not override the selected `mode`.

### Exchange adapter

An exchange adapter is code that owns concrete exchange or API behavior. For a futures adapter, that includes instrument metadata, contract semantics, order payloads, positions, margin, leverage, funding, liquidation, and risk and safety handling.

### Session registry

The session registry records or describes session metadata and should not be read as execution authority unless the code path proves adapter binding and runtime behavior.

### Dashboard capability label

A dashboard capability label is display metadata. It must not be treated as proof of adapter support, testnet safety, futures readiness, or Live permission.

## Current repo finding

The audit found that `kraken_futures_testnet` is primarily an `env_name` or registry metadata label in the inspected repo state.

The inspected path showed:

- `--env-name` flows into config or session record metadata.
- `LiveSessionConfig` does not contain `env_name`.
- Pipeline selection is governed by `mode`, not by `env_name`.
- In the inspected `testnet` mode path, `LiveSessionRunner._build_pipeline` builds Shadow-pipeline semantics.
- No proven Kraken Futures exchange adapter or call path was identified.
- `src/exchange/kraken_testnet.py` is a spot REST style Kraken testnet or validation surface against `api.kraken.com`; it should not be represented as a Kraken Futures derivatives adapter without a separate governed proof.

## Non-authority rules

1. `env_name` is metadata unless a governed adapter or runner contract proves otherwise.
2. A futures-like string in `env_name` is not futures capability.
3. A dashboard label is not execution support.
4. A registry entry is not adapter support.
5. A testnet label is not a testnet execution proof.
6. A spot exchange testnet client is not a futures derivatives adapter.
7. No `env_name` value grants Master V2 approval, Double Play authority, PRE_LIVE completion, First-Live readiness, operator authorization, production readiness, testnet execution permission, or Live permission.

## Kraken futures / `kraken_futures_testnet` classification

Until a future governed adapter slice proves otherwise, classify `kraken_futures_testnet` as:

- metadata or label surface,
- not a proven Kraken Futures adapter,
- not a futures-testnet execution proof,
- not a futures trading capability,
- not a Live or testnet authorization surface.

Any UI, dashboard, runbook, registry, or CLI help text must avoid presenting `kraken_futures_testnet` as supported futures trading capability by name alone.

## Dashboard implications

A Market Dashboard may display `kraken_futures_testnet` only with an explicit warning such as:

> Metadata label only — no governed Kraken Futures adapter or futures execution path proven.

The dashboard must not provide controls for:

- placing orders,
- enabling testnet,
- enabling Live,
- arming execution,
- toggling risk gates,
- toggling kill switches,
- writing evidence,
- writing archives,
- starting sessions.

For futures-oriented dashboard work, required display fields should be capability-aware and may include:

- instrument type,
- exchange,
- symbol,
- adapter status,
- testnet status,
- futures capability status,
- margin, leverage, funding, liquidation model status,
- data provenance,
- cache or write status,
- no-live banner.

## Future governed adapter slice requirements

A future Kraken Futures implementation must be a separate governed slice.

Minimum requirements include:

1. Explicit exchange adapter surface.
2. Futures instrument metadata:
   - contract type,
   - perpetual or expiry,
   - contract size,
   - tick size,
   - lot size,
   - quote, base, settle currency.
3. Futures order payload support:
   - reduce-only,
   - post-only,
   - close-position behavior where applicable,
   - stop-market or take-profit-market behavior where applicable.
4. Position and risk model:
   - notional exposure,
   - margin mode,
   - leverage,
   - maintenance margin,
   - liquidation distance,
   - funding and funding PnL.
5. Risk, Safety, and KillSwitch contracts.
6. Dry-run and testnet-only tests that do not imply Live readiness.
7. Operator evidence and provenance boundaries.
8. No Live authorization without the existing Master V2 or PRE_LIVE governance path.

## Master V2 / Double Play / Live boundary

This note does not change Master V2 logic.

It does not adapt Master V2 to older exchange labels.

It requires any future futures adapter, dashboard capability, or execution path to adapt to Master V2 and Double Play governance, Scope and Capital Envelope, Risk and Exposure Caps, Safety and Kill-Switches, staged execution enablement, and candidate-specific operator evidence.

## Safety statement

This is a docs-only non-authority note.

It changes no runtime behavior, no session behavior, no exchange behavior, no dashboard behavior, no registry behavior, no testnet behavior, and no Live behavior.

It grants no permission to run sessions, contact exchanges, fetch market data, place orders, write evidence, write archives, or authorize Live.
