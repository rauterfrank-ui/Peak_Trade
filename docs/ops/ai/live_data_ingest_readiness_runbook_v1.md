# Live Data Ingest Readiness Runbook v1 (P85)

## Purpose
Verify live data ingest readiness: connectivity, schema, persistency. **No execution, no model calls.**

## Prerequisites
- Peak_Trade repo
- Network access (for connectivity check)
- `OUT_DIR` under `out&#47;ops&#47;`

## Usage

```bash
OUT_DIR="out/ops/p85_run_$(date -u +%Y%m%dT%H%M%SZ)"
MODE="shadow" RUN_ID="p85" bash scripts/ops/p85_live_data_ingest_readiness_v1.sh
```

## Outputs
- `OUT_DIR&#47;P85_RESULT.json` — checks + overall_ok
- `OUT_DIR&#47;P85_RUN.log` — run log

## Overrides
- `P85_CONNECTIVITY_URL` — override default (Kraken Time API)
- `MODE` — paper|shadow only
