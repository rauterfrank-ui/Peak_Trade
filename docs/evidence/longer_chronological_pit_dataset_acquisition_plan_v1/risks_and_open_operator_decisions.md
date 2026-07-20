# Risks and open operator decisions

## Risks

| Risk | Mitigation |
|---|---|
| Public candle history shorter than 36 months | Depth probe first; fall back to 24m PARTIAL or commercial GO |
| Delisted symbols invisible on live instruments API | Lifecycle snapshots + optional curated recovery list; fail-closed if missing |
| Survivorship temptation (use today's 118 forever) | PIT universe rebuild per epoch; gate G03&#47;G18 |
| Silent forward fill to “heal” gaps | Forbidden; G20 |
| Fee schedule drift ignored | PROXY tag mandatory if no schedule table |
| Rate-limit bans mid-acquire | Resume partitions; polite limiter; no parallel storm |
| Mixing sealed v1 digests with new bytes | Additive dataset ID; never overwrite v1 |
| Scope creep into strategy tuning | Separate workstream; this plan forbids |
| Live activation drift | Safety flags forced false in all evidence |

## Open operator decisions (minimized)

Only these require later human GO:

1. **Public-first vs commercial historical source** if depth probe cannot reach ≥24 months PIT-safe.
2. **Storage budget** confirmation (≥20 GiB recommended before bulk acquire).
3. **Accept 24-month PARTIAL** instead of 36-month PASS if public depth is insufficient.

Everything else uses conservative defaults documented in the target contract.

## Non-decisions (already frozen)

- Venue = OKX
- Futures linear USDT only
- BTC &#47; spot excluded
- PT1H UTC
- Economic gate closed
- No private keys
- No paid booking in this plan PR
- No bulk download in this plan PR
