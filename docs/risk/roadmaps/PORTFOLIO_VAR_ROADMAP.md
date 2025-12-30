# Portfolio VaR Roadmap - Peak_Trade

**Status:** Planning  
**Owner:** Risk Management Team  
**Last Updated:** 2025-12-25

---

## Vision

Erweitere Peak_Trade um ein umfassendes Portfolio-Level Value-at-Risk (VaR) Framework, das von Backtest über Paper-Trading bis zu Live-Trading skaliert und dabei höchste Safety- und Validierungsstandards einhält.

---

## Current State (Risk Layer v1 - ✅ Completed)

### Implemented Features

- ✅ **Portfolio-Level Risk Management**
  - Gross/Net Exposure Limits
  - Position Weight Limits
  - Portfolio Snapshot Architecture

- ✅ **VaR/CVaR Metrics**
  - Historical VaR/CVaR (empirical quantiles)
  - Parametric VaR/CVaR (Normal distribution)
  - Configurable alpha levels (0.01, 0.05, 0.10)
  - Rolling-window support (30-365 days)

- ✅ **Stress Testing**
  - 5 scenario types (shock, vol_spike, flash_crash, regime_bear, regime_sideways)
  - Batch scenario execution
  - Metrics aggregation

- ✅ **Risk Enforcement**
  - Circuit-breaker semantics (HARD breaches → Trading HALT)
  - 3 breach severities (INFO, WARNING, HARD)
  - Deterministic decision path

- ✅ **Testing & Documentation**
  - 96 unit/integration tests (100% pass)
  - Operator guide (300+ lines)
  - Stress-testing script

### Current Limitations

- ⚠️ **Single-Asset Focus**: VaR berechnet auf Equity-Returns, nicht auf Multi-Asset-Portfolio-Returns
- ⚠️ **No Correlation Analysis**: Keine Asset-Korrelationsmatrix im Enforcement-Flow
- ⚠️ **Backtest-Only**: Noch keine Live-Trading-Integration
- ⚠️ **Static Limits**: Keine adaptiven oder ML-basierten Limits
- ⚠️ **Limited Distribution Models**: Nur Normal-Annahme für parametric VaR

---

## Roadmap Overview

### Phase 1: Multi-Asset Portfolio VaR (Q1 2026)
**Goal:** Erweitere VaR/CVaR auf echte Multi-Asset-Portfolios mit Korrelationsanalyse

### Phase 2: Advanced Distribution Models (Q1-Q2 2026)
**Goal:** Gehe über Normal-Annahme hinaus (Student-t, GARCH, Empirical)

### Phase 3: Paper-Trading Validation (Q2 2026)
**Goal:** Validiere VaR-Modelle im Paper-Trading mit real-time Data

### Phase 4: Adaptive & ML-based Limits (Q2-Q3 2026)
**Goal:** Dynamische Limits basierend auf Regime/Volatility

### Phase 5: Live-Trading Integration (Q3-Q4 2026)
**Goal:** Aktiviere VaR-basiertes Risk-Management in Live-Trading (Safety-First!)

---

## Phase 1: Multi-Asset Portfolio VaR (Q1 2026)

### Objectives

1. **Portfolio-Returns-Berechnung**
   - Berechne Returns auf Portfolio-Ebene (nicht nur Equity)
   - Nutze Asset-Weights und Asset-Returns
   - Formel: `R_portfolio = Σ(w_i * R_i)` wobei `w_i` = Weights, `R_i` = Asset-Returns

2. **Correlation Matrix Integration**
   - Implementiere `correlation_matrix()` in Enforcement-Flow
   - Prüfe Max-Correlation-Limits zwischen Assets
   - Warnung bei hoher Correlation (>0.95) zwischen vermeintlich diversifizierten Assets

3. **Covariance-based VaR**
   - Implementiere Variance-Covariance VaR: `VaR = sqrt(w' * Σ * w) * z_alpha`
   - Nutze Korrelationsmatrix für realistische Portfolio-VaR
   - Vergleiche mit Historical VaR (Validation)

### Implementation Steps

#### 1.1 Multi-Asset Returns Tracking

**File:** `src/risk/portfolio.py`

