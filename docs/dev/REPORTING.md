# Peak Trade - Reporting Overview

Documentation index for all reporting and visualization capabilities.

## Quick Start

### Smoke Test (HTML)

Minimal report to validate Quarto infrastructure:

```bash
make report-smoke          # Generate report
make report-smoke-open     # Generate and open in browser
```

See: [REPORTING_SMOKE.md](REPORTING_SMOKE.md)

## Report Types

### 1. Smoke Test Reports

- **Purpose:** Validate Quarto setup and rendering pipeline
- **Format:** HTML (self-contained)
- **Dependencies:** Quarto only
- **Location:** `reports/quarto/smoke.qmd`
- **Output:** `reports/quarto/_smoke/smoke.html`

### 2. Strategy Reports (Planned)

- Backtest performance metrics
- Strategy comparison tables
- Equity curves and drawdown charts
- Risk metrics and statistics

### 3. Portfolio Reports (Planned)

- Multi-strategy portfolio analysis
- Correlation matrices
- Risk attribution
- Performance decomposition

### 4. Live Monitoring Reports (Planned)

- Real-time position tracking
- Live P&L monitoring
- Risk limit status
- Alert summaries

## Technology Stack

- **Quarto:** Primary reporting engine
- **HTML:** Default output format (self-contained)
- **PDF:** Available for production reports (requires TinyTeX)
- **Python:** Data processing and visualization (optional)
- **R:** Statistical analysis (optional)

## CI/CD Integration

GitHub Actions workflows automatically generate reports:

- **Smoke Test:** `.github/workflows/quarto_smoke.yml`
  - Triggers on changes to smoke report or scripts
  - Uploads HTML artifact (7-day retention)
  - Runs on push/PR to main branches

## Development Guidelines

### Creating New Reports

1. Create `.qmd` file in appropriate `reports/` subdirectory
2. Use `embed-resources: true` for self-contained HTML
3. Add corresponding script in `scripts/dev/` if needed
4. Update Makefile with new target
5. Document in this file

### Report Organization

```
reports/
├── quarto/
│   ├── smoke.qmd              # Smoke test report (committed)
│   ├── _smoke/                # Smoke output (ignored)
│   ├── strategy/              # Strategy reports (planned)
│   └── portfolio/             # Portfolio reports (planned)
└── assets/                    # Shared images, CSS, etc.
```

### Output Management

- Source files (`.qmd`) are committed to git
- Generated outputs (`.html`, `.pdf`) are ignored
- CI artifacts are retained for 7 days
- Production reports should be archived separately

## See Also

- [REPORTING_SMOKE.md](REPORTING_SMOKE.md) - Smoke test documentation
- [../EXECUTION_REPORTING.md](../EXECUTION_REPORTING.md) - Live execution reports
- [../EXPERIMENT_EXPLORER.md](../EXPERIMENT_EXPLORER.md) - Research experiment reports
