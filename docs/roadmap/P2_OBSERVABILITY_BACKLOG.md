# P2 Observability Backlog

**Status:** NOT STARTED
**Priority:** Deferred (P0+P1 sufficient for current production needs)
**Owner:** TBD
**Last Updated:** 2025-12-18

## Overview

Phase 2 (P2) of the Peak Tool Stack focuses on long-term data storage, advanced querying, and production-grade observability. This document outlines the planned components, exit criteria, and non-goals for P2.

**Context:** P0 (production safety) and P1 (evidence chain) are complete and production-ready. P2 is designed for scale and advanced analytics but is **not required** for current operations.

## Motivation

### Why P2?

P1 Evidence Chain creates reproducible artifacts for every run, but:
- **No historical analysis:** Can't easily query "all runs with Sharpe > 2.0 in Q4 2024"
- **No data lake:** Artifacts are file-based, hard to aggregate across runs
- **No production telemetry:** Limited observability into live system behavior (beyond logs)

P2 addresses these gaps for teams that need:
- Historical trend analysis
- A/B testing across strategies
- Production-grade monitoring dashboards
- Long-term data retention and governance

### When to Start P2?

Start P2 when you encounter:
1. **Query pain:** Manually grepping through `results/` directories becomes tedious
2. **Scale issues:** Thousands of runs, need efficient filtering/aggregation
3. **Production blind spots:** Logs insufficient, need real-time metrics/traces
4. **Compliance needs:** Data retention policies, audit trails, governance

**If you're not hitting these limits, P2 can wait.**

## Planned Components

### 1. Data Lake (`src/data/lake/`)

**Purpose:** Long-term storage and query layer for all Evidence Chain artifacts

**Technology Stack:**
- **Storage format:** Parquet (columnar, efficient for analytics)
- **Query engine:** DuckDB (in-process, SQL interface)
- **Schema:** Star schema with fact/dimension tables

**Proposed Structure:**

```
src/data/lake/
├── __init__.py
├── schema.py               # Table definitions (runs, stats, trades, etc.)
├── ingest.py               # Load Evidence Chain artifacts into lake
├── query.py                # High-level query API (filter runs, aggregate stats)
└── maintenance.py          # Compaction, retention policies, backups
```

**Schema Design (Draft):**

```sql
-- Fact table: runs
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    strategy TEXT,
    symbol TEXT,
    start_date DATE,
    end_date DATE,
    git_sha TEXT,
    timestamp TIMESTAMP,
    stage TEXT,  -- backtest, research, live
    runner TEXT  -- run_backtest.py, research_cli.py, etc.
);

-- Fact table: stats
CREATE TABLE stats (
    run_id TEXT REFERENCES runs(run_id),
    metric TEXT,  -- sharpe, max_dd, total_return, etc.
    value DOUBLE,
    PRIMARY KEY (run_id, metric)
);

-- Fact table: trades (denormalized)
CREATE TABLE trades (
    run_id TEXT REFERENCES runs(run_id),
    timestamp TIMESTAMP,
    symbol TEXT,
    side TEXT,  -- buy, sell
    quantity DOUBLE,
    price DOUBLE,
    pnl DOUBLE
);

-- Dimension table: strategies
CREATE TABLE strategies (
    strategy TEXT PRIMARY KEY,
    tier TEXT,  -- A, B, C
    category TEXT,  -- trend, mean_reversion, etc.
    last_updated TIMESTAMP
);
```

**API Examples:**

```python
from src.data.lake import ingest_run, query_runs, aggregate_stats

# Ingest Evidence Chain run into lake
ingest_run("results/exp_ma_v2_001/")

# Query: Find all runs with Sharpe > 2.0 in Q4 2024
runs = query_runs(
    filters={"sharpe > 2.0", "start_date >= 2024-10-01"},
    order_by="sharpe DESC",
    limit=10
)

# Aggregate: Average Sharpe by strategy
stats = aggregate_stats(
    metric="sharpe",
    group_by="strategy",
    period="2024-Q4"
)
```

**Exit Criteria:**
- ✅ Schema defined and tested
- ✅ Ingest pipeline converts Evidence Chain artifacts to Parquet
- ✅ Query API supports filtering, aggregation, time-range queries
- ✅ Retention policies implemented (e.g., purge runs older than 1 year)
- ✅ Documentation with examples