```python
def compute_portfolio_returns_from_positions(
    positions: List[PositionSnapshot],
    prices_history: pd.DataFrame,  # {symbol: price_series}
    equity: float,
) -> pd.Series:
    """
    Berechnet Portfolio-Returns aus Position-Snapshots und Price-History.

    Returns:
        Series mit Portfolio-Returns über Zeit
    """
    # 1. Compute weights per position
    weights = compute_weights(positions, equity)

    # 2. Compute asset returns from prices
    asset_returns = prices_history.pct_change().dropna()

    # 3. Compute portfolio returns
    return portfolio_returns(asset_returns, weights)
```

#### 1.2 Correlation-based Risk Checks

**File:** `src/risk/enforcement.py`

```python
class RiskEnforcer:
    def _check_correlations(
        self,
        returns_df: pd.DataFrame,  # Multi-asset returns
        limits: RiskLimitsV2,
    ) -> List[RiskBreach]:
        """
        Prüft Correlation-Limits zwischen Assets.

        Breaches:
        - MAX_CORRELATION: Pairwise correlation > limit
        - HIGH_CORRELATION_WARNING: Correlation > 0.90 (warning)
        """
        if limits.max_corr is None:
            return []

        corr = correlation_matrix(returns_df)
        breaches = []

        # Check all pairwise correlations
        for i, asset_i in enumerate(corr.columns):
            for j, asset_j in enumerate(corr.columns):
                if i >= j:  # Skip diagonal and duplicates
                    continue

                corr_val = corr.loc[asset_i, asset_j]

                if abs(corr_val) > limits.max_corr:
                    breaches.append(
                        RiskBreach(
                            code="MAX_CORRELATION",
                            message=f"Correlation {asset_i}/{asset_j} = {corr_val:.2%} exceeds limit {limits.max_corr:.2%}",
                            severity=BreachSeverity.HARD,
                            metrics={"asset_i": asset_i, "asset_j": asset_j, "corr": corr_val},
                        )
                    )

        return breaches
```

#### 1.3 Covariance-based VaR

**File:** `src/risk/var.py`

```python
def covariance_var(
    returns_df: pd.DataFrame,  # Multi-asset returns
    weights: Dict[str, float],  # Asset weights
    alpha: float = 0.05,
) -> float:
    """
    Variance-Covariance VaR (parametric, assumes Normal).

    Formula: VaR = sqrt(w' * Σ * w) * z_alpha

    Args:
        returns_df: DataFrame mit Asset-Returns (columns = assets)
        weights: Dict {asset: weight}
        alpha: Confidence level

    Returns:
        VaR als positive Zahl
    """
    # 1. Filter assets
    available = [col for col in returns_df.columns if col in weights]
    if not available:
        return 0.0

    # 2. Build weight vector
    w = np.array([weights[asset] for asset in available])
    w = w / w.sum()  # Normalize

    # 3. Compute covariance matrix
    cov = returns_df[available].cov()

    # 4. Portfolio variance: w' * Σ * w
    portfolio_var = w @ cov @ w
    portfolio_std = np.sqrt(portfolio_var)

    # 5. VaR = std * z_alpha
    z_alpha = _get_normal_quantile(alpha)
    var = -z_alpha * portfolio_std

    return max(var, 0.0)
```

### Testing Strategy

1. **Unit-Tests** (`tests/risk/test_portfolio_multi_asset.py`)
   - Portfolio-Returns mit 2-3 Assets
   - Correlation-Matrix mit bekannten Werten
   - Covariance-VaR vs Historical-VaR (sollte ähnlich sein)

2. **Integration-Tests** (`tests/risk/test_backtest_multi_asset.py`)
   - Backtest mit Multi-Asset-Strategy
   - Max-Correlation-Limit verletzt → Trading HALT
   - Covariance-VaR-Limit verletzt → Trading HALT

3. **Validation**
   - Vergleiche Historical vs Covariance VaR (sollten korrelieren)
   - Backtests mit/ohne Correlation-Limits
   - Stress-Tests: Correlation-Spike-Szenarien

### Config Extensions

