# P85 — Live Data Ingest Readiness v1

## Goal
Dry online / live-data ingest readiness: verify connectivity, rate limit, schema, and persistency to `out&#47;ops`. No execution, no model calls.

## Scope
- **IN**: MODE (paper|shadow), OUT_DIR, RUN_ID
- **OUT**: `OUT_DIR&#47;P85_RESULT.json`, `OUT_DIR&#47;P85_RUN.log`

## Entrypoint
- `scripts&#47;ops&#47;p85_live_data_ingest_readiness_v1.sh`
- `python3 -m src.ops.p85.run_live_data_ingest_readiness_v1` (reads MODE, RUN_ID, OUT_DIR from env)

## Checks
1. **Connectivity**: REST GET to configurable URL (default: Kraken public Time API)
2. **Schema**: Validate response structure (e.g. `result.unixtime`)
3. **Rate limit**: Best-effort (public endpoints typically OK)
4. **Persist**: Write evidence to `out&#47;ops`

## Notes
- Paper&#47;shadow only. Live&#47;record blocked.
- Requires network for connectivity check unless mocked.
