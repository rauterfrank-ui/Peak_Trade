# Canonical Chain Economic Reevaluation v1

```text
SLICE=CANONICAL_CHAIN_ECONOMIC_REEVALUATION_V1
BASE_SHA=bf74d4e3b15daeb6b4d25411ebd016694c54370b
BRANCH=audit/canonical-chain-economic-reevaluation-v1
PRODUCTIVE_FILES_CHANGED=false
STATUS=PASS
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
ENTRY_SIDE=NONE
LIVE_AUTHORIZED=false
ORDERS=false
PRIMARY_BLOCKER_CLASS=E
```

## Verdict

After PR #5338 / #5340 / #5341 the repaired canonical offline chain is
**technically bound and reachable** on the four representative futures fixtures
(1INCH, BONK, AVAX, SOL). The earlier **system-wide zero-trade** finding is
technically lifted (1INCH records 1 offline trade). Economically, the panel
remains **low-sample / fixture-insufficient** (class **E**): total trades = 1
across 11 812 hooked bars, exit/reduce intents dominate entry intents
(~9448∶71), SHORT is state-reachable but **not executed** as a classified
trade side, and the single 1INCH trade shows negative gross/net PnL (−50 /
−0.5% return) without a separable fee/slippage decomposition on that ledger row.

## Scope

READ-ONLY / EVIDENCE-ONLY. No productive code changes. No parameter tuning.
No candidate strategy. No runtime-bridge / live / orders / shadow / scheduler.
Foreign untracked evidence dirs and stashes left untouched.

## Separation of concerns

| Layer | Finding |
|-------|---------|
| 1 Technical reachability | Bound: `mv2_decision_replay_series` → integrated offline replay → `transition_state` / composition / entry-exit |
| 2 Executed trade direction | 1 trade total; LONG/SHORT side columns not classified on ledger (`long_trades=0`, `short_trades=0`); SHORT SideState reachable |
| 3 Gross economy | 1INCH gross_pnl=−50 / gross_return=−0.005; others 0 trades → gross N/A or 0 |
| 4 Cost effect | Bound break-even roundtrip = 30 bps (fee 10 + slip 5 ×2); per-trade fee/slippage separable fields mostly `NOT_AVAILABLE` / fee ledger 0 |
| 5 Sample quality | All instruments &lt; 20 trades → no Sharpe/robustness/walk-forward |
| 6 Primary blocker | **E** low sample + exit dominance annotation |

## Instrument matrix (summary)

| Instrument | Bars | Entry intents | Exit intents | Trades | Gross PnL | Net PnL | Class |
|------------|-----:|--------------:|-------------:|-------:|----------:|--------:|:-----:|
| 1INCH | 2953 | 9 | 2492 | 1 | −50 | −50 | E |
| BONK | 2953 | 52 | 1905 | 0 | 0 | 0 | E |
| AVAX | 2953 | 8 | 2343 | 0 | 0 | 0 | E |
| SOL | 2953 | 2 | 2708 | 0 | 0 | 0 | E |

## Artifacts

| File | Purpose |
|------|---------|
| `summary.env` | Machine-readable closeout |
| `instrument_metrics.csv` | Per-instrument metrics |
| `instrument_classification.md` | A–I classification |
| `chain_binding_proof.txt` | Static + runtime chain binding |
| `economic_reevaluation_probe_v1.py` | Non-authoritative audit harness |
| `probe_summary.json` | Full machine summary |
| `commands.txt` / `tests.txt` / `git_state.txt` | Repro + gates |

## Safety

`RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED`, `ENTRY_SIDE=NONE`,
`LIVE_AUTHORIZED=false`, `ORDERS=false`, no second authority, no classic bypass.