```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.05
window = 252
use_covariance_var = true  # NEW: Nutze Covariance-VaR statt Equity-Returns-VaR

[risk.limits]
max_gross_exposure = 1.5
max_position_weight = 0.35
max_var = 0.08
max_cvar = 0.12
max_corr = 0.90  # NEW: Max pairwise Correlation

[risk.multi_asset]  # NEW Section
enabled = true
min_assets_for_correlation = 2  # Mindestanzahl Assets für Corr-Check
correlation_window = 60  # Tage für Rolling-Correlation
```

### Acceptance Criteria

- [ ] Portfolio-Returns aus Multi-Asset-Positions berechnet
- [ ] Correlation-Matrix-Checks im Enforcement-Flow
- [ ] Covariance-VaR implementiert + getestet
- [ ] 20+ neue Tests (Multi-Asset-Coverage)
- [ ] Dokumentation: "Multi-Asset VaR Guide"
- [ ] Backtest-Validation: 3 Multi-Asset-Strategien

---

## Phase 2: Advanced Distribution Models (Q1-Q2 2026)

### Objectives

1. **Student-t Distribution VaR**
   - Bessere Modellierung von Fat Tails
   - MLE-basierte Parameter-Schätzung

2. **GARCH(1,1) VaR**
   - Time-varying volatility
   - Bessere Capture von Volatility-Clustering

3. **Extreme Value Theory (EVT)**
   - Modellierung extremer Tails
   - GPD (Generalized Pareto Distribution) für Tail-Fit

### Implementation Plan

#### 2.1 Student-t VaR

**Dependencies:** `scipy.stats.t`

```python
def student_t_var(
    returns: pd.Series,
    alpha: float = 0.05,
) -> float:
    """
    Parametric VaR mit Student-t-Distribution (Fat Tails).

    Steps:
    1. MLE-Fit für degrees-of-freedom (df)
    2. Compute scale parameter
    3. VaR = t_alpha(df) * scale
    """
    from scipy.stats import t

    # 1. Fit Student-t
    params = t.fit(returns.dropna())
    df, loc, scale = params

    # 2. Quantil
    quantile = t.ppf(alpha, df, loc, scale)

    # 3. VaR
    var = -quantile if quantile < 0 else 0.0
    return var
```

#### 2.2 GARCH VaR

**Dependencies:** `arch` library

```python
def garch_var(
    returns: pd.Series,
    alpha: float = 0.05,
    horizon: int = 1,
) -> float:
    """
    GARCH(1,1)-based VaR with forecast.

    Steps:
    1. Fit GARCH(1,1) model
    2. Forecast volatility (horizon steps)
    3. VaR = forecast_std * z_alpha
    """
    from arch import arch_model

    # 1. Fit GARCH
    model = arch_model(returns * 100, vol='Garch', p=1, q=1)
    res = model.fit(disp='off')

    # 2. Forecast
    forecast = res.forecast(horizon=horizon)
    forecast_var = forecast.variance.values[-1, -1]
    forecast_std = np.sqrt(forecast_var) / 100  # Back to decimal

    # 3. VaR
    z_alpha = _get_normal_quantile(alpha)
    var = -z_alpha * forecast_std

    return max(var, 0.0)
```

### Testing & Validation

- **Backtesting:** Compare VaR-Models (Historical vs Student-t vs GARCH)
- **Kupiec Test:** Validate VaR-Model via Backtesting (Count violations)
- **Christoffersen Test:** Independence of violations

### Config

```toml
[risk.var_models]
primary = "historical"  # historical, student_t, garch, covariance
fallback = "historical"  # Falls primary fehlschlägt
garch_p = 1
garch_q = 1
```

---

## Phase 3: Paper-Trading Validation (Q2 2026)

### Objectives

**Goal:** Validiere VaR-Modelle in Paper-Trading mit Real-Time-Data **bevor** Live-Trading.

### Implementation Plan

1. **Real-Time VaR Calculation**
   - Integriere VaR-Berechnung in Paper-Trading-Loop
   - Update VaR jede Minute/Stunde
   - Log VaR-History

2. **Backtesting Framework**
   - Sammle VaR-Forecasts vs Actual-Returns
   - Kupiec/Christoffersen-Tests automatisch
   - Violation-Rate-Tracking

3. **Alert System**
   - Alert bei VaR-Model-Failure (zu viele Violations)
   - Alert bei VaR-Spike (plötzlicher Anstieg)

