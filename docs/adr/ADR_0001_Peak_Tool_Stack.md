# ADR-0001: Peak Tool Stack – Observability & Reproducibility

**Status:** ACTIVE
**Date:** 2025-12-18
**Deciders:** Core Team
**Context:** Peak_Trade production readiness requires systematic observability, experiment tracking, and data lake architecture.

## Decision

Implement observability and reproducibility infrastructure in three phases:

### Phase 0 (P0): Production Safety – ✅ DONE

**Scope:** Minimum viable production safety net

**Components:**
- Structured logging (`src&#47;utils&#47;logger.py`)
- CI/CD guards (pre-commit hooks, GitHub Actions)
- Config validation (`src&#47;config&#47;registry.py`)
- Basic testing infrastructure

**Status:** Production-ready, in use across all core modules.

**Implementation Notes:**
- Structured logging with JSON output for production environments
- Pre-commit hooks enforce code quality (black, ruff, mypy)
- GitHub Actions run tests and validation on every PR
- Config registry validates all strategy/portfolio/risk configs at runtime
- Comprehensive test coverage for core modules

### Phase 1 (P1): Evidence Chain – ✅ DONE

**Scope:** Reproducible research artifacts + optional reporting

**Components:**
- `src/experiments/evidence_chain.py` (flat module architecture)
- Standard artifact structure: `results&#47;<run_id>&#47;`
- Optional MLflow integration (graceful degradation)
- Optional Quarto reporting (graceful degradation)
- Integration with existing `src/reporting/` ecosystem

**Status:** Fully implemented and integrated with core runners.

**Implementation Notes:**

#### Flat Architecture Decision
P1 is implemented as a **flat module** (`src/experiments/evidence_chain.py`) rather than a nested package structure (`src/experiments/tracking/`). This design choice reflects:

1. **Simplicity:** Single-file module with clear API surface
2. **Minimal dependencies:** No package hierarchy needed for current scope
3. **Integration pattern:** Works as a utility layer, not a framework

#### Artifact Structure
Each run creates standardized artifacts under `results&#47;<run_id>&#47;`:
```
results/<run_id>/
├── config_snapshot.json    # Meta + Params
├── stats.json              # Performance metrics
├── equity.csv              # Equity curve
├── trades.parquet          # Optional (if parquet engine available)
├── report_snippet.md       # Markdown summary
└── report/                 # Optional (if Quarto enabled)
    └── backtest.html       # Rendered report
```

#### Integration Points

**1. Core Runners:**
- `scripts/run_backtest.py`: Full evidence chain + optional Quarto report
- Future: `research_cli.py`, `live_ops.py` (minimal evidence chain)

**2. Reporting Ecosystem:**
- **Templates:** `templates/quarto/backtest_report.qmd` (policy-compliant, no tracked `reports/`)
- **Rendering:** `scripts/utils/render_last_report.sh` (optional, writes to `results&#47;<run_id>&#47;report&#47;`)
- **Integration:** Binds to existing `src/reporting/` modules (plots, stats, visualizations)

**3. Optional Dependencies:**
- **MLflow:** `get_optional_tracker()` returns `NullTracker` if mlflow not installed
- **Quarto:** Report rendering skipped with warning if quarto not in PATH
- **Parquet:** `trades.parquet` skipped if pyarrow/fastparquet not available

#### Graceful Degradation
Evidence Chain core functions **always work**, regardless of optional dependencies:
- ✅ JSON/CSV artifacts: Always written
- ⚠️ Parquet artifacts: Skipped if no parquet engine
- ⚠️ MLflow tracking: Falls back to `NullTracker`
- ⚠️ Quarto reports: Skipped with warning

#### CI Integration
- `.gitignore` ensures `results/` and `reports/` are never tracked
- Pre-commit hooks validate that no generated reports leak into commits
- Evidence Chain unit tests (`tests/test_evidence_chain.py`) run on every PR

**Exit Criteria:** ✅ All met
- ✅ Artifacts created for every backtest run
- ✅ Optional Quarto reports render correctly
- ✅ Graceful degradation tested (no mlflow, no quarto, no parquet)
- ✅ CI guards prevent tracking generated files
- ✅ Documentation complete (`docs/reporting/REPORTING_QUICKSTART.md`)

### Phase 2 (P2): Data Lake + Observability – ❌ NOT STARTED

**Scope:** Long-term storage, query layer, production telemetry

**Planned Components:**
- `src/data/lake/` – DuckDB + Parquet data lake
- `src/obs/otel.py` – OpenTelemetry SDK wiring
- `ops&#47;observability&#47;` – Grafana/Loki/Tempo/Prometheus stack (Docker Compose)

**Status:** Backlog. See `docs/roadmap/P2_OBSERVABILITY_BACKLOG.md` for detailed plan.

**Non-Goals (P2):**
- Real-time dashboards (covered by existing `src/reporting/live_status_report.py`)
- Live alerting (covered by existing `src/notifications/`)
- Experiment versioning (covered by P1 Evidence Chain + git SHA)

## Consequences

### Positive
- ✅ **P0:** Production systems have basic safety net (logging, validation, CI)
- ✅ **P1:** Every research run is reproducible (artifacts + metadata + optional reports)
- ✅ **P1:** Flat architecture keeps codebase simple and maintainable
- ✅ **P1:** Graceful degradation enables use without heavy dependencies
- ✅ **P1:** Integration with existing reporting ecosystem (no duplication)
- 🔜 **P2:** Data lake will enable historical analysis, A/B testing, drift detection

### Negative
- ⚠️ **P1:** Flat module may need refactoring if tracking complexity grows significantly
  - **Mitigation:** Evidence Chain API is stable; internal refactoring possible without breaking callers
- ⚠️ **P2:** Not started – no long-term data lake or production telemetry yet
  - **Mitigation:** P0+P1 sufficient for current production needs; P2 can wait for demand

### Technical Debt
- None for P0/P1 (stable, tested, production-ready)
- P2 deferred by design (no immediate need)

## References

- **P1 Merge Log:** `docs/ops/PR_143_MERGE_LOG.md`
- **P1 Quickstart:** `docs/reporting/REPORTING_QUICKSTART.md`
- **P1 Implementation:** `src/experiments/evidence_chain.py`
- **P1 Tests:** `tests/test_evidence_chain.py`
- **P2 Roadmap:** `docs/roadmap/P2_OBSERVABILITY_BACKLOG.md`

## Review Schedule

This ADR should be reviewed:
- When P2 implementation begins
- If Evidence Chain complexity requires nested package structure
- If new observability requirements emerge from production operations
