# Limitations and blockers

## Limitations

1. Instrument input is a policy-compatible scaffold lifecycle **sample**, not the
   sealed production universe / lifecycle registry dump (none was present locally
   as a git-readable artifact). No second universe truth was committed.
2. Per-instrument request cap (4–5) finds whether the target 3-year window appears
   reachable; it is not an exhaustive archive crawl to absolute genesis.
3. Sample `listing_time` values can differ by hours/days from public candle
   earliest timestamps → overall `lifecycle_clipping_valid=false` even when the
   partition planner clips correctly to the sample listing.
4. `LUNA-USDT-SWAP` public history appears recent-only (`three_year_depth=NO`);
   treat as edge-case / possible relist discontinuity, not as panel coverage.
5. Raw OKX responses are hashed externally; only compact metadata is in git.

## Blockers

- none for this probe slice
- next acquisition steps remain blocked on operator GO for mass download and on
  binding to the sealed production lifecycle registry for authoritative listing
  times

## Explicit non-claims

- MASS_DOWNLOAD_STARTED=false
- CREDENTIALS_USED=false
- ORDERS=false
- ECONOMIC_GATE_OPENED=false
- PROMOTION_ELIGIBLE=false
- no economic reevaluation performed