### Safety Gate

**🚨 CRITICAL: Paper-Trading Validation MUSS erfolgreich sein, bevor Live-Trading aktiviert wird!**

**Kriterien:**
- Mindestens 30 Tage Paper-Trading
- VaR-Violation-Rate innerhalb Expected-Range (z.B. 5% ± 2% für alpha=0.05)
- Keine systematischen Fehler (Kupiec-Test pass)
- Manual Review: Risk-Team sign-off

---

## Phase 4: Adaptive & ML-based Limits (Q2-Q3 2026)

### Objectives

**Goal:** Dynamische Risk-Limits basierend auf Markt-Regime und Volatilität.

### Implementation Ideas

1. **Regime-Dependent Limits**
   ```python
   if regime == "high_vol":
       max_var = 0.12  # Higher limit
   elif regime == "low_vol":
       max_var = 0.06  # Tighter limit
   ```

2. **Volatility-Scaled Limits**
   ```python
   current_vol = returns.std()
   baseline_vol = 0.02
   vol_ratio = current_vol / baseline_vol
   adjusted_max_var = base_max_var * vol_ratio
   ```

3. **ML-based Limit Prediction**
   - Train Model: Input (regime, vol, returns) → Output (optimal_max_var)
   - Backtest-based Training-Data
   - Conservative: Start with ML-recommendations as INFO, human override

### Safety

- **Limits-Limits:** ML darf Limits nur innerhalb bestimmter Ranges ändern
- **Human-in-the-Loop:** ML-Recommendations müssen approved werden
- **Fallback:** Bei ML-Failure → Static Conservative Limits

---

## Phase 5: Live-Trading Integration (Q3-Q4 2026)

### Objectives

**Goal:** Aktiviere VaR-basiertes Risk-Management in Live-Trading (Safety-First!).

### Implementation Plan

1. **Pre-Trade VaR-Check**
   - Vor jedem Live-Trade: Compute Portfolio-VaR if Trade executed
   - If VaR > Limit → Block Trade
   - Log decision

2. **Real-Time Monitoring**
   - Dashboard: Current VaR, Historical VaR, Limit
   - Alerts bei Limit-Approach (z.B. 80% of Limit)

3. **Circuit-Breaker Integration**
   - Bei HARD Breach: Immediate Trading HALT
   - Alert: Ops-Team + Risk-Team
   - Manual override erforderlich zum Resume

### Safety Gates (Multi-Stage)

**Stage 1: Testnet (1 Monat)**
- Aktiviere VaR-Limits auf Testnet
- Zero Real Money
- Validation: System funktioniert korrekt

**Stage 2: Live-Paper-Hybrid (1 Monat)**
- Aktiviere auf Live-Exchange, aber nur für Paper-Account
- Real Market-Data, kein Real Money
- Validation: System funktioniert mit Live-Data

**Stage 3: Live-Micro (2 Wochen)**
- Aktiviere für Small-Cap-Account (z.B. 1.000 €)
- Real Money, aber minimales Risk
- Validation: System funktioniert mit Real-Execution

**Stage 4: Live-Full (Gradual Rollout)**
- Schrittweise Erhöhung des Capitals
- +10% Capital pro Woche (wenn keine Issues)
- Full Rollout nach 10 Wochen (wenn erfolgreich)

**🚨 ABORT-Criteria:**
- Jeglicher Unintended-Trading-HALT
- VaR-Model-Failure (systematische Fehler)
- Execution-Errors
- Manual Risk-Team Decision

---

## Dependencies & Prerequisites

### Technical Dependencies

| Phase | Dependencies | Installation |
|-------|-------------|--------------|
| Phase 1 | None (nur stdlib) | ✅ Ready |
| Phase 2 | `scipy`, `arch` | `pip install scipy arch` |
| Phase 3 | Live-Data-Feed | Existing |
| Phase 4 | `scikit-learn`, `xgboost` (optional) | `pip install scikit-learn xgboost` |
| Phase 5 | Live-Exchange-Integration | Existing |

### Team Prerequisites

- **Risk Analyst:** Validiert VaR-Models, interpretiert Backtesting-Results
- **Ops Engineer:** Implementiert Real-Time-Monitoring, Alert-System
- **Data Scientist:** (Phase 4) ML-basierte Limits

