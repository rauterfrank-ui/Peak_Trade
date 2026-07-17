# Before → After (Product Recovery v1)

## Before (operator viewing 20260717T043328Z)

- Giant `unavailable` price typography
- Empty chart ~450px / ~65% viewport
- Green `Active` on Double Play while Decision Blocked
- DE/EN locale mix
- Env-var spam as primary empty content
- Review server without market fixture binding; PID orphan

## After (this slice)

- Compact empty hero: "Governed futures snapshot unavailable" + meta line
- Compact empty chart (`data-market-chart-empty-compact-v1`, ~8.5rem)
- Decision triage marked above-fold after compact chart
- `display_ready` → `CONFIGURED` (muted CSS, not go-live green)
- English operator empty strings
- Recovery bindings in `<details>`
- `PEAK_TRADE_WEBUI_REVIEW_BIND_FIXTURES=1` + identity-ok PID adopt on review_server.sh
- State-aware harness composition contract (empty vs available)


## Evidence capture notes

- Fixtures bound but chart still compact-empty.
