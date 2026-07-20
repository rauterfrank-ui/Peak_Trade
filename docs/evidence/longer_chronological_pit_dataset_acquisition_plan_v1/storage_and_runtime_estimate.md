# Storage and runtime estimate (conservative)

No downloads performed. Estimates are order-of-magnitude planning figures.

## Assumptions

| Assumption | Value |
|---|---|
| Instruments (active over span, union) | 150–300 (wider than sealed 118 due to listings&#47;delistings) |
| Bars &#47; instrument &#47; year | ≈ 8 760 PT1H |
| Years | 3 |
| Raw JSON candle row | ≈ 120–200 bytes |
| Funding rows | ≪ candle volume |
| Metadata snapshots | small (&lt;1 GiB) |
| Digests &#47; manifests &#47; logs | &lt;1 GiB |

## Storage bands

| Layer | Low | Mid | High |
|---|---:|---:|---:|
| Raw candles | 0.5 GiB | 1.5 GiB | 4 GiB |
| Raw funding + meta | 0.1 GiB | 0.3 GiB | 1 GiB |
| Normalized panels | 0.5 GiB | 2 GiB | 5 GiB |
| Quarantine &#47; retries | 0.1 GiB | 0.5 GiB | 2 GiB |
| **Total public-first candles path** | **≈1.2 GiB** | **≈4 GiB** | **≈12 GiB** |

Commercial L2 &#47; tick archives (out of default scope): **100 GiB–multi TB** — blocked without operator GO.

## Runtime (public REST, indicative)

| Phase | Estimate |
|---|---|
| Bounded depth probe (no bulk) | minutes–1 hour |
| Full 3y candle+funding acquire @ polite rate limits | hours–few days wall-clock |
| Normalize + validate | tens of minutes–few hours |
| PIT universe build | minutes–1 hour |
| Qualification suite | minutes–1 hour |

Rate limits dominate wall clock; design for resume.

## Operator storage default

Assume **≥20 GiB free** dedicated research volume before bulk acquisition GO. If budget &lt;5 GiB, restrict to 24-month PARTIAL target or fewer instruments — requires explicit GO.