---

## Success Metrics

### Phase 1 (Multi-Asset VaR)
- [ ] Covariance-VaR implementiert
- [ ] Backtest-Validation: VaR-Models correlate (Historical vs Covariance r>0.8)
- [ ] 3 Multi-Asset-Strategien erfolgreich mit Correlation-Limits

### Phase 2 (Advanced Models)
- [ ] Student-t VaR implementiert
- [ ] GARCH VaR implementiert
- [ ] Kupiec-Test pass (Violation-Rate within expected range)

### Phase 3 (Paper-Trading)
- [ ] 30 Tage Paper-Trading erfolgreich
- [ ] VaR-Violation-Rate: 5% ± 2% (alpha=0.05)
- [ ] Manual Risk-Team Sign-off

### Phase 4 (Adaptive Limits)
- [ ] Regime-dependent Limits implementiert
- [ ] Backtest-Validation: Adaptive > Static (Sharpe-Ratio +10%)

### Phase 5 (Live-Trading)
- [ ] Stage 1-4 erfolgreich abgeschlossen
- [ ] Zero Unintended-HALTs in 3 Monaten
- [ ] Full Capital Rollout nach Validation

---

## Risk & Mitigation

### Risk 1: VaR-Model-Failure (Underestimation)

**Impact:** HIGH - Model unterschätzt Risk → Losses höher als erwartet

**Mitigation:**
- Multiple VaR-Models parallel (Historical, Parametric, GARCH)
- Conservative: Use Maximum of all Models
- Backtesting: Continuous Validation (Kupiec/Christoffersen)
- Safety-Gate: Paper-Trading Validation BEFORE Live

### Risk 2: Over-Constraining (Too Conservative)

**Impact:** MEDIUM - Zu enge Limits → Missed Opportunities

**Mitigation:**
- A/B-Testing: Compare Performance with/without Limits
- Adaptive Limits (Phase 4): Loosen in Low-Vol-Regimes
- Human Override: Risk-Team kann Limits temporär anpassen

### Risk 3: Implementation Bugs

**Impact:** HIGH - Trading HALT durch Bug (nicht durch echtes Risk)

**Mitigation:**
- Extensive Testing (96+ Tests in v1, 200+ in v2)
- Staged Rollout (Testnet → Paper → Micro → Full)
- Monitoring: Alert bei jeglichem HALT, Manual Review
- Rollback-Plan: Deactivate VaR-Limits within minutes

### Risk 4: Correlation-Breakdown (Crisis)

**Impact:** HIGH - Assets de-correlate in Crisis (diversification fails)

**Mitigation:**
- Stress-Testing: Correlation-Spike-Scenarios
- Dynamic Correlation-Window (shorter in High-Vol)
- Conservative: Assume higher correlations in Stress

---

## References

- **Risk Layer v1 Implementation:** `docs/risk_layer_v1.md`
- **Operator Guide:** `docs/risk/RISK_LAYER_V1_OPERATOR_GUIDE.md`
- **Tests:** `tests/risk/`
- **Literature:**
  - Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk*
  - McNeil, A.J., Frey, R., Embrechts, P. (2015). *Quantitative Risk Management*

---

## Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| **Phase 1:** Multi-Asset VaR | 6 weeks | Q1 2026 | Q1 2026 |
| **Phase 2:** Advanced Models | 8 weeks | Q1 2026 | Q2 2026 |
| **Phase 3:** Paper-Trading Validation | 8 weeks | Q2 2026 | Q2 2026 |
| **Phase 4:** Adaptive Limits | 10 weeks | Q2 2026 | Q3 2026 |
| **Phase 5:** Live-Trading Integration | 16 weeks | Q3 2026 | Q4 2026 |
| **TOTAL** | **~48 weeks** | Q1 2026 | Q4 2026 |

---

## Approval & Sign-off

| Role | Name | Sign-off | Date |
|------|------|----------|------|
| Risk Manager | TBD | ☐ | - |
| Head of Trading | TBD | ☐ | - |
| CTO | TBD | ☐ | - |

---

**Status:** DRAFT - Awaiting Review  
**Next:** Review Meeting → Approval → Phase 1 Kickoff
