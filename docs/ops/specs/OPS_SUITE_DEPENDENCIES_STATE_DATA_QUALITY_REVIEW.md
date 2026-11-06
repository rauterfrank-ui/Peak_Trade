# OPS Suite — Dependencies State Data-Quality Review (Read-Only)

status: DRAFT
last_updated: 2026-03-13
owner: Peak_Trade
purpose: Read-only review of dependencies_state data-quality gaps and hardening options
docs_token: DOCS_TOKEN_OPS_SUITE_DEPENDENCIES_STATE_DATA_QUALITY_REVIEW

## Scope
This document is a **read-only review** of `dependencies_state` in the Ops Cockpit. No code changes, no mutations. It identifies gaps and recommends data-quality hardening options for future implementation.

## Baseline
- **main@2a7c020d**
- **Related:** OPS_SUITE_DASHBOARD_VNEXT_SPEC, incident_state (telemetry + kill_switch), evidence_state (telemetry blended)

---

## 1. Current dependencies_state Implementation

### 1.1 Schema (ops_cockpit.py ~613–617)

| Field | Current Source | Real Signal? |
|-------|----------------|--------------|
| `summary` | Derived from _tel_status + _degraded | **Hardened** — telemetry |
| `exchange` | Hardcoded `"unknown"` | **Placeholder** |
| `telemetry` | `_tel_status` from run_health_checks | **Hardened** |
| `degraded` | `_degraded` (list of check names) | **Hardened** |

### 1.2 run_health_checks (telemetry)

`run_health_checks(telemetry_root)` checks:
- disk_usage
- retention_staleness
- compression_failures
- parse_error_rate

All are **telemetry-log** quality, not exchange or market-data quality.

### 1.3 OPS_SUITE_DASHBOARD_VNEXT_SPEC Expectations

Incident / Safety view (Section 4):
- degraded dependencies

Health / Drift view (Section 7):
- service health
- stale data
- feed/runtime drift indicators

---

## 2. Gap Analysis

### 2.1 exchange — always "unknown"

| Aspect | Current | Gap |
|--------|---------|-----|
| Value | Always `"unknown"` | No derivation from any data source |
| Spec | "service health", "feed/runtime drift" | Exchange connectivity / data availability expected |

**Constraint:** Ops Cockpit is read-only. It must not trigger live API calls during payload build. Real signals must come from **persisted artifacts** written by other processes.

**Real signal candidates:**

| Source | Location | Type | Network? |
|--------|----------|------|----------|
| P85_RESULT.json | `out&#47;ops&#47;*&#47;P85_RESULT.json` | Connectivity check result | No (read-only) |
| Kraken cache health | `check_data_health_only()` | Cache data quality | No (offline) |

### 2.2 P85 — Live Data Ingest Readiness

**Data source:** `src&#47;ops&#47;p85&#47;run_live_data_ingest_readiness_v1.py`

- Runs connectivity check (Kraken Time API)
- Writes `OUT_DIR&#47;P85_RESULT.json` with `connectivity.ok`, `overall_ok`
- Typically run by scheduler/cron; OUT_DIR e.g. `out&#47;ops&#47;p85_run_*`

**Recommendation:** When a recent P85_RESULT.json exists (e.g. under `out/ops` or configurable path):
- Read `connectivity.ok` → map to exchange: `"ok"` if True, `"degraded"` if False
- Consider staleness: if file older than threshold (e.g. 1h), treat as `"unknown"`
- Fallback: `"unknown"` when no file or parse error

**Path resolution:** Config or `repo_root &#47; "out" &#47; "ops"`; search for `**&#47;P85_RESULT.json`, pick most recent by mtime.

### 2.3 Kraken Cache — Market Data Quality

**Data source:** `src&#47;data&#47;kraken_cache_loader.py` — `check_data_health_only()`

- Reads local Parquet cache (no network)
- Returns `KrakenDataHealth` with status: ok, missing_file, too_few_bars, empty, invalid_format, other
- Config: `real_market_smokes.base_path` (default `data&#47;cache`)

**Recommendation:** When cache path exists:
- Call `check_data_health_only(base_path, market, timeframe, min_bars)` (use config defaults)
- Map: `ok` → `"ok"`, `missing_file`/`too_few_bars`/`empty`/`invalid_format` → `"degraded"`, `other` → `"warn"`
- Add optional field `market_data_cache` or derive `exchange` from it when P85 not available

**Note:** Cache quality is a **proxy** for "we had recent successful data ingest" — not live exchange connectivity. Distinguish:
- `exchange`: connectivity (P85) or "unknown"
- `market_data_cache`: cache quality (KrakenDataHealth) — optional new field

### 2.4 summary — blend with exchange / cache

| Aspect | Current | Gap |
|--------|---------|-----|
| summary | telemetry only | Does not consider exchange or cache |

**Recommendation:** Once exchange (and optionally market_data_cache) have real signals:
- summary = worst of (telemetry, exchange, market_data_cache)
- Ranking: ok &lt; partial/warn &lt; degraded/critical &lt; unknown

---

## 3. Real-Signal Mapping Options

### 3.1 Existing Real Signals

| Source | Location | Relevance |
|--------|----------|-----------|
| P85_RESULT.json | out/ops/*/P85_RESULT.json | connectivity.ok |
| check_data_health_only | kraken_cache_loader | KrakenDataHealth.status |
| run_health_checks | telemetry_health | _tel_status, _degraded (already used) |

### 3.2 Recommended Mapping (for future PR)

| dependencies_state field | Option | Real signal | Fallback |
|--------------------------|--------|-------------|----------|
| exchange | Primary | P85_RESULT.json connectivity.ok | "unknown" |
| market_data_cache | Optional | check_data_health_only() status | omit or "unknown" |
| summary | Primary | Blend telemetry + exchange + (optional) cache | current (telemetry only) |

### 3.3 P85 Path Resolution

- Config: `ops.p85_result_path` or `ops.p85_out_base` (e.g. `out/ops`)
- Search: `glob("**&#47;P85_RESULT.json")` under base, sort by mtime desc, take first
- Staleness: if `mtime` &gt; 3600 seconds ago, treat as stale → "unknown"

### 3.4 Kraken Cache Path

- Config: `real_market_smokes.base_path` (default `data&#47;cache`)
- Path: `repo_root &#47; base_path` or `Path(base_path)` when repo_root is None

### 3.5 Risk

- **Low:** Read-only; no execution authority.
- **P85 file may not exist:** Normal when P85 has never been run. Fallback "unknown" is correct.
- **Cache may not exist:** Normal for synthetic-only setups. Fallback or omit market_data_cache.

---

## 4. Out of Scope (this review)

- Live exchange API calls during payload build
- New scheduled jobs (P85 is assumed to exist from external scheduler)
- Execution authority changes

---

## 5. Summary

| Field | Current | Recommended Hardening |
|-------|---------|------------------------|
| exchange | "unknown" | From P85_RESULT.json connectivity.ok when file exists and fresh |
| market_data_cache | — | Optional: from check_data_health_only() |
| summary | Telemetry only | Blend with exchange (and optional cache) |
| telemetry | Hardened | No change |
| degraded | Hardened | No change |

**Next step:** Explicit approval for implementation PR when ready.
