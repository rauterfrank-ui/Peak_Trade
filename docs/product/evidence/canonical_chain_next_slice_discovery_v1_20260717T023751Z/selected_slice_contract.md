# Selected Slice Contract — NONE

## Decision
`SELECTED_NEXT_SLICE=NONE`

No new bounded implementation slice is authorized by this discovery.

## Exact scope
Discovery/evidence only. No code mutation of trading, strategy, risk, execution,
authority, runtime bridge, dashboard, CI, or tests beyond this evidence pack.

## Exact owners
- Discovery evidence owner: `docs/product/evidence/canonical_chain_next_slice_discovery_v1_<UTC>/`
- Canonical total decision owner (unchanged): `run_integrated_offline_trading_logic_replay_v1`
- Canonical replay input builder (unchanged): `build_integrated_offline_replay_input_v1`

## Allowed files
- Only this evidence directory in the discovery PR.

## Forbidden files
- `src/**` trading/backtest/runtime owners
- dashboard templates/CSS/tests
- CI workflow / required-check mutations
- any runtime activation surface

## Invariants
- `RUNTIME_BRIDGE_STATE=BOUND_NOT_ACTIVATED`
- Strategy→core binding remains via suitability agreement material on MV2 canonical path
- Classic engine remains fill simulator on system path / legacy-non-authoritative on research path
- Strategy outputs must not project into CanonicalMarketContextV1 feature maps
- `LIVE_AUTHORIZED=false`, `ORDERS=false`, `SHADOW=false`, `PAPER=false`, `TESTNET=false`

## Acceptance tests (for this discovery PR)
- Evidence MANIFEST verifies
- Docs reference targets / token policy if applicable
- No productive code diff

## Rollback boundary
- Revert this docs/evidence commit only.

## Explicit non-goals
- Re-implement STRATEGY_SIGNAL_TO_CANONICAL_CORE_BINDING_V1
- Force classic research callers through integrated orchestrator
- Project strategy signals into CMC
- Activate runtime bridge
- Create StrategySignal consumer redesign
- Economic evaluation / promotion

## Separate implementation GO required
`SELECTED_SLICE_SEPARATE_GO_REQUIRED=true`

Any future implementation requires a new uncertainty statement and a separate
operator GO naming an exact new scope. This discovery does not authorize mutation.
