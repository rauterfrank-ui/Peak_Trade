# Observability Ports Contract

## Metrics Port
- Canonical env: `PEAK_TRADE_METRICSD_PORT` (default: 9111)
- Legacy fallback: `PEAKTRADE_METRICS_PORT` (deprecated; kept for backward compatibility)

## Modes
- Mode A (session in-process metrics): may expose `/metrics` in-process
- Mode B (metricsd): dedicated `/metrics` server

**Contract:** Only one process may bind the metrics port at a time.
Startup performs fail-fast port checks and exits with an error when port is in use.
