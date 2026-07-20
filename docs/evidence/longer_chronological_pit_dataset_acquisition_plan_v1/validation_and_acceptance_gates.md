# Validation and acceptance gates

Machine-checkable gates for `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1`.
Verdicts: `PASS` | `PARTIAL` | `FAIL`.

Economic reevaluation is allowed only on `PASS`, or on `PARTIAL` with explicit operator GO and reduced claim set.

## Gate catalog (20)

| ID | Gate | PASS | PARTIAL | FAIL |
|---|---|---|---|---|
| G01 | Coverage per instrument-month | ≥95% expected PT1H bars for eligible months | 80–95% with logged gaps | &lt;80% or missing month unmarked |
| G02 | Panel calendar span | ≥36 months continuous claim window | 24–36 months | &lt;24 months |
| G03 | PIT universe correctness | Epoch membership matches lifecycle registry exactly | N&#47;A | Any look-ahead include |
| G04 | Listing parity | Every member has `listing_time` ≤ first eligible bar | Rare unknown listing with quarantine | Missing listing used as member |
| G05 | Delisting parity | No bars after `delisting_time` | N&#47;A | Post-delist bars present |
| G06 | Time monotonicity | Strictly increasing timestamps per instrument | N&#47;A | Any regression |
| G07 | Duplicates | Zero duplicate timestamps | N&#47;A | Any duplicate |
| G08 | Candle gaps | Gaps enumerated; coverage still meets G01 | Gaps cause PARTIAL coverage | Silent gap fill detected |
| G09 | OHLC cross-field | high≥max(o,c), low≤min(o,c), all finite | N&#47;A | Violation |
| G10 | Extreme jump screen | Flags only; research may proceed if documented | Spike rate elevated | Impossible prices (≤0) |
| G11 | Funding timeline | Funding present for ≥80% eligible instrument-months | 50–80% | &lt;50% without PROXY tag |
| G12 | Contract metadata | Spec snapshots cover membership | Sparse snapshots with provenance | Unknown contract used for sizing claims |
| G13 | Fee provenance | Versioned fee table or explicit CONFIG_BOUND_PROXY intervals | PROXY for full span | Silent fee assumption undocumented |
| G14 | Slippage provenance | MODEL_PROXY tagged; no fake L2 | N&#47;A | Claimed L2 without source |
| G15 | Hash reproducibility | Second normalize reproduces digests | N&#47;A | Digest drift |
| G16 | Manifest completeness | All required digests present | N&#47;A | Missing digest |
| G17 | Repeat acquisition | Re-fetch sample partitions match sha256 | N&#47;A | Byte drift unexplained |
| G18 | Look-ahead leak scan | Zero future-listed instruments in past epochs | N&#47;A | Any leak |
| G19 | BTC &#47; spot exclusion | Zero BTC &#47; spot members | N&#47;A | Any present |
| G20 | No forward fill | Detector finds zero filled holes | N&#47;A | Forward fill detected |

## Aggregate qualification

| Aggregate | Rule |
|---|---|
| PASS | All of G03–G09, G15–G20 PASS; G01–G02 PASS; G11–G14 PASS or tagged PARTIAL with approval not required if funding&#47;fee PROXY explicitly accepted in contract defaults |
| PARTIAL | G02 PARTIAL (24–36m) **or** G01 PARTIAL **or** G11&#47;G13 PARTIAL; no FAIL gates |
| FAIL | Any FAIL gate |

## Conservative defaults baked into this plan

- Fee PROXY allowed for research economics with tag (G13 PARTIAL acceptable without extra GO).
- Slippage remains MODEL_PROXY (G14 PASS when tagged).
- Funding PARTIAL does not block OHLCV-only qualification but blocks funding-factor strategies.

## Automation expectation (later implementation PR)

Emit `gates&#47;Gxx.json` plus `qualification_verdict.json`. Tests must assert fail-closed on G03&#47;G18&#47;G19&#47;G20.
