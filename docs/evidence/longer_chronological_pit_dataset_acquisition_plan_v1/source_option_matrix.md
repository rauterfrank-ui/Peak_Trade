# Source option matrix

UNCERTAIN cells are marked explicitly. No vendor is asserted as proven 3-year PIT-complete without probe evidence.

## Options

| Option | Description |
|---|---|
| A. Local sealed archive | Existing `extended_chronological_v1` staging under operator Documents archive |
| B. Public OKX REST | `history-candles`, `funding-rate-history`, instruments endpoints via existing bounded fetch helpers |
| C. Public OKX bulk &#47; candle archives | Any public OKX historical archive pages &#47; dumps if still offered (UNCERTAIN availability) |
| D. Commercial historical vendor | Optional later (Kaiko &#47; Tardis &#47; similar) — **operator GO + license + budget required** |

## Comparison

| Criterion | A Local | B Public REST | C Public archive | D Commercial |
|---|---|---|---|---|
| Real PIT eligibility | PARTIAL — only sealed 4m proven | UNCERTAIN until lifecycle history reconstructed | UNCERTAIN | Potentially strong if vendor provides listing metadata (must verify) |
| Instrument metadata history | Limited to what was snapshotted | Live instruments ≠ historical; need periodic snapshots + other sources | UNCERTAIN | Often better; verify |
| Listing &#47; delisting coverage | Unknown outside sealed window | Weak if only current instruments listed | UNCERTAIN | Often strong |
| OHLCV coverage depth | Equals prior sample (~4m) | Rate-limited; history depth UNCERTAIN per symbol | UNCERTAIN | Usually multi-year |
| Funding coverage | Present in sealed companion manifests | Endpoint exists in repo fetch helper; depth UNCERTAIN | UNCERTAIN | Usually available |
| Fee history | Not in panel | Not a candle endpoint; reconstruct policy tables | Unlikely | Sometimes |
| Spread &#47; L2 history | Absent | Absent on public candle API | Unlikely | Typical differentiator |
| Rate limits | N&#47;A | Real — must throttle &#47; resume | Lower once downloaded | Vendor SLA |
| Reproducibility | High for sealed digests | High if raw partitions + hashes stored | Medium | High if raw stored |
| License | Operator-local archive | OKX public terms | Check terms | Paid license |
| Expected volume (3y PT1H, ~100–300 symbols) | Already on disk for 4m | Roughly **1–5 GiB** raw+normalized conservative estimate | Similar | Candles small; L2 can be **100s GiB–TBs** |
| Operative complexity | Low | Medium (resume, quarantine) | Medium | Higher (procurement) |
| Cost class | sunk | free &#47; infra only | free &#47; infra | paid |
| Central blind spots | No longer chrono depth | History depth; delisted symbol recovery; fee schedule | Availability drift | Cost; contract lock-in |

## Conservative default (this plan)

1. **Public-first (Option B)** as the only path authorized to plan without further GO.
2. Use **Option A** as regression baseline (must bit-reproduce sealed digests before claiming new period).
3. **Option D** remains an explicit operator decision if public depth probe cannot reach ≥24 months PIT-safe coverage.
4. Do **not** book or integrate commercial APIs in this PR.

## Blind spots to force into gates

- Delisted instruments not returned by current `instruments` endpoint.
- Symbol renames &#47; instId changes.
- Candle history truncated by venue.
- Funding holes around suspensions.
- Fee tier changes over 2021–2024.
- Any temptation to forward-fill missing hours → forbidden.
