# Risk Layer v1.0 - Agent Handoff Instructions

**Von:** Agent A0 (Architect & Repo Alignment)  
**An:** Agents A1-A6  
**Datum:** 2025-12-28  
**Status:** READY FOR IMPLEMENTATION

---

## Übersicht

Agent A0 hat die Architektur-Entscheidungen getroffen und das Scaffold für Risk Layer v1.0 erstellt. Alle Placeholder-Module sind angelegt und bereit für die Implementierung.

**Siehe:** `docs/risk/RISK_LAYER_ALIGNMENT.md` für vollständige Architektur-Details.

---

## Agent Assignments

### Agent A3: VaR Backtesting Extensions

**Verantwortlich für:**
1. Christoffersen Independence Test
2. Christoffersen Conditional Coverage Test
3. Basel Traffic Light System

**Dateien:**

| Datei | Status | Aufgabe |
|-------|--------|---------|
| `src/risk_layer/var_backtest/christoffersen_tests.py` | ⭐ PLACEHOLDER | Implementiere Christoffersen Tests |
| `src/risk_layer/var_backtest/traffic_light.py` | ⭐ PLACEHOLDER | Implementiere Basel Traffic Light |
| `tests/risk_layer/test_christoffersen.py` | 🆕 NEU | Unit Tests für Christoffersen |
| `tests/risk_layer/test_traffic_light.py` | 🆕 NEU | Unit Tests für Traffic Light |

**Implementierungs-Details:**

1. **Christoffersen Independence Test:**
   - Berechne 2x2 Transition Matrix aus Violations
   - Likelihood Ratio Test: LR_ind ~ χ²(1)
   - H0: Violations sind unabhängig (keine Clusterung)

2. **Conditional Coverage Test:**
   - LR_cc = LR_uc + LR_ind (kombiniert Kupiec + Independence)
   - LR_cc ~ χ²(2)
   - H0: Korrektes Coverage + Unabhängigkeit

3. **Basel Traffic Light:**
   - Zone-Klassifikation: GREEN (0-4), YELLOW (5-9), RED (≥10) bei 99% VaR, 250 Tage
   - Berechne Thresholds via Binomial-Quantile
   - Optional: `TrafficLightMonitor` für Live-Monitoring

**Referenzen:**
- Christoffersen, P. F. (1998). Evaluating Interval Forecasts. International Economic Review, 39(4), 841-862.
- Basel Committee (1996). Supervisory Framework for Backtesting.

**Tests:**
- Alle Tests müssen mit `pytest` laufen
- Nutze `scipy.stats.chi2` für Chi-Squared Tests
- Test-Coverage: >80%

**Config-Integration:**
- Nutze `[risk.var_backtest]` Section aus `config/risk_layer_v1_scaffold.toml`
- Alle Features sind opt-in (via `enabled` Flags)

---

### Agent A5: Monte Carlo VaR Calculator

**Verantwortlich für:**
1. Bootstrap-basierte Monte Carlo VaR
2. Parametric Monte Carlo VaR (MVN)
3. Copula-basierte Monte Carlo VaR (Gaussian/t-copula)

**Dateien:**

| Datei | Status | Aufgabe |
|-------|--------|---------|
| `src/risk/monte_carlo.py` | ✅ DONE | Monte Carlo VaR (bootstrap, normal, student_t) |
| `tests/risk/test_monte_carlo.py` | ✅ DONE | Unit Tests für MC VaR (27 tests) |

**Implementierungs-Details:**

1. **Bootstrap Method:**
   - Resample aus historischen Returns (mit Replacement)
   - Berechne Portfolio-Returns für jedes Sample
   - VaR = Quantil der simulierten Verteilung

2. **Parametric Method:**
   - Schätze μ, Σ aus historischen Returns
   - Ziehe n_simulations aus MVN(μ, Σ)
   - Berechne Portfolio-Returns

3. **Copula Method:**
   - Fit Copula (Gaussian oder t) auf marginale Verteilungen
   - Sample aus Copula
   - Transformiere zurück zu Returns

4. **Horizon Scaling:**
   - Multi-Day VaR: Scale σ mit sqrt(horizon_days) (für Parametric)
   - Bootstrap: Compound returns über horizon_days

**Output:**
- `MonteCarloVaRResult` mit VaR, CVaR, simulated_returns
- Simulated returns als numpy array für Inspektionen