**Non-Goals:**
- Real-time ingestion (batch daily is sufficient)
- Distributed storage (single-node DuckDB sufficient for <10M runs)
- Complex joins across strategies (star schema keeps queries simple)

### 2. Observability Stack (`src/obs/otel.py`)

**Purpose:** Production telemetry using OpenTelemetry SDK

**Technology Stack:**
- **Tracing:** OpenTelemetry SDK + Jaeger/Tempo backend
- **Metrics:** OpenTelemetry SDK + Prometheus backend
- **Logs:** Structured JSON logs (already in place via P0) + Loki aggregation

**Proposed Structure:**

```
src/obs/
├── __init__.py
├── otel.py                 # OpenTelemetry SDK wiring
├── tracer.py               # Trace decorator (@trace_span)
├── metrics.py              # Counter/Gauge/Histogram helpers
└── config.py               # OTEL_EXPORTER_* env var config
```

**Usage Examples:**

```python
from src.obs import trace_span, counter, histogram

# Trace a backtest run
@trace_span("backtest.run")
def run_backtest(strategy, params):
    # Automatically creates trace with timing
    ...

# Increment counter
counter("backtest.runs.total", labels={"strategy": "ma_crossover"})

# Record histogram
histogram("backtest.duration_seconds", value=42.5)
```

**Backend Stack (Docker Compose):**

```yaml
# ops/observability/docker-compose.yml
services:
  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]

  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]

  tempo:
    image: grafana/tempo:latest
    ports: ["3200:3200", "4317:4317"]  # OTLP gRPC

  loki:
    image: grafana/loki:latest
    ports: ["3100:3100"]
```

**Exit Criteria:**
- ✅ OpenTelemetry SDK integrated (traces, metrics)
- ✅ Docker Compose stack runs locally (Grafana + Prometheus + Tempo + Loki)
- ✅ Example Grafana dashboards (backtest metrics, live session traces)
- ✅ Documentation with setup guide
- ✅ Optional: Production deployment guide (cloud-native observability)

**Non-Goals:**
- Custom dashboards for every strategy (use Grafana templating)
- Real-time alerting (already covered by `src/notifications/`)
- Log parsing/ETL (structured JSON logs already parseable)

### 3. Orchestration & Automation (`ops/observability/`)

**Purpose:** Deployment scripts, config templates, runbooks

**Proposed Structure:**

```
ops/observability/
├── docker-compose.yml      # Local dev stack (Grafana, Prometheus, etc.)
├── prometheus.yml          # Prometheus config (scrape targets)
├── grafana/
│   ├── dashboards/
│   │   ├── backtest_metrics.json
│   │   └── live_session_traces.json
│   └── datasources/
│       ├── prometheus.yml
│       └── tempo.yml
└── runbooks/
    ├── OTEL_SETUP.md       # How to enable OpenTelemetry
    └── GRAFANA_GUIDE.md    # How to use dashboards
```

**Exit Criteria:**
- ✅ `docker-compose up` starts full observability stack
- ✅ Grafana pre-configured with dashboards and datasources
- ✅ Runbooks document setup, troubleshooting, and common queries
- ✅ CI integration (optional): GitHub Actions runs observability smoke tests

**Non-Goals:**
- Production Kubernetes deployment (out of scope for P2, add if needed)
- Multi-tenancy (single team/deployment assumed)

## Implementation Plan (Draft)

### Phase 2.1: Data Lake Foundation (4-6 weeks)

**Goals:**
- Define schema (`src/data/lake/schema.py`)
- Implement ingest pipeline (`src/data/lake/ingest.py`)
- Basic query API (`src/data/lake/query.py`)
- Unit tests for ingest/query

**Deliverables:**
- Working DuckDB data lake
- CLI tool to ingest Evidence Chain runs
- Example queries in documentation

### Phase 2.2: Observability Wiring (3-4 weeks)

**Goals:**
- Integrate OpenTelemetry SDK (`src/obs/otel.py`)
- Add trace decorators to core modules
- Export metrics (counters, histograms)
- Docker Compose stack

**Deliverables:**
- OTEL instrumentation in `run_backtest.py`, `live_ops.py`
- Grafana dashboards with example metrics/traces
- Runbooks for setup and usage

