# Phase 77 – Strategy-Smoke-Tests in GitHub Actions CI

**Status:** Abgeschlossen
**Datum:** 2025-12-07

## Zusammenfassung

Diese Phase integriert die in Phase 76 implementierten Strategy-Smoke-Tests als festen Bestandteil der CI-Pipeline (GitHub Actions). Jeder Commit/Pull-Request failt nun, wenn:

1. Die Strategy-Smoke-CLI fehlschlaegt (Exit-Code != 0), oder
2. Die dazugehoerigen Tests (`tests/test_strategy_smoke_cli.py`) scheitern.

## Aenderungen

### Geaenderte Dateien

| Datei | Aenderung |
|-------|-----------|
| `.github/workflows/ci.yml` | Neuer Job `strategy-smoke` hinzugefuegt |

### Neuer CI-Job: `strategy-smoke`

Der Job wird nach dem erfolgreichen Durchlauf des `tests`-Jobs ausgefuehrt (`needs: tests`).

**Ablauf:**
1. Checkout des Repositories
2. Python 3.11 Setup
3. pip Cache (gleiche Logik wie Haupt-Tests)
4. Dependency-Installation (`requirements.txt` + pytest)
5. Ausfuehrung der Smoke-Tests via pytest
6. Ausfuehrung der Smoke-CLI mit JSON/Markdown-Output
7. Upload der Ergebnisse als GitHub Actions Artifact

## CI-Workflow YAML

```yaml
strategy-smoke:
  runs-on: ubuntu-latest
  needs: tests  # Run after main tests pass

  steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Set up Python 3.11
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Cache pip
      uses: actions/cache@v4
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt', '**/pyproject.toml') }}
        restore-keys: |
          ${{ runner.os }}-pip-

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest

    - name: Run strategy smoke pytest
      run: |
        pytest tests/test_strategy_smoke_cli.py -v --tb=short

    - name: Create smoke results directory
      run: |
        mkdir -p test_results/strategy_smoke

    - name: Run strategy smoke CLI
      run: |
        python scripts/strategy_smoke_check.py \
          --output-json test_results/strategy_smoke/ci_smoke_latest.json \
          --output-md test_results/strategy_smoke/ci_smoke_latest.md

    - name: Upload smoke test artifacts
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: strategy-smoke-results
        path: test_results/strategy_smoke/
        retention-days: 30
```

## Kommandos in CI

| Step | Kommando |
|------|----------|
| pytest | `pytest tests/test_strategy_smoke_cli.py -v --tb=short` |
| CLI | `python scripts/strategy_smoke_check.py --output-json ... --output-md ...` |

## Failure-Path

### Szenario 1: pytest fehlschlaegt
- Step "Run strategy smoke pytest" failt
- CI-Job `strategy-smoke` wird rot
- Gesamter CI-Build failt
- Artifacts werden dennoch hochgeladen (`if: always()`)

### Szenario 2: Strategie-Smoke-CLI gibt Exit-Code 1
- Step "Run strategy smoke CLI" failt
- CI-Job `strategy-smoke` wird rot
- Gesamter CI-Build failt
- JSON/Markdown-Reports zeigen, welche Strategie gefailt hat
- Artifacts werden hochgeladen fuer Debugging

### Szenario 3: Haupt-Tests fehlschlagen
- Job `tests` failt
- Job `strategy-smoke` wird uebersprungen (`needs: tests`)
- Entwickler muss zuerst Haupt-Tests fixen

## Artifacts

Nach jedem CI-Run (auch bei Failures) werden folgende Dateien als Artifacts verfuegbar:

| Artifact | Inhalt |
|----------|--------|
| `strategy-smoke-results` | `ci_smoke_latest.json`, `ci_smoke_latest.md` |

Diese koennen im GitHub Actions UI unter "Artifacts" heruntergeladen werden.

## Safety-Garantien

- **Keine Live-/Testnet-Exchanges:** Der Job verwendet ausschliesslich synthetische Backtest-Daten
- **Keine API-Keys:** Keine Secrets werden geladen oder verwendet
- **Keine Aenderungen an Live-Code:** `src/execution/*` und `src/live/*` wurden nicht angefasst
- **Rein offline:** Alle Tests laufen lokal ohne Netzwerkzugriff auf Exchanges

## Lokale Verifikation

Die CI-Schritte koennen lokal reproduziert werden:

```bash
# Quick command (recommended)
make ci-smoke

# Or manually:
# Smoke pytest
pytest tests/test_strategy_smoke_cli.py -v

# Smoke CLI
mkdir -p test_results/strategy_smoke
python scripts/strategy_smoke_check.py \
  --output-json test_results/strategy_smoke/ci_smoke_latest.json \
  --output-md test_results/strategy_smoke/ci_smoke_latest.md
```

**CI Output Location:**
- Fast lane reports: `test_results/ci_smoke/`
- Artifacts: `junit.xml`, `pytest.txt`, `env.txt`, JSON, MD

**Operator Guide:**
- Troubleshooting: `docs/ops/ci_smoke_fastlane.md`

## Done-Kriterien

- [x] GitHub Actions Workflow in `.github/workflows/ci.yml` erweitert
- [x] Strategy-Smoke-CLI wird in CI ausgefuehrt
- [x] `tests/test_strategy_smoke_cli.py` wird in CI ausgefuehrt
- [x] Bei Fehlern failt der Build (Exit-Code propagiert)
- [x] Artifacts werden hochgeladen (JSON/Markdown)
- [x] Keine Aenderungen an Live-/Execution-Code
- [x] Rein offline/safe

## Naechste Schritte

- Optional: Smoke-Tests fuer weitere Strategien erweitern
- Optional: Zusaetzliche Metriken in Reports aufnehmen
- Optional: Slack-Notification bei Smoke-Test-Failures

---

*Generiert im Rahmen von Phase 77 – CI Strategy Smoke Tests*