**Dependencies:**
- `scipy.stats` für Copulas (multivariate_normal, multivariate_t)
- Eventuell `copulas` Library (optional, nicht in requirements.txt)

**Tests:**
- Test Bootstrap vs Known Distribution (z.B. Normal)
- Test Parametric gegen analytische Lösung
- Test Euler Property: Σ CompVaR = Total VaR (falls applicable)

**Config-Integration:**
- Nutze `[risk.monte_carlo]` Section aus `config/risk_layer_v1_scaffold.toml`
- Builder: `build_monte_carlo_var_from_config()`

---

### Agent A4: Stress Testing Extensions (OPTIONAL)

**Verantwortlich für:**
1. Stress-Testing Enhancements (falls nötig)
2. Scenario Library Loader
3. Alerting bei Stress-Breach

**Dateien:**

| Datei | Status | Aufgabe |
|-------|--------|---------|
| `src/risk/stress.py` | ✅ EXISTIERT | Erweitere falls nötig |
| `config/scenarios/*.toml` | 🆕 NEU | Scenario-Bibliothek |

**Hinweis:** Dies ist OPTIONAL. Die bestehende `src/risk/stress.py` ist bereits funktional. Agent A4 kann ergänzen falls erweiterte Features gewünscht sind.

---

### Agent A6: Integration & Documentation

**Verantwortlich für:**
1. End-to-End Integration Tests
2. Dokumentation (Risk Layer v1.0 Guide)
3. Example Notebooks
4. Production Readiness Review

**Dateien:**

| Datei | Status | Aufgabe |
|-------|--------|---------|
| `tests/integration/test_risk_layer_e2e.py` | 🆕 NEU | Integration Tests |
| `docs/risk/RISK_LAYER_V1_GUIDE.md` | 🆕 NEU | User Guide |
| `notebooks/risk_layer_demo.ipynb` | 🆕 NEU | Demo Notebook |

**Integration Tests:**
- Test vollständiger Backtest mit allen Risk Features
- Test RiskGate mit MC VaR + Christoffersen Backtest
- Test Config-Loading für alle neuen Features

**Dokumentation:**
- User-friendly Guide für Risk Layer v1.0
- API Reference
- Best Practices
- Troubleshooting

---

## Files Ready for Implementation

### ✅ SCAFFOLD COMPLETE

**Core Risk (src/risk/):**
- [x] `monte_carlo.py` - Placeholder + API-Definition

**Risk Layer (src/risk_layer/var_backtest/):**
- [x] `christoffersen_tests.py` - Placeholder + API-Definition
- [x] `traffic_light.py` - Placeholder + API-Definition

**Exports:**
- [x] `src/risk/__init__.py` - Updated with MC VaR exports
- [x] `src/risk_layer/var_backtest/__init__.py` - Updated with new exports

**Config:**
- [x] `config/risk_layer_v1_scaffold.toml` - Template für neue Sections

**Documentation:**
- [x] `docs/risk/RISK_LAYER_ALIGNMENT.md` - Architecture Decision
- [x] `docs/risk/AGENT_HANDOFF.md` - Dieses Dokument

---

## Workflow für Agents

### 1. Lese Architektur-Entscheidungen
```bash
cat docs/risk/RISK_LAYER_ALIGNMENT.md
```

### 2. Lese Placeholder-Code
```bash
# Für Agent A5:
cat src/risk/monte_carlo.py

# Für Agent A3:
cat src/risk_layer/var_backtest/christoffersen_tests.py
cat src/risk_layer/var_backtest/traffic_light.py
```

### 3. Implementiere Feature
- Ersetze `raise NotImplementedError(...)` durch echte Implementierung
- Folge den docstrings und Theory-Sections

### 4. Schreibe Tests
```bash
# Für Agent A5:
pytest tests/risk/test_monte_carlo.py -v

# Für Agent A3:
pytest tests/risk_layer/test_christoffersen.py -v
pytest tests/risk_layer/test_traffic_light.py -v
```

### 5. Prüfe Linter
```bash
# MyPy Type Checking
mypy src/risk/monte_carlo.py
mypy src/risk_layer/var_backtest/christoffersen_tests.py
mypy src/risk_layer/var_backtest/traffic_light.py

# Ruff Linting
ruff check src/risk/monte_carlo.py
```

### 6. Integriere mit Config
- Teste Config-Loading aus `config/risk_layer_v1_scaffold.toml`
- Prüfe Builder-Functions: `build_monte_carlo_var_from_config()`

