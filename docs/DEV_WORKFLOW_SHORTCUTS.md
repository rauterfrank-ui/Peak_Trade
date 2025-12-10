# Dev Workflow Shortcuts

Kurze Referenz für häufige Developer-Commands im Peak_Trade-Projekt.

> **Tipp:** Nutze diese Commands nach größeren Änderungen, um sicherzustellen, dass die wichtigsten Pfade sauber bleiben.

---

## Test-Suite

### Vollständige Test-Suite

```bash
pytest -q
```

### Spezifische Test-Gruppen

```bash
# Nur Live-bezogene Tests
pytest -q tests/test_live_* tests/test_generate_live_status_report_cli.py

# Nur Backtest-Tests
pytest -q tests/test_backtest_*

# Nur Strategy-Tests
pytest -q tests/test_strategy_*

# Mit Coverage
pytest -q --cov=src --cov-report=html
```

---

## CLI Smoke-Tests

### Research-CLI

```bash
# Help anzeigen
python scripts/research_cli.py --help

# Portfolio-Subcommand
python scripts/research_cli.py portfolio --help

# Pipeline-Subcommand
python scripts/research_cli.py pipeline --help
```

### Live-Ops CLI

```bash
# Help anzeigen
python scripts/live_ops.py --help

# Health-Check
python scripts/live_ops.py health --config config/config.toml

# Portfolio-Snapshot
python scripts/live_ops.py portfolio --config config/config.toml --json
```

### Live-Status-Report

```bash
# Help anzeigen
python scripts/generate_live_status_report.py --help

# Quick-Test (mit Test-Config)
python scripts/generate_live_status_report.py \
  --config config/config.test.toml \
  --output-dir /tmp/test_reports \
  --format markdown \
  --tag test
```

---

## Code-Quality Checks

### Linting (falls konfiguriert)

```bash
# Ruff (falls installiert)
ruff check src/ scripts/

# Flake8 (falls installiert)
flake8 src/ scripts/
```

### Type-Checking (falls konfiguriert)

```bash
# mypy (falls installiert)
mypy src/
```

---

## Quick-Development-Workflows

### Neues Feature testen

```bash
# 1. Tests laufen lassen
pytest -q

# 2. CLI-Smoke-Test
python scripts/research_cli.py --help
python scripts/live_ops.py --help

# 3. Quick-Integration-Test (falls relevant)
python scripts/generate_live_status_report.py --help
```

### Vor Commit

```bash
# 1. Tests
pytest -q

# 2. Git-Status prüfen
git status

# 3. Diff prüfen
git diff
```

---

## Häufige Debug-Commands

### Config prüfen

```bash
# Config laden und validieren
python -c "from src.core.peak_config import load_config; cfg = load_config('config/config.toml'); print('OK')"
```

### Registry prüfen

```bash
# Experiment-Registry anzeigen
python scripts/list_experiments.py --limit 10
```

---

## Weitere Ressourcen

- **CLI-Referenz:** [`docs/CLI_CHEATSHEET.md`](CLI_CHEATSHEET.md)
- **Getting Started:** [`docs/GETTING_STARTED.md`](GETTING_STARTED.md)
- **Architektur:** [`docs/ARCHITECTURE_OVERVIEW.md`](ARCHITECTURE_OVERVIEW.md)
- **Tech-Debt Backlog:** [`docs/TECH_DEBT_BACKLOG.md`](TECH_DEBT_BACKLOG.md)

---

**Built with ❤️ and continuous improvement**