### Phase 2.3: Polish & Documentation (2-3 weeks)

**Goals:**
- Retention policies for data lake
- Grafana dashboard templates
- CI integration (smoke tests)
- Comprehensive documentation

**Deliverables:**
- Production-ready data lake with governance policies
- Grafana dashboards for all key workflows
- Updated ADR_0001 with P2 completion status

**Total Estimated Effort:** 9-13 weeks (part-time) or 4-6 weeks (full-time)

## Exit Criteria (Summary)

P2 is **DONE** when:

1. **Data Lake:**
   - ✅ Schema defined and tested
   - ✅ Ingest pipeline converts Evidence Chain artifacts to Parquet
   - ✅ Query API supports common use cases (filter, aggregate, time-range)
   - ✅ Retention policies implemented

2. **Observability:**
   - ✅ OpenTelemetry SDK integrated (traces, metrics)
   - ✅ Docker Compose stack (Grafana, Prometheus, Tempo, Loki) runs locally
   - ✅ Example dashboards created
   - ✅ Runbooks documented

3. **Documentation:**
   - ✅ Data lake API examples
   - ✅ Observability setup guide
   - ✅ Troubleshooting runbooks
   - ✅ ADR_0001 updated

4. **Testing:**
   - ✅ Unit tests for data lake (ingest, query)
   - ✅ Smoke tests for observability stack (CI integration)

## Non-Goals (Explicit)

P2 does **NOT** include:

1. **Real-time dashboards:** Already covered by `src/reporting/live_status_report.py`
2. **Live alerting:** Already covered by `src/notifications/`
3. **Experiment versioning:** Already covered by P1 Evidence Chain + git SHA
4. **Multi-region deployment:** Single-region assumed
5. **Custom data science pipelines:** Use Jupyter/Pandas on top of data lake
6. **Advanced ML ops:** MLflow (optional in P1) is sufficient for current needs

**Rationale:** P2 focuses on infrastructure (data lake + observability). Higher-level workflows build on top.

## Dependencies

### Internal
- **P0:** Logging, config validation (already done)
- **P1:** Evidence Chain artifacts (already done)

### External
- **DuckDB:** Python library (`pip install duckdb`)
- **OpenTelemetry SDK:** Python library (`pip install opentelemetry-sdk`)
- **Docker:** For local observability stack
- **Grafana/Prometheus/Tempo/Loki:** Docker images (no installation needed)

### Optional
- Cloud storage (S3/GCS) for data lake backups
- Cloud observability (Datadog, New Relic) instead of self-hosted stack

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| DuckDB doesn't scale to millions of runs | High | Switch to ClickHouse or BigQuery (query API unchanged) |
| OTEL overhead slows production | Medium | Make instrumentation opt-in via env var |
| Grafana dashboards require constant tuning | Low | Use templating, document common queries |
| Data lake ingestion too slow | Low | Batch ingest overnight, optimize Parquet schema |

## Questions & Decisions (TBD)

1. **Data lake location:** Local disk vs. S3/GCS?
   - **Proposal:** Start local, add cloud sync later
2. **OTEL sampling:** 100% traces or sampled?
   - **Proposal:** 100% for backtests (cheap), 10% for live (high volume)
3. **Grafana hosting:** Self-hosted vs. Grafana Cloud?
   - **Proposal:** Self-hosted for dev, Grafana Cloud for production
4. **Retention policy:** How long to keep runs?
   - **Proposal:** 1 year for backtests, 3 months for research, forever for live

## Next Steps (When Starting P2)

1. **Kick-off meeting:** Review this backlog, assign owners
2. **Spike:** Prototype DuckDB schema with 1000 runs (1 week)
3. **ADR:** Document key decisions (DuckDB vs. alternatives, OTEL sampling)
4. **Implementation:** Follow phased plan (2.1 → 2.2 → 2.3)
5. **Review:** Update ADR_0001 when P2 complete

## References

- **ADR_0001:** `docs/adr/ADR_0001_Peak_Tool_Stack.md`
- **P1 Evidence Chain:** `src/experiments/evidence_chain.py`
- **Current observability:** `src/reporting/live_status_report.py`, `src/notifications/`
- **DuckDB docs:** https://duckdb.org/docs/
- **OpenTelemetry Python:** https://opentelemetry.io/docs/languages/python/