### 7. Update Tests (Regressions)
```bash
# Prüfe, dass bestehende Tests weiterhin funktionieren
pytest tests/risk/ -v
pytest tests/risk_layer/ -v
```

### 8. Commit
```bash
git add src/risk/monte_carlo.py tests/risk/test_monte_carlo.py
git commit -m "feat(risk): implement Monte Carlo VaR Calculator (Agent A5)"
```

---

## Testing Strategy

### Unit Tests (Agent-spezifisch)

**Agent A3:**
```python
# tests/risk_layer/test_christoffersen.py
def test_independence_test_no_clustering():
    """Test Independence Test on independent violations."""
    violations = [False, True, False, False, True, ...]  # Random
    result = christoffersen_independence_test(violations, alpha=0.05)
    assert result.passed  # Should pass if truly independent

def test_traffic_light_green_zone():
    """Test Basel Traffic Light GREEN zone."""
    result = basel_traffic_light(n_violations=2, n_observations=250, alpha=0.01)
    assert result.zone == BaselZone.GREEN
```

**Agent A5:**
```python
# tests/risk/test_monte_carlo.py
def test_bootstrap_var_basic():
    """Test Bootstrap VaR on synthetic data."""
    returns = generate_synthetic_returns(mean=0.001, std=0.02, n=500)
    config = MonteCarloVaRConfig(n_simulations=10000, method="bootstrap")
    calc = MonteCarloVaRCalculator(returns, config)
    result = calc.calculate(weights={"asset1": 1.0}, portfolio_value=100000)
    assert result.var > 0
    assert result.cvar > result.var  # CVaR should be greater than VaR
```

### Integration Tests (Agent A6)

```python
# tests/integration/test_risk_layer_e2e.py
def test_full_risk_layer_with_mc_var():
    """Test full Risk Layer with MC VaR + Backtesting."""
    cfg = load_config("config/config.toml")

    # Build MC VaR
    mc_calc = build_monte_carlo_var_from_config(returns_df, cfg)
    result = mc_calc.calculate(weights, portfolio_value)

    # Run Backtest
    backtest_results = run_full_var_backtest(violations, alpha=0.05)
    assert backtest_results["all_passed"]

    # Check Traffic Light
    traffic_result = basel_traffic_light(n_violations, n_observations, alpha=0.01)
    assert traffic_result.zone == BaselZone.GREEN
```

---

## Dependencies (bereits installiert)

Alle nötigen Dependencies sind bereits in `requirements.txt`:
- ✅ `numpy`
- ✅ `pandas`
- ✅ `scipy`

**Optional (falls nötig):**
- `copulas` (für advanced Copula-fitting, falls Agent A5 entscheidet)

---

## Success Criteria (für alle Agents)

✅ **No Breaking Changes:**
- Alle bestehenden Tests laufen unverändert

✅ **Tests:**
- Unit Tests für alle neuen Features
- Test Coverage >80%

✅ **Type Safety:**
- MyPy-Check ohne Fehler

✅ **Documentation:**
- Docstrings für alle Public Functions
- Theory Sections in Docstrings (wo relevant)

✅ **Config-Integration:**
- Builder-Functions funktionieren mit `config/config.toml`

---

## Rollout Timeline

| Phase | Agent | ETA | Status |
|-------|-------|-----|--------|
| **Phase 0** | A0 | ✅ DONE | Scaffold + Architecture |
| **Phase 1** | A3 | 🔜 NEXT | Christoffersen Tests + Basel Traffic Light |
| **Phase 2** | A5 | 🔜 NEXT | Monte Carlo VaR Calculator |
| **Phase 3** | A4 | ⏸️  OPTIONAL | Stress Testing Extensions |
| **Phase 4** | A6 | ⏳ PENDING | Integration + Documentation |

---

## Kontakt & Fragen

Bei Fragen zur Architektur oder Unklarheiten:
- Siehe `docs/risk/RISK_LAYER_ALIGNMENT.md` (vollständiges Decision Memo)
- Prüfe Placeholder-Code (enthält detaillierte Implementation-Hints)

**Agent A0 hat sichergestellt:**
- ✅ Keine Breaking Changes
- ✅ Klare File-Ownership
- ✅ Public APIs sind definiert
- ✅ Config-Schema ist festgelegt
- ✅ Exports sind aktualisiert

---

**Ready for Implementation!** 🚀

Viel Erfolg an Agents A3, A5, A4, A6! 🎯
